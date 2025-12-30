
from dotenv import load_dotenv
import os, base64
import httpx
from urllib.parse import urlencode
import hashlib
import boto3
import json
from loguru import logger
import pytesseract
# from PIL import Image
# import cv2
# import numpy as np
from botocore.exceptions import BotoCoreError, ClientError
import shutil
import traceback
# import openpyxl
# import xlrd
from datetime import date, datetime
# Load the .env file
load_dotenv()
failed_url = os.getenv("failed_url")
success_url = os.getenv("success_url")
#----------------- outlook ------------------#
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
REDIRECT_URI = os.getenv("REDIRECT_URI")
GRAPH_API = os.getenv("GRAPH_API")
#---------------outlook end ----------------------#
#---------------Google---------------------------#
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
# TENANT_ID = os.getenv("TENANT_ID")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
GMAIL_API = os.getenv("GMAIL_API")

#---------------Google end-------------------------#

# --------- boto3 session for AWS Bedrock------
session = boto3.Session(
    aws_access_key_id=os.getenv("aws_access_key_id"),
    aws_secret_access_key=os.getenv("aws_secret_access_key"),
    region_name=os.getenv("region_name")  # Adjust as per your model access
)
client = session.client("bedrock-runtime")
# --------- boto3 session for AWS Bedrock------

from datetime import datetime, timezone,timedelta
import re
from typing import List, Dict, Any, Optional
import html
import io

import aiohttp, json
from datetime import datetime, timezone
from typing import List, Dict, Any
from pptx import Presentation  # for PPTX support
from fastapi.responses import RedirectResponse
try:
    # Optional import to avoid circular issues in other contexts
    from app.db.repositories.mails import MailsRepository
except Exception:
    MailsRepository = None  # type: ignore

try:
    import PyPDF2  # type: ignore
except Exception as e:
    print("PyPDF2 import failed:", e)
    PyPDF2 = None  # type: ignore

try:
    import docx  # python-docx
except Exception:
    docx = None  # type: ignore
import asyncio

# this code is used for outlook
# def get_auth_url():
#     return (
#         f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize?"
#         f"client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}"
#         f"&response_mode=query&scope=offline_access%20Mail.Read%20Mail.ReadWrite"
#         f"&prompt=login"   # ðŸ”‘ This forces login screen every time
#     )

def get_auth_url(provider: str):
    if provider == "outlook":
        return (
            f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize?"
            f"client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}"
            # f"&response_mode=query&scope=offline_access%20Mail.Read%20Mail.ReadWrite%20Calendars.Read"
            f"&response_mode=query&scope=offline_access%20Mail.Read"
            f"&prompt=login"   # ðŸ”‘ This forces login screen every time
        )
    elif provider == "google":
        params = {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/calendar.readonly https://www.googleapis.com/auth/userinfo.email openid",
            "access_type": "offline",
            "prompt": "consent"
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    else:
        raise ValueError("Invalid provider")


# async def exchange_code_for_token(code: str):
#     url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
#     data = {
#         'client_id': CLIENT_ID,
#         # 'scope': 'Mail.Read Mail.ReadWrite offline_access Calendars.Read Calendars.ReadWrite',
#         'scope': 'Mail.Read Mail.ReadWrite',
#         'code': code,
#         'redirect_uri': REDIRECT_URI,
#         'grant_type': 'authorization_code',
#         'client_secret': CLIENT_SECRET
#     }
#     timeout = httpx.Timeout(connect=10.0, read=30.0, write=30.0, pool=30.0)
#     async with httpx.AsyncClient(timeout=timeout) as client:
#         # response = await client.post(url, data=data)
#         headers = {
#             "Content-Type": "application/x-www-form-urlencoded"
#         }
#         response = await client.post(url, data=data, headers=headers)

#         token_json = response.json()
    
#     access_token = token_json.get("access_token")
#     if access_token:
#         # Redirect to frontend with token in query (or better, store in cookie or session)
#         return f"{success_url}?mail_token={access_token}"
#         # return f"http://localhost:3000//dashboard/user?mail_token={access_token}" # use in local system
#         #return f"http://139.144.4.191:3000//dashboard/user?mail_token={access_token}" # use in server
#     return {"error": "Token exchange failed"}

async def exchange_code_for_token(code: str):
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        'client_id': CLIENT_ID,
        'scope': 'offline_access Mail.Read',  # must match authorization URL
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code',
        'client_secret': CLIENT_SECRET
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, read=30.0)) as client:
        response = await client.post(url, data=data, headers=headers)
        token_json = response.json()

    if response.status_code != 200 or "access_token" not in token_json:
        return {"error": "Token exchange failed", "details": token_json}

    return {
        "access_token": token_json.get("access_token"),
        "refresh_token": token_json.get("refresh_token"),
        "expires_in": token_json.get("expires_in"),
        "url": f"{success_url}?mail_token={token_json.get('access_token')}"
    }


    
    access_token = token_json.get("access_token")
    if access_token:
        # Redirect to frontend with token in query (or better, store in cookie or session)
        # 1. Build the destination URL (your React route)
        # This points to: http://localhost:5173//dashboard/user?mail_token=...
        destination_url = f"{success_url}?mail_token={access_token}"
        
        # 2. Force the browser to go there
        # This loads your React app, and React Router will take over from there.
        return RedirectResponse(url=destination_url, status_code=303)
        # return f"http://localhost:3000//dashboard/user?mail_token={access_token}" # use in local system
        #return f"http://139.144.4.191:3000//dashboard/user?mail_token={access_token}" # use in server
    return {"error": "Token exchange failed"}
    
    
# this code is used to generate token for gmail(Google api)
async def exchange_code_for_token_for_gmail(code: str) -> dict:
        """Exchange auth code for access/refresh tokens"""
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient() as client:
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            resp = await client.post(token_url, data=data, headers=headers)
            return resp.json()


