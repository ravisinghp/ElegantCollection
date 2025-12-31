from starlette.requests import Request
from app.models.domain.AdminDomain import SchedulerRequest
from app.services import SystemAdminSchedularService 
from fastapi import APIRouter, HTTPException,Query,Depends
from app.core.security import get_current_user
from app.services.SystemAdminSchedularService import SchedulerService


router = APIRouter()
@router.post("/configure-scheduler")
async def configure_scheduler(
    payload: SchedulerRequest,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role_id"] != 2:
        raise HTTPException(403, "Only system admin allowed")

    await SchedulerService.configure(payload, request)

    return {
        "status": "success",
        "message": "Scheduler configured successfully"
    }