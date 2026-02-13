from sched import scheduler
from typing import Callable

from fastapi import FastAPI
from loguru import logger

from app.db.events import close_db_connection, connect_to_db
from app.scheduler.escalation_scheduler import run_escalation_job
from app.scheduler.escalation_scheduler import scheduler



# def create_start_app_handler(app: FastAPI) -> Callable:  # type: ignore
#     async def start_app() -> None:
#         await connect_to_db(app)

#     return start_app


# def create_stop_app_handler(app: FastAPI) -> Callable:  # type: ignore
#     @logger.catch
#     async def stop_app() -> None:
#         await close_db_connection(app)

#     return stop_app


def create_start_app_handler(app: FastAPI):
    async def start_app() -> None:
        # DB
        await connect_to_db(app)

        #  Scheduler job
        scheduler.add_job(
            func=run_escalation_job,
            trigger="cron",
            day_of_week="mon-fri",
            # minute="*/2",     #  EVERY 2 MINUTES
            hour=8,
            minute=0,
            args=[app],
            id="escalation_job",
            replace_existing=True,
        )

        #  Start scheduler ONLY once
        if not scheduler.running:
            scheduler.start()

    return start_app


def create_stop_app_handler(app: FastAPI):
    async def stop_app() -> None:
        # Stop scheduler safely
        if scheduler.running:
            scheduler.shutdown()

        # Close DB
        await close_db_connection(app)

    return stop_app
