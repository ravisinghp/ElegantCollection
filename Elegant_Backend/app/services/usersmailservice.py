
from dotenv import load_dotenv
import os, base64
import httpx
from urllib.parse import urlencode
import hashlib
# import openpyxl
# import xlrd

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

from datetime import datetime, timezone,timedelta
import re
from typing import List, Dict, Any, Optional
import html
import io

import aiohttp, json
from datetime import datetime, timezone
from typing import List, Dict, Any
from pptx import Presentation  # for PPTX support

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

#### This code is written by sushanth and this code will fetching emails and attachment and return to the frontend #########

# async def fetch_mails(access_token: str):
#     headers = {"Authorization": f"Bearer {access_token}"}
    
        
#     current_date = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
#     print(current_date)
        
#     url = f"{GRAPH_API}/me/messages?$top=100"
#     # url = f"{GRAPH_API}/me/events"
#     # url = f"{GRAPH_API}/me/messages?$filter=receivedDateTime ge {current_date}&$orderby=receivedDateTime desc"


#     results = []
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url, headers=headers)
#         messages = response.json().get('value', [])
#         for msg in messages:
#             subject = msg.get('subject', '')
#             body = msg.get('bodyPreview', '')
#             has_attachments = msg.get('hasAttachments', False)

#             if any(k in subject.lower() or k in body.lower() for k in ["search", "research", "r&d"]):
#                 email = {
#                     "subject": subject,
#                     "from": msg['from']['emailAddress']['address'],
#                     "bodyPreview": body,
#                     "id": msg['id'],
#                     "attachments": []
#                 }

#                 if has_attachments:
#                     att_url = f"{GRAPH_API}/me/messages/{msg['id']}/attachments"
#                     att_resp = await client.get(att_url, headers=headers)
#                     for att in att_resp.json().get('value', []):
#                         filename = att['name']
#                         content = base64.b64decode(att['contentBytes'])
#                         os.makedirs("attachments", exist_ok=True)
#                         with open(f"attachments/{filename}", "wb") as f:
#                             f.write(content)
#                         email["attachments"].append(filename)

#                 results.append(email)

#     return results

##### This code is used to fetch inbox email by r&d,research,search keyword and save into the database with attachment also #########

# async def fetch_and_save_mails(access_token: str, mails_repo: "MailsRepository") -> List[Dict[str, Any]]:
#     headers = {"Authorization": f"Bearer {access_token}"}

#     # Select explicit fields to ensure we have body and recipients
#     url = (
#         f"{GRAPH_API}/me/messages?$top=100"
#         f"&$select=id,subject,body,from,toRecipients,ccRecipients,bccRecipients,hasAttachments,receivedDateTime"
#     )

#     def strip_html_and_count_words(html_content: Optional[str]) -> int:
#         if not html_content:
#             return 0
#         text = re.sub(r"<[^>]+>", " ", html_content)
#         words = re.findall(r"\w+", text)
#         return len(words)

#     def strip_html_to_text(html_content: Optional[str]) -> str:
#         if not html_content:
#             return ""
#         # Remove tags
#         text = re.sub(r"<[^>]+>", " ", html_content)
#         # Unescape entities
#         text = html.unescape(text)
#         # Normalize whitespace
#         text = re.sub(r"\s+", " ", text).strip()
#         return text

#     def clean_email_body(body_text: str) -> str:
#         """Remove embedded headers/metadata from body while keeping message content."""
#         if not body_text:
#             return ""
#         lines = body_text.split("\n")
#         cleaned_lines: List[str] = []
#         # Patterns to skip when they appear at the start of a line (case-insensitive)
#         skip_line_starts = [
#             r"^From:", r"^To:", r"^Cc:", r"^CC:", r"^BCC:", r"^Bcc:", r"^Sent:", r"^Subject:", r"^Date:",
#             r"^Reply-To:", r"^Message-ID:", r"^X-.*?:", r"^Content-Type:", r"^Content-Transfer-Encoding:", r"^MIME-Version:",
#             r"^Return-Path:", r"^Delivered-To:", r"^Received:", r"^On .* wrote:", r"^-----Original Message-----",
#             # common meeting/footer noise
#             r"^Microsoft Teams$", r"^Need help\?$", r"^Join the meeting now$", r"^Meeting ID:", r"^Passcode:",
#             r"^For organisers:", r"^Meeting options$", r"^_{6,}$",
#         ]
#         # Also skip lines that are just URLs
#         url_re = re.compile(r"^(https?://|www\.)", re.IGNORECASE)
#         skip_res = [re.compile(pat, re.IGNORECASE) for pat in skip_line_starts]
#         for raw_line in lines:
#             line = raw_line.strip()
#             if not line:
#                 continue
#             if url_re.match(line):
#                 continue
#             should_skip = any(rx.match(line) for rx in skip_res)
#             if should_skip:
#                 continue
#             cleaned_lines.append(line)
#         cleaned_text = " ".join(cleaned_lines)
#         cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
#         return cleaned_text or body_text.strip()

