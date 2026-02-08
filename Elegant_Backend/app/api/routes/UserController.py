from fastapi import APIRouter, HTTPException,Query
from starlette.requests import Request

from app.services import UserService 
from typing import List, Dict, Any
# from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from app.models.domain.AdminDomain import UpdatePoCommentRequest, GenerateMissingPoReport, DownloadMissingMismatchRequest,FetchMissingMismatchReport,FolderMappingRequest,DownloadCombinedMissingMismatchRequest,DownloadAllMissingMismatchRequest,DownloadCombinedAllPORequest
from fastapi.encoders import jsonable_encoder
from app.models.schemas.users import BusinessAdminSearchRequest


#User Dashboard Card Data 
router = APIRouter()
@router.get("/user_dashboard_card_data")
async def get_dashboard_stats(request: Request,userId:int):
    user_id = userId
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    try:
        # user_id = int(user_id)
       #total_effort = await UserService.get_total_user_effort_by_user_id(user_id, from_date, to_date, request)
        emails_processed = await UserService.get_emails_processed_by_user_id(user_id, request)
        documents_analyzed = await UserService.get_documents_analyzed_by_user_id(user_id, request)
        #meetings_processed = await UserService.get_meetings_processed_by_user_id(user_id, from_date, to_date, request)
        return {
       # "total_effort": total_effort,
        "emails_processed": emails_processed,
        "documents_analyzed": documents_analyzed,
        #"meetings_processed":meetings_processed,
        }
    except Exception as e :
        return None
    
    #Donwload Missing Report and Missmatch Report 
