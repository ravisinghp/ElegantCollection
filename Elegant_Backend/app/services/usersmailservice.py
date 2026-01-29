
from dotenv import load_dotenv
import os, base64
import httpx
from urllib.parse import urlencode
import json
from decimal import Decimal
from loguru import logger
import jwt
from datetime import date, datetime
from openai import OpenAI
from rapidfuzz import fuzz

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
JWTSECRET_KEY=os.getenv("JWTSECRET_KEY")
#---------------outlook end ----------------------#

#---------------Google---------------------------#
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
# TENANT_ID = os.getenv("TENANT_ID")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
GMAIL_API = os.getenv("GMAIL_API")
#---------------Google end-------------------------#

#---------------OpenAI Client------------------
openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)
#----------OpenAI Client end ------------------

from datetime import datetime,timedelta
import re
from typing import List, Dict, Any, Optional
import html
import io
import aiohttp, json
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

# this code is used for outlook
# def get_auth_url():
#     return (
#         f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize?"
#         f"client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}"
#         f"&response_mode=query&scope=offline_access%20Mail.Read%20Mail.ReadWrite"
#         f"&prompt=login"   # ðŸ”‘ This forces login screen every time
#     )

def get_auth_url(provider: str, user_id: int):

    state = jwt.encode(
        {"user_id": user_id},
        JWTSECRET_KEY,
        algorithm="HS256"
    )
    
    if isinstance(state, bytes):
        state = state.decode("utf-8")
      
    if provider == "outlook":
        return (
            # f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize?"
            # f"client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}"
            # # f"&response_mode=query&scope=offline_access%20Mail.Read%20Mail.ReadWrite%20Calendars.Read"
            # f"&response_mode=query&scope=offline_access%20Mail.Read"
            # f"&prompt=login"   # ðŸ”‘ This forces login screen every time

             f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize?"
            f"client_id={CLIENT_ID}"
            f"&response_type=code"
            f"&redirect_uri={REDIRECT_URI}"
            f"&response_mode=query"
            f"&scope=offline_access%20Mail.Read%20User.Read"
            f"&state={state}"
            f"&prompt=login"
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

# mansi-------------------------------------------------------------

async def refresh_outlook_access_token(refresh_token: str) -> dict:
    url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": "https://graph.microsoft.com/.default",
    }

    timeout = httpx.Timeout(connect=10.0, read=30.0, write=30.0, pool=30.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, data=data)
        resp.raise_for_status()
        return resp.json()


# mansi --------------------------------------------------------------------------------------------------------
async def get_valid_outlook_token(
    user_id: int,
    repo: MailsRepository,
) -> str:
    token = await repo.get_outlook_token(user_id)

    if token.token_expiry > datetime.utcnow() + timedelta(minutes=2):
        return token.access_token

    new_tokens = await refresh_outlook_access_token(token.refresh_token)

    new_expiry = datetime.utcnow() + timedelta(
        seconds=int(new_tokens["expires_in"])
    )

    await repo.update_outlook_token(
        user_id=user_id,
        access_token=new_tokens["access_token"],
        refresh_token=new_tokens.get("refresh_token", token.refresh_token),
        token_expiry=new_expiry,
    )

    return new_tokens["access_token"]

# ------------------Email + Attachment Fetching + LLM logic start ------------------ #
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


# ------------------- normalize text ------------------- #
def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\xa0", " ")    
    text = text.replace("\u200b", " ")   
    text = text.replace("\r", "\n")

    # normalize separators
    text = re.sub(r"[=]", ":", text)

    # collapse whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def extract_po_fields_regex(text: str) -> dict:
    text = normalize_text(text)
    out = EMPTY_PO.copy()

    for field, patterns in PO_REGEX_PATTERNS.items():
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                out[field] = match.group(1).strip()
                break

    return out if any(out.values()) else EMPTY_PO
 

MANDATORY_FIELDS = ["po_number", "customer_name"]

async def extract_po_fields(text: str) -> dict:
    regex_data = extract_po_fields_regex(text)

    # Check if mandatory fields are present
    if all(regex_data.get(f) for f in MANDATORY_FIELDS):
        return regex_data

    # Otherwise call LLM
    llm_data = await extract_po_fields_from_llm(text)

    # Merge: REGEX ALWAYS WINS
    final = regex_data.copy()
    for k, v in llm_data.items():
        if final.get(k) is None and v:
            final[k] = v

    return final if any(final.values()) else EMPTY_PO


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


