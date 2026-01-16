# app/api/sharepoint_api.py
from fastapi import APIRouter, Depends, HTTPException, Query
from starlette.requests import Request
from starlette.status import HTTP_400_BAD_REQUEST

from app.db.repositories.sharepoint_repo import SharepointRepo
from app.db.repositories.mails import MailsRepository
from app.services.sharepoint_service import SharepointService
from app.api.dependencies.database import get_repository
from app.services.usersmailservice import get_valid_outlook_token

router = APIRouter()


# ---------------- LIST ALL FOLDERS RECURSIVE ---------------- #
@router.get("/sharepoint_all_folders")
async def get_all_sharepoint_folders(
    user_id: int = Query(..., description="Logged-in user ID"),
    site_url: str = Query(..., description="SharePoint site hostname"),
    site_path: str = Query(..., description="SharePoint site path"),
    library_name: str = Query(..., description="Library name"),
    sp_repo: SharepointRepo = Depends(get_repository(SharepointRepo)),
    mail_repo: MailsRepository = Depends(get_repository(MailsRepository)),
):
    """
    Fetch all SharePoint folders recursively (Outlook-style tree)
    """

    # Get Microsoft Graph token stored for user
    access_token = await get_valid_outlook_token(user_id, mail_repo)

    service = SharepointService(sp_repo)

    # Build site ID correctly
    site_id = await service.get_site_id(
        access_token,
        site_url,
        site_path
    )

    # Get document library (drive)
    drive_id = await service.get_drive_id(
        access_token,
        site_id
    )

    # Fetch folders recursively
    folders = await service.list_folders_recursive(
        access_token,
        drive_id
    )

    return {"folders": folders}


# ---------------- SYNC FILES ---------------- #
@router.post("/sync_sharepoint_files")
async def sync_sharepoint_files(
    request: Request,
    sp_repo: SharepointRepo = Depends(get_repository(SharepointRepo)),
):
    body = await request.json()

    user_id = body.get("user_id")
    site_url = body.get("site_url")
    library_name = body.get("library_name")
    folder_path = body.get("folder_path")
    from_date = body.get("from_date")
    to_date = body.get("to_date")

    if not all([user_id, site_url, library_name, from_date, to_date]):
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Missing required fields")

    access_token = await get_valid_outlook_token(user_id, sp_repo)
    service = SharepointService(sp_repo)

    return await service.fetch_and_save_sharepoint_files(
        access_token=access_token,
        user_id=user_id,
        site_url=site_url,
        library_name=library_name,
        folder_path=folder_path,
        from_date=from_date,
        to_date=to_date,
    )