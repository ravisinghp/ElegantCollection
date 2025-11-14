from fastapi import  APIRouter, Request
from fastapi.responses import RedirectResponse
from app.services.auth_service import get_auth_url, exchange_code_for_token, fetch_mails


router = APIRouter()



@router.get("/login")
def login():
    return {"auth_url": get_auth_url()}



@router.get("/callback")
async def callback(code: str):
    url = await exchange_code_for_token(code)
    # Redirect to frontend with token in query (or better, store in cookie or session)
    return RedirectResponse(url)
    



@router.post("/emails")
async def get_emails(request: Request):
    body = await request.json()
    token = body.get("access_token")
    return await fetch_mails(token)
   
   
   