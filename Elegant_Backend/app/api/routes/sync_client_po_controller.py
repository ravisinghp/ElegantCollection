from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from app.db.mssql_dependency import get_mssql_repository
from app.api.dependencies.database import get_repository
from app.db.repositories.sync_client_po_repo import MSSQLRepo
from app.db.repositories.system_po_repo import SystemPORepo
from app.services.sync_client_po_service import SyncClientPOService

router = APIRouter()

# -------------------Sync Client PO and Insert into MySQL-------------------#
@router.post("/fetch_nd_store_client_pos", status_code=status.HTTP_200_OK)
async def sync_client_po(
    mssql_repo: MSSQLRepo = Depends(get_mssql_repository(MSSQLRepo)),
    mysql_repo: SystemPORepo = Depends(get_repository(SystemPORepo))
):
    try:
        service = SyncClientPOService(mssql_repo, mysql_repo)
        result = await service.sync_po()

        return {
            "status": "success",
            "message": "Client PO Synced and Inserted successfully",
            "data": result
        }

    except ValueError as ve:
        # business logic errors (validation, empty data, etc.)
        logger.warning(f"Validation error in sync_client_po: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )

    except Exception as e:
        # unexpected / DB / driver errors
        logger.exception("Unexpected error while syncing client PO")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync client PO data"
        )