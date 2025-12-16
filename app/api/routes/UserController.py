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


