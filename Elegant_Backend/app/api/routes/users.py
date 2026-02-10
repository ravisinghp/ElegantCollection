from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from starlette.status import HTTP_400_BAD_REQUEST
from app.api.dependencies.database import get_repository
from app.db.repositories.mails import MailsRepository
from app.core.redis import redis_client
from app.services.usersmailservice import (
    get_auth_url,
    fetch_and_save_mails_by_folders,
    fetch_all_folders,
    fetch_all_labels,
    fetch_and_save_mails_by_labels,
    generate_missing_po_report_service,
    get_valid_outlook_token
)
from datetime import datetime, timedelta
import requests, json, time, os
from dotenv import load_dotenv
import asyncio

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
TENANT_ID = os.getenv("TENANT_ID")
JWTSECRET_KEY = os.getenv("JWTSECRET_KEY")
DEVICE_CODE_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/devicecode"
TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
SCOPE = "offline_access Mail.Read User.Read"
success_url = os.getenv("success_url")
failed_url = os.getenv("failed_url")

router = APIRouter()


# ---------------- LOGIN URL ----------------
@router.get("/login")
def login(provider: str = Query(..., regex="^(google|outlook)$"), userId: int = Query(...)):
    """Return login URL or device code instructions"""
    return {"auth_url": get_auth_url(provider, userId)}


# ---------------- OUTLOOK DEVICE CODE ----------------
@router.get("/outlook/device-code")
def get_device_code(user_id: int):
    """Get device code and instructions for Outlook"""
    res = requests.post(
        DEVICE_CODE_URL,
        data={"client_id": CLIENT_ID, "scope": SCOPE}
    ).json()

    if "device_code" not in res:
        raise HTTPException(status_code=400, detail=res)

    # Store device data in Redis with expiry
    redis_client.setex(
        f"device:{user_id}",
        res["expires_in"],
        json.dumps(res)
    )

    return {
        "verification_uri": res.get("verification_uri"),
        "user_code": res.get("user_code"),
        "expires_in": res.get("expires_in"),
        "interval": res.get("interval")
    }

@router.get("/outlook/poll")
async def poll_token(
    user_id: int,
    repo: MailsRepository = Depends(get_repository(MailsRepository)),
):
    """
    Poll Outlook token ONLY if:
    - Device login triggered
    - First login flag is True
    Stop polling once access_token + refresh_token are received.
    """

    # Step 0: Check trigger and first login

    user_flags = {
        "isTriggered": True,   # set True to allow polling
        "isFirstLogin": False   # set True to allow polling
    }
    #user_flags =  {"isTriggered": false, "isFirstLogin": bool}# Implement: returns {"isTriggered": bool, "isFirstLogin": bool}
    if not user_flags.get("isTriggered") and not user_flags.get("isFirstLogin"):
        return {"status": "skipped", "message": "Polling not triggered or not first login."}

    # Step 1: Check if token already exists (prevents re-polling)
    token = await repo.get_outlook_token(user_id)
    if token and token.access_token and token.refresh_token:
        return {
            "status": "connected",
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "expires_in": int((token.token_expiry - datetime.utcnow()).total_seconds())
        }

    # Step 2: Get device info from Redis
    device_data = redis_client.get(f"device:{user_id}")
    if not device_data:
        raise HTTPException(status_code=400, detail="Call /outlook/device-code first")

    device = json.loads(device_data)
    interval = device.get("interval", 5)
    expiry_time = time.time() + device.get("expires_in", 600)

    # Step 3: Poll Outlook token (stops immediately on success)
    while time.time() < expiry_time:
        await asyncio.sleep(interval)

        token_res = await asyncio.to_thread(
            lambda: requests.post(
                TOKEN_URL,
                data={
                    "client_id": CLIENT_ID,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "device_code": device["device_code"],
                },
            ).json()
        )

        if "access_token" in token_res:
            access_token = token_res["access_token"]
            refresh_token = token_res.get("refresh_token")
            expires_in = token_res["expires_in"]
            token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)

            # Step 4: Save token in Redis
            redis_client.set(
                f"token:{user_id}",
                json.dumps({
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expires_in": expires_in
                })
            )

            # Step 5: Save token in DB (insert or update)
            exists = await repo.user_token_exists(user_id)
            if exists:
                await repo.update_outlook_token(
                    user_id=user_id,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    token_expiry=token_expiry
                )
            else:
                await repo.insert_outlook_token(
                    user_id=user_id,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    token_expiry=token_expiry
                )
                await repo.update_first_login_flag(user_id)  # Marks first login done

            # Step 6: Polling stops here — return immediately
            return {
                "status": "connected",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": expires_in
            }

        # If still pending, continue polling
        if token_res.get("error") in ("authorization_pending", "slow_down"):
            continue

        # Any other error, stop polling
        return {"status": "failed", "error": token_res.get("error")}

    return {"status": "expired", "message": "Device code expired. Please start login again."}


# ---------------- CHECK OUTLOOK STATUS ----------------
@router.get("/outlook/status")
async def outlook_status(
    user_id: int,
    repo: MailsRepository = Depends(get_repository(MailsRepository))
):
    """Check if user has a valid token"""
    try:
        token = await get_valid_outlook_token(user_id, repo)
        return {"connected": bool(token)}
    except Exception:
        return {"connected": False}


# ---------------- FETCH EMAILS ----------------
@router.post("/emails")
async def get_emails(
    request: Request,
    mails_repo: MailsRepository = Depends(get_repository(MailsRepository))
):
    """Fetch emails by folders/labels"""
    try:
        body = await request.json()
        token = body.get("access_token")
        folders = body.get("folders", [])
        user_id = body.get("user_id")
        org_id = body.get("org_id", "1")
        provider = body.get("provider")
        from_date = body.get("from_date")
        to_date = body.get("to_date")

        # validations
        if not all([token, folders, user_id, provider, from_date, to_date]):
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail={"error": "Missing required fields"}
            )

        if provider == "outlook":
            response = await fetch_and_save_mails_by_folders(
                token, folders, user_id, from_date, to_date, mails_repo
            )
            po_det_ids = response.get("extracted_po_ids", [])
            if po_det_ids:
                await generate_missing_po_report_service(
                    user_id=user_id, po_det_ids=po_det_ids, mails_repo=mails_repo
                )
            return {"status": "success"}

        elif provider == "google":
            return await fetch_and_save_mails_by_labels(
                token, folders, user_id, org_id, mails_repo
            )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})


# ---------------- FETCH ALL FOLDERS ----------------
@router.post("/fetch-all-folders")
async def get_emails_folders(
    request: Request,
    mails_repo: MailsRepository = Depends(get_repository(MailsRepository))
):
    """Get all folders (Outlook) or labels (Google)"""
    try:
        body = await request.json()
        token = body.get("access_token")
        provider = body.get("provider")

        if not token or provider not in ["google", "outlook"]:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail={"error": "access_token or provider missing"}
            )

        if provider == "google":
            return await fetch_all_labels(token)
        elif provider == "outlook":
            return await fetch_all_folders(token)

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})


# ---------------- GET STORED OUTLOOK TOKEN ----------------
@router.get("/outlook/token")
async def get_outlook_token(
    user_id: int,
    repo: MailsRepository = Depends(get_repository(MailsRepository))
):
    """Return stored token for a user"""
    try:
        token = await get_valid_outlook_token(user_id, repo)
        if not token:
            raise HTTPException(status_code=404, detail="Token not found")
        return {"access_token": token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------- SIMPLE HEALTH CHECK ----------------
@router.get("/health")
def health_check():
    return {"status": "ok"}