#     def iso_to_date(iso_dt: Optional[str]) -> Optional[str]:
#         if not iso_dt:
#             return None
#         try:
#             return iso_dt[:10]
#         except Exception:
#             return None

#     def truncate(value: Optional[str], max_len: int) -> Optional[str]:
#         if value is None:
#             return None
#         return value if len(value) <= max_len else value[:max_len]

#     results: List[Dict[str, Any]] = []
#     timeout = httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=30.0)
#     async with httpx.AsyncClient(timeout=timeout) as client:
#         response = await client.get(url, headers=headers)
#         response.raise_for_status()
#         messages = response.json().get('value', [])
#         for msg in messages:

#             graph_mail_id = msg.get('id')
#             # Skip if this email is already in DB
#             if await mails_repo.mail_exists(graph_mail_id):
#                 continue

#             subject = msg.get('subject', '')
#             body_obj = msg.get('body') or {}
#             body_content = body_obj.get('content')
#             body_preview = msg.get('bodyPreview', '')
#             body_used = body_content or body_preview or ''

#             # Convert to plain text and compute word count from plain text
#             body_plain = strip_html_to_text(body_used)
#             body_clean = clean_email_body(body_plain)
#             if not body_clean.strip():
#                 body_clean = body_plain
#             word_count_int = len(re.findall(r"\w+", body_clean))
#             word_count_str = str(word_count_int)

#             # Build matched keywords list/CSV and skip if none
#             keywords_to_check = ["search", "research", "r&d"]
#             lower_subject = subject.lower() if subject else ""
#             lower_body = body_clean.lower()
#             matched_keywords_list = [k for k in keywords_to_check if (k in lower_subject or k in lower_body)]
#             if not matched_keywords_list:
#                 continue
#             matched_keywords_csv = ", ".join(matched_keywords_list)

#             # Build counts for matched keywords across subject+body
#             keyword_counts: Dict[str, int] = {}
#             for k in keywords_to_check:
#                 # count = lower_subject.count(k) + lower_body.count(k)
#                 # Whole word pattern
#                 pattern = r'\b' + re.escape(k.lower()) + r'\b'

#                 subject_matches = re.findall(pattern, lower_subject)
#                 body_matches = re.findall(pattern, lower_body)

#                 count = len(subject_matches) + len(body_matches)
#                 if count > 0:
#                     keyword_counts[k] = count
#             matched_keyword_counts_csv = ", ".join(f"{k}:{c}" for k, c in keyword_counts.items())

#             from_email = (
#                 (msg.get('from') or {}).get('emailAddress', {}).get('address')
#                 if msg.get('from') else None
#             )

#             def collect_addresses(key: str) -> Optional[str]:
#                 out: List[str] = []
#                 for rec in msg.get(key, []) or []:
#                     address = (rec.get('emailAddress') or {}).get('address')
#                     if address:
#                         out.append(address)
#                 return ",".join(out) if out else None

#             to_emails = collect_addresses('toRecipients')
#             cc_emails = collect_addresses('ccRecipients')
#             bcc_emails = collect_addresses('bccRecipients')
#             mail_cc_merged = ",".join([p for p in [cc_emails, bcc_emails] if p]) or None

#             has_attachments = bool(msg.get('hasAttachments', False))
#             received_dt = msg.get('receivedDateTime')
#             date_only = iso_to_date(received_dt)

#             # Truncate to fit DB schema
#             # subject_trunc = truncate(subject, 500)
#             # from_trunc = truncate(from_email, 255)
#             # to_trunc = truncate(to_emails, 255)
#             # cc_trunc = truncate(mail_cc_merged, 255)

#             # Insert into mail_details and get mail_dtl_id
#             mail_dtl_id = await mails_repo.insert_mail_detail(
#                 subject=subject,
#                 body=body_clean,
#                 date_time=date_only,
#                 mail_from=from_email,
#                 mail_to=to_emails,
#                 mail_cc=mail_cc_merged,
#                 word_count=word_count_str,
#                 keyword=matched_keywords_csv,
#                 repeated_keyword=matched_keyword_counts_csv,
#                 graph_mail_id=graph_mail_id,  # store unique Graph ID
#             )