async def detect_keywords(
    text: str,
    db_keywords: list[str]
):
    if not text or not text.strip():
        return [], None

    text_l = text.lower()
    keywords = [normalize_keyword(k) for k in db_keywords]

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
    ai_hits = await openai_keyword_fallback(text, keywords)
    if ai_hits:
        return ai_hits, "OPENAI"

    return [], None


def normalize_keyword(k: str) -> str:
    return re.sub(r"\s+", " ", k.strip().lower())


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
        return EMPTY_PO

    if not re.search(r"(po|order|\d{3,})", text, re.IGNORECASE):
        return EMPTY_PO

    prompt = f"""
Extract ONLY explicitly present values.
Return null if missing.
Never guess.

Return JSON with keys:
{PO_FIELD_NAMES}

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
            return EMPTY_PO

        data = json.loads(match.group())
        out = EMPTY_PO.copy()

        for f in PO_FIELD_NAMES:
            v = data.get(f)
            out[f] = v if v not in ["", None, "null", "N/A"] else None

        return out if any(out.values()) else EMPTY_PO

    except Exception:
        return EMPTY_PO

def normalize_po_date_ddmmyyyy(date_str: Optional[str]) -> Optional[str]:
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

    for m in ITEM_REGEX.finditer(text):
        items.append({
            "description": m.group("description").strip(),
            "gold_karat": re.search(r"\d{2}", m.group("material")).group(),
            "quantity": int(m.group("quantity")),
            "delivery_date": m.group("delivery_date")
        })

    return items


async def extract_po_header(text: str):
    return await extract_po_fields(text)


# ------------------- Main Function to Fetch and Save Emails + Attachments ------------------- #
async def fetch_and_save_mails_by_folders(
    access_token: str,
    folder_names: list[str],
    user_id: int,
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


                keywords = await mails_repo.fetch_keywords()
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
                matched_keywords, match_source = await detect_keywords(
                    body_clean,
                    keywords
                )

                if not matched_keywords:
                    continue  #skip mail

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
                    user_id=user_id,
                    subject=subject,
                    body=body_clean,
                    date_time=date_only,
                    mail_from=from_email,
                    mail_to=to_emails,
                    mail_cc=merged_cc,
                    created_by=user_id,
                    updated_by=user_id,
                    is_active=1,
                    graph_mail_id=graph_mail_id,
                    folder_name=folder_name
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
                            # elif content_type.startswith("image/") or ext.endswith((".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff")):
                            #     attachment_text = ocr_from_image_bytes(content_bytes)
                        except Exception:
                            attachment_text = None

                        if attachment_text:
                            attachment_texts.append(attachment_text)
                            attach_keywords, match_type = await detect_keywords(attachment_text, keywords)

                        else:
                            attach_keywords = []

                        if not attach_keywords:
                            logger.info(f"Skipping attachment '{filename}' — no keyword match.")
                            continue

                        try:
                            await mails_repo.insert_attachment(
                                mail_dtl_id=mail_id,
                                user_id=user_id,
                                attach_name=filename,
                                attach_type=content_type,
                                attach_path=file_path,
                                created_by=user_id,
                                updated_by=user_id,
                                is_active=1,
                                file_hash=file_hash,
                            )
                            saved_attachments.append(filename)
                        except Exception as e:
                            logger.error("Attachment insert failed (%s): %s", filename, e)

                
                # ---------------- Insert PO data from email body ----------------
                po_data_body = await extract_po_fields(body_clean)
                if any(po_data_body.values()):
                    await mails_repo.insert_po_details(
                        mail_dtl_id=mail_id,
                        user_id=user_id,
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

                # ----------------Insert PO data from attachments ----------------
                for att_text in attachment_texts:
                    normalized_text = normalize_attachment_text(att_text)
                    # ---------------- PO HEADER FROM ATTACHMENT ----------------
                    header = await extract_po_header(normalized_text)

                    if not any(header.values()):
                        continue

                    # ---------------- PO ITEMS FROM ATTACHMENT ----------------
                    items = extract_po_items(normalized_text)

                    # Fallback: if no items found, insert header-only
                    if not items:
                        await mails_repo.insert_po_details(
                            mail_dtl_id=mail_id,
                            user_id=user_id,
                            po_number=header.get("po_number"),
                            customer_name=header.get("customer_name"),
                            vendor_number=header.get("vendor_number"),
                            po_date=normalize_po_date_ddmmyyyy(header.get("po_date")),
                            delivery_date=header.get("delivery_date"),
                            cancel_date=normalize_po_date_ddmmyyyy(header.get("cancel_date")),
                            gold_karat=header.get("gold_karat"),
                            ec_style_number=header.get("ec_style_number"),
                            customer_style_number=header.get("customer_style_number"),
                            color=header.get("color"),
                            quantity=header.get("quantity"),
                            description=header.get("description"),
                            mail_folder=folder_name,
                            created_by=user_id,
                        )
                    else:
                        # MULTIPLE ROW INSERTS
                        for item in items:
                            await mails_repo.insert_po_details(
                                mail_dtl_id=mail_id,
                                user_id=user_id,
                                po_number=header.get("po_number"),
                                customer_name=header.get("customer_name"),
                                vendor_number=header.get("vendor_number"),
                                po_date=normalize_po_date_ddmmyyyy(header.get("po_date")),
                                delivery_date=item.get("delivery_date"),
                                cancel_date=normalize_po_date_ddmmyyyy(header.get("cancel_date")),
                                gold_karat=item.get("gold_karat"),
                                ec_style_number=header.get("ec_style_number"),
                                customer_style_number=header.get("customer_style_number"),
                                color=header.get("color"),
                                quantity=item.get("quantity"),
                                description=item.get("description"),
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
# ------------------Email + Attachment Fetching + LLM logic end ------------------ #

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

#--------------------------data comparison logic start--------------------------#
# # -------------------------- NORMALIZATION -------------------------- #
# def normalize(value, field=None):
#     if value is None:
#         return ""

#     text = str(value).strip().lower()
#     field = (field or "").strip().lower()

#     # ------------------ GOLD KARAT / GOLD LOCK / KT ------------------ #
#     if field in ("gold_karat", "gold_lock", "kt"):
#         # unify 24, 24k, 24 kt, 24ct, 24 carat
#         text = re.sub(r"[^\d]", "", text)  # remove letters, spaces
#         return text

#     # ------------------ QUANTITY ------------------ #
#     if field == "quantity":
#         nums = re.findall(r"\d+", text)
#         return nums[0] if nums else ""

#     # ------------------ DATE FIELDS ------------------ #
#     if field in ("po_date", "delivery_date", "cancel_date"):
#         if isinstance(value, (date, datetime)):
#             return value.strftime("%Y-%m-%d")
#         text = re.sub(r"[/.]", "-", text)
#         m = re.search(r"\d{4}-\d{1,2}-\d{1,2}", text)
#         if m:
#             y, mth, d = m.group().split("-")
#             return f"{int(y):04d}-{int(mth):02d}-{int(d):02d}"
#         return ""

#     # ------------------ TEXT FIELDS ------------------ #
#     text = re.sub(r"[^\w\s]", " ", text)
#     text = re.sub(r"\s+", " ", text)

#     # handle common abbreviations
#     replacements = {
#         "pvt": "private",
#         "ltd": "limited",
#         "co": "company",
#         "corp": "corporation",
#     }
#     for k, v in replacements.items():
#         text = re.sub(rf"\b{k}\b", v, text)

#     return text.strip()


# # -------------------------- CUSTOMER NAME CLEANER -------------------------- #
# def clean_customer_name(name):
#     text = normalize(name, "customer_name")

#     # Remove legal suffixes
#     text = re.sub(
#         r"\b(private limited|private|limited|ltd|co|corporation)\b",
#         "",
#         text
#     )

#     # 🔥 NORMALIZE SPELLING VARIANTS
#     spelling_map = {
#         "jewellers": "jeweler",
#         "jewellery": "jeweler",
#         "jewelers": "jeweler",
#         "jwellers": "jeweler",
#         "jwellery": "jeweler",
#     }

#     for k, v in spelling_map.items():
#         text = re.sub(rf"\b{k}\b", v, text)

#     text = re.sub(r"\s+", " ", text)
#     return text.strip()



# # -------------------------- PO KEY -------------------------- #
# def build_po_key(po: dict) -> tuple:
#     return (
#         clean_customer_name(po.get("customer_name")),
#         normalize(po.get("po_number"), "po_number"),
#     )


# # -------------------------- JSON SAFE -------------------------- #
# def make_json_safe(obj):
#     if isinstance(obj, (date, datetime)):
#         return obj.isoformat()
#     if isinstance(obj, Decimal):
#         return float(obj)
#     if isinstance(obj, bytes):
#         try:
#             return obj.decode("utf-8")
#         except UnicodeDecodeError:
#             return base64.b64encode(obj).decode("utf-8")
#     return obj


# # -------------------------- CANDIDATE SYSTEM PO SEARCH -------------------------- #
# def candidate_system_pos(scanned, system_pos):
#     scanned_cust = clean_customer_name(scanned.get("customer_name"))
#     scanned_po = normalize(scanned.get("po_number"), "po_number")

#     candidates = []
#     for sys in system_pos:
#         if not sys.get("customer_name") or not sys.get("po_number"):
#             continue

#         cust_sim = fuzz.partial_ratio(scanned_cust, clean_customer_name(sys["customer_name"]))
#         po_sim = fuzz.partial_ratio(scanned_po, normalize(sys["po_number"], "po_number"))

#         if po_sim >= 70 or cust_sim >= 80:
#             candidates.append(sys)
#     return candidates[:5]


# # -------------------------- FIELDS TO COMPARE -------------------------- #
# FIELDS_TO_COMPARE = [
#     "customer_name", "vendor_number", "po_date", "po_number",
#     "delivery_date", "cancel_date", "gold_lock", "ec_style_number",
#     "customer_style_number", "kt", "color", "quantity", "description"
# ]


# def compare_po_fields(scanned, system):
#     mismatches = []
#     for field in FIELDS_TO_COMPARE:
#         s_val = scanned.get(field)
#         sys_val = system.get(field)
#         # ------------------ SPECIAL HANDLING ------------------ #
#         if field == "customer_name":
#             s_val = clean_customer_name(s_val)
#             sys_val = clean_customer_name(sys_val)
#         elif field in ("gold_karat", "gold_lock", "kt"):
#             s_val = normalize(s_val, "gold_karat")
#             sys_val = normalize(sys_val, "gold_karat")
#         else:
#             s_val = normalize(s_val, field)
#             sys_val = normalize(sys_val, field)

#         if s_val != sys_val:
#             mismatches.append({
#                 "field": field,
#                 "scanned": scanned.get(field),
#                 "system": system.get(field)
#             })

#     return mismatches

# # -------------------------- LLM FALLBACK -------------------------- #
# async def llm_fallback_match(scanned_po, candidates):
#     safe_scanned = {k: make_json_safe(v) for k, v in scanned_po.items()}
#     safe_candidates = [{k: make_json_safe(v) for k, v in c.items()} for c in candidates]

#     prompt = f"""
# You are a PO reconciliation engine.

