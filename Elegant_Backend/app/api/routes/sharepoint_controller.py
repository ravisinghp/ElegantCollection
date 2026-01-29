from fastapi import APIRouter, Depends, HTTPException, Query, Request
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from app.db.repositories.sharepoint_repo import SharepointRepo
from app.db.repositories.mails import MailsRepository
from app.services.sharepoint_service import SharepointService
from app.api.dependencies.database import get_repository
from app.services.usersmailservice import get_valid_outlook_token
import logging
from app.models.schemas.sharepoint_schema import FolderRequestParams
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from app.models.domain.AdminDomain import GenerateMissingPoReport,SharepointFetchMissingMismatchReport,DownloadSharepointMissingMismatchRequest


router = APIRouter()

# Setup logger
logger = logging.getLogger("sharepoint")
logger.setLevel(logging.INFO)

@router.get("/sharepoint_dashboard_card_data")
async def get_sharepoint_dashboard_stats(request: Request,userId:int):
    user_id = userId
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    try:
        documents_analyzed = await SharepointService.get_documents_analyzed_by_user_id(user_id, request)
        return {
        "documents_analyzed": documents_analyzed,
        }
    except Exception as e :
        return None


@router.post("/sharepoint_all_folders")
async def get_all_sharepoint_folders(
    request: FolderRequestParams,
    sp_repo: SharepointRepo = Depends(get_repository(SharepointRepo)),
    mail_repo: MailsRepository = Depends(get_repository(MailsRepository)),
):
    """
    Fetch all SharePoint folders recursively (Outlook-style tree)
    """

    # Validate user_id
    if request.user_id <= 0:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid user_id")

    try:
        # Get access token
        access_token = await get_valid_outlook_token(request.user_id, mail_repo)
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
    
# CONTROLLER ENDPOINT (IN SAME FILE)
# ---------------------------------------------------------------------
@router.post("/generate_sharepoint_missing_po_report")
async def generate_missing_po_report(
    request : GenerateMissingPoReport,
    sp_repo: SharepointRepo = Depends(get_repository(SharepointRepo))
):
    service = SharepointService(sp_repo)
    result = await service.generate_sharepoint_missing_po_report_service(request.user_id)
    return JSONResponse(content=jsonable_encoder(result))

#----------------------Sharepoint Table Data-------------------------
@router.post("/sharepoint_missing_po")
async def missing_po_data_fetch(request: Request, frontendRequest: SharepointFetchMissingMismatchReport):
    try:
        data = await SharepointService.missing_po_data_fetch(request, frontendRequest)
        # Convert dates to strings and return
        return jsonable_encoder(data)
    except Exception as e:
        print(f"Error fetching Missing POs: {e}")
        return []

@router.post("/sharepoint_mismatch_po")
async def mismatch_po_data_fetch(request: Request, frontendRequest: SharepointFetchMissingMismatchReport):
    try:
        data = await SharepointService.mismatch_po_data_fetch(request, frontendRequest)
        return jsonable_encoder(data)
    except Exception as e:
        print(f"Error fetching Mismatch POs: {e}")
        return []

@router.post("/sharepoint_matched_po")
async def matched_po_data_fetch(request: Request, frontendRequest: SharepointFetchMissingMismatchReport):
    try:
        data = await SharepointService.matched_po_data_fetch(request, frontendRequest)
        return jsonable_encoder(data)
    except Exception as e:
        print(f"Error fetching Matched POs: {e}")
        return []
    
    
 #Donwload Missing Report and Missmatch Report 
@router.post("/download_sharepoint_missing_po_report")
async def download_sharepoint_missing_po_report(
    request: Request,
    payload: DownloadSharepointMissingMismatchRequest,
    format: str = Query("excel", regex="^(excel|pdf)$")
):
    try:
        file_stream, filename, media_type = await SharepointService.download_sharepoint_missing_po_report(
            request=request,
            user_id =payload.user_id,
            role_id=payload.role_id,
            format=format
        )

        return StreamingResponse(
            file_stream,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#Donwload Missing Report and Missmatch Report 
@router.post("/download_sharepoint_mismatch_po_report")
async def download_sharepoint_mismatch_po_report(
    request: Request,
    payload: DownloadSharepointMissingMismatchRequest,
    format: str = Query("excel", regex="^(excel|pdf)$")
):
    try:
        file_stream, filename, media_type = await SharepointService.download_sharepoint_mismatch_po_report(
            request,
            user_id=payload.user_id,
            role_id=payload.role_id,
            format=format
        )

        return StreamingResponse(
            file_stream,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
# #Last Sync On User Dashboard        
@router.get("/sharepoint_dashboard_last_sync")
async def get_last_sync_by_user_id(user_id: int,role_id: int,request: Request):
    try: 
        result = await SharepointService.get_last_sync_by_user_id(user_id,role_id,request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



