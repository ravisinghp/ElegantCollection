import aiohttp
from datetime import datetime
from typing import List,Optional
from app.db.repositories.sharepoint_repo import SharepointRepo
import os,base64
import hashlib
from dotenv import load_dotenv
import logging
import re, json, io, PyPDF2, docx
from pptx import Presentation
from rapidfuzz import fuzz
from openai import OpenAI
from decimal import Decimal
from datetime import date, datetime
from fastapi import APIRouter, HTTPException,Query,Request
import pandas as pd
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
            
    @staticmethod
    def _generate_po_pdf(df, filename_prefix):
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        import io

        output = io.BytesIO()
        pdf = canvas.Canvas(output, pagesize=A4)

        width, height = A4
        x_start = 30
        y = height - 40

        # Header
        for col in df.columns:
            pdf.drawString(x_start, y, str(col))
            x_start += 100

        y -= 20
        x_start = 30

        # Rows
        for _, row in df.iterrows():
            for val in row:
                pdf.drawString(x_start, y, str(val))
                x_start += 100

            y -= 20
            x_start = 30

            if y < 40:
                pdf.showPage()
                y = height - 40

        pdf.save()
        output.seek(0)

        return (
            output,
            f"{filename_prefix}.pdf",
            "application/pdf"
        )

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
            
    #Fetching Total Numbers of Attachments on User Dashboard
    async def get_documents_analyzed_by_user_id(user_id: int, request: Request):
        try:
            return await SharepointRepo.fetch_documents_analyzed_by_user_id(user_id,  request)
        except Exception as e:
            return None

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
    
    EMPTY_PO = {
    "po_number": None,
    "customer_name": None,
    "vendor_number": None,
    "po_date": None,
    "delivery_date": None,
    "cancel_date": None,
    "gold_karat": None,
    "ec_style_number": None,
    "customer_style_number": None,
    "color": None,
    "quantity": None,
    "description": None,
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
    
    MANDATORY_FIELDS = ["po_number", "customer_name"]

    async def extract_po_fields(self, text: str) -> dict:
        regex_data = self.extract_po_fields_regex(text)
        # Check if mandatory fields are present
        if all(regex_data.get(f) for f in self.MANDATORY_FIELDS):
            return regex_data

        # Otherwise call LLM
        llm_data = await self.extract_po_fields_from_llm(text)

        # Merge: REGEX ALWAYS WINS
        final = regex_data.copy()
        for k, v in llm_data.items():
            if final.get(k) is None and v:
                final[k] = v

        return final if any(final.values()) else self.EMPTY_PO
    
    
    async def extract_po_fields_from_llm(self, text: str) -> dict:
        if not text or not text.strip():
            return self.EMPTY_PO

        if not re.search(r"(po|order|\d{3,})", text, re.IGNORECASE):
            return self.EMPTY_PO

        prompt = f"""
    Extract ONLY explicitly present values.
    Return null if missing.
    Never guess.

    Return JSON with keys:
    {self.PO_FIELD_NAMES}

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
                return self.EMPTY_PO

            data = json.loads(match.group())
            out = self.EMPTY_PO.copy()

            for f in self.PO_FIELD_NAMES:
                v = data.get(f)
                out[f] = v if v not in ["", None, "null", "N/A"] else None

            return out if any(out.values()) else self.EMPTY_PO

        except Exception:
            return self.EMPTY_PO
        
    def normalize_po_date_ddmmyyyy(self,date_str: Optional[str]) -> Optional[str]:
        """
        Converts LLM date output to DD-MM-YYYY string.
        Returns None if parsing fails.
        """
        if not date_str:
            return None

        date_str = date_str.strip()

        for fmt in ("%Y-%m-%d", "%m/%d/%y", "%d/%m/%y", "%d-%m-%Y", "%m-%d-%Y", "%y-%m-%d"):
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        return None

    def normalize_attachment_text(self,text: str) -> str:
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

    def extract_po_items(self,text: str):
            items = []

            for m in self.ITEM_REGEX.finditer(text):
                items.append({
                    "description": m.group("description").strip(),
                    "gold_karat": re.search(r"\d{2}", m.group("material")).group(),
                    "quantity": int(m.group("quantity")),
                    "delivery_date": m.group("delivery_date")
                })

            return items


    async def extract_po_header(self,text: str):
        return await self.extract_po_fields(text)
    
    
    def extract_relative_folder_path(self, graph_path: str) -> str:
        """
        Converts:
        /drives/{id}/root:/Elegant Collection Software/SubFolder
        → Elegant Collection Software/SubFolder
        """
        if not graph_path:
            return ""

        # Everything after 'root:/'
        if "root:/" in graph_path:
            return graph_path.split("root:/", 1)[1]

        return graph_path


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
                        
                        parent_path = f.get("parentReference", {}).get("path", "")
                        folder_name = self.extract_relative_folder_path(parent_path)

                        await self.sp_repo.save_sharepoint_file(
                            user_id=user_id,
                            file_name=f["name"],
                            file_type=f["file"]["mimeType"],
                            file_path=f["webUrl"],
                            file_size=f.get("size", 0),
                            folder_name=folder_name,
                            uploaded_on=self.graph_datetime_to_mysql(f["createdDateTime"]),
                            file_hash=h,
                            created_by=user_id,
                        )

                        po = await self.extract_po_fields(text)
                        if any(po.values()):
                            await self.sp_repo.insert_sharepoint_po_details(
                                user_id=user_id,
                                po_number=po.get("po_number"),
                                customer_name=po.get("customer_name"),
                                vendor_number=po.get("vendor_number"),
                                po_date=self.normalize_po_date_ddmmyyyy(po.get("po_date")),
                                delivery_date=po.get("delivery_date"),
                                cancel_date=self.normalize_po_date_ddmmyyyy(po.get("cancel_date")),
                                gold_karat=po.get("gold_karat"),
                                ec_style_number=po.get("ec_style_number"),
                                customer_style_number=po.get("customer_style_number"),
                                color=po.get("color"),
                                quantity=po.get("quantity"),
                                description=po.get("description"),
                                created_by=user_id,
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
        
    #--------------------------data comparison logic start--------------------------#
    # -------------------------- NORMALIZATION -------------------------- #
    def normalize(self, value, field=None):
        if value is None:
            return ""

        text = str(value).strip().lower()
        field = (field or "").strip().lower()

        # ------------------ GOLD KARAT / GOLD LOCK / KT ------------------ #
        if field in ("gold_karat", "gold_lock", "kt"):
            # unify 24, 24k, 24 kt, 24ct, 24 carat
            text = re.sub(r"[^\d]", "", text)  # remove letters, spaces
            return text

        # ------------------ QUANTITY ------------------ #
        if field == "quantity":
            nums = re.findall(r"\d+", text)
            return nums[0] if nums else ""

        # ------------------ DATE FIELDS ------------------ #
        if field in ("po_date", "delivery_date", "cancel_date"):
            if isinstance(value, (date, datetime)):
                return value.strftime("%Y-%m-%d")
            text = re.sub(r"[/.]", "-", text)
            m = re.search(r"\d{4}-\d{1,2}-\d{1,2}", text)
            if m:
                y, mth, d = m.group().split("-")
                return f"{int(y):04d}-{int(mth):02d}-{int(d):02d}"
            return ""

        # ------------------ TEXT FIELDS ------------------ #
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text)

        # handle common abbreviations
        replacements = {
            "pvt": "private",
            "ltd": "limited",
            "co": "company",
            "corp": "corporation",
        }
        for k, v in replacements.items():
            text = re.sub(rf"\b{k}\b", v, text)

        return text.strip()


    # -------------------------- CUSTOMER NAME CLEANER -------------------------- #
    def clean_customer_name(self, name):
        text = self.normalize(name, "customer_name")
        # Remove common suffixes to avoid mismatch
        text = re.sub(r"\b(private limited|private|limited|ltd|co|corporation)\b", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()


    # -------------------------- PO KEY -------------------------- #
    def build_po_key(self, po: dict) -> tuple:
        return (
            self.clean_customer_name(po.get("customer_name")),
            self.normalize(po.get("po_number"), "po_number"),
        )


    # -------------------------- JSON SAFE -------------------------- #
    def make_json_safe(obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, bytes):
            try:
                return obj.decode("utf-8")
            except UnicodeDecodeError:
                return base64.b64encode(obj).decode("utf-8")
        return obj


    # -------------------------- CANDIDATE SYSTEM PO SEARCH -------------------------- #
    def candidate_system_pos(self,scanned, system_pos):
        scanned_cust = self.clean_customer_name(scanned.get("customer_name"))
        scanned_po = self.normalize(scanned.get("po_number"), "po_number")

        candidates = []
        for sys in system_pos:
            if not sys.get("customer_name") or not sys.get("po_number"):
                continue

            cust_sim = fuzz.partial_ratio(scanned_cust, self.clean_customer_name(sys["customer_name"]))
            po_sim = fuzz.partial_ratio(scanned_po, self.normalize(sys["po_number"], "po_number"))

            if po_sim >= 70 or cust_sim >= 80:
                candidates.append(sys)
        return candidates[:5]


    # -------------------------- FIELDS TO COMPARE -------------------------- #
    FIELDS_TO_COMPARE = [
        "customer_name", "vendor_number", "po_date", "po_number",
        "delivery_date", "cancel_date", "gold_lock", "ec_style_number",
        "customer_style_number", "kt", "color", "quantity", "description"
    ]


    def compare_po_fields(self,scanned, system):
        mismatches = []
        for field in self.FIELDS_TO_COMPARE:
            s_val = scanned.get(field)
            sys_val = system.get(field)
            # ------------------ SPECIAL HANDLING ------------------ #
            if field == "customer_name":
                s_val = self.clean_customer_name(s_val)
                sys_val = self.clean_customer_name(sys_val)
            elif field in ("gold_karat", "gold_lock", "kt"):
                s_val = self.normalize(s_val, "gold_karat")
                sys_val = self.normalize(sys_val, "gold_karat")
            else:
                s_val = self.normalize(s_val, field)
                sys_val = self.normalize(sys_val, field)

            if s_val != sys_val:
                mismatches.append({
                    "field": field,
                    "scanned": scanned.get(field),
                    "system": system.get(field)
                })

        return mismatches

    # -------------------------- LLM FALLBACK -------------------------- #
    async def llm_fallback_match(self,scanned_po, candidates):
        safe_scanned = {k: self.make_json_safe(v) for k, v in scanned_po.items()}
        safe_candidates = [{k: self.make_json_safe(v) for k, v in c.items()} for c in candidates]

        prompt = f"""
    You are a PO reconciliation engine.

    Task: Match a scanned PO to one of the system POs.

    Rules:
    1. PO Number is strongest signal.
    2. Customer Name: handle abbreviations, typos, word order.
    3. Gold Karat / Gold Lock / Kt differences are ignored.
    4. Quantity units may differ.
    5. Date fields normalized to YYYY-MM-DD.
    6. Color & Description: ignore word order, minor typos.
    7. Respond ONLY in JSON:
    {{ "matched_index": number | null, "confidence": 0.0-1.0 }}

    Scanned PO:
    {json.dumps(safe_scanned, indent=2)}

    System PO Candidates:
    {json.dumps(safe_candidates, indent=2)}
    """
        resp = openai_client.chat.completions.create(
            model="gpt-4.1-mini",
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r"^```json|```$", "", raw, flags=re.IGNORECASE).strip()
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return None
        result = json.loads(match.group())
        if result.get("matched_index") is None or result.get("confidence", 0) < 0.85:
            return None
        idx = result["matched_index"]
        return candidates[idx] if 0 <= idx < len(candidates) else None


    # -------------------------- MAIN SERVICE -------------------------- #
    async def generate_sharepoint_missing_po_report_service(self, user_id: int):
        scanned_pos = await self.sp_repo.get_all_sharepoint_po_details()
        system_pos = await self.sp_repo.get_all_system_po_details()

        system_map = {
            self.build_po_key(po): po
            for po in system_pos
            if po.get("customer_name") and po.get("po_number")
        }

        existing_mismatches = await self.sp_repo.get_all_sharepoint_mismatches()
        existing_keys = {
            (m["sharepoint_po_det_id"], m["system_po_id"], m["mismatch_attribute"])
            for m in existing_mismatches
        }

        llm_cache = {}

        for scanned in scanned_pos:
            if not scanned.get("customer_name") or not scanned.get("po_number"):
                continue

            scanned_key = self.build_po_key(scanned)
            system_po = system_map.get(scanned_key)

            # ------------------ USE FUZZY / LLM MATCH ------------------ #
            if not system_po:
                if scanned_key not in llm_cache:
                    candidates = self.candidate_system_pos(scanned, system_pos)
                    # Call LLM fallback if needed
                    if candidates:
                        system_po = await self.llm_fallback_match(scanned, candidates)
                    llm_cache[scanned_key] = system_po
                else:
                    system_po = llm_cache[scanned_key]

            # ------------------ MARK PO AS MISSING ------------------ #
            if not system_po:
                exists = await self.sp_repo.get_existing_sharepoint_po_missing(sharepoint_po_det_id=scanned["sharepoint_po_det_id"])
                if not exists:
                    await self.sp_repo.insert_sharepoint_po_missing(
                        sharepoint_po_det_id=scanned["sharepoint_po_det_id"],
                        user_id=user_id,
                        system_po_id=None,
                        attribute="po_missing",
                        system_value="",
                        scanned_value=scanned.get("po_number"),
                        comment="PO not found"
                    )
                continue

            # ------------------ COMPARE FIELDS ------------------ #
            mismatches = self.compare_po_fields(scanned, system_po)
            for m in mismatches:
                key = (
                    scanned["sharepoint_po_det_id"],
                    system_po["system_po_id"],
                    m["field"]
                )
                if key in existing_keys:
                    continue

                await self.sp_repo.insert_sharepoint_mismatch(
                    sharepoint_po_det_id=scanned["sharepoint_po_det_id"],
                    user_id=user_id,
                    system_po_id=system_po["system_po_id"],
                    field=m["field"],
                    system_value=str(m["system"]),
                    scanned_value=str(m["scanned"]),
                    comment=f"{m['field']} mismatch"
                )
                existing_keys.add(key)

        return {
            "status": "success",
            "message": "PO missing & mismatch report generated successfully"
        }
    # --------------------------data comparison logic end--------------------------#
    
    
    
    #---------------------------Table Data ----------------------------
    async def missing_po_data_fetch(request: Request, frontendRequest):
        data = await SharepointRepo.fetch_missing_po_data(request, frontendRequest)
        # FIX: Return empty list if None, and return the LIST directly (no wrapper object)
        return data if data else []
            
    async def mismatch_po_data_fetch(request: Request, frontendRequest):
        data = await SharepointRepo.fetch_mismatch_po_data(request, frontendRequest)
        return data if data else []
            
    async def matched_po_data_fetch(request: Request, frontendRequest):
        data = await SharepointRepo.fetch_matched_po_data(request, frontendRequest)
        return data if data else []
    
    
    #Download Missing Report and Mismatch Report
    async def download_sharepoint_missing_po_report(
        request: Request,
        user_id: int,
        role_id: int,
        format: str
    ):
        data = await SharepointRepo.download_sharepoint_missing_po_report(request, user_id, role_id)

        if not data:
            raise HTTPException(status_code=404, detail="No missing PO data available")

        df = pd.DataFrame(data)
        filename_prefix = "po_missing_report"

        if format == "excel":
            output = io.BytesIO()
            df.to_excel(output, index=False)
            output.seek(0)

            return (
                output,
                f"{filename_prefix}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        elif format == "pdf":
            return SharepointService._generate_po_pdf(df, filename_prefix)

        else:
            raise HTTPException(status_code=400, detail="Invalid file format")

    async def download_sharepoint_mismatch_po_report(
        request: Request,
        user_id: int,
        role_id: int,
        format: str
    ):
        data = await SharepointRepo.download_sharepoint_mismatch_po_report(request, user_id, role_id)

        if not data:
            raise HTTPException(status_code=404, detail="No mismatch PO data available")

        df = pd.DataFrame(data)
        filename_prefix = "po_mismatch_report"

        if format == "excel":
            output = io.BytesIO()
            df.to_excel(output, index=False)
            output.seek(0)

            return (
                output,
                f"{filename_prefix}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        elif format == "pdf":
            return SharepointService._generate_po_pdf(df, filename_prefix)

        else:
            raise HTTPException(status_code=400, detail="Invalid file format")
        
    # #Last Sync On Dashboard(Sharepoint)
    async def get_last_sync_by_user_id(user_id: int,role_id: int,request: Request):
        try:
            last_sync_data = await SharepointRepo.get_last_sync_by_user_id(user_id,role_id,request)
            return last_sync_data
        except Exception as e:
            raise Exception(f"Error fetching last sync data: {str(e)}")


   