# Task: Match a scanned PO to one of the system POs.

# Rules:
# 1. PO Number is strongest signal.
# 2. Customer Name: handle abbreviations, typos, word order.
# 3. Gold Karat / Gold Lock / Kt differences are ignored.
# 4. Quantity units may differ.
# 5. Date fields normalized to YYYY-MM-DD.
# 6. Color & Description: ignore word order, minor typos.
# 7. Respond ONLY in JSON:
# {{ "matched_index": number | null, "confidence": 0.0-1.0 }}

# Scanned PO:
# {json.dumps(safe_scanned, indent=2)}

# System PO Candidates:
# {json.dumps(safe_candidates, indent=2)}
# """
#     resp = openai_client.chat.completions.create(
#         model="gpt-4.1-mini",
#         temperature=0,
#         messages=[{"role": "user", "content": prompt}]
#     )

#     raw = resp.choices[0].message.content.strip()
#     raw = re.sub(r"^```json|```$", "", raw, flags=re.IGNORECASE).strip()
#     match = re.search(r"\{.*\}", raw, re.DOTALL)
#     if not match:
#         return None
#     result = json.loads(match.group())
#     if result.get("matched_index") is None or result.get("confidence", 0) < 0.85:
#         return None
#     idx = result["matched_index"]
#     return candidates[idx] if 0 <= idx < len(candidates) else None


