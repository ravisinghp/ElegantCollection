from fastapi import APIRouter, HTTPException,Query
from starlette.requests import Request

from app.services import UserService 
from typing import List, Dict, Any
# from pydantic import BaseModel


#User Dashboard Card Data 
router = APIRouter()
@router.get("/userDashboardCardData")
async def get_dashboard_stats(request: Request, from_date: str, to_date: str, userId:int):
    user_id = userId
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    try:
        # user_id = int(user_id)
        total_effort = await UserService.get_total_user_effort_by_user_id(user_id, from_date, to_date, request)
        emails_processed = await UserService.get_emails_processed_by_user_id(user_id, from_date, to_date, request)
        documents_analyzed = await UserService.get_documents_analyzed_by_user_id(user_id, from_date, to_date, request)
        meetings_processed = await UserService.get_meetings_processed_by_user_id(user_id, from_date, to_date, request)
        return {
        "total_effort": total_effort,
        "emails_processed": emails_processed,
        "documents_analyzed": documents_analyzed,
        "meetings_processed":meetings_processed,
        }
    except Exception as e :
        return None



### This code is used to fetch calculateing one month to current date data week wise
@router.get("/weekly-hours-previous-month")
async def get_weekly_hours_previous_month(
    request: Request,  
    org_id: int,
    user_id: int,
    from_date: str = Query(...),  # Expecting 'YYYY-MM-DD'
    to_date: str = Query(...),
   
) -> List[Dict[str, Any]]:
    try:
        return await UserService.get_weekly_hours_previous_month(
            request, from_date,to_date,org_id, user_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
<<<<<<< HEAD
=======




#Fetching Top Keywords On User Dashboard 
@router.get("/top-keywords")
async def get_top_keywords(request: Request,org_id: int, user_id: int,from_date: str = Query(...),to_date: str = Query(...),):
    try:
        top_5 = await UserService.get_top_keywords(request, org_id, user_id,from_date,to_date)
        return {"org_id": org_id, "top_keywords": top_5}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        # print(e)
        # return []
        
        
#Last Sync On User Dashboard        
@router.get("/lastSync")
async def get_last_sync_by_user_id(user_id: int,request: Request):
    try: 
        result = await UserService.get_last_sync_by_user_id(user_id,request)
        return {"data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
 
 
     
#Update Term Condition Fleg When User login once   
@router.post("/update_term_condition_flag")
async def update_term_condition_flag(request: Request, user_id: int, role_id: int, org_id: int):
    try:
        result = await UserService.update_term_condition_flag(user_id, role_id, org_id, request)
        if not result:
            raise HTTPException(status_code=400, detail="User not found or update failed")
        return {"success": True, "message": "Terms accepted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from fastapi import APIRouter, HTTPException,Query
from starlette.requests import Request

from app.services import UserService 
from typing import List, Dict, Any
# from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from app.models.domain.AdminDomain import UpdatePoCommentRequest
#User Dashboard Card Data 
router = APIRouter()
@router.get("/userDashboardCardData")
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
@router.get("/downloadMissingPOReport")
async def download_missing_po_report(
    request: Request,
    format: str = Query("excel", regex="^(excel|pdf)$")
):
    try:
        file_stream, filename, media_type = await UserService.download_missing_po_report(
            format=format,
            request=request
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


@router.get("/downloadMismatchPOReport")
async def download_mismatch_po_report(
    request: Request,
    format: str = Query("excel", regex="^(excel|pdf)$")
):
    try:
        file_stream, filename, media_type = await UserService.download_mismatch_po_report(
            format=format,
            request=request
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


#Update the PO Comment On UI 
@router.put("/updatePoComment")
async def update_po_comment(
    request: Request,
    payload: UpdatePoCommentRequest,
    report_type: str = Query(..., regex="^(missing|mismatch)$")
):

    if report_type == "missing":
        if not payload.po_missing_id:
            raise HTTPException(
                status_code=400,
                detail="po_missing_id is required for missing report"
            )
        record_id = payload.po_missing_id

    elif report_type == "mismatch":
        if not payload.po_mismatch_id:
            raise HTTPException(
                status_code=400,
                detail="po_mismatch_id is required for mismatch report"
            )
        record_id = payload.po_mismatch_id

    updated = await UserService.update_po_comment(
        report_type=report_type,
        record_id=record_id,
        comment=payload.comment,
        request=request
    )

    if not updated:
        raise HTTPException(status_code=404, detail="Record not found or inactive")

    return {
        "status": "success",
        "message": "Comment updated successfully"
    }


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
>>>>>>> c91285d3e10beced0bc4f53193cdf2f4f500bcd7




<<<<<<< HEAD
#Fetching Top Keywords On User Dashboard 
@router.get("/top-keywords")
async def get_top_keywords(request: Request,org_id: int, user_id: int,from_date: str = Query(...),to_date: str = Query(...),):
    try:
        top_5 = await UserService.get_top_keywords(request, org_id, user_id,from_date,to_date)
        return {"org_id": org_id, "top_keywords": top_5}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        # print(e)
        # return []
        
        
#Last Sync On User Dashboard        
@router.get("/lastSync")
async def get_last_sync_by_user_id(user_id: int,request: Request):
    try: 
        result = await UserService.get_last_sync_by_user_id(user_id,request)
        return {"data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
=======
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
# @router.get("/lastSync")
# async def get_last_sync_by_user_id(user_id: int,request: Request):
#     try: 
#         result = await UserService.get_last_sync_by_user_id(user_id,request)
#         return {"data": result}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
>>>>>>> c91285d3e10beced0bc4f53193cdf2f4f500bcd7
    
 
 
     
#Update Term Condition Fleg When User login once   
<<<<<<< HEAD
@router.post("/update_term_condition_flag")
async def update_term_condition_flag(request: Request, user_id: int, role_id: int, org_id: int):
    try:
        result = await UserService.update_term_condition_flag(user_id, role_id, org_id, request)
        if not result:
            raise HTTPException(status_code=400, detail="User not found or update failed")
        return {"success": True, "message": "Terms accepted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
=======
# @router.post("/update_term_condition_flag")
# async def update_term_condition_flag(request: Request, user_id: int, role_id: int, org_id: int):
#     try:
#         result = await UserService.update_term_condition_flag(user_id, role_id, org_id, request)
#         if not result:
#             raise HTTPException(status_code=400, detail="User not found or update failed")
#         return {"success": True, "message": "Terms accepted"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
>>>>>>> c91285d3e10beced0bc4f53193cdf2f4f500bcd7