# this code is used to fetch email from google api
async def get_user_email(access_token: str) -> str | None:
        """Fetch user email from Google API"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            data = resp.json()
            return data.get("email")

###------------------This code is used to fetch folder names upto 200 folders------------------
async def fetch_all_folders(access_token: str) -> List[Dict[str, Any]]:
    headers = {"Authorization": f"Bearer {access_token}"}
    timeout = httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=30.0)

    folder_list = []
    url = f"{GRAPH_API}/me/mailFolders?$top=200&$expand=childFolders"

    async with httpx.AsyncClient(timeout=timeout) as client:
        while url:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()

            for folder in data.get("value", []):
                folder_list.append({
                    "id": folder.get("id"),
                    "name": folder.get("displayName")
                })

            # If Graph gives a nextLink, continue paging
            url = data.get("@odata.nextLink")

    return folder_list

# ------------------Email + Attachment Fetching + LLM keyword logic start ------------------ #
def strip_html_to_text(html_content: Optional[str]) -> str:
    if not html_content:
        return ""
    text = re.sub(r"<[^>]+>", " ", html_content)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def clean_email_body(body_text: str) -> str:
    if not body_text:
        return ""
    lines = body_text.split("\n")
    cleaned_lines: List[str] = []
    skip_line_starts = [
        r"^From:", r"^To:", r"^Cc:", r"^CC:", r"^BCC:", r"^Bcc:", r"^Sent:", r"^Subject:", r"^Date:",
        r"^Reply-To:", r"^Message-ID:", r"^X-.*?:", r"^Content-Type:", r"^Content-Transfer-Encoding:", r"^MIME-Version:",
        r"^Return-Path:", r"^Delivered-To:", r"^Received:", r"^On .* wrote:", r"^-----Original Message-----",
        r"^Microsoft Teams$", r"^Need help\?$", r"^Join the meeting now$", r"^Meeting ID:", r"^Passcode:",
        r"^For organisers:", r"^Meeting options$", r"^_{6,}$",
    ]
    url_re = re.compile(r"^(https?://|www\.)", re.IGNORECASE)
    skip_res = [re.compile(pat, re.IGNORECASE) for pat in skip_line_starts]
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if url_re.match(line):
            continue
        if any(rx.match(line) for rx in skip_res):
            continue
        cleaned_lines.append(line)
    cleaned_text = " ".join(cleaned_lines)
    return re.sub(r"\s+", " ", cleaned_text).strip() or body_text.strip()


def iso_to_date(iso_dt: Optional[str]) -> Optional[str]:
    if not iso_dt:
        return None
    return iso_dt[:10]


def collect_addresses_from_message(msg: Dict[str, Any], key: str) -> Optional[str]:
    out: List[str] = []
    for rec in msg.get(key, []) or []:
        address = (rec.get('emailAddress') or {}).get('address')
        if address:
            out.append(address)
    return ",".join(out) if out else None


def compute_file_hash(content: bytes) -> str:
    import hashlib
    return hashlib.sha256(content).hexdigest()


# ------------------- AWS Bedrock Keyword Extraction ------------------- #
def normalize_text(text: str) -> str:
    """
    Normalize text for PO and invoice parsing.
    - Lowercase everything
    - Keep alphanumerics, spaces, dots, colons, #, dashes, and slashes
    - Reduce multiple spaces to single space
    - Strip leading/trailing spaces
    """
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r'[^a-z0-9\.\-/:#\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()



# ---------------------- OCR Helper ---------------------- #
# Create Textract client from session
textract_client = session.client("textract")

def ocr_from_image_bytes(image_bytes: bytes) -> str:
    """
    Perform OCR using AWS Textract DetectDocumentText.
    Handles scanned and structured documents (POs, invoices, forms).
    """
    if not image_bytes:
        logger.warning("No image bytes provided for OCR.")
        return ""

    try:
        response = textract_client.detect_document_text(
            Document={"Bytes": image_bytes}
        )

        # Extract lines of text
        lines = [
            block["Text"]
            for block in response.get("Blocks", [])
            if block["BlockType"] == "LINE"
        ]

        extracted_text = "\n".join(lines).strip()
        logger.info(f"Textract OCR extracted {len(lines)} lines.")
        return extracted_text

    except (BotoCoreError, ClientError) as e:
        logger.error(f"AWS Textract OCR FAILED: {e}")
        return ""
    except Exception as e:
        logger.error(f"Unexpected error during OCR: {e}")
        return ""


# Usage example
# if __name__ == "__main__":
#     file_path = "po_image.jpg"
#     with open(file_path, "rb") as f:
#         img_bytes = f.read()

#     text = ocr_aws_textract(img_bytes)
#     print(text)
    
    

async def get_keywords_from_llm(text: str) -> list[str]:
    if not text or not text.strip():
        return []

    #Normalize text
    norm = normalize_text(text)
    tokens = norm.split()

    #PO detection
    if "po" in tokens:
        return ["PO#"]

    ROOT_KEYWORDS = [
        "PO#",
        "Customer name",
        "Vendor Number",
        "PO DATE",
        "Delivery date",
        "Cancel date",
        "Gold lock",
        "EC Style#",
        "Customer style #",
        "Kt",
        "Color",
        "Quantity",
        "Description"
    ]

    keyword_list = "\n".join(f"- {k}" for k in ROOT_KEYWORDS)

    prompt = f"""
You are an expert semantic keyword detector.

### TASK
Identify which ROOT KEYWORDS are present in meaning,
even if the exact words differ.