#             saved_attachments: List[str] = []
#             if has_attachments:
#                 att_url = f"{GRAPH_API}/me/messages/{msg.get('id')}/attachments"
#                 att_resp = await client.get(att_url, headers=headers)
#                 att_resp.raise_for_status()
#                 for att in att_resp.json().get('value', []):
#                     filename = att.get('name')
#                     content_type = att.get('contentType')
#                     content_bytes_b64 = att.get('contentBytes')
#                     if not content_bytes_b64:
#                         continue
#                     content = base64.b64decode(content_bytes_b64)
#                     # Remove/replace invalid or risky characters
#                     safe_filename = re.sub(r'[\\/*?:"<>|&]', "_", filename)  # replace & as well
#                     os.makedirs("attachments", exist_ok=True)
#                     file_path = os.path.join("attachments", safe_filename)
#                     try:
#                         with open(file_path, "wb") as f:
#                             f.write(content)
#                     except Exception:
#                         file_path = None

#                     # Compute attachment word count where feasible
#                     attach_word_count_str: Optional[str] = None
#                     attachment_text: Optional[str] = None
#                     try:
#                         ct = (content_type or "").lower()
#                         fname = (filename or "").lower()
#                         if ct.startswith("text/") or fname.endswith((".txt", ".md", ".csv", ".log")):
#                             try:
#                                 attachment_text = content.decode("utf-8", errors="ignore")
#                                 attach_word_count_str = str(len(re.findall(r"\w+", attachment_text)))
#                             except Exception:
#                                 attach_word_count_str = None
#                         elif ct == "application/pdf" or fname.endswith(".pdf"):
#                             if PyPDF2 is not None:
#                                 try:
#                                     reader = PyPDF2.PdfReader(io.BytesIO(content))
#                                     pages_text = []
#                                     for page in getattr(reader, "pages", []):
#                                         try:
#                                             pages_text.append(page.extract_text() or "")
#                                         except Exception:
#                                             continue
#                                     attachment_text = " ".join(pages_text)
#                                     attach_word_count_str = str(len(re.findall(r"\w+", attachment_text)))
#                                 except Exception:
#                                     attach_word_count_str = None
#                         elif (
#                             ct in (
#                                 "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
#                                 "application/msword",
#                             )
#                             or fname.endswith(".docx")
#                         ):
#                             if docx is not None:
#                                 try:
#                                     document = docx.Document(io.BytesIO(content))
#                                     attachment_text = " ".join([p.text or "" for p in document.paragraphs])
#                                     attach_word_count_str = str(len(re.findall(r"\w+", attachment_text)))
#                                 except Exception:
#                                     attach_word_count_str = None
#                     except Exception:
#                         attach_word_count_str = None

#                     # Check for keywords in attachment text
#                     attachment_keywords = []
#                     attachment_keyword_counts = {}
#                     if attachment_text:
#                         lower_attachment_text = attachment_text.lower()
#                         for keyword in keywords_to_check:
#                             # count = lower_attachment_text.count(keyword.lower())
#                             # \b ensures whole word match, re.escape handles special characters in keyword
#                             pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
#                             matches = re.findall(pattern, lower_attachment_text)
#                             count = len(matches)
#                             if count > 0:
#                                 attachment_keywords.append(keyword)
#                                 attachment_keyword_counts[keyword] = count
                    
#                     # Save attachment only if keywords are found
#                     if attachment_keywords:
#                         attachment_keywords_csv = ", ".join(attachment_keywords)  # "r&d,search"
#                         attachment_keyword_counts_csv = ", ".join([f"{k}:{c}" for k, c in attachment_keyword_counts.items()])  # "r&d:3,search:2"
                        
#                         await mails_repo.insert_attachment(
#                             mail_dtl_id=mail_dtl_id,
#                             attach_name=filename,
#                             attach_type=content_type,
#                             attach_path=file_path,
#                             word_count=attach_word_count_str,
#                             keyword=attachment_keywords_csv,  # Save keywords found in attachment like "r&d,search"
#                             repeated_keyword=attachment_keyword_counts_csv,  # Save keyword counts like "r&d:3,search:2"
#                         )
#                         if filename:
#                             saved_attachments.append(filename)
                    
                    

#             results.append({
#                 "mail_dtl_id": mail_dtl_id,
#                 "subject": subject,
#                 "from": from_email,
#                 "to": to_emails,
#                 "cc": mail_cc_merged,
#                 "word_count": word_count_int,
#                 "has_attachments": has_attachments,
#                 "attachments": saved_attachments,
#             })

