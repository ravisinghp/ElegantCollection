from starlette.requests import Request
from app.models.domain.AdminDomain import SchedulerRequest 
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
        if not payload.date or not payload.days:
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


# -------------------Scheduler for testing by postman-------------------
#Scheduler
#@router.post("/configure-scheduler")
# async def configure_scheduler(
#     request: Request,
#     current_user: dict = Depends(get_current_user)
# ):
#     if current_user["role_id"] != 2:
#         raise HTTPException(403, "Only system admin allowed")
    
#     await SchedulerService.run_job(request)


#     await SchedulerService.configure(request)

#     return {
#         "status": "success",
#         "message": "Scheduler configured successfully"
#     }