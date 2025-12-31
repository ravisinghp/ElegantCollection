from fastapi import APIRouter, Body, Depends, HTTPException, Query
from starlette.status import HTTP_400_BAD_REQUEST

from app.api.dependencies.authentication import get_current_user_authorizer
from app.api.dependencies.database import get_repository
from app.core import config
from app.db.repositories.users import UsersRepository
from app.models.domain.users import User
from app.models.schemas.users import (
    UserInResponse,
    UserInUpdate,
    UserWithToken,
    UserWithoutToken,
)
from app.resources import strings
from app.services import jwt
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from app.models.domain.AdminDomain import GenerateMissingPoReport

# from app.services.authentication import check_email_is_taken, check_username_is_taken
from app.services.usersmailservice import (
    get_auth_url,
    exchange_code_for_token,
    fetch_and_save_mails_by_folders,
    fetch_all_folders,
    exchange_code_for_token_for_gmail,
    get_user_email,
    fetch_all_labels,
    fetch_and_save_mails_by_labels,
    generate_missing_po_report_service
)
from typing import List

from starlette.requests import Request

from starlette.responses import RedirectResponse
from starlette.responses import JSONResponse


# New imports for saving emails
from app.db.repositories.mails import MailsRepository

# from app.services.usersmailservice import fetch_and_save_mails_by_folders
from urllib.parse import urlparse, parse_qs
import os, base64
from dotenv import load_dotenv

# Load the .env file
load_dotenv()


router = APIRouter()

### urls getting from .env file
failed_url = os.getenv("failed_url")
success_url = os.getenv("success_url")

# this is working
# @router.get("/login")
# def login():
#     return {"auth_url": get_auth_url()}


@router.get("/login")
def login(provider: str = Query(..., regex="^(google|outlook)$")):
    return {"auth_url": get_auth_url(provider)}


@router.get("/callback")
async def callback(
    code: str,  
    mails_repo: MailsRepository = Depends(get_repository(MailsRepository)),
):
    # url = await exchange_code_for_token(code)
    # Attempt to fetch-and-save mails immediately server-side, then redirect
    try:
        url = await exchange_code_for_token(code)
        parsed_url = urlparse(url['url'])
        query_params = parse_qs(parsed_url.query)
        token = query_params.get("mail_token", [None])[0]
        if token:
            # await fetch_and_save_mails(token, mails_repo)
            # await fetch_and_save_mails_by_folders(token, mails_repo)
            return RedirectResponse(url['url'])
    except Exception:
        # If anything goes wrong, still continue with redirect
        pass
        # Fallback if no token
        return RedirectResponse(f"{failed_url}")
        # return RedirectResponse("http://localhost:3000/login?error=callback_failed")
        # return RedirectResponse("http://139.144.4.191:3000/login?error=callback_failed")


# from fastapi import APIRouter, Depends, HTTPException
# from fastapi.responses import RedirectResponse
# from app.services.outlook_oauth import exchange_code_for_token
# from app.db.repositories.mails import MailsRepository

# router = APIRouter(prefix="/auth/outlook")

# SUCCESS_REDIRECT = "http://localhost:5173/dashboard/user"
# FAIL_REDIRECT = "http://localhost:5173/login?error=outlook_failed"

# @router.get("/callback")
# async def callback(
#     code: str,
#     mails_repo: MailsRepository = Depends(get_repository(MailsRepository)),
# ):
#     try:
#         token_data = await exchange_code_for_token(code)

#         access_token = token_data.get("access_token")
#         refresh_token = token_data.get("refresh_token")

#         if not refresh_token:
#             raise HTTPException(status_code=400, detail="No refresh token")

#         # # ✅ SAVE REFRESH TOKEN
#         # await mails_repo.save_refresh_token(
#         #     refresh_token=refresh_token
#         # )

#         # (optional) use access token now
#         # await fetch_and_save_mails(access_token, mails_repo)

#         # ✅ REDIRECT TO REACT DASHBOARD
#         return RedirectResponse(
#             url="http://localhost:3000/dashboard?outlook=connected",
#             status_code=302
#         )

#     except Exception as e:
#         return RedirectResponse(
#             url="http://localhost:3000/dashboard?outlook=failed",
#             status_code=302
#         )


