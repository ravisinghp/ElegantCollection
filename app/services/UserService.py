
from starlette.requests import Request
from fastapi import HTTPException
from app.db.repositories import UserRepo
from typing import List, Dict, Any
from collections import Counter

#Total R&D Effort On User Dashboard
async def get_total_user_effort_by_user_id(user_id: int, from_date: str, to_date: str, request: Request):
    try:
        return await UserRepo.fetch_total_user_effort_by_id(user_id, from_date, to_date, request)
    except Exception as e:
        return None


#Fetching Total Numbers of Emails on User Dashboard
async def get_emails_processed_by_user_id(user_id: int, from_date: str, to_date: str, request: Request):
    try:
        return await UserRepo.fetch_emails_processed_by_user_id(user_id, from_date, to_date, request)
    except Exception as e:
        return None


#Fetching Total Numbers of Attachments on User Dashboard
async def get_documents_analyzed_by_user_id(user_id: int, from_date: str, to_date: str, request: Request):
    try:
        return await UserRepo.fetch_documents_analyzed_by_user_id(user_id, from_date, to_date, request)
    except Exception as e:
        return None
    
    
 #Fetching Total Numbers of Meeting on User Dashboard   
async def get_meetings_processed_by_user_id(user_id: int, from_date: str, to_date: str, request: Request):
    try:
        return await UserRepo.fetch_meetings_processed_by_user_id(user_id, from_date, to_date, request)
    except Exception as e:
        return None



### This code is used to fetch calculateing one month to current date data week wise
async def get_weekly_hours_previous_month(

    request,from_date:str,to_date:str,org_id: int, user_id: int
) -> List[Dict[str, Any]]:
    try:
        return await UserRepo.get_weekly_hours_previous_month(request, from_date,to_date,org_id, user_id,)
    except Exception as e:
        return None



#Fetching Top Keywords On User Dashboard 
async def get_top_keywords(request, org_id: int, user_id: int,from_date:str,to_date:str, limit: int = 5):
    try:
        rows = await UserRepo.fetch_keywords_by_userId(request, org_id, user_id,from_date,to_date)

        # Flatten keywords (split by comma, strip spaces)
        all_keywords = []
        for (kw,) in rows:
            if kw:
                parts = [k.strip().lower() for k in kw.split(",")]
                all_keywords.extend(parts)

        # Count top N
        counter = Counter(all_keywords)
        return counter.most_common(limit)
    except Exception as e:
        return []
    

#Last Sync On User Dashboard
async def get_last_sync_by_user_id(user_id: int,request: Request):
    try:
        last_sync_data = await UserRepo.get_last_sync_by_user_id(user_id,request)
        return last_sync_data
    except Exception as e:
        raise Exception(f"Error fetching last sync data: {str(e)}")
    
    
#Update Term Condition Fleg When User login once
async def update_term_condition_flag(user_id: int, role_id: int, org_id: int, request: Request):
    try:
        return await UserRepo.update_term_condition_flag(user_id, role_id, org_id, request)
    except Exception as e:
        raise Exception(f"Error updating terms flag: {str(e)}")