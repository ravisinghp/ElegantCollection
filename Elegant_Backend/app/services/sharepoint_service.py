import aiohttp
from datetime import datetime
from typing import List
from app.db.repositories.sharepoint_repo import SharepointRepo
import os
import hashlib
from dotenv import load_dotenv
import logging
import re, json, io, PyPDF2, docx
from pptx import Presentation
from rapidfuzz import fuzz
from openai import OpenAI

# Load env
load_dotenv()
GRAPH_API = os.getenv("GRAPH_API")

# -------------- SharePoint Config start-------------- #
SHAREPOINT_SITE_URL = os.getenv("SHAREPOINT_SITE_URL")
SHAREPOINT_SITE_PATH = os.getenv("SHAREPOINT_SITE_PATH")
LIBRARY_NAME = os.getenv("LIBRARY_NAME")
# ------------- SharePoint Config end----------------- #

#---------------OpenAI Client------------------
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
#----------OpenAI Client end ------------------

logger = logging.getLogger("sharepoint_service")
logger.setLevel(logging.INFO)


class SharepointService:
    def __init__(self, sp_repo: SharepointRepo):
        self.sp_repo = sp_repo

    # ---------------- GET SITE ID ---------------- #
    async def get_site_id(self, access_token: str):
        url = f"{GRAPH_API}/sites/{SHAREPOINT_SITE_URL}:{SHAREPOINT_SITE_PATH}"
        headers = {"Authorization": f"Bearer {access_token}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(f"Failed to get site ID: {resp.status} | {text}")
                    raise Exception(f"Failed to get site ID: {resp.status}")
                data = await resp.json()
                return data.get("id")

    # ---------------- GET DRIVE ID ---------------- #
    async def get_drive_id(self, access_token: str, site_id: str):
        headers = {"Authorization": f"Bearer {access_token}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{GRAPH_API}/sites/{site_id}/drive", headers=headers) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(f"Failed to get drive ID: {resp.status} | {text}")
                    raise Exception(f"Failed to get drive ID: {resp.status}")
                data = await resp.json()
                return data.get("id")

    # ---------------- LIST ALL FOLDERS RECURSIVELY ---------------- #
    async def list_folders_recursive(self, access_token: str, drive_id: str, folder_path: str = ""):
        folders = []

        async def fetch_children(path: str, parent_path: str = ""):
            url = f"{GRAPH_API}/drives/{drive_id}/root"
            if path:
                url += f":/{path}:/children"
            else:
                url += "/children"

            headers = {"Authorization": f"Bearer {access_token}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        logger.error(f"Failed to fetch folders: {resp.status} | {text}")
                        return
                    data = await resp.json()
                    for item in data.get("value", []):
                        if "folder" in item:
                            folder_name = item.get("name")
                            full_path = f"{parent_path}/{folder_name}" if parent_path else folder_name
                            folders.append({"id": item.get("id"), "name": folder_name, "path": full_path})
                            await fetch_children(full_path, full_path)

        await fetch_children(folder_path)
        return folders

    # ---------------- FETCH FILES ---------------- #
    async def fetch_drive_files(self, access_token: str, drive_id: str, folder_path: str = "",
                                from_date: str = None, to_date: str = None) -> List[dict]:
        url = f"{GRAPH_API}/drives/{drive_id}/root"
        if folder_path:
            url += f":/{folder_path}:/children"
        else:
            url += "/children"

        headers = {"Authorization": f"Bearer {access_token}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(f"Failed to fetch files: {resp.status} | {text}")
                    return []
                data = await resp.json()
                files = data.get("value", [])

        # Filter by date
        if from_date or to_date:
            from_dt = datetime.fromisoformat(from_date) if from_date else None
            to_dt = datetime.fromisoformat(to_date) if to_date else None
            filtered = []
            for f in files:
                created_dt = datetime.fromisoformat(f.get("createdDateTime")[:19])
                if from_dt and created_dt < from_dt:
                    continue
                if to_dt and created_dt > to_dt:
                    continue
                filtered.append(f)
            files = filtered

        return files

    # ---------------- FETCH & SAVE FILES ---------------- #
    @staticmethod
    def graph_datetime_to_mysql(dt_str: str | None) -> str | None:
        if not dt_str:
            return None
        try:
            if dt_str.endswith("Z"):
                dt_str = dt_str.replace("Z", "+00:00")
            return datetime.fromisoformat(dt_str).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return None

    @staticmethod
    async def generate_file_hash(file_bytes: bytes) -> str:
        sha256 = hashlib.sha256()
        sha256.update(file_bytes)
        return sha256.hexdigest()

    @staticmethod
    def extract_text_from_bytes(
        content_bytes: bytes,
        filename: str,
        content_type: str
    ) -> str | None:

        try:
            ext = (filename or "").lower()
            ct = (content_type or "").lower()

            if ct.startswith("text/") or ext.endswith((".txt", ".md", ".csv", ".log")):
                return content_bytes.decode("utf-8", errors="ignore")

            if ct == "application/pdf" or ext.endswith(".pdf"):
                reader = PyPDF2.PdfReader(io.BytesIO(content_bytes))
                return " ".join((p.extract_text() or "") for p in reader.pages)

            if ct in (
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword"
            ) or ext.endswith((".docx", ".doc")):
                document = docx.Document(io.BytesIO(content_bytes))
                return " ".join(p.text for p in document.paragraphs)

            if ct in (
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "application/vnd.ms-powerpoint"
            ) or ext.endswith((".pptx", ".ppt")):
                prs = Presentation(io.BytesIO(content_bytes))
                return " ".join(
                    shape.text
                    for slide in prs.slides
                    for shape in slide.shapes
                    if hasattr(shape, "text")
                )
        except Exception:
            return None

        return None

    @staticmethod
    def normalize_keyword(k: str) -> str:
        return re.sub(r"\s+", " ", k.strip().lower())

    @staticmethod
    async def openai_keyword_fallback(text: str, keywords: list[str]) -> list[str]:
        prompt = f"""
        Match text to keyword names ONLY if clearly present.
        If unsure return [].

        KEYWORDS:
        {keywords}

        TEXT:
        {text}

        Return JSON array only.
        """
        try:
            resp = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = resp.choices[0].message.content.strip()
            match = re.search(r"\[.*\]", raw, re.DOTALL)
            return json.loads(match.group()) if match else []
        except Exception:
            return []

    async def detect_keywords(self, text: str, db_keywords: list[str]):
        if not text or not text.strip():
            return [], None

        text_l = text.lower()
        keywords = [self.normalize_keyword(k) for k in db_keywords]

        # ---------------- 1 EXACT MATCH ----------------
        for k in keywords:
            if k in text_l:
                return [k], "EXACT"

        # ---------------- 2 REGEX MATCH ----------------
        for k in keywords:
            pattern = r"\b" + re.escape(k).replace(r"\ ", r"\s*") + r"\b"
            if re.search(pattern, text_l, re.IGNORECASE):
                return [k], "REGEX"

        # ---------------- 3 FUZZY MATCH ----------------
        for k in keywords:
            if fuzz.partial_ratio(k, text_l) >= 85:
                return [k], "FUZZY"

        # ---------------- 4 OPENAI (LAST OPTION) ----------------
        ai_hits = await self.openai_keyword_fallback(text, keywords)
        if ai_hits:
            return ai_hits, "OPENAI"

        return [], None

    # ------------------- Extraction ------------------- #
    PO_FIELD_NAMES = [
        "po_number",
        "customer_name",
        "vendor_number",
        "po_date",
        "delivery_date",
        "cancel_date",
        "ec_style_number",
        "customer_style_number",
        "quantity",
        "gold_karat",
        "color",
        "description",
    ]

    EMPTY_PO = {field: None for field in PO_FIELD_NAMES}

    
    async def extract_po_fields_from_llm(text: str) -> dict:
        if not text or not text.strip():
            return SharepointService.EMPTY_PO

        if not re.search(r"(po|order|\d{3,})", text, re.IGNORECASE):
            return SharepointService.EMPTY_PO

        prompt = f"""
        Extract ONLY explicitly present values.
        Return null if missing.
        Never guess.

        Return JSON with keys:
        {SharepointService.PO_FIELD_NAMES}

        TEXT:
        {text}
        """
        try:
            resp = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = resp.choices[0].message.content
            match = re.search(r"\{{.*\}}", raw, re.DOTALL)
            if not match:
                return SharepointService.EMPTY_PO

            data = json.loads(match.group())
            out = SharepointService.EMPTY_PO.copy()
            for f in SharepointService.PO_FIELD_NAMES:
                v = data.get(f)
                out[f] = v if v not in ["", None, "null", "N/A"] else None

            return out if any(out.values()) else SharepointService.EMPTY_PO

        except Exception:
            return SharepointService.EMPTY_PO
        

    ITEM_REGEX = re.compile(
        r"""
        (?P<description>[A-Za-z\s\-]+?)
        \s+
        (?P<material>\d{2}K\s+Gold(?:\s*\+\s*Diamond)?)
        \s+
        (?P<quantity>\d+)
        \s+
        (?P<delivery_date>\d{4}-\d{2}-\d{2})
        """,
        re.IGNORECASE | re.VERBOSE
    )


    def extract_po_items(text: str):
        items = []

        for m in SharepointService.ITEM_REGEX.finditer(text):
            items.append({
                "description": m.group("description").strip(),
                "gold_karat": re.search(r"\d{2}", m.group("material")).group(),
                "quantity": int(m.group("quantity")),
                "delivery_date": m.group("delivery_date")
            })

        return items


    MANDATORY_FIELDS = ["po_number", "customer_name"]


    async def extract_po_fields(text: str) -> dict:
        regex_data = SharepointService.extract_po_fields_regex(text)

        # Check if mandatory fields are present
        if all(regex_data.get(f) for f in SharepointService.MANDATORY_FIELDS):
            return regex_data

        # Otherwise call LLM
        llm_data = await SharepointService.extract_po_fields_from_llm(text)

        # Merge: REGEX ALWAYS WINS
        final = regex_data.copy()
        for k, v in llm_data.items():
            if final.get(k) is None and v:
                final[k] = v

        return final if any(final.values()) else SharepointService.EMPTY_PO

    async def extract_po_header(text: str):
        return await SharepointService.extract_po_fields(text)
    

    def normalize_attachment_text(text: str) -> str:
        if not text:
            return ""

        # normalize OCR dashes
        text = text.replace("\u2013", "-").replace("\u2014", "-")

        # fix spaced hyphens in PO numbers and dates
        text = re.sub(r"\s*-\s*", "-", text)

        # fix broken multiline item descriptions
        text = re.sub(r"(\w+)\s*-\s*\n\s*(\w+)", r"\1 - \2", text)

        # fix broken multiline item descriptions
        text = re.sub(r"([A-Za-z])\s*-\s*\n\s*([A-Za-z])", r"\1 - \2", text)

        # CRITICAL: flatten remaining newlines
        text = re.sub(r"\n", " ", text)

        # normalize dates like 2025-07-06
        text = re.sub(
            r"(\d{4})-(\d{1,2})-(\d{1,2})",
            lambda m: f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}",
            text,
        )

        # collapse extra spaces
        text = re.sub(r"[ \t]+", " ", text)

        # clean blank lines
        text = re.sub(r"\n\s*\n", "\n", text)

        return text.strip()


    # -------------------- fetch_and_save_sharepoint_files -------------------- #
    async def fetch_and_save_sharepoint_files(
        self,
        access_token: str,
        user_id: int,
        folders: list[str],
        from_date: str,
        to_date: str,
    ):
        headers = {"Authorization": f"Bearer {access_token}"}
        saved_files = []
        failed_files = []

        try:
            site_id = await self.get_site_id(access_token)
            drive_id = await self.get_drive_id(access_token, site_id)

            keywords = await self.sp_repo.fetch_keywords()
            folders_to_process = folders or [""]

            async with aiohttp.ClientSession(headers=headers) as session:

                for folder_path in folders_to_process:
                    files = await self.fetch_drive_files(
                        access_token, drive_id, folder_path, from_date, to_date
                    )

                    for f in files:
                        file_name = f.get("name")
                        mime_type = f.get("file", {}).get("mimeType", "")
                        download_url = f.get("@microsoft.graph.downloadUrl")

                        try:
                            if not download_url:
                                continue

                            # -------- Download file --------
                            async with session.get(download_url) as resp:
                                if resp.status != 200:
                                    raise Exception("Download failed")
                                file_bytes = await resp.read()

                            # -------- Hash & duplicate check --------
                            file_hash = await self.generate_file_hash(file_bytes)

                            if await self.sp_repo.file_exists(user_id, file_hash):
                                continue

                            # -------- Extract text --------
                            extracted_text = self.extract_text_from_bytes(file_bytes, file_name, mime_type)
                            if not extracted_text:
                                continue

                            # -------- Keyword check --------
                            matched_keywords, _ = await self.detect_keywords(extracted_text, keywords)
                            if not matched_keywords:
                                continue

                            # -------- Save SharePoint file --------
                            await self.sp_repo.save_sharepoint_file(
                                user_id=user_id,
                                file_name=file_name,
                                file_type=mime_type,
                                file_path=f.get("webUrl"),
                                file_size=f.get("size", 0),
                                folder_name=folder_path,
                                uploaded_on=self.graph_datetime_to_mysql(f.get("createdDateTime")),
                                file_hash=file_hash,
                                created_by=user_id,
                            )

                            # -------- PO extraction --------
                            normalized_text = SharepointService.normalize_attachment_text(extracted_text)
                            po_header = await SharepointService.extract_po_header(normalized_text)

                            if any(po_header.values()):
                                items = SharepointService.extract_po_items(normalized_text)

                                if not items:
                                    await self.sp_repo.insert_po_details_from_sharepoint(
                                        user_id=user_id,
                                        po_data=po_header,
                                        folder_name=folder_path,
                                    )
                                else:
                                    for item in items:
                                        merged = po_header | item
                                        await self.sp_repo.insert_po_details_from_sharepoint(
                                            user_id=user_id,
                                            po_data=merged,
                                            folder_name=folder_path,
                                        )

                            saved_files.append(file_name)

                        except Exception as e:
                            failed_files.append({"file": file_name, "reason": str(e)})

            return {
                "saved_count": len(saved_files),
                "failed_count": len(failed_files),
                "saved_files": saved_files,
                "failed_files": failed_files,
            }

        except Exception as e:
            logger.exception("SharePoint sync failed")
            raise Exception("SharePoint sync failed") from e