### HARD RULE
Any appearance of the standalone token "po" (example: po, po:, po., po#, p.o.)
ALWAYS maps to ROOT KEYWORD "PO#".

### ROOT KEYWORDS (allowed output ONLY)
{keyword_list}

### VARIATION MAPPING EXAMPLES
PO# → po number, po no, p.o., po#, po #, purchase order, purchase order number, po, p.o. number 
Customer name → customer, customer:, cust, customer name  
Vendor Number → vendor, vendor no, vend no, vendor number, Vendor #   
PO DATE → po date, order date, purchase order date, date:  
Delivery date → delivery date, expected delivery, est delivery  
Cancel date → cancel date, cancellation date  
Gold lock → gold lock, g lock  
EC Style# → ec style, e.c style, style ec  
Customer style # → customer style, cust style, style number, customer#
Kt → kt, k.t, karat  
Color → color, colour, clr  
Quantity → quantity, qty, qnty, pcs, pieces  
Description → description, desc, item description, item desc  

### RULES
- Match based on meaning
- Return ONLY ROOT KEYWORDS
- No new keywords
- If no match → []
- OUTPUT MUST be valid JSON array ONLY

### TEXT:
{norm}

### OUTPUT:
JSON array only.
"""

    try:
        response = client.invoke_model(
            modelId="mistral.mistral-large-2402-v1:0",
            body=json.dumps({
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 200,
                "temperature": 0.0
            })
        )

        resp_str = response["body"].read().decode("utf-8")
        result = json.loads(resp_str)

        raw = result["choices"][0]["message"]["content"].strip()

        # If pure JSON
        if raw.startswith("[") and raw.endswith("]"):
            return json.loads(raw)

        # Extract JSON inside text
        match = re.search(r'\[.*?\]', raw, re.DOTALL)
        if match:
            return json.loads(match.group(0))

        return []

    except Exception as e:
        print("LLM keyword detection failed:", e)
        return []


# ------------------- AWS Bedrock Extraction ------------------- #
po_fields = [
    "po_number", "customer_name", "vendor_number", "po_date", "delivery_date",
    "cancel_date", "gold_karat", "ec_style_number", "customer_style_number",
    "color", "quantity", "description"
]

EMPTY_PO = {field: None for field in po_fields}


async def extract_po_fields_from_llm(text: str) -> dict:
    """
    Safely extracts PO fields using AWS Bedrock LLM.
    Prevents hallucination — returns null values if not explicitly present.
    """

    if not text or not text.strip():
        return EMPTY_PO

    cleaned = text.strip()

    # ✅ EARLY EXIT — if message clearly not a PO
    # PO always contains at least one number, date, or code
    if len(cleaned) < 30 or not re.search(r"\d{2,}", cleaned):
        return EMPTY_PO

    # ✅ Another safety — no known PO keywords
    po_keywords = ["po", "purchase order", "qty", "quantity", "vendor", "invoice"]
    if not any(k.lower() in cleaned.lower() for k in po_keywords):
        return EMPTY_PO

    # ✅ STRICT ANTI-HALLUCINATION PROMPT
    prompt = f"""
You are a strict information extractor.

Extract ONLY if the value is explicitly present in the text.
If unsure — return null.
Never guess, infer, assume, create examples, or fabricate PO data.
Do NOT use prior knowledge or imagination.

Return JSON only with these exact keys:
{po_fields}

Text:
\"\"\"{cleaned}\"\"\"

Output rules:
- JSON only — no explanation
- Values MUST come from the text
- Null if missing
"""

    try:
        response = client.invoke_model(
            modelId="mistral.mistral-7b-instruct-v0:2",
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "prompt": prompt,
                "max_tokens": 300,
                "temperature": 0.0
            }),
        )

        raw = response["body"].read().decode()
        llm_text = json.loads(raw)["outputs"][0]["text"]

        # ✅ Extract JSON safely
        json_match = re.search(r"\{.*\}", llm_text, re.DOTALL)
        if not json_match:
            return EMPTY_PO

        data = json.loads(json_match.group(0))

        # ✅ Ensure only allowed fields + convert invalid to null
        cleaned_output = EMPTY_PO.copy()
        for f in po_fields:
            val = data.get(f)
            cleaned_output[f] = val if val not in ["", "N/A", "null", None] else None

        # ✅ Extra check — if ALL fields null → discard
        if all(v is None for v in cleaned_output.values()):
            return EMPTY_PO

        return cleaned_output

    except Exception as e:
        logger.error(f"PO extraction failed: {e} | text={text[:80]}")
        return EMPTY_PO


# ------------------- Main Function to Fetch and Save Emails ------------------- #
def normalize_po_date_ddmmyyyy(date_str: Optional[str]) -> Optional[str]:
    """
    Converts LLM date output to DD-MM-YYYY string.
    Returns None if parsing fails.
    """
    if not date_str:
        return None

    date_str = date_str.strip()

    # Try common LLM formats
    for fmt in ("%Y-%m-%d", "%m/%d/%y", "%d/%m/%y", "%d-%m-%Y", "%m-%d-%Y", "%y-%m-%d"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None



# ---------------------- Merge data ---------------------- #
def merge_po_data(body_data: dict, attachments_data: list[dict]) -> dict:
    merged = body_data.copy()
    for att_data in attachments_data:
        for k, v in att_data.items():
            if not merged.get(k) and v:
                merged[k] = v
    return merged


async def fetch_and_save_mails_by_folders(
    access_token: str,
    folder_names: list[str],
    user_id: int,
    org_id: int,
    from_date: str,
    to_date: str,
    mails_repo: "MailsRepository"
) -> List[Dict[str, Any]]:

    headers = {"Authorization": f"Bearer {access_token}"}
    results: List[Dict[str, Any]] = []

    from_date_iso = f"{from_date}T00:00:00Z"
    to_date_iso = f"{to_date}T23:59:59Z"

    timeout = httpx.Timeout(connect=10.0, read=300.0, write=60.0, pool=30.0)

    async with httpx.AsyncClient(timeout=timeout) as client:

        # ---------------- FETCH FOLDERS ----------------
        try:
            folder_resp = await client.get(
                f"{GRAPH_API}/me/mailFolders?$top=200&$expand=childFolders",
                headers=headers
            )
            folder_resp.raise_for_status()
        except Exception as e:
            logger.error("Failed to fetch folders: %s", e)
            return []

        folders = folder_resp.json().get("value", [])
        wanted = {f.lower() for f in folder_names}

        # ---------------- PROCESS FOLDERS ----------------
        for folder in folders:
            folder_id = folder.get("id")
            folder_name = folder.get("displayName", "")

            if not folder_id or folder_name.lower() not in wanted:
                continue

            url = (
                f"{GRAPH_API}/me/mailFolders/{folder_id}/messages"
                f"?$filter=receivedDateTime ge {from_date_iso} and receivedDateTime le {to_date_iso}"
                f"&$select=id,subject,body,from,toRecipients,ccRecipients,bccRecipients,"
                f"hasAttachments,receivedDateTime,bodyPreview"
            )

            messages = []
            next_url = url

            # ---------------- PAGINATION ----------------
            while next_url:
                try:
                    resp = await client.get(next_url, headers=headers)
                    resp.raise_for_status()
                except Exception as e:
                    logger.error("Failed to fetch messages from folder %s: %s", folder_name, e)
                    break

                data = resp.json()
                messages.extend(data.get("value", []))
                next_url = data.get("@odata.nextLink")

            # ---------------- PROCESS EACH MESSAGE ----------------
            for msg in messages:
                graph_mail_id = msg.get("id")
                if not graph_mail_id:
                    continue

                if msg.get('@odata.type') in (
                    '#microsoft.graph.eventMessage',
                    '#microsoft.graph.eventMessageRequest'
                ):
                    continue

                if await mails_repo.mail_exists(graph_mail_id, user_id):
                    continue

                subject = msg.get('subject', '')
                body_obj = msg.get('body') or {}
                body_content = body_obj.get('content') or msg.get('bodyPreview', '')

                body_plain = strip_html_to_text(body_content)
                body_clean = clean_email_body(body_plain)

                # ---------------- LLM KEYWORD MATCH ----------------
                matched_keywords = await get_keywords_from_llm(body_clean)
                if not matched_keywords:
                    continue

                from_email = (msg.get('from') or {}).get('emailAddress', {}).get('address')
                to_emails = collect_addresses_from_message(msg, 'toRecipients')
                cc = collect_addresses_from_message(msg, 'ccRecipients')
                bcc = collect_addresses_from_message(msg, 'bccRecipients')
                merged_cc = ",".join(filter(None, [cc, bcc])) or None
                has_attachments = bool(msg.get('hasAttachments'))
                date_only = iso_to_date(msg.get('receivedDateTime'))

                # ---------------- INSERT MAILS ----------------
                try:
                    mail_id = await mails_repo.insert_mail_detail(
                        subject=subject,
                        body=body_clean,
                        date_time=date_only,
                        mail_from=from_email,
                        mail_to=to_emails,
                        mail_cc=merged_cc,
                        keyword=None,
                        graph_mail_id=graph_mail_id,
                        folder_name=folder_name,
                        user_id=user_id,
                        created_by=user_id,
                    )
                except Exception as e:
                    logger.error("DB insert failed for mail %s: %s", graph_mail_id, e)
                    continue

                saved_attachments = []
                attachment_texts = []

                # ---------------- ATTACHMENTS ----------------
                if has_attachments:
                    try:
                        att_resp = await client.get(
                            f"{GRAPH_API}/me/messages/{graph_mail_id}/attachments",
                            headers=headers
                        )
                        att_resp.raise_for_status()
                        att_list = att_resp.json().get("value", [])
                    except Exception as e:
                        logger.error("Failed fetching attachments for %s: %s", graph_mail_id, e)
                        att_list = []

                    for att in att_list:
                        filename = att.get("name")
                        content_type = (att.get("contentType") or "").lower()
                        content_bytes = base64.b64decode(att.get("contentBytes") or "")
                        if not content_bytes:
                            continue

                        file_hash = compute_file_hash(content_bytes)
                        if await mails_repo.attachment_exists(file_hash):
                            continue

                        # Save File
                        safe_filename = re.sub(r'[\\/*?:"<>|&]', "_", filename)
                        os.makedirs("attachments", exist_ok=True)
                        file_path = os.path.join("attachments", safe_filename)
                        with open(file_path, "wb") as f:
                            f.write(content_bytes)

                        # -------- Extract text from attachments --------
                        attachment_text = None
                        ext = (filename or "").lower()
                        ct = (content_type or "").lower()
                        try:
                            if ct.startswith("text/") or ext.endswith((".txt", ".md", ".csv", ".log")):
                                attachment_text = content_bytes.decode("utf-8", errors="ignore")
                            elif ct == "application/pdf" or ext.endswith(".pdf"):
                                reader = PyPDF2.PdfReader(io.BytesIO(content_bytes))
                                attachment_text = " ".join((p.extract_text() or "") for p in reader.pages)
                            elif ct in ("application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                        "application/msword") or ext.endswith((".docx", ".doc")):
                                document = docx.Document(io.BytesIO(content_bytes))
                                attachment_text = " ".join(p.text for p in document.paragraphs)
                            elif ct in ("application/vnd.openxmlformats-officedocument.presentationml.presentation",
                                        "application/vnd.ms-powerpoint") or ext.endswith((".pptx", ".ppt")):
                                prs = Presentation(io.BytesIO(content_bytes))
                                attachment_text = " ".join(
                                    shape.text
                                    for slide in prs.slides
                                    for shape in slide.shapes
                                    if hasattr(shape, "text")
                                )
                            elif content_type.startswith("image/") or ext.endswith((".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff")):
                                attachment_text = ocr_from_image_bytes(content_bytes)
                        except Exception:
                            attachment_text = None

                        if attachment_text:
                            attachment_texts.append(attachment_text)
                            attach_keywords = await get_keywords_from_llm(attachment_text)
                        else:
                            attach_keywords = []

                        if not attach_keywords:
                            logger.info(f"Skipping attachment '{filename}' — no keyword match.")
                            continue

                        try:
                            await mails_repo.insert_attachment(
                                mail_dtl_id=mail_id,
                                attach_name=filename,
                                attach_type=content_type,
                                attach_path=file_path,
                                keyword=None,
                                user_id=user_id,
                                created_by=user_id,
                                file_hash=file_hash,
                            )
                            saved_attachments.append(filename)
                        except Exception as e:
                            logger.error("Attachment insert failed (%s): %s", filename, e)

                
                # ---------------- PO data from email body ----------------
                po_data_body = await extract_po_fields_from_llm(body_clean)
                if po_data_body:
                    await mails_repo.insert_po_details(
                        mail_dtl_id=mail_id,
                        po_number=po_data_body.get("po_number"),
                        customer_name=po_data_body.get("customer_name"),
                        vendor_number=po_data_body.get("vendor_number"),
                        po_date=normalize_po_date_ddmmyyyy(po_data_body.get("po_date")),
                        delivery_date=po_data_body.get("delivery_date"),
                        cancel_date=normalize_po_date_ddmmyyyy(po_data_body.get("cancel_date")),
                        gold_karat=po_data_body.get("gold_karat"),
                        ec_style_number=po_data_body.get("ec_style_number"),
                        customer_style_number=po_data_body.get("customer_style_number"),
                        color=po_data_body.get("color"),
                        quantity=po_data_body.get("quantity"),
                        description=po_data_body.get("description"),
                        mail_folder=folder_name,
                        created_by=user_id,
                    )

                # ---------------- PO data from attachments ----------------
                for att_text in attachment_texts:
                    po_data_att = await extract_po_fields_from_llm(att_text)

                    if isinstance(po_data_att, list):
                        for po in po_data_att:
                            if not po:
                                continue

                            await mails_repo.insert_po_details(
                                mail_dtl_id=mail_id,
                                po_number=po.get("po_number"),
                                customer_name=po.get("customer_name"),
                                vendor_number=po.get("vendor_number"),
                                po_date=normalize_po_date_ddmmyyyy(po.get("po_date")),
                                delivery_date=po.get("delivery_date"),
                                cancel_date=normalize_po_date_ddmmyyyy(po.get("cancel_date")),
                                gold_karat=po.get("gold_karat"),
                                ec_style_number=po.get("ec_style_number"),
                                customer_style_number=po.get("customer_style_number"),
                                color=po.get("color"),
                                quantity=po.get("quantity"),
                                description=po.get("description"),
                                mail_folder=folder_name,
                                created_by=user_id,
                            )
                    else:
                        po = po_data_att
                        if po:
                            await mails_repo.insert_po_details(
                                mail_dtl_id=mail_id,
                                po_number=po.get("po_number"),
                                customer_name=po.get("customer_name"),
                                vendor_number=po.get("vendor_number"),
                                po_date=normalize_po_date_ddmmyyyy(po.get("po_date")),
                                delivery_date=po.get("delivery_date"),
                                cancel_date=normalize_po_date_ddmmyyyy(po.get("cancel_date")),
                                gold_karat=po.get("gold_karat"),
                                ec_style_number=po.get("ec_style_number"),
                                customer_style_number=po.get("customer_style_number"),
                                color=po.get("color"),
                                quantity=po.get("quantity"),
                                description=po.get("description"),
                                mail_folder=folder_name,
                                created_by=user_id,
                            )
                # ---------------- COLLECT RESULT ----------------
                results.append({
                    "mail_dtl_id": mail_id,
                    "subject": subject,
                    "from": from_email,
                    "to": to_emails,
                    "cc": merged_cc,
                    "has_attachments": has_attachments,
                    "attachments": saved_attachments,
                    "folder": folder_name,
                })

    return results
# ------------------Email + Attachment Fetching + LLM keyword logic end ------------------ #

#### This api is used to fetch past event to current date time events and store counts also
# keywords = ["analysis", "research", "market"]

async def fetch_and_save_past_events(access_token: str, user_id: int, orgid: int, keywords: str, from_date: str, to_date: str, mails_repo):
    now = datetime.utcnow().isoformat() + "Z"
    url = "https://graph.microsoft.com/v1.0/me/events"

    # This code is used to fetch current to past events
    # params = {
    #     "$filter": f"end/dateTime le '{now}'",
    #     # "$filter": f"start/dateTime le '{now}'",
    #     "$orderby": "start/dateTime DESC",
    # }
    # This code is used to fetch events between two dates
    params = {
        "$filter": f"start/dateTime ge '{from_date}' and end/dateTime le '{to_date}'",
        "$orderby": "start/dateTime DESC",
    }
    #"$filter": f"start/dateTime le '{now}'"  # it fetch ongoing + past events

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    results = []
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as resp:
                if resp.status != 200:
                    error_msg = f"Failed to fetch events: {resp.status} {await resp.text()}"
                    raise Exception(error_msg)

                data = await resp.json()
                events = data.get("value", [])

                for event in events:
                    event_id = event.get("id")

                    # Skip if no event id
                    if not event_id:
                        continue

                    # âœ… Save into DB only if not exists
                    exists = await mails_repo.check_event_exists(event_id)
                    if exists:
                        continue

                    subject = event.get("subject", "") or ""
                    body_content = (event.get("body", {}).get("content", "") or "")

                    # âœ… Clean text before counting words
                    # clean_text = re.sub(r"[_]+", " ", subject + " " + body_content)
                    # clean_text = re.sub(r"<[^>]+>", " ", clean_text)  # remove HTML tags
                    # words = re.findall(r"\b\w+\b", clean_text)
                    # word_count = len(words)

                    # âœ… Clean text before counting words (BODY ONLY)
                    clean_text = re.sub(r"[_]+", " ", body_content)
                    clean_text = re.sub(r"<[^>]+>", " ", clean_text)  # remove HTML tags
                    words = re.findall(r"\b\w+\b", clean_text)
                    word_count = len(words)


                    # âœ… Keyword frequency
                    keyword_counts = {
                        k: subject.lower().count(k) + clean_text.lower().count(k)
                        for k in keywords
                    }
                    matched_keywords = {k: c for k, c in keyword_counts.items() if c > 0}

                    if matched_keywords:
                        organiser = (
                            event.get("organizer", {})
                            .get("emailAddress", {})
                            .get("address", "")
                        )
                        attendees = ",".join(
                            [
                                a.get("emailAddress", {}).get("address", "")
                                for a in event.get("attendees", [])
                            ]
                        )
                        description = event.get("bodyPreview", "")
                        title = subject

                        # âœ… Event start & end datetime
                        start_str = event.get("start", {}).get("dateTime")
                        end_str = event.get("end", {}).get("dateTime")

                        start_dt = datetime.fromisoformat(start_str) if start_str else None
                        end_dt = datetime.fromisoformat(end_str) if end_str else None

                        # âœ… Meeting duration in minutes
                        duration_minutes = None
                        if start_dt and end_dt:
                            duration_minutes = int((end_dt - start_dt).total_seconds() / 60)

                        

                        # âœ… Save into DB
                        await mails_repo.insert_calendar_event(
                            event_id=event_id,
                            user_id=user_id,
                            organiser=organiser,
                            attendees=attendees,
                            title=title,
                            description=description,
                            word_count=word_count,
                            keyword=",".join(matched_keywords.keys()),
                            repeated_keyword=json.dumps(matched_keywords),
                            event_start_datetime=start_str,  # store event start
                            event_end_datetime=end_str,      # store event end
                            duration_minutes=duration_minutes, # store duration
                            created_by=user_id,
                            # updated_by=user_id,
                        )

                        results.append(
                            {
                                "title": title,
                                "event_start_datetime": start_str,
                                "event_end_datetime": end_str,
                                "duration_minutes": duration_minutes,
                                "word_count": word_count,
                                "keywords": matched_keywords,
                            }
                        )
    except Exception as e:
        error_msg = f"Error fetching past events: {str(e)}"
        print(error_msg)
        return {"error": error_msg}

    return results


## this code is used to fetch gmails form google mails

async def fetch_all_labels(access_token: str) -> List[Dict[str, Any]]:
    """
    Fetch all Gmail labels for the authenticated user.
    """
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{GMAIL_API}/labels", headers=headers)
        resp.raise_for_status()
        labels = resp.json().get("labels", [])
        
        label_list = []
        for label in labels:
            label_list.append({
                "id": label.get("id"),
                "name": label.get("name"),
            })
        return label_list


# âœ… helper: recursive body extraction
def extract_body(payload):
    if "parts" in payload:
        for part in payload["parts"]:
            mime_type = part.get("mimeType", "")
            if mime_type in ["text/html", "text/plain"]:
                data = part.get("body", {}).get("data")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            # go deeper if nested multipart
            if "parts" in part:
                body = extract_body(part)
                if body:
                    return body
    else:
        data = payload.get("body", {}).get("data")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    return ""




async def fetch_and_save_mails_by_labels(access_token: str, label_names: list[str], user_id: int, org_id: int, mails_repo: "MailsRepository") -> List[Dict[str, Any]]:
    headers = {"Authorization": f"Bearer {access_token}"}
    results: List[Dict[str, Any]] = []

    # âœ… reuse your helpers
    def strip_html_to_text(html_content: Optional[str]) -> str:
        if not html_content:
            return ""
        text = re.sub(r"<[^>]+>", " ", html_content)
        text = html.unescape(text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def clean_email_body(body_text: str) -> str:
        if not body_text:
            return ""
        lines = body_text.split("\n")
        cleaned_lines: List[str] = []
        skip_line_starts = [
            r"^From:", r"^To:", r"^Cc:", r"^Subject:", r"^Date:",
            r"^Reply-To:", r"^Message-ID:", r"^X-.*?:",
            r"^Content-Type:", r"^MIME-Version:",
            r"^Received:", r"^On .* wrote:", r"^-----Original Message-----",
        ]
        url_re = re.compile(r"^(https?://|www\.)", re.IGNORECASE)
        skip_res = [re.compile(pat, re.IGNORECASE) for pat in skip_line_starts]
        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue
            if url_re.match(line):
                continue
            if any(rx.match(line) for rx in skip_res):
                continue
            cleaned_lines.append(line)
        cleaned_text = " ".join(cleaned_lines)
        cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
        return cleaned_text or body_text.strip()

    async with httpx.AsyncClient() as client:
        # fetch label IDs from names
        labels_resp = await client.get(f"{GMAIL_API}/labels", headers=headers)
        labels_resp.raise_for_status()
        labels = labels_resp.json().get("labels", [])
        wanted = {l.lower() for l in label_names}
        label_ids = [l["id"] for l in labels if l["name"].lower() in wanted]

        keywords = await mails_repo.fetch_keywords(org_id)

        for label_id in label_ids:
            # fetch messages for label
            msg_list_resp = await client.get(f"{GMAIL_API}/messages?labelIds={label_id}&maxResults=100", headers=headers)
            msg_list_resp.raise_for_status()
            messages = msg_list_resp.json().get("messages", [])

            for msg_meta in messages:
                msg_id = msg_meta.get("id")
                if not msg_id:
                    continue
                if await mails_repo.mail_exists(msg_id, user_id):
                    continue

                # fetch message details
                msg_resp = await client.get(f"{GMAIL_API}/messages/{msg_id}?format=full", headers=headers)
                msg_resp.raise_for_status()
                msg = msg_resp.json()

                payload = msg.get("payload", {})
                headers_list = payload.get("headers", [])
                headers_map = {h["name"].lower(): h["value"] for h in headers_list if "name" in h and "value" in h}

                subject = headers_map.get("subject", "")
                from_email = headers_map.get("from", "")
                to_emails = headers_map.get("to", "")
                cc_emails = headers_map.get("cc", "")
                bcc_emails = headers_map.get("bcc", "")
                mail_cc_merged = ",".join([p for p in [cc_emails, bcc_emails] if p]) or None

                # decode body
                body_data = ""
                # if "parts" in payload:
                #     for part in payload["parts"]:
                #         if part.get("mimeType") == "text/html":
                #             body_data = base64.urlsafe_b64decode(part["body"].get("data", "")).decode("utf-8", errors="ignore")
                #             break
                #         elif part.get("mimeType") == "text/plain":
                #             body_data = base64.urlsafe_b64decode(part["body"].get("data", "")).decode("utf-8", errors="ignore")
                # else:
                #     body_data = base64.urlsafe_b64decode(payload.get("body", {}).get("data", "")).decode("utf-8", errors="ignore")

                body_data = extract_body(payload)
                body_plain = strip_html_to_text(body_data)
                body_clean = clean_email_body(body_plain)

                word_count_int = len(re.findall(r"\w+", body_clean))
                word_count_str = str(word_count_int)

                # keyword match
                lower_subject = subject.lower()
                lower_body = body_clean.lower()
                matched_keywords_list = [k for k in keywords if (k in lower_subject or k in lower_body)]
                if not matched_keywords_list:
                    continue
                matched_keywords_csv = ", ".join(matched_keywords_list)

                # keyword count
                keyword_counts: Dict[str, int] = {}
                for k in keywords:
                    pattern = r'\b' + re.escape(k.lower()) + r'\b'
                    subject_matches = re.findall(pattern, lower_subject)
                    body_matches = re.findall(pattern, lower_body)
                    count = len(subject_matches) + len(body_matches)
                    if count > 0:
                        keyword_counts[k] = count
                matched_keyword_counts_csv = ", ".join(f"{k}:{c}" for k, c in keyword_counts.items())
                if int(word_count_str) == 0:
                    continue
                # save mail
                
                
                # If you have Gmail API message object
                internal_date_ms = msg['internalDate']  # e.g., 1696831740000
                date_time = datetime.fromtimestamp(int(internal_date_ms)/1000)  # convert ms -> sec -> datetime
                mail_dtl_id = await mails_repo.insert_mail_detail(
                    subject=subject,
                    body=body_clean,
                    date_time=date_time,  # Gmail has internalDate if you want
                    mail_from=from_email,
                    mail_to=to_emails,
                    mail_cc=mail_cc_merged,
                    word_count=word_count_str,
                    keyword=matched_keywords_csv,
                    repeated_keyword=matched_keyword_counts_csv,
                    graph_mail_id=msg_id,
                    folder_name=label_id,
                    user_id=user_id,
                    created_by=user_id,
                )

                # attachments (similar to Outlook, Gmail parts include attachments)
                saved_attachments: List[str] = []
                parts = payload.get("parts", [])
                for part in parts:
                    if part.get("filename"):
                        attach_id = part["body"].get("attachmentId")
                        if not attach_id:
                            continue
                        att_resp = await client.get(f"{GMAIL_API}/messages/{msg_id}/attachments/{attach_id}", headers=headers)
                        att_resp.raise_for_status()
                        att = att_resp.json()
                        content_bytes_b64 = att.get("data")
                        if not content_bytes_b64:
                            continue
                        content = base64.urlsafe_b64decode(content_bytes_b64)
                        filename = part["filename"]
                        content_type = part.get("mimeType")

                        safe_filename = re.sub(r'[\\/*?:"<>|&]', "_", filename)
                        os.makedirs("attachments", exist_ok=True)
                        file_path = os.path.join("attachments", safe_filename)
                        try:
                            with open(file_path, "wb") as f:
                                f.write(content)
                        except Exception:
                            file_path = None
                        # word count/type extraction intentionally left same as existing flow
                        # (reuse simplified path to avoid altering current behavior)
                        # Compute attachment word count where feasible
                        attach_word_count_str: Optional[str] = None
                        attachment_text: Optional[str] = None
                        try:
                            ct = (content_type or "").lower()
                            fname = (filename or "").lower()
                            if ct.startswith("text/") or fname.endswith((".txt", ".md", ".csv", ".log")):
                                try:
                                    attachment_text = content.decode("utf-8", errors="ignore")
                                    attach_word_count_str = str(len(re.findall(r"\w+", attachment_text)))
                                except Exception:
                                    attach_word_count_str = None
                            elif ct == "application/pdf" or fname.endswith(".pdf"):
                                if PyPDF2 is not None:
                                    try:
                                        reader = PyPDF2.PdfReader(io.BytesIO(content))
                                        pages_text = []
                                        for page in getattr(reader, "pages", []):
                                            try:
                                                pages_text.append(page.extract_text() or "")
                                            except Exception:
                                                continue
                                        attachment_text = " ".join(pages_text)
                                        attach_word_count_str = str(len(re.findall(r"\w+", attachment_text)))
                                    except Exception:
                                        attach_word_count_str = None
                            elif (
                                ct in (
                                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    "application/msword",
                                )
                                or fname.endswith(".docx")
                            ):
                                if docx is not None:
                                    try:
                                        document = docx.Document(io.BytesIO(content))
                                        attachment_text = " ".join([p.text or "" for p in document.paragraphs])
                                        attach_word_count_str = str(len(re.findall(r"\w+", attachment_text)))
                                    except Exception:
                                        attach_word_count_str = None

                            # PowerPoint (PPTX)
                            elif (
                                ct in (
                                    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                                    "application/vnd.ms-powerpoint",
                                )
                                or fname.endswith((".pptx", ".ppt"))
                            ):
                                try:
                                    prs = Presentation(io.BytesIO(content))
                                    slides_text = []
                                    for slide in prs.slides:
                                        for shape in slide.shapes:
                                            if hasattr(shape, "text"):
                                                slides_text.append(shape.text)
                                    attachment_text = " ".join(slides_text)
                                    attach_word_count_str = str(len(re.findall(r"\w+", attachment_text)))
                                except Exception:
                                    attach_word_count_str = None

                            elif (
                                ct in (
                                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    "application/vnd.ms-excel",
                                )
                                or fname.endswith((".xlsx", ".xls"))
                            ):
                                try:
                                    attachment_text = ""
                                    attach_word_count_str = None

                                    if fname.endswith(".xlsx"):
                                        import openpyxl
                                        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
                                        cells_text = []
                                        for sheet in wb.worksheets:
                                            for row in sheet.iter_rows(values_only=True):
                                                row_text = " ".join([str(cell) for cell in row if cell is not None])
                                                cells_text.append(row_text)
                                        attachment_text = " ".join(cells_text)
                                    
                                    elif fname.endswith(".xls"):
                                        import xlrd
                                        wb = xlrd.open_workbook(file_contents=content)
                                        cells_text = []
                                        for sheet in wb.sheets():
                                            for row_idx in range(sheet.nrows):
                                                row_values = sheet.row_values(row_idx)
                                                row_text = " ".join([str(cell) for cell in row_values if cell])
                                                cells_text.append(row_text)
                                        attachment_text = " ".join(cells_text)

                                    if attachment_text:
                                        attach_word_count_str = str(len(re.findall(r"\w+", attachment_text)))

                                except Exception:
                                    attach_word_count_str = None

                        except Exception:
                            attach_word_count_str = None

                        # Check for keywords in attachment text
                        attachment_keywords = []
                        attachment_keyword_counts = {}
                        if attachment_text:
                            lower_attachment_text = attachment_text.lower()
                            for keyword in keywords:
                                # count = lower_attachment_text.count(keyword.lower())
                                # \b ensures whole word match, re.escape handles special characters in keyword
                                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                                matches = re.findall(pattern, lower_attachment_text)
                                count = len(matches)
                                if count > 0:
                                    attachment_keywords.append(keyword)
                                    attachment_keyword_counts[keyword] = count
                        
                        # Save attachment only if keywords are found
                        if attachment_keywords:
                            attachment_keywords_csv = ", ".join(attachment_keywords)  # "r&d,search"
                            attachment_keyword_counts_csv = ", ".join([f"{k}:{c}" for k, c in attachment_keyword_counts.items()])  # "r&d:3,search:2"                          

                            await mails_repo.insert_attachment(
                                mail_dtl_id=mail_dtl_id,
                                attach_name=filename,
                                attach_type=content_type,
                                attach_path=file_path,
                                word_count=attach_word_count_str,
                                keyword=attachment_keywords_csv,
                                repeated_keyword=attachment_keyword_counts_csv,
                                user_id=user_id,
                                created_by=user_id,
                            )
                            if filename:
                                saved_attachments.append(filename)

                results.append({
                    "mail_dtl_id": mail_dtl_id,
                    "subject": subject,
                    "from": from_email,
                    "to": to_emails,
                    "cc": mail_cc_merged,
                    "word_count": word_count_int,
                    "has_attachments": len(saved_attachments) > 0,
                    "attachments": saved_attachments,
                    "folder": label_id,
                })

        # fetch past events and save into cal_master
        events = await fetch_and_save_past_events_google(
            access_token=access_token,
            user_id=user_id,
            orgid=org_id,
            keywords= keywords,
            mails_repo=mails_repo
        )

    return results

## this api is used to fetch events from google
async def fetch_and_save_past_events_google(access_token: str, user_id: int, orgid: int, keywords: list[str], mails_repo):
    now = datetime.utcnow().isoformat() + "Z"
    past_limit = (datetime.utcnow() - timedelta(days=365)).isoformat() + "Z"  # last 1 year (adjust as needed)

    url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
    #"https://www.googleapis.com/calendar/v3/users/me/calendarList"
    params = {
        "timeMin": past_limit,   # âœ… lower bound
        "timeMax": now,   # âœ… Only past events
        "orderBy": "startTime",
        "singleEvents": "true",
        "maxResults": 100,
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

    results = []
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as resp:
                if resp.status != 200:
                    error_msg = f"Failed to fetch Google events: {resp.status} {await resp.text()}"
                    raise Exception(error_msg)

                data = await resp.json()
                events = data.get("items", [])

                for event in events:
                    event_id = event.get("id")
                    if not event_id:
                        continue

                    # âœ… Skip if already in DB
                    exists = await mails_repo.check_event_exists(event_id)
                    if exists:
                        continue

                    subject = event.get("summary", "") or ""
                    body_content = event.get("description", "") or ""

                    # âœ… Word count (body only, same as Outlook)
                    clean_text = re.sub(r"[_]+", " ", body_content)
                    clean_text = re.sub(r"<[^>]+>", " ", clean_text)  # remove HTML tags
                    words = re.findall(r"\b\w+\b", clean_text)
                    word_count = len(words)

                    # âœ… Keyword frequency
                    keyword_counts = {
                        k: subject.lower().count(k) + body_content.lower().count(k)
                        for k in keywords
                    }
                    matched_keywords = {k: c for k, c in keyword_counts.items() if c > 0}

                    if matched_keywords:
                        organiser = event.get("organizer", {}).get("email", "")
                        attendees = ",".join(
                            [a.get("email", "") for a in event.get("attendees", [])]
                        )
                        description = event.get("description", "")
                        title = subject

                        # âœ… Start & End time
                        start_str = event.get("start", {}).get("dateTime")
                        end_str = event.get("end", {}).get("dateTime")

                        start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00")) if start_str else None
                        end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00")) if end_str else None

                        duration_minutes = None
                        if start_dt and end_dt:
                            duration_minutes = int((end_dt - start_dt).total_seconds() / 60)

                        # âœ… Save into DB (same as Outlook)
                        await mails_repo.insert_calendar_event(
                            event_id=event_id,
                            user_id=user_id,
                            organiser=organiser,
                            attendees=attendees,
                            title=title,
                            description=description,
                            word_count=word_count,
                            keyword=",".join(matched_keywords.keys()),
                            repeated_keyword=json.dumps(matched_keywords),
                            event_start_datetime=start_str,
                            event_end_datetime=end_str,
                            duration_minutes=duration_minutes,
                            created_by=user_id,
                        )

                        results.append(
                            {
                                "title": title,
                                "event_start_datetime": start_str,
                                "event_end_datetime": end_str,
                                "duration_minutes": duration_minutes,
                                "word_count": word_count,
                                "keywords": matched_keywords,
                            }
                        )
    except Exception as e:
        error_msg = f"Error fetching past Google events: {str(e)}"
        print(error_msg)
        return {"error": error_msg}

    return results





def is_valid_po_key(po):
    return (
        po.get("po_number") not in (None, "", "NULL")
        and po.get("po_date") is not None
    )


def build_po_key(po):
    return (
        normalize_value(po["po_number"]),
        normalize_value(po["vendor_number"]),
        normalize_value(po["po_date"]),
    )


def normalize_value(val):
    if val is None:
        return ""

    if isinstance(val, datetime):
        return val.date().isoformat()

    if isinstance(val, date):
        return val.isoformat()

    val = str(val).strip()

    if val.startswith('"') and val.endswith('"'):
        val = val[1:-1]

    return val


async def generate_missing_po_report_service(mails_repo):

    po_details = await mails_repo.get_all_po_details()
    sys_po_details = await mails_repo.get_all_system_po_details()

    # -------------------------------
    # BUILD LOOKUP MAPS
    # -------------------------------
    scanned_map = {
        (
            normalize_value(po["po_number"]),
            normalize_value(po["vendor_number"]),
            normalize_value(po["po_date"]),
        ): po
        for po in po_details
        if po.get("po_number") and po.get("vendor_number") and po.get("po_date")
    }

    sys_map = {
        (
            normalize_value(row["po_number"]),
            normalize_value(row["vendor_number"]),
            normalize_value(row["po_date"]),
        ): row
        for row in sys_po_details
        if row.get("po_number") and row.get("vendor_number") and row.get("po_date")
    }

    generated_missing_ids = []
    generated_mismatch_ids = []

    # ==================================================
    # PASS 1: SCANNED → SYSTEM
    # ==================================================
    for po in po_details:

        if not is_valid_po_key(po):
            continue

        po_number = po.get("po_number")
        vendor_number = po.get("vendor_number")
        po_date = po.get("po_date")

        # CASE 1: Vendor missing
        if not vendor_number or vendor_number in ("", "NULL"):

            duplicate = await mails_repo.get_existing_po_missing(
                po_det_id=po["po_det_id"]
            )

            if duplicate is None:
                missing_id = await mails_repo.insert_po_missing(
                    po_det_id=po["po_det_id"],
                    system_po_id=None,
                    attribute="po_missing",
                    system_value="",
                    scanned_value=po_number,
                    comment="Vendor number missing in scanned PO"
                )
                generated_missing_ids.append(missing_id)
            continue

        key = (
            normalize_value(po_number),
            normalize_value(vendor_number),
            normalize_value(po_date),
        )

        # CASE 2: PO not found in system
        if key not in sys_map:

            duplicate = await mails_repo.get_existing_po_missing(
                po_det_id=po["po_det_id"]
            )

            if duplicate is None:
                missing_id = await mails_repo.insert_po_missing(
                    po_det_id=po["po_det_id"],
                    system_po_id=None,
                    attribute="po_missing",
                    system_value="",
                    scanned_value=po_number,
                    comment="PO not found in system"
                )
                generated_missing_ids.append(missing_id)
            continue

        # CASE 3: Exists → mismatch check
        system_row = sys_map[key]

        fields_to_compare = [
            "delivery_date",
            "cancel_date",
            "ec_style_number",
            "customer_style_number",
            "color",
            "gold_karat",
            "quantity",
            "description",
        ]

        for field in fields_to_compare:

            val_scanned = normalize_value(po.get(field))
            val_system = normalize_value(system_row.get(field))

            if field == "quantity":
                try:
                    val_scanned = int(val_scanned)
                    val_system = int(val_system)
                except:
                    pass

            if field == "gold_karat":
                try:
                    val_scanned = float(val_scanned)
                    val_system = float(val_system)
                except:
                    pass

            if val_scanned != val_system:

                duplicate = await mails_repo.get_existing_mismatch(
                    po_det_id=po["po_det_id"],
                    system_po_id=system_row["system_po_id"],
                    mismatch_attribute=field
                )

                if duplicate:
                    continue

                mismatch_id = await mails_repo.insert_mismatch(
                    po_det_id=po["po_det_id"],
                    system_po_id=system_row["system_po_id"],
                    field=field,
                    system_value=str(val_system),
                    scanned_value=str(val_scanned),
                    comment=f"{field} mismatch"
                )
                generated_mismatch_ids.append(mismatch_id)

    # ==================================================
    # PASS 2: SYSTEM → SCANNED (Missing in scanned)
    # ==================================================
    for key, system_row in sys_map.items():

        if key not in scanned_map:

            duplicate = await mails_repo.get_existing_po_missing_by_system_po(
                system_po_id=system_row["system_po_id"]
            )

            if duplicate:
                continue

            missing_id = await mails_repo.insert_po_missing(
                po_det_id=None,
                system_po_id=system_row["system_po_id"],
                attribute="po_missing",
                system_value=system_row["po_number"],
                scanned_value="",
                comment="PO exists in system but not found in scanned data"
            )
            generated_missing_ids.append(missing_id)

    return {
        "status": "success",
        "message": "Missing & mismatch report generated",
        "summary": {
            "missing_count": len(generated_missing_ids),
            "mismatch_count": len(generated_mismatch_ids),
        },
        "generated_ids": {
            "missing_po_ids": generated_missing_ids,
            "mismatch_po_ids": generated_mismatch_ids,
        }
    }
