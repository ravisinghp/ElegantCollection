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


    # ---------------- FETCH DRIVE FILES ---------------- #
    async def fetch_drive_files(
        self,
        access_token: str,
        drive_id: str,
        folder_path: str = "",
        from_date: str = None,
        to_date: str = None,
    ) -> List[dict]:

        headers = {"Authorization": f"Bearer {access_token}"}
        collected_files = []

        async def walk(path: str):
            url = f"{GRAPH_API}/drives/{drive_id}/root"
            if path:
                url += f":/{path}:/children"
            else:
                url += "/children"

            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        logger.error(f"Failed to fetch files: {resp.status} | {text}")
                        return

                    data = await resp.json()

            for item in data.get("value", []):
                # FILE
                if "file" in item:
                    collected_files.append(item)

                # FOLDER → RECURSE
                elif "folder" in item:
                    sub_path = f"{path}/{item['name']}" if path else item["name"]
                    await walk(sub_path)

        await walk(folder_path)

        # ---------- DATE FILTER ----------
        if from_date or to_date:
            from_dt = datetime.fromisoformat(from_date) if from_date else None
            to_dt = datetime.fromisoformat(to_date) if to_date else None

            filtered = []
            for f in collected_files:
                created_dt = datetime.fromisoformat(f["createdDateTime"][:19])
                if from_dt and created_dt < from_dt:
                    continue
                if to_dt and created_dt > to_dt:
                    continue
                filtered.append(f)

            collected_files = filtered

        return collected_files

    # ---------------- UTILS ---------------- #
    @staticmethod
    def graph_datetime_to_mysql(dt_str: str | None) -> str | None:
        if not dt_str:
            return None
        return datetime.fromisoformat(
            dt_str.replace("Z", "+00:00")
        ).strftime("%Y-%m-%d %H:%M:%S")

    # ---------------- FILE HASHING ---------------- #
    @staticmethod
    async def generate_file_hash(file_bytes: bytes) -> str:
        return hashlib.sha256(file_bytes).hexdigest()

    # ---------------- TEXT EXTRACTION ---------------- #
    @staticmethod
    def extract_text_from_bytes(content_bytes: bytes, filename: str, content_type: str) -> str | None:
        try:
            ext = filename.lower()
            ct = content_type.lower()

            if ct.startswith("text/") or ext.endswith((".txt", ".csv", ".log", ".md")):
                return content_bytes.decode("utf-8", errors="ignore")

            if ct == "application/pdf" or ext.endswith(".pdf"):
                reader = PyPDF2.PdfReader(io.BytesIO(content_bytes))
                return " ".join(p.extract_text() or "" for p in reader.pages)

            if ct in (
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword",
            ) or ext.endswith((".docx", ".doc")):
                doc = docx.Document(io.BytesIO(content_bytes))
                return " ".join(p.text for p in doc.paragraphs)

            if ct in (
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "application/vnd.ms-powerpoint",
            ) or ext.endswith((".pptx", ".ppt")):
                prs = Presentation(io.BytesIO(content_bytes))
                return " ".join(
                    s.text for slide in prs.slides for s in slide.shapes if hasattr(s, "text")
                )
        except Exception:
            return None

        return None

    # ---------------- KEYWORD DETECTION ---------------- #
    @staticmethod
    def normalize_keyword(k: str) -> str:
        return re.sub(r"\s+", " ", k.strip().lower())

    # ---------------- KEYWORD DETECTION ---------------- #
    async def detect_keywords(self, text: str, db_keywords: list[str]):
        if not text:
            return [], None

        text_l = text.lower()
        keywords = [self.normalize_keyword(k) for k in db_keywords]

        hits = []

        for k in keywords:
            if k in text_l:
                hits.append(k)

        if hits:
            return hits, "EXACT"

        for k in keywords:
            pat = r"\b" + re.escape(k).replace(r"\ ", r"\s*") + r"\b"
            if re.search(pat, text_l, re.IGNORECASE):
                hits.append(k)

        if hits:
            return hits, "REGEX"

        for k in keywords:
            if fuzz.partial_ratio(k, text_l) >= 85:
                hits.append(k)

        if hits:
            return hits, "FUZZY"

        return [], None

    # ---------------- PO EXTRACTION ---------------- #
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

    EMPTY_PO = {k: None for k in PO_FIELD_NAMES}

    
    #--------------------Regex-----------------------------
    PO_REGEX_PATTERNS = {

        # ---------------- PO NUMBER ----------------
        "po_number": [
            r"(?:po_number|po_no)\s*:\s*(PO[\w\-_/]+)",
            r"(?:po\s*number|po\s*no|po#|p\.o\.|purchase\s*order|po)\s*[:\-]?\s*(PO[\w\-_/]+)",
            r"\b(PO[\s\-_:]*[0-9]{1,}[A-Z0-9\/_.\-]*)",
            r"(?:po\s*number|po\s*no|po#|p\.o\.|purchase\s*order)\s*[:\-]?\s*(PO[\- ]?[A-Z0-9\/_.\-]+)",
            # --------- allow any prefix like JPO, SPO, etc. ----------
            r"(?:po\s*number|po\s*no|po#|p\.o\.|purchase\s*order)\s*[:\-]?\s*([A-Z]{1,5}-\d{4,}-\d+)"
        ],

        # ---------------- CUSTOMER NAME ----------------
        "customer_name": [
            r"(?:customer\s*name|customer|buyer|client)\s*[:\-]?\s*([A-Za-z][A-Za-z\s&\.]+?)"
            r"(?=\s+(?:vendor|vendor_no|vendor_number|supplier|po|delivery|cancel|date|quantity|gold|color|description)\b|$)",
            r"customer_name\s*:\s*([A-Za-z][A-Za-z\s&\.]+?)"
            r"(?=\s+(?:vendor|vendor_no|vendor_number|supplier|po|delivery|cancel|date|quantity|gold|color|description)\b|$)"
        ],

        # ---------------- VENDOR NUMBER ----------------
        "vendor_number": [
            r"(?:vendor_number|vendor_no)\s*:\s*([A-Za-z0-9\-_]+)",
            r"(?:vendor\s*number|vendor\s*no|supplier\s*code)\s*[:\-]?\s*([A-Za-z0-9\-_]+)",
            r"\bvendor\b\s*[:\-]?\s*([A-Za-z0-9\-_]+)"
        ],

        # ---------------- PO DATE ----------------
        "po_date": [
            r"(?:po\s*date|order\s*date|date)\s*[:\-]?\s*(\d{4}-\d{1,2}-\d{1,2})",
            r"po_date\s*:\s*(\d{4}-\d{2}-\d{2})",
            # --------- allow 'Date:' label ----------
            r"date\s*[:\-]?\s*(\d{4}-\d{2}-\d{2})"
        ],

        # ---------------- DELIVERY DATE ----------------
        "delivery_date": [
            r"(?:delivery\s*date|expected\s*delivery)\s*[:\-]?\s*(\d{4}-\d{2}-\d{2})",
            r"delivery_date\s*:\s*(\d{4}-\d{2}-\d{2})",
            # --------- allow inline in item row ----------
            r"\b(\d{4}-\d{2}-\d{2})\b"
        ],

        # ---------------- CANCEL DATE ----------------
        "cancel_date": [
            r"(?:cancel\s*date|cancellation\s*date)\s*[:\-]?\s*(\d{4}-\d{1,2}-\d{1,2})",
            r"cancel_date\s*:\s*(\d{4}-\d{2}-\d{2})"
        ],

        # ---------------- EC STYLE NUMBER ----------------
        "ec_style_number": [
            r"(?:ec\s*style\s*number|ec\s*style|ec\s*no)\s*[:\-]?\s*([A-Z0-9\-]+)",
            r"(?:ec_style_number|ec_style_no)\s*:\s*([A-Z0-9\-]+)"
        ],

        # ---------------- CUSTOMER STYLE NUMBER ----------------
        "customer_style_number": [
            r"(?:customer\s*style\s*number|customer\s*style|cust\s*style)\s*[:\-]?\s*([A-Z0-9\-]+)",
            r"(?:customer_style_number|customer_style_no)\s*:\s*([A-Z0-9\-]+)"
        ],

        # ---------------- QUANTITY ----------------
        "quantity": [
            r"(?:qty|quantity|pcs|pieces)\s*[:\-]?\s*(\d+)",
            r"\b(\d+)\s*(?:pcs|pieces|nos)\b"
        ],

        # ---------------- GOLD KARAT ----------------
        "gold_karat": [
            r"(?:gold\s*karat|karat|kt|gold\s*purity)\s*[:\-]?\s*(\d{1,2})(?:\s*K)?",
            r"\b(24|22|18|14|10)\s*K?\b"
        ],

        # ---------------- COLOR ----------------
        "color": [
            r"(?:color|colour)\s*[:\-]?\s*([A-Za-z]+(?:\s+[A-Za-z]+)*)"
            r"(?=\s+(?:quantity|gold|karat|description|remarks|details)\s*:|$)",
            r"color\s*:\s*([A-Za-z\s]+)"
        ],

        # ---------------- DESCRIPTION ----------------
        "description": [
            r"(?:description|remarks|details|order\s*details)\s*[:\-]?\s*(.+)$",
            r"description\s*:\s*(.+)$"
            # --------- capture item description in item rows ----------
            r"([A-Za-z\s]+)\s*-\s*([A-Za-z\s]+)"
        ]
    }

    @staticmethod
    def normalize_text(text: str) -> str:
        text = re.sub(r"\s+", " ", text.replace("\n", " "))
        return text.strip()

    # ---------------- PO FIELD EXTRACTION ---------------- #
    @staticmethod
    def extract_po_fields_regex(text: str) -> dict:
        out = SharepointService.EMPTY_PO.copy()
        text = SharepointService.normalize_text(text)

        for field, patterns in SharepointService.PO_REGEX_PATTERNS.items():
            for pat in patterns:
                m = re.search(pat, text, re.IGNORECASE)
                if m:
                    out[field] = m.group(1) if m.groups() else m.group(0)
                    break

        return out

    async def extract_po_fields(self, text: str) -> dict:
        regex_data = self.extract_po_fields_regex(text)
        return regex_data if any(regex_data.values()) else self.EMPTY_PO

    # ---------------- MAIN FLOW ---------------- #
    async def fetch_and_save_sharepoint_files(
        self,
        access_token: str,
        user_id: int,
        folders: list[str],
        from_date: str,
        to_date: str,
    ):
        saved, failed = [], []

        site_id = await self.get_site_id(access_token)
        drive_id = await self.get_drive_id(access_token, site_id)
        keywords = await self.sp_repo.fetch_keywords()

        async with aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {access_token}"}
        ) as session:

            for folder in folders or [""]:
                files = await self.fetch_drive_files(
                    access_token, drive_id, folder, from_date, to_date
                )

                for f in files:
                    try:
                        url = f.get("@microsoft.graph.downloadUrl")
                        if not url:
                            continue

                        async with session.get(url) as r:
                            data = await r.read()

                        h = await self.generate_file_hash(data)
                        if await self.sp_repo.file_exists(user_id, h):
                            continue

                        text = self.extract_text_from_bytes(
                            data, f["name"], f["file"]["mimeType"]
                        )
                        if not text:
                            continue

                        kw, _ = await self.detect_keywords(text, keywords)
                        if not kw:
                            continue

                        await self.sp_repo.save_sharepoint_file(
                            user_id=user_id,
                            file_name=f["name"],
                            file_type=f["file"]["mimeType"],
                            file_path=f["webUrl"],
                            file_size=f.get("size", 0),
                            folder_name=f.get("parentReference", {}).get("path", ""),
                            uploaded_on=self.graph_datetime_to_mysql(f["createdDateTime"]),
                            file_hash=h,
                            created_by=user_id,
                        )

                        po = await self.extract_po_fields(text)
                        if any(po.values()):
                            await self.sp_repo.insert_po_details_from_sharepoint(
                                user_id=user_id, po_data=po, folder_name=folder
                            )

                        saved.append(f["name"])

                    except Exception as e:
                        failed.append({"file": f.get("name"), "error": str(e)})

        return {
            "saved_count": len(saved),
            "failed_count": len(failed),
            "saved_files": saved,
            "failed_files": failed,
        }