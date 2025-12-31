from fastapi import APIRouter, HTTPException,Query
from starlette.requests import Request
from fastapi.responses import JSONResponse

from app.models.schemas.AdminSchema import UserCreate, UserUpdate
from app.services.AdminServices import register_user, update_user
from app.models.schemas.AdminSchema import (
    RoleResponse,
    PaginatedUsersResponse
)
from app.services import AdminServices as admin_service
from typing import List, Dict, Any

router = APIRouter()


#---------------User Creation---------------
@router.post("/createUser")
async def create_user(user: UserCreate, request: Request):
    try:
        response = await register_user(request, user)
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

##--------------User Deletion---------------
@router.delete("/deleteUser/{user_id}")
async def delete_user(user_id: int, request: Request):
    try:
        result = await admin_service.delete_user(request, user_id)
        if result:
            return {"message": "User deleted successfully", "user_id": user_id}
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#------------listing all users on System dashboard----------------
@router.get("/get_all_users", response_model=PaginatedUsersResponse)
async def get_all_users(
    request: Request
):
    try:
        result = await admin_service.get_all_users(
            request
        )

        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#--------------Fetch all roles----------------
@router.get("/fetch_roles", response_model=list[RoleResponse])
async def get_all_roles(request: Request):
    try:
        return await admin_service.get_all_roles(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


##---------------User Updation---------------
@router.put("/updateUser/{user_id}")
async def update_user(user_id: int, user_data: UserUpdate, request: Request):
    try:
        await update_user(request, user_id, user_data)
        return {"message": "User updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# listing the dashboard card data on admin dashboard
@router.get("/dashboardCardData")
async def get_dashboard_stats(
    request: Request, from_date: str, to_date: str, userId: int, org_id: int, role_id:int
):
    try:
        total_effort = await admin_service.get_total_effort(
            request, from_date, to_date, org_id
        )
        active_users = await admin_service.get_active_users(
            request, from_date, to_date, userId, org_id, role_id
        )
        emails_processed = await admin_service.get_emails_processed(
            request, from_date, to_date, org_id
        )
        
        meetings_processed = await admin_service.get_meetings_processed(request,from_date,to_date,org_id)
        
        documents_analyzed = await admin_service.get_documents_analyzed(
            request, from_date, to_date, org_id
        )

        return {
            "total_effort": total_effort,
            "active_users": active_users,
            "emails_processed": emails_processed,
            "meetings_processed":meetings_processed,
            "documents_analyzed": documents_analyzed,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/weekly-hours-previous-month")
async def get_weekly_hours_previous_month(
    request: Request,
    org_id: int,
    from_date: str = Query(...),  # Expecting 'YYYY-MM-DD'
    to_date: str = Query(...)
) -> List[Dict[str, Any]]:
    try:
        return await admin_service.get_weekly_hours_previous_month(
            request, org_id,from_date, to_date
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# This code is used to fetch top 5 keywords for a given organization
@router.get("/top-keywords")
async def get_top_keywords(org_id: int, user_id: int, request: Request,from_date: str = Query(...),to_date: str = Query(...)):
    try:
        top_5 = await admin_service.get_top_keywords(request, org_id, user_id,from_date,to_date)
        return {"org_id": org_id, "top_keywords": top_5}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        # print(e)
        # return []



# Update each users Status
@router.post("/updateUserStatus")
async def update_user_status(
    request: Request, user_id: int, is_active: int, org_id: int
):
    try:
        if is_active not in (0, 1):
            raise HTTPException(status_code=400, detail="Invalid status value")
        result = await admin_service.update_user_status(
            request, user_id, is_active, org_id
        )
        if not result:
            raise HTTPException(
                status_code=404, detail="User not found or org_id mismatch"
            )
        return JSONResponse(
            content={"success": True, "message": "User status updated successfully"}
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#find Last sync of each user
@router.get("/lastSyncEachUser")
async def get_last_sync(org_id: int,request: Request):
    try: 
        result = await admin_service.get_last_sync_by_users(org_id,request)
        return {"data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
    
    

@router.get("/searchUser")
async def search_user(
    request: Request,
    org_id: int,
    query: str = Query("", min_length=1),
    page: int = 1,
    limit: int = 10
):
    try:
        result = await admin_service.search_user(request, org_id, query, page, limit)
        return JSONResponse(content=result)
    except Exception as e:
        print("Error in /searchUser:", e)  # <-- Log the actual error
        raise HTTPException(status_code=500, detail="Internal server error")


# --- Search Keywords ---
@router.get("/searchKeyword")
async def search_keyword(
    request: Request,
    org_id: int,
    query: str = Query("", min_length=1),
    page: int = 1,
    limit: int = 10
):
    try:
        result = await admin_service.search_keyword(request, org_id, query, page, limit)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Search Categories ---
@router.get("/searchCategory")
async def search_category(
    request: Request,
    org_id: int,
    query: str = Query("", min_length=1),
    page: int = 1,
    limit: int = 10
):
    try:
        result = await admin_service.search_category(request, org_id, query, page, limit)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))