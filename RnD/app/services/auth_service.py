
from dotenv import load_dotenv
import os, base64
import httpx

# Load the .env file
load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
REDIRECT_URI = os.getenv("REDIRECT_URI")
GRAPH_API = os.getenv("GRAPH_API")

from datetime import datetime, timezone




def get_auth_url():
    return (
        f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize?"
        f"client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}"
        f"&response_mode=query&scope=offline_access%20Mail.Read%20Mail.ReadWrite"
    )

async def exchange_code_for_token(code: str):
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        'client_id': CLIENT_ID,
        # 'scope': 'Mail.Read Mail.ReadWrite offline_access Calendars.Read Calendars.ReadWrite',
        'scope': 'Mail.Read Mail.ReadWrite',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code',
        'client_secret': CLIENT_SECRET
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data)
        token_json = response.json()
    
    access_token = token_json.get("access_token")
    if access_token:
        # Redirect to frontend with token in query (or better, store in cookie or session)
        return f"http://localhost:5173/mails?token={access_token}"
    return {"error": "Token exchange failed"}
    
    
    
async def fetch_mails(access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    
        
    current_date = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    print(current_date)
        
    url = f"{GRAPH_API}/me/messages?$top=100"
    # url = f"{GRAPH_API}/me/events"
    # url = f"{GRAPH_API}/me/messages?$filter=receivedDateTime ge {current_date}&$orderby=receivedDateTime desc"


    results = []
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        messages = response.json().get('value', [])
        for msg in messages:
            subject = msg.get('subject', '')
            body = msg.get('bodyPreview', '')
            has_attachments = msg.get('hasAttachments', False)

            if any(k in subject.lower() or k in body.lower() for k in ["search", "research", "r&d"]):
                email = {
                    "subject": subject,
                    "from": msg['from']['emailAddress']['address'],
                    "bodyPreview": body,
                    "id": msg['id'],
                    "attachments": []
                }

                if has_attachments:
                    att_url = f"{GRAPH_API}/me/messages/{msg['id']}/attachments"
                    att_resp = await client.get(att_url, headers=headers)
                    for att in att_resp.json().get('value', []):
                        filename = att['name']
                        content = base64.b64decode(att['contentBytes'])
                        os.makedirs("attachments", exist_ok=True)
                        with open(f"attachments/{filename}", "wb") as f:
                            f.write(content)
                        email["attachments"].append(filename)

                results.append(email)

    return results