# This code is used for generaing token for gmail(Google OAuth)
@router.get("/google/callback")
async def google_callback(code: str):
    """Step 2: Google redirects here with code, exchange for token"""
    token_data = await exchange_code_for_token_for_gmail(code)
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")

    if not access_token:
        return RedirectResponse(f"{failed_url}")
        # return RedirectResponse("http://localhost:3000/login?error=token_failed")
        # return RedirectResponse("http://139.144.4.191:3000/login?error=callback_failed")

    # Get user email
    user_email = await get_user_email(access_token)

    # Redirect frontend with token & email
    return RedirectResponse(
        f"{success_url}?mail_token={access_token}&email={user_email}"
        # f"http://localhost:3000/dashboard/user?mail_token={access_token}&email={user_email}"
        # f"http://139.144.4.191:3000//dashboard/user?mail_token={access_token}&email={user_email}" # use in server
    )


# @router.post("/emails")
# async def get_emails(request: Request, mails_repo: MailsRepository = Depends(get_repository(MailsRepository))):
#     body = await request.json()
#     token = body.get("access_token")
#     if not token:
#         raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail={"error": "access_token missing"})
#     return await fetch_and_save_mails(token, mails_repo)


@router.post("/emails")
async def get_emails(
    request: Request,
    mails_repo: MailsRepository = Depends(get_repository(MailsRepository)),
):
    try:
        body = await request.json()
        token = body.get("access_token")
        folders = body.get("folders", [])  # <-- frontend sends list of folder names
        user_id = body.get("user_id")
        org_id = body.get("org_id")
        provider = body.get("provider")
        from_date = body.get("from_date")
        to_date = body.get("to_date")
        if not token:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail={"error": "access_token missing"},
            )

        if not folders:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail={"error": "folders list missing"},
            )

        if not user_id:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST, detail={"error": "user_id missing"}
            )

        if not org_id:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST, detail={"error": "org_id missing"}
            )

        if not provider:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail={"error": "provider is missing"},
            )

        if not from_date:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail={"error": "from_date is missing"},
            )

        if not to_date:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST, detail={"error": "to_date is missing"}
            )

        if provider == "outlook":
            # Call your mail fetching function
            return await fetch_and_save_mails_by_folders(
                token, folders, user_id, org_id, from_date, to_date, mails_repo
            )
        elif provider == "google":
            return await fetch_and_save_mails_by_labels(
                token, folders, user_id, org_id, mails_repo
            )

    except HTTPException as http_exc:
        # Pass through expected HTTP errors
        raise http_exc

    except Exception as e:
        # Catch unexpected errors
        raise HTTPException(
            status_code=500, detail={"error": f"Failed to fetch emails: {str(e)}"}
        )


@router.post("/fetch-all-folders")
async def get_emails_folders(
    request: Request,
    mails_repo: MailsRepository = Depends(get_repository(MailsRepository)),
):
    try:
        body = await request.json()
        token = body.get("access_token")
        provider = body.get("provider")  # Default to outlook if not provided
        if not token and provider not in ["google", "outlook"]:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail={"error": "access_token and provider missing"},
            )

        # Call your mail fetching function
        if provider == "google":
            return await fetch_all_labels(token)
        elif provider == "outlook":
            return await fetch_all_folders(token)
        else:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail={"error": "Invalid provider specified"},
            )

    except HTTPException as http_exc:
        # Pass through expected HTTP errors
        raise http_exc

    except Exception as e:
        # Catch unexpected errors
        raise HTTPException(
            status_code=500, detail={"error": f"Failed to fetch emails: {str(e)}"}
        )


# ---------------Simple health check endpoint--------------
@router.get("/health")
def health_check():
    return {"status": "ok"}


# ---------------------------------------------------------------------
# CONTROLLER ENDPOINT (IN SAME FILE)
# ---------------------------------------------------------------------
@router.post("/generate-missing-po-report")
async def generate_missing_po_report(
    request : GenerateMissingPoReport,
    repo: MailsRepository = Depends(get_repository(MailsRepository))
):
    result = await generate_missing_po_report_service(repo, request.user_id)
    return JSONResponse(content=jsonable_encoder(result))

