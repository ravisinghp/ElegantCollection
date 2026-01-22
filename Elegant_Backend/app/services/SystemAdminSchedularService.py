from apscheduler.schedulers.background import BackgroundScheduler
from app.services import usersmailservice 
from app.db.repositories import UserRepo
import asyncio
from datetime import date,datetime,time
from fastapi import Request
from app.db.repositories.mails import MailsRepository
#from app.main import app  # import your FastAPI app instance
from app.api.routes.users import get_valid_outlook_token
from asyncmy.cursors import DictCursor



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

            from_date = schedule["time"].date().isoformat()
            to_date = schedule["time"].date().isoformat()

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
                            await usersmailservice.fetch_and_save_mails_by_folders(
                                access_token=access_token,
                                folder_names=folders,
                                user_id=user_id,
                                from_date=from_date,
                                to_date=to_date,
                                mails_repo=repo
                            )
                            
                            #Generate PO missing & mismatch report
                            await usersmailservice.generate_missing_po_report_service(
                                repo=repo,
                                user_id=user_id
                            )

                    print(f"Done user {user_id}")

                except Exception as user_err:
                    print(f"User {user_id} failed:", user_err)

        except Exception as e:
            print("Scheduler crashed:", e)

    
      
    #------------------ save schedule details----------------------      
    async def save_schedule(request, payload, user_id: int):
        try:
            # convert days list → string
            days_str = ",".join(payload.days)

            #combine date + hour + minute → datetime
            schedule_time = datetime.combine(
                payload.date,
                time(payload.hour, payload.minute)
            )

            return await UserRepo.save_schedule(
                request=request,
                schedule_date=payload.date,
                days=days_str,
                schedule_time=schedule_time,
                created_by=user_id
            )

        except Exception as e:
            raise Exception(f"Service error while saving scheduler: {str(e)}")
