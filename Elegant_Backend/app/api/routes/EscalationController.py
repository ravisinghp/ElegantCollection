from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.EscalationService import EscalationService
from app.db.repositories.escalationRepo import EscalationRepository
import aiomysql

router = APIRouter()


# ------------------------Escalation Scheduler--------------------------
@router.get("/run-escalation")
async def run_escalation(request: Request):
    try:
        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                repo = EscalationRepository(cur)
                service = EscalationService(repo)
                data = await service.run_escalation()

        return {
            "success": True,
            "missing_count": len(data["missing"]),
            "mismatch_count": len(data["mismatch"]),
            "data": data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
