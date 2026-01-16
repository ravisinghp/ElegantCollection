from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.EscalationService import EscalationService
from app.db.repositories.escalationRepo import EscalationRepository


router = APIRouter()

# @router.post("/run-escalation")
# async def run_escalation(request: Request):
#     try:
#         await EscalationService.run_escalation(request)
#         return {"success": True, "message": "Escalation completed"}
#     except Exception as e:
#         raise HTTPException(500, str(e))



# from fastapi import APIRouter, HTTPException, Request, Query
# from app.services.EscalationService import EscalationService
# from app.db.repositories.escalationRepo import EscalationRepository

# router = APIRouter(prefix="/escalation", tags=["Escalation"])


# @router.post("/run-escalation")
# async def run_escalation(
#     request: Request,
#     report_type: str = Query(..., regex="^(missing|mismatch)$")
# ):
#     try:
#         async with request.app.state.pool.acquire() as conn:
#             async with conn.cursor() as cur:
#                 repo = EscalationRepository(cur)
#                 service = EscalationService(repo)

#                 # ✅ CORRECT CALL
#                 await service.run_escalation(report_type)

#         return {
#             "success": True,
#             "message": f"Escalation completed for {report_type}"
#         }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


from fastapi import APIRouter, Request, HTTPException, Query
import aiomysql
router = APIRouter(prefix="/escalation", tags=["Escalation"])

# @router.post("/run-escalation")
# async def run_escalation(
#     request: Request,
#     report_type: str = Query(..., pattern="^(missing|mismatch)$")
# ):
#     try:
#         async with request.app.state.pool.acquire() as conn:
#             async with conn.cursor(aiomysql.DictCursor) as cur:
#                 repo = EscalationRepository(cur)
#                 service = EscalationService(repo)

#                 # await service.run_escalation(report_type)
#                 data = await service.run_escalation(report_type)

#             return {
#                 "success": True,
#                 "count": len(data),
#                 "data": data
#             }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


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