# # -------------------------- MAIN SERVICE -------------------------- #
# async def generate_missing_po_report_service(repo, user_id: int):
#     scanned_pos = await repo.get_all_po_details()
#     system_pos = await repo.get_all_system_po_details()

#     system_map = {
#         build_po_key(po): po
#         for po in system_pos
#         if po.get("customer_name") and po.get("po_number")
#     }

#     existing_mismatches = await repo.get_all_mismatches()
#     existing_keys = {
#         (m["po_det_id"], m["system_po_id"], m["mismatch_attribute"])
#         for m in existing_mismatches
#     }

#     llm_cache = {}

#     for scanned in scanned_pos:
#         if not scanned.get("customer_name") or not scanned.get("po_number"):
#             continue

#         scanned_key = build_po_key(scanned)
#         system_po = system_map.get(scanned_key)

#         # ------------------ USE FUZZY / LLM MATCH ------------------ #
#         if not system_po:
#             if scanned_key not in llm_cache:
#                 candidates = candidate_system_pos(scanned, system_pos)
#                 # Call LLM fallback if needed
#                 if candidates:
#                     system_po = await llm_fallback_match(scanned, candidates)
#                 llm_cache[scanned_key] = system_po
#             else:
#                 system_po = llm_cache[scanned_key]

#         # ------------------ MARK PO AS MISSING ------------------ #
#         if not system_po:
#             exists = await repo.get_existing_po_missing(po_det_id=scanned["po_det_id"])
#             if not exists:
#                 await repo.insert_po_missing(
#                     po_det_id=scanned["po_det_id"],
#                     user_id=user_id,
#                     system_po_id=None,
#                     attribute="po_missing",
#                     system_value="",
#                     scanned_value=scanned.get("po_number"),
#                     comment="PO not found"
#                 )
#             continue

