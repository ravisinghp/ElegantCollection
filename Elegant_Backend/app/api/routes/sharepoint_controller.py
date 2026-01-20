from fastapi import APIRouter, Depends, HTTPException, Query, Request
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from app.db.repositories.sharepoint_repo import SharepointRepo
from app.db.repositories.mails import MailsRepository
from app.services.sharepoint_service import SharepointService
from app.api.dependencies.database import get_repository
from app.services.usersmailservice import get_valid_outlook_token
import logging


router = APIRouter()

# Setup logger
logger = logging.getLogger("sharepoint")
logger.setLevel(logging.INFO)


@router.get("/sharepoint_all_folders")
async def get_all_sharepoint_folders(
    user_id: int = Query(..., description="Logged-in user ID"),
    sp_repo: SharepointRepo = Depends(get_repository(SharepointRepo)),
    mail_repo: MailsRepository = Depends(get_repository(MailsRepository)),
):
    """
    Fetch all SharePoint folders recursively (Outlook-style tree)
    """

    # Validate user_id
    if user_id <= 0:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid user_id")

    try:
        # Get access token
        access_token = await get_valid_outlook_token(user_id, mail_repo)
        if not access_token:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Unable to retrieve access token")

        service = SharepointService(sp_repo)

        # Get site ID
        try:
            site_id = await service.get_site_id(access_token)
        except Exception as e:
            logger.error(f"Error fetching site ID: {e}")
            raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get site ID: {str(e)}")

        # Get drive ID
        try:
            drive_id = await service.get_drive_id(access_token, site_id)
        except Exception as e:
            logger.error(f"Error fetching drive ID: {e}")
            raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get drive ID: {str(e)}")

        # Fetch folders recursively
        try:
            folders = await service.list_folders_recursive(access_token, drive_id)
        except Exception as e:
            logger.error(f"Error listing folders: {e}")
            raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list folders: {str(e)}")

        if not folders:
            return {"message": "No folders found", "folders": []}

        return {"folders": folders}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in /sharepoint_all_folders: {e}")
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


# ---------------- SYNC FILES ---------------- #
@router.post("/sync_sharepoint_files")
async def sync_sharepoint_files(
    request: Request,
    sp_repo: SharepointRepo = Depends(get_repository(SharepointRepo)),
    mail_repo: MailsRepository = Depends(get_repository(MailsRepository)),
):
    body = await request.json()
    user_id = body.get("user_id")
    folders = body.get("folders", [])  # list of folder paths
    from_date = body.get("from_date")
    to_date = body.get("to_date")

    if not all([user_id, from_date, to_date, folders]):
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Missing required fields")

    access_token = await get_valid_outlook_token(user_id, mail_repo)
    service = SharepointService(sp_repo)

    return await service.fetch_and_save_sharepoint_files(
        access_token=access_token,
        user_id=user_id,
        folders=folders,
        from_date=from_date,
        to_date=to_date,
    )
