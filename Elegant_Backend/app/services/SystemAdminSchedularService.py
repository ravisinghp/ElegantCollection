from apscheduler.schedulers.background import BackgroundScheduler
from app.services import usersmailservice 
from app.db.repositories import UserRepo
import asyncio


scheduler = BackgroundScheduler()


class SchedulerService:

    @staticmethod
    async def configure(payload, request):
        scheduler.remove_all_jobs()

        scheduler.add_job(
            SchedulerService._job_wrapper,  # ✅ sync
            trigger="cron",
            day_of_week=",".join(payload.days),
            hour=payload.hour,
            minute=payload.minute,
            args=[request]
        )

        if not scheduler.running:
            scheduler.start()

    @staticmethod
    def _job_wrapper(request):
        asyncio.create_task(SchedulerService.run_job(request))

    @staticmethod
    async def run_job(request):
        print("⏰ Scheduler triggered")

        users = await UserRepo.get_active_users(request)

        for user_id in users:
            await usersmailservice.fetch_and_save_mails_by_folders(
                user_id=user_id,
                request=request
            )