#     return results




##This code is used to fetch folder names which is present in outlook of that user
# async def fetch_all_folders(access_token: str) -> List[Dict[str, Any]]:
#     """
#     Fetch all Outlook mail folders for the authenticated user.
#     """
#     headers = {"Authorization": f"Bearer {access_token}"}
    
#     timeout = httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=30.0)
#     async with httpx.AsyncClient(timeout=timeout) as client:
#         folder_resp = await client.get(f"{GRAPH_API}/me/mailFolders", headers=headers)
#         folder_resp.raise_for_status()
#         folders = folder_resp.json().get("value", [])

#         folder_list = []
#         for folder in folders:
#             folder_list.append({
#                 "id": folder.get("id"),
#                 "name": folder.get("displayName")
#             })
        
#         return folder_list

### This code is used to fetch folder names upto 200 folders
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



async def fetch_and_save_mails_by_folders(access_token: str, folder_names: list[str], user_id: int, org_id: int, from_date: str, to_date: str, mails_repo: "MailsRepository") -> List[Dict[str, Any]]:
    headers = {"Authorization": f"Bearer {access_token}"}
    results: List[Dict[str, Any]] = []

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
        cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
        return cleaned_text or body_text.strip()

    def iso_to_date(iso_dt: Optional[str]) -> Optional[str]:
        if not iso_dt:
            return None
        try:
            return iso_dt[:10]
        except Exception:
            return None

    def collect_addresses_from_message(msg: Dict[str, Any], key: str) -> Optional[str]:
        out: List[str] = []
        for rec in msg.get(key, []) or []:
            address = (rec.get('emailAddress') or {}).get('address')
            if address:
                out.append(address)
        return ",".join(out) if out else None

    results: List[Dict[str, Any]] = []

    # Convert to full ISO datetime range
    from_date_iso = f"{from_date}T00:00:00Z"       # start of day
    to_date_iso = f"{to_date}T23:59:59Z"           # end of day

    print("From:", from_date_iso)
    print("To:  ", to_date_iso)
    # timeout = httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=30.0)
    timeout = httpx.Timeout(connect=10.0, read=300.0, write=60.0, pool=30.0)## This code is 
    async with httpx.AsyncClient(timeout=timeout) as client:
        folder_resp = await client.get(f"{GRAPH_API}/me/mailFolders?$top=200&$expand=childFolders", headers=headers)
        folder_resp.raise_for_status()
        folders = folder_resp.json().get("value", [])

        # Convert frontend input to lowercase for comparison
        wanted = {f.lower() for f in folder_names}
        print("wanted:",wanted)
        #This code is used to fetch keyword from database
        keywords = await mails_repo.fetch_keywords(org_id)

        for folder in folders:
            folder_id = folder.get("id")
            folder_name = folder.get("displayName", "")
            print("folderid:",folder_id)
            print("folder_name:",folder_name)
            if folder_name.lower() not in wanted:
                continue
            if not folder_id:
                continue

            # url = (
            #     f"{GRAPH_API}/me/mailFolders/{folder_id}/messages?$top=100"
            #     f"&$select=id,subject,body,from,toRecipients,ccRecipients,bccRecipients,hasAttachments,receivedDateTime,bodyPreview"
            # )
            # Initial URL with filter
            url = (
                f"{GRAPH_API}/me/mailFolders/{folder_id}/messages"
                f"?$filter=receivedDateTime ge {from_date_iso} and receivedDateTime le {to_date_iso}"
                f"&$select=id,subject,body,from,toRecipients,ccRecipients,bccRecipients,hasAttachments,receivedDateTime,bodyPreview"
            )
            
            print("url:",url)

            # response = await client.get(url, headers=headers)
            # response.raise_for_status()
            # messages = response.json().get("value", [])
            messages: list[dict] = []
            next_url = url

            # Loop to fetch all messages using pagination
            while next_url:
                response = await client.get(next_url, headers=headers)
                response.raise_for_status()

                print("mailresponse status:", response.status_code)

                data = response.json()
                print("mailresponsedata:", data)  # Be careful — large responses may clutter logs

                messages.extend(data.get("value", []))

                # Get next page URL if present
                next_url = data.get("@odata.nextLink")

                print(f"Total messages fetched: {len(messages)}")

            for msg in messages:
                graph_mail_id = msg.get('id')
                if not graph_mail_id:
                    continue

                # Skip event/meeting messages
                if msg.get('@odata.type') in ['#microsoft.graph.eventMessage', '#microsoft.graph.eventMessageRequest']:
                    continue

                if await mails_repo.mail_exists(graph_mail_id, user_id):
                    continue

                subject = msg.get('subject', '')
                body_obj = msg.get('body') or {}
                body_content = body_obj.get('content')
                print(body_content)
                body_preview = msg.get('bodyPreview', '')
                body_used = body_content or body_preview or ''

                body_plain = strip_html_to_text(body_used)
                body_clean = clean_email_body(body_plain)
                if not body_clean.strip():
                    body_clean = body_plain
                word_count_int = len(re.findall(r"\w+", body_clean))
                word_count_str = str(word_count_int)

                keywords_to_check = keywords
                # keywords_to_check = ["analysis", "market", "research"]
                lower_subject = subject.lower() if subject else ""
                lower_body = body_clean.lower()
                
                # Only check keywords in the body
                matched_keywords_list_in_body = [k for k in keywords_to_check if k in lower_body]
                if not matched_keywords_list_in_body:
                    # Skip saving if no keywords found in the body
                    continue
                
                matched_keywords_list = [k for k in keywords_to_check if (k in lower_subject or k in lower_body)]
                if not matched_keywords_list:
                    continue
                matched_keywords_csv = ", ".join(matched_keywords_list)

                keyword_counts: Dict[str, int] = {}
                for k in keywords_to_check:
                    pattern = r'\b' + re.escape(k.lower()) + r'\b'
                    subject_matches = re.findall(pattern, lower_subject)
                    body_matches = re.findall(pattern, lower_body)
                    count = len(subject_matches) + len(body_matches)
                    if count > 0:
                        keyword_counts[k] = count
                matched_keyword_counts_csv = ", ".join(f"{k}:{c}" for k, c in keyword_counts.items())

                from_email = (
                    (msg.get('from') or {}).get('emailAddress', {}).get('address')
                    if msg.get('from') else None
                )
                to_emails = collect_addresses_from_message(msg, 'toRecipients')
                cc_emails = collect_addresses_from_message(msg, 'ccRecipients')
                bcc_emails = collect_addresses_from_message(msg, 'bccRecipients')
                mail_cc_merged = ",".join([p for p in [cc_emails, bcc_emails] if p]) or None

                has_attachments = bool(msg.get('hasAttachments', False))
                received_dt = msg.get('receivedDateTime')
                date_only = iso_to_date(received_dt)

                mail_dtl_id = await mails_repo.insert_mail_detail(
                    subject=subject,
                    body=body_clean,
                    date_time=date_only,
                    mail_from=from_email,
                    mail_to=to_emails,
                    mail_cc=mail_cc_merged,
                    word_count=word_count_str,
                    keyword=matched_keywords_csv,
                    repeated_keyword=matched_keyword_counts_csv,
                    graph_mail_id=graph_mail_id,
                    folder_name=folder_name,
                    user_id=user_id,
                    created_by=user_id,
                )

                saved_attachments: List[str] = []
                if has_attachments:
                    att_url = f"{GRAPH_API}/me/messages/{graph_mail_id}/attachments"
                    att_resp = await client.get(att_url, headers=headers)
                    att_resp.raise_for_status()
                    for att in att_resp.json().get('value', []):
                        filename = att.get('name')
                        content_type = att.get('contentType')
                        content_bytes_b64 = att.get('contentBytes')
                        if not content_bytes_b64:
                            continue
                        content = base64.b64decode(content_bytes_b64)
                        ## This code is used to to check attachment is already presnt in db or not
                        file_hash = compute_file_hash(content)

                        # âœ… Skip duplicate attachment
                        if await mails_repo.attachment_exists(file_hash):
                            continue

                        #------- code end--------------------#
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
                            for keyword in keywords_to_check:
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
                                keyword=attachment_keywords_csv,  # Save keywords found in attachment like "r&d,search"
                                repeated_keyword=attachment_keyword_counts_csv,  # Save keyword counts like "r&d:3,search:2"
                                user_id=user_id,
                                created_by=user_id,
                                file_hash=file_hash,  # Save computed file hash
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
                    "has_attachments": has_attachments,
                    "attachments": saved_attachments,
                    "folder": folder_name,
                })

        # fetch past events and save into cal_master
        events = await fetch_and_save_past_events(
            access_token=access_token,
            user_id=user_id,
            orgid=org_id,
            keywords= keywords,
            from_date=from_date_iso,
            to_date=to_date_iso,
            mails_repo=mails_repo
        )

    return results


def compute_file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

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