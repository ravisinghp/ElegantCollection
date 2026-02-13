from apscheduler.schedulers.background import BackgroundScheduler
from app.services import usersmailservice 
from app.db.repositories import UserRepo
import asyncio
from datetime import date,datetime,time,timedelta
from fastapi import Request
from app.db.repositories.mails import MailsRepository
#from app.main import app  # import your FastAPI app instance
from app.api.routes.users import get_valid_outlook_token
from asyncmy.cursors import DictCursor

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
    def job_wrapper():
        fake_request = create_scheduler_request(SchedulerService.app)
        asyncio.run_coroutine_threadsafe(
            SchedulerService.run_job(fake_request),
            SchedulerService.loop
        )

    #----------------get call from main.py------------------
    @staticmethod
    async def configure():
        scheduler.remove_all_jobs() #remove old jobs

        fake_request = create_scheduler_request(SchedulerService.app)
        schedule = await UserRepo.get_active_schedule(fake_request) #getting an active schedule

        # VERY IMPORTANT CHECK
        if not schedule:
            print("No active schedule found. Scheduler not started.")
            return
        
        #add the job in cron
        scheduler.add_job(
            SchedulerService.job_wrapper,
            trigger="cron",
            day_of_week=schedule["day"],
            hour=schedule["time"].hour,
            minute=schedule["time"].minute,
            id="mail_scheduler",
            replace_existing=True
        )

        if not scheduler.running:
            scheduler.start()

        print("Scheduler running automatically")
     
    #-------------------Scheduler is running-------------------    
    async def run_job(request):
        print("Scheduler triggered")

        try:
            schedule = await UserRepo.get_active_schedule(request)

            schedule_datetime = schedule["time"]  # TIMESTAMP from DB

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
                            po_det_ids = response.get("extracted_po_ids", [])
                            if po_det_ids:
                                await usersmailservice.generate_missing_po_report_service(
                                    user_id=user_id, po_det_ids=po_det_ids, mails_repo=repo
                                )
                            return {"status": "success"}
                            
                            # #Generate PO missing & mismatch report
                            # await usersmailservice.generate_missing_po_report_service(
                            #     repo=repo,
                            #     user_id=user_id
                            # )

                    print(f"Done user {user_id}")

                except Exception as user_err:
                    print(f"User {user_id} failed:", user_err)

        except Exception as e:
            print("Scheduler crashed:", e)

    
      
    #------------------ save schedule details----------------------      
    async def save_schedule(request, payload, user_id: int):
 
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
                raise ValueError(
                    f"Scheduler already exists for {day} at "
                    f"{schedule_time.strftime('%Y-%m-%d %H:%M')}"
                )
 
        for day in payload.days:
 
            run_date = get_selected_weekday_date(day)
 
            schedule_time = datetime.combine(
                run_date,
                time(payload.hour, payload.minute)
            )
 
            await UserRepo.save_schedule(
                request=request,
                days=day,
                schedule_time=schedule_time,
                created_by=user_id
            )
 
        return True
 