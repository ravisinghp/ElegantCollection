from starlette.requests import Request
from app.models.domain.AdminDomain import SchedulerRequest,FetchSchedulerRequest,DeleteSchedulerRequest
from fastapi import APIRouter, HTTPException,Query,Depends
from app.core.security import get_current_user
from app.services.SystemAdminSchedularService import SchedulerService


router = APIRouter()
#---------------------Schedule by System Admin Endpoint--------------------
@router.post("/save_schedule")
async def save_schedule(
    payload: SchedulerRequest,
    request: Request,
):
    try:
        if not payload.days:
            raise ValueError("Invalid scheduler payload")


        await SchedulerService.save_schedule(
            request=request,
            payload=payload,
            user_id=payload.user_id,
        )   
         #reload scheduler with new DB time
        await SchedulerService.configure()

        return {
            "status": "success",
            "message": "Scheduler saved successfully"
        }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
  
#Display all active  Scheduler ON UI  
@router.post("/fetch_all_schedulers")
async def fetch_all_scheduler(request: Request, payload: FetchSchedulerRequest):
    try:
        role_id = payload.role_id

        data = await SchedulerService.fetch_all_scheduler(
            request=request,
            role_id=role_id
           # user_id=user_id
        )

        return {
            "status": "success",
            "data": data
        }

    except HTTPException as http_err:
        raise http_err

    except Exception as e:
        print("Controller Error:", e)
        raise HTTPException(status_code=500, detail=str(e))
    
    
@router.post("/delete_scheduler")
async def delete_scheduler(request: Request, payload: DeleteSchedulerRequest):
    try:
        task_sd_id = payload.task_sd_id

        data = await SchedulerService.delete_scheduler(
            request=request,
            task_sd_id=task_sd_id
           # user_id=user_id
        )

        return {
            "status": "success",
            "data": data
        }

    except HTTPException as http_err:
        raise http_err

    except Exception as e:
        print("Controller Error:", e)
        raise HTTPException(status_code=500, detail=str(e))