@router.post("/download_missing_po_report")
async def download_missing_po_report(
    request: Request,
    payload: DownloadMissingMismatchRequest,
    format: str = Query("excel", regex="^(excel|pdf)$")
):
    try:
        file_stream, filename, media_type = await UserService.download_missing_po_report(
            request=request,
            user_id =payload.user_id,
            role_id=payload.role_id,
            #selected_ids=payload.selected_ids,
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
@router.post("/download_mismatch_po_report")
async def download_mismatch_po_report(
    request: Request,
    payload: DownloadMissingMismatchRequest,
    format: str = Query("excel", regex="^(excel|pdf)$")
):
    try:
        file_stream, filename, media_type = await UserService.download_mismatch_po_report(
            request=request,
            user_id=payload.user_id,
            role_id=payload.role_id,
            #selected_ids=payload.selected_ids,
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



#For Business admin Dashboard download all missing pos 
@router.post("/download_All_missing_po_report")
async def download_all_missing_po_report(
    request: Request,
    payload: DownloadMissingMismatchRequest,
    format: str = Query("excel", regex="^(excel|pdf)$")
):
    try:
        file_stream, filename, media_type = await UserService.download_all_missing_po_report(
            request=request,
            format=format
        )

        return StreamingResponse(
            file_stream,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#For Business admin Dashboard download all mismatch pos 
@router.post("/download_All_mismatch_po_report")
async def download_all_mismatch_po_report(
    request: Request,
    payload: DownloadAllMissingMismatchRequest,
    format: str = Query("excel", regex="^(excel|pdf)$")
):
    try:
        file_stream, filename, media_type = await UserService.download_all_mismatch_po_report(
            request=request,
            format=format
        )

        return StreamingResponse(
            file_stream,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/download_combined_all_po_report")
async def download_combined_all_po_report(
    request: Request,
    payload: DownloadCombinedAllPORequest,
    format: str = Query("excel", regex="^(excel|pdf)$")
):
    try:
        file_stream, filename, media_type = await UserService.download_combined_all_po_report(
            request=request,
            user_id=payload.user_id,
            role_id=payload.role_id,
            email_missing_ids=payload.email_missing_ids,
            email_mismatch_ids=payload.email_mismatch_ids,
            sharepoint_missing_ids=payload.sharepoint_missing_ids,
            sharepoint_mismatch_ids=payload.sharepoint_mismatch_ids,
            format=format
        )

        return StreamingResponse(
            file_stream,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



#Adding and Update comment for po missing and po mismatch from UI
@router.put("/save_po_comment")
async def save_po_comment(
    request: Request,
    payload: UpdatePoCommentRequest,
    report_type: str = Query(..., regex="^(missing|mismatch)$")
):
    if report_type == "missing":
        if not payload.po_missing_id:
            raise HTTPException(400, "po_missing_id is required")
        record_id = payload.po_missing_id

    elif report_type == "mismatch":
        if not payload.po_mismatch_id:
            raise HTTPException(400, "po_mismatch_id is required")
        record_id = payload.po_mismatch_id

    saved = await UserService.save_po_comment(
        report_type=report_type,
        record_id=record_id,
        comment=payload.comment,
        request=request
    )

    if not saved:
        raise HTTPException(404, "Record not found or inactive")

    return {
        "status": "success",
        "message": "Comment saved successfully"
    }


#For Fetching the PO comment ON UI 
@router.get("/fetch_po_comment")
async def fetch_po_comment(
    request: Request,
    report_type: str = Query(..., regex="^(missing|mismatch)$"),
    po_missing_id: int | None = None,
    po_mismatch_id: int | None = None,
):
    if report_type == "missing":
        if not po_missing_id:
            raise HTTPException(400, "po_missing_id is required")
        record_id = po_missing_id

    elif report_type == "mismatch":
        if not po_mismatch_id:
            raise HTTPException(400, "po_mismatch_id is required")
        record_id = po_mismatch_id

    comment = await UserService.fetch_po_comment(
        report_type=report_type,
        record_id=record_id,
        request=request
    )

    if comment is None:
        raise HTTPException(404, "Comment not found")

    return {
        "status": "success",
        "comment": comment
    }


#For Ignoring the PO in Next Sync On UI
@router.put("/ignore_po")
async def ignore_po(
    request: Request,
    report_type: str = Query(..., regex="^(missing|mismatch)$"),
    po_missing_id: int | None = None,
    po_mismatch_id
    : int | None = None,
):
    if report_type == "missing":
        if not po_missing_id:
            raise HTTPException(400, "po_missing_id is required")
        record_id = po_missing_id

    elif report_type == "mismatch":
        if not po_mismatch_id:
            raise HTTPException(400, "po_mismatch_id is required")
        record_id = po_mismatch_id

    ignored = await UserService.ignore_po(
        report_type=report_type,
        record_id=record_id,
        request=request
    )

    if not ignored:
        raise HTTPException(404, "Record not found or already ignored")

    return {
        "status": "success",
        "message": "PO ignored successfully"
    }


# @router.post("/createPoComment")
# async def create_po_comment(
#     request: Request,
#     payload: UpdatePoCommentRequest,
#     report_type: str = Query(..., regex="^(missing|mismatch)$")
# ):
#     if report_type == "missing":
#         if not payload.po_missing_id:
#             raise HTTPException(400, "po_missing_id is required")
#         record_id = payload.po_missing_id

#     elif report_type == "mismatch":
#         if not payload.po_mismatch_id:
#             raise HTTPException(400, "po_mismatch_id is required")
#         record_id = payload.po_mismatch_id

#     created = await UserService.create_po_comment(
#         report_type=report_type,
#         record_id=record_id,
#         comment=payload.comment,
#         request=request
#     )

#     if not created:
#         raise HTTPException(404, "Record not found or inactive")

#     return {
#         "status": "success",
#         "message": "Comment added successfully"
#     }

# #Update the PO Comment On UI 
# @router.put("/updatePoComment")
# async def update_po_comment(
#     request: Request,
#     payload: UpdatePoCommentRequest,
#     report_type: str = Query(..., regex="^(missing|mismatch)$")
# ):

#     if report_type == "missing":
#         if not payload.po_missing_id:
#             raise HTTPException(
#                 status_code=400,
#                 detail="po_missing_id is required for missing report"
#             )
#         record_id = payload.po_missing_id

#     elif report_type == "mismatch":
#         if not payload.po_mismatch_id:
#             raise HTTPException(
#                 status_code=400,
#                 detail="po_mismatch_id is required for mismatch report"
#             )
#         record_id = payload.po_mismatch_id

#     updated = await UserService.update_po_comment(
#         report_type=report_type,
#         record_id=record_id,
#         comment=payload.comment,
#         request=request
#     )

#     if not updated:
#         raise HTTPException(status_code=404, detail="Record not found or inactive")

#     return {
#         "status": "success",
#         "message": "Comment updated successfully"
#     }



# @router.get("/missing-po")
# async def missing_po_data_fetch(request: Request):
#     return await UserService.missing_po_data_fetch(request)


# @router.get("/mismatch-po")
# async def mismatch_po_data_fetch(request: Request):
#     return await UserService.mismatch_po_data_fetch(request)

# @router.get("/matched-po")
# async def matched_po_data_fetch(request: Request):
#     return await UserService.matched_po_data_fetch(request)
#table Data ON User Dashboard 
@router.post("/missing_po")
async def missing_po_data_fetch(request: Request, frontendRequest: FetchMissingMismatchReport):
    try:
        data = await UserService.missing_po_data_fetch(request, frontendRequest)
        # Convert dates to strings and return
        return jsonable_encoder(data)
    except Exception as e:
        print(f"Error fetching Missing POs: {e}")
        return []

@router.post("/mismatch_po")
async def mismatch_po_data_fetch(request: Request, frontendRequest: FetchMissingMismatchReport):
    try:
        data = await UserService.mismatch_po_data_fetch(request, frontendRequest)
        return jsonable_encoder(data)
    except Exception as e:
        print(f"Error fetching Mismatch POs: {e}")
        return []

@router.post("/matched_po")
async def matched_po_data_fetch(request: Request, frontendRequest: FetchMissingMismatchReport):
    try:
        data = await UserService.matched_po_data_fetch(request, frontendRequest)
        return jsonable_encoder(data)
    except Exception as e:
        print(f"Error fetching Matched POs: {e}")
        return []



#Business admin fetching users list and vendor number list on dashboard
@router.get("/fetch_users_for_business_admin")
async def get_all_users_by_role_id_business_admin(
    request: Request
):
    try:
        result =  await UserService.get_all_users_by_role_id_business_admin(
            request=request
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch users list: {str(e)}"
        )


@router.get("/fetch_vendors_for_business_admin")
async def get_vendors_business_admin(request: Request):
    try:
        result = await UserService.get_vendors_business_admin(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch vendor list: {str(e)}"
        )
    
#----------------Search PO for Business Admin Dashboard-----------------#
@router.post("/business_admin_search_pos")
async def search_pos_business_admin(
    request: Request,
    filters: BusinessAdminSearchRequest
):
    try:
        data = await UserService.search_pos_business_admin(
            request=request,
            filters=filters
        )

        # If data is a string, treat as validation error
        if isinstance(data, str):
            return {"success": False, "message": data, "data": []}

        return {"success": True, "message": "Search completed", "data": data}

    except Exception as e:
        return {"success": False, "message": f"Search failed: {str(e)}", "data": []}


### This code is used to fetch calculateing one month to current date data week wise
# @router.get("/weekly-hours-previous-month")
# async def get_weekly_hours_previous_month(
#     request: Request,  
#     org_id: int,
#     user_id: int,
#     from_date: str = Query(...),  # Expecting 'YYYY-MM-DD'
#     to_date: str = Query(...),
   
# ) -> List[Dict[str, Any]]:
#     try:
#         return await UserService.get_weekly_hours_previous_month(
#             request, from_date,to_date,org_id, user_id,
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))




# #Fetching Top Keywords On User Dashboard 
# @router.get("/top-keywords")
# async def get_top_keywords(request: Request,org_id: int, user_id: int,from_date: str = Query(...),to_date: str = Query(...),):
#     try:
#         top_5 = await UserService.get_top_keywords(request, org_id, user_id,from_date,to_date)
#         return {"org_id": org_id, "top_keywords": top_5}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
#         # print(e)
#         # return []
        
        
# #Last Sync On User Dashboard        
@router.get("/last_sync")
async def get_last_sync_by_user_id(user_id: int,role_id: int,request: Request):
    try: 
        result = await UserService.get_last_sync_by_user_id(user_id,role_id,request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Save the Folder in Folder mapping for scheduler to get sync
@router.post("/save_folder_mapping")
async def save_folder_mapping(payload: FolderMappingRequest, request: Request ):
    try:
        if not payload.user_id or not payload.folder_name:
            raise ValueError("Invalid payload")

        await UserService.save_folder_mapping_service(
            request=request,
            user_id=payload.user_id,
            folder_name=payload.folder_name
        )

        return {
            "status": "success",
            "message": "Folder mapping saved successfully"
        }

    except ValueError as ve:
        #logger.warning("Validation error: %s", ve)
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        #logger.error("Failed to save folder mapping", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error while saving folder mapping"
        )   
 
 
     
#Update Term Condition Fleg When User login once   
# @router.post("/update_term_condition_flag")
# async def update_term_condition_flag(request: Request, user_id: int, role_id: int, org_id: int):
#     try:
#         result = await UserService.update_term_condition_flag(user_id, role_id, org_id, request)
#         if not result:
#             raise HTTPException(status_code=400, detail="User not found or update failed")
#         return {"success": True, "message": "Terms accepted"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


