from apscheduler.schedulers.background import BackgroundScheduler
from app.services import usersmailservice
from app.db.repositories import UserRepo
import asyncio
from datetime import date,datetime,time,timedelta
from fastapi import Request,HTTPException
from app.db.repositories.mails import MailsRepository
#from app.main import app  # import your FastAPI app instance
from app.api.routes.users import get_valid_outlook_token
from asyncmy.cursors import DictCursor
from loguru import logger
from app.core.websocket_manager import manager
 
WEEKDAY_MAP = {
    "mon": 0, "monday": 0,
    "tue": 1, "tues": 1, "tuesday": 1,
    "wed": 2, "wednesday": 2,
    "thu": 3, "thurs": 3, "thursday": 3,
    "fri": 4, "friday": 4,
    "sat": 5, "saturday": 5,
    "sun": 6, "sunday": 6,
}
#---------------Getting date of selected day--------------------
def get_selected_weekday_date(day_name: str) -> date:
    if not day_name:
        raise ValueError("Day name is empty")
 
    key = day_name.lower().strip()
 
    if key not in WEEKDAY_MAP:
        raise ValueError(f"Invalid weekday received: {day_name}")
 
    today = date.today()
    target_weekday = WEEKDAY_MAP[key]
 
    days_ahead = target_weekday - today.weekday()
    if days_ahead < 0:
        days_ahead += 7
 
    return today + timedelta(days=days_ahead)
 
 
#--------------------Background Scheduler----------------
scheduler = BackgroundScheduler()
def create_scheduler_request(app):
    scope = {
        "type": "http",
        "app": app,  #this gives access to app.state.pool
    }
    return Request(scope)
 
class SchedulerService:
    app = None
    loop = None
   
    # ----------------bridge between APScheduler and async code-----------------
    @staticmethod
    def job_wrapper(task_id):
        fake_request = create_scheduler_request(SchedulerService.app)
        asyncio.run_coroutine_threadsafe(
            SchedulerService.run_job(fake_request,task_id),
            SchedulerService.loop
        )
 
    #----------------get call from main.py------------------
    @staticmethod
    async def configure():
        scheduler.remove_all_jobs() #remove old jobs
 
        fake_request = create_scheduler_request(SchedulerService.app)
        schedules = await UserRepo.get_all_active_schedule(fake_request) #getting an active schedule
 
        # VERY IMPORTANT CHECK
        if not schedules:
            print("No active schedule found. Scheduler not started.")
            return
       
        #add the job in cron
        for schedule in schedules:
            scheduler.add_job(
                SchedulerService.job_wrapper,
                trigger="cron",
                day_of_week=schedule["day"],
                hour=schedule["next_scheduler_time"].hour,
                minute=schedule["next_scheduler_time"].minute,
                id=f"mail_scheduler_{schedule['task_sd_id']}",
                replace_existing=True,
                args=[schedule["task_sd_id"]]
            )
 
            if not scheduler.running:
                scheduler.start()
 
            print(f"{len(schedules)}Scheduler running automatically")
     
    #-------------------Scheduler is running-------------------    
    async def run_job(request,task_id):
        print(f"Scheduler triggered for task{task_id}")
 
        try:
            schedule = await UserRepo.get_schedule_by_id(request, task_id)
 
            if not schedule:
                logger.error(f"No schedule found for task_id {task_id}")
                return
 
            schedule_datetime = schedule["next_scheduler_time"]  # TIMESTAMP from DB
 
            to_date = schedule_datetime.date()
            from_date = to_date - timedelta(days=1)
 
            from_date = from_date.isoformat()
            to_date = to_date.isoformat()
 
            users = await UserRepo.get_users_with_refresh_token(request)
            print(f"Users found: {len(users)}")
 
            for user in users:
                try:
                    user_id = user["user_id"]
                    print(f"Processing user {user_id}")
 
                    folders = await UserRepo.get_user_folders(request, user_id) #getting folders
                    print(f"Folders: {folders}")
 
                    if not folders:
                        print(f"No folders for user {user_id}, skipping")
                        continue
 
                    # CREATE DB SESSION PER USER
                    async with request.app.state.pool.acquire() as conn:
                        async with conn.cursor(DictCursor) as cur:
                            repo = MailsRepository(cur)
 
                            #this is refresh token(access token)
                            access_token = await get_valid_outlook_token(
                                user_id=user_id,
                                repo=repo
                            )
 
                            #fetch emails and sync
                            response = await usersmailservice.fetch_and_save_mails_by_folders(
                                access_token=access_token,
                                folder_names=folders,
                                user_id=user_id,
                                from_date=from_date,
                                to_date=to_date,
                                mails_repo=repo
                            )
                            logger.info(f"User {user_id} - Emails fetched and saved: {response}")
 
                            po_det_ids = response.get("extracted_po_ids", [])
                            if po_det_ids:
                                await usersmailservice.compare_scanned_and_system_pos(
                                    user_id=user_id, po_det_ids=po_det_ids, mails_repo=repo
                                )
                            logger.info(f"User {user_id} - PO comparison completed for PO IDs: {po_det_ids}")              
 
                except Exception as user_err:
                    logger.exception(f"Error processing user {user_id} in scheduler job : {user_err}")
                   
            await UserRepo.update_pre_next_schedule_time(request, task_id)
            await asyncio.sleep(0.1)
            await manager.broadcast({
            "type": "SCHEDULER_UPDATED",
            "task_id": task_id
        })  
            return {"status": "success"}
       
        except Exception as e:
            logger.exception(f"Scheduler crashed: {e}")
 
   
     
    #------------------ save schedule details----------------------      
    async def save_schedule(request, payload, user_id: int):
        current_time = datetime.now()
 
        for day in payload.days:
 
            run_date = get_selected_weekday_date(day)
 
            schedule_time = datetime.combine(
                run_date,
                time(payload.hour, payload.minute)
            )
 
            is_duplicate = await UserRepo.check_duplicate_schedule(
                request,
                day,
                schedule_time
            )
 
            if is_duplicate:
                raise HTTPException(
                    status_code="duplicates",
                    detail=f"Scheduler already exists for {day} at "
                        f"{schedule_time.strftime('%Y-%m-%d %H:%M')}"
                )
 
        for day in payload.days:
 
            run_date = get_selected_weekday_date(day)
 
            schedule_time = datetime.combine(
                run_date,
                time(payload.hour, payload.minute)
            )
             #Validate past date/time
            if schedule_time <= current_time:
                raise HTTPException(
                    status_code="error",
                    detail="Cannot schedule a task for a past date or time. Please select a future time."
                )
 
            await UserRepo.save_schedule(
                request=request,
                days=day,
                schedule_time=schedule_time,
                created_by=user_id
            )
 
        return True
 
    #Display all active  Scheduler ON UI
    async def fetch_all_scheduler(request: Request, role_id: int):
        try:
 
            data = await UserRepo.fetch_all_scheduler(
                request=request,
                role_id=role_id
                #user_id=user_id
            )
 
            return data if data else []
 
        except Exception as e:
            print("Service Error:", e)
            raise e
       
    async def delete_scheduler(request: Request, task_sd_id: int):
        try:
 
            data = await UserRepo.delete_scheduler(
                request=request,
                task_sd_id=task_sd_id
                #user_id=user_id
            )
 
            return data if data else []
 
        except Exception as e:
            print("Service Error:", e)
            raise e
 