from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import aiomysql
from fastapi import FastAPI

import app
from app.db.repositories.escalationRepo import EscalationRepository
from app.services.EscalationService import EscalationService


scheduler = AsyncIOScheduler()


async def run_escalation_job(app: FastAPI):
    try:
        pool = app.state.pool
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                repo = EscalationRepository(cur)
                service = EscalationService(repo)
                await service.run_escalation()

        print(" Escalation job ran at", datetime.now())

    except Exception as e:
        print(" Escalation job failed:", e)