#         # ------------------ COMPARE FIELDS ------------------ #
#         mismatches = compare_po_fields(scanned, system_po)
#         for m in mismatches:
#             key = (
#                 scanned["po_det_id"],
#                 system_po["system_po_id"],
#                 m["field"]
#             )
#             if key in existing_keys:
#                 continue

#             await repo.insert_mismatch(
#                 po_det_id=scanned["po_det_id"],
#                 user_id=user_id,
#                 system_po_id=system_po["system_po_id"],
#                 field=m["field"],
#                 system_value=str(m["system"]),
#                 scanned_value=str(m["scanned"]),
#                 comment=f"{m['field']} mismatch"
#             )
#             existing_keys.add(key)

#     return {
#         "status": "success",
#         "message": "PO missing & mismatch report generated successfully"
#     }

FIELDS_TO_COMPARE = [
    "customer_name",
    "vendor_number",
    "po_date",
    "po_number",
    "delivery_date",
    "cancel_date",
    "gold_lock",
    "ec_style_number",
    "customer_style_number",
    "gold_karat",
    "color",
    "quantity",
    "description"
]

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


async def llm_batch_match(scanned_pos, system_pos):
    prompt = f"""
You are a PO matching engine.

Match scanned POs to system POs using ONLY:
- customer_name
- po_number

Rules:
- Handle spelling mistakes, abbreviations, extra/missing letters.
- One scanned PO matches at most one system PO.
- If no confident match exists, return null.

Return ONLY JSON:
[
  {{
    "scanned_po_det_id": number,
    "system_po_id": number | null,
    "confidence": 0.0-1.0
  }}
]

Scanned POs:
{json.dumps(scanned_pos)}

System POs:
{json.dumps(system_pos)}
"""

    resp = openai_client.chat.completions.create(
        model="gpt-4.1-mini",
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = resp.choices[0].message.content.strip()
    raw = re.sub(r"^```json|```$", "", raw, flags=re.IGNORECASE).strip()
    return json.loads(raw)


async def llm_batch_compare(matched_pairs):
    prompt = f"""
You are an expert PO field comparison engine.

Compare ONLY the following fields:
{FIELDS_TO_COMPARE}

Your goal is to detect **real business mismatches**. Do NOT report differences caused by minor spelling mistakes, abbreviations, word order, or formatting.

Rules:
1. Treat minor spelling errors, missing/extra letters, or phonetic variations as SAME.
2. Treat abbreviations and expansions (e.g., Pvt, Ltd, Private Limited) as SAME.
3. Ignore punctuation, dots, commas, extra spaces, capitalization.
4. Ignore word order in names, colors, or descriptions.
5. Ignore formatting differences in dates (YYYY-MM-DD, DD/MM/YYYY) or numbers/quantities.
6. Only report a mismatch if the values clearly indicate different meanings or entities.

Return ONLY JSON in the following format:
[
  {{
    "po_det_id": number,
    "system_po_id": number,
    "field": string,
    "scanned_value": string,
    "system_value": string
  }}
]

Here are the matched PO pairs to compare:
{json.dumps(matched_pairs, indent=2)}
"""

    # Call OpenAI LLM
    resp = openai_client.chat.completions.create(
        model="gpt-4.1-mini",
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )

    # Clean up response
    raw = resp.choices[0].message.content.strip()
    raw = re.sub(r"^```json|```$", "", raw, flags=re.IGNORECASE).strip()

    # Parse JSON
    try:
        result = json.loads(raw)
        if not isinstance(result, list):
            raise ValueError("LLM response is not a JSON list")
        return result
    except Exception as e:
        # fallback: return empty list if parsing fails
        print(f"LLM parsing error: {e}")
        return []


def chunk(data, size):
    for i in range(0, len(data), size):
        yield data[i:i + size]


async def generate_missing_po_report_service(repo, user_id: int):

    scanned_pos = await repo.get_all_po_details()
    system_pos = await repo.get_all_system_po_details()

    scanned_pos = [{k: make_json_safe(v) for k, v in po.items()} for po in scanned_pos]
    system_pos = [{k: make_json_safe(v) for k, v in po.items()} for po in system_pos]

    matched_scanned_ids = set()
    matched_system_ids = set()

    # Chunk ONLY scanned POs
    for scanned_batch in chunk(scanned_pos, 25):

        matches = await llm_batch_match(scanned_batch, system_pos)

        matched_pairs = []

        for m in matches:
            scanned = next(
                (p for p in scanned_batch if p["po_det_id"] == m["scanned_po_det_id"]),
                None
            )

            if not scanned:
                continue

            if m["system_po_id"] and m["confidence"] >= 0.85:
                system = next(
                    (p for p in system_pos if p["system_po_id"] == m["system_po_id"]),
                    None
                )

                if system:
                    matched_scanned_ids.add(scanned["po_det_id"])
                    matched_system_ids.add(system["system_po_id"])

                    matched_pairs.append({
                        "po_det_id": scanned["po_det_id"],
                        "system_po_id": system["system_po_id"],
                        "scanned": {f: scanned.get(f) for f in FIELDS_TO_COMPARE},
                        "system": {f: system.get(f) for f in FIELDS_TO_COMPARE}
                    })

        # Compare ONLY matched pairs
        if matched_pairs:
            mismatches = await llm_batch_compare(matched_pairs)

            for mm in mismatches:
                # Check in DB if mismatch already exists
                exists = await repo.mismatch_exists(
                    user_id=user_id,
                    po_det_id=mm["po_det_id"],
                    system_po_id=mm["system_po_id"],
                    mismatch_attribute=mm["field"],
                    scanned_value=str(mm["scanned_value"]),
                    system_value=str(mm["system_value"])
                )
                if not exists:
                    await repo.insert_mismatch(
                        po_det_id=mm["po_det_id"],
                        user_id=user_id,
                        system_po_id=mm["system_po_id"],
                        field=mm["field"],
                        system_value=str(mm["system_value"]),
                        scanned_value=str(mm["scanned_value"]),
                        comment=f"{mm['field']} mismatch"
                    )

    # Missing scanned POs (ONCE)
    for po in scanned_pos:
        if po["po_det_id"] not in matched_scanned_ids:
            # Check if already exists
            exists = await repo.po_missing_exists(
                user_id=user_id,
                po_det_id=po["po_det_id"],
                system_po_id=None,
                mismatch_attribute="po_missing",
                scanned_value=po.get("po_number"),
                system_value=""
            )
            if not exists:
                await repo.insert_po_missing(
                    po_det_id=po["po_det_id"],
                    user_id=user_id,
                    system_po_id=None,
                    attribute="po_missing",
                    system_value="",
                    scanned_value=po.get("po_number"),
                    comment="PO not found in system"
                )

    # Missing system POs (ONCE)
    for po in system_pos:
        if po["system_po_id"] not in matched_system_ids:
            exists = await repo.po_missing_exists(
                user_id=user_id,
                po_det_id=None,
                system_po_id=po["system_po_id"],
                mismatch_attribute="po_missing",
                scanned_value="",
                system_value=po.get("po_number")
            )
            if not exists:
                await repo.insert_po_missing(
                    po_det_id=None,
                    user_id=user_id,
                    system_po_id=po["system_po_id"],
                    attribute="po_missing",
                    system_value=po.get("po_number"),
                    scanned_value="",
                    comment="PO not found in scanned data"
                )

    return {
        "status": "success",
        "message": "LLM-based PO missing & mismatch report generated successfully (duplicate-safe)"
    }
# --------------------------data comparison logic end--------------------------#