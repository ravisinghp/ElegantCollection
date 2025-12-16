from fastapi import APIRouter, Depends, Query
from app.db.repositories.category_section_repo import CategoryRepo
from app.services.category_section_service import CategoryService
from app.api.dependencies.database import get_repository
from app.models.schemas.category_section_schema import (
    CategoryRequest,
    UpdateCategoryRequest,
    PaginatedCategoriesResponse
)

from fastapi import APIRouter, HTTPException
from starlette.requests import Request
from fastapi.responses import JSONResponse

router = APIRouter()


# ------------------- create category -------------------
@router.post("/save_category")
async def save_category(
    request: CategoryRequest,
    repo: CategoryRepo = Depends(get_repository(CategoryRepo)),
):
    service = CategoryService(repo)
    result = await service.create_category(request)
    return result


# ------------------- update category -------------------
@router.post("/update_category")
async def update_category(
    request: UpdateCategoryRequest,
    repo: CategoryRepo = Depends(get_repository(CategoryRepo)),
):
    service = CategoryService(repo)
    result = await service.update_category(request)
    return result


# -------------------fetch categories -------------------
@router.get("/fetch_categories", response_model=PaginatedCategoriesResponse)
async def fetch_categories(
    org_id: int = Query(...),
    user_id: int = Query(...),
    page: int = Query(1),
    limit: int = Query(5),
    repo: CategoryRepo = Depends(get_repository(CategoryRepo)),
):
    service = CategoryService(repo)
    return await service.fetch_categories(org_id, user_id, page, limit)



#--------------------Category Status--------------

@router.post("/updateCategoryStatus")
async def update_category_status(
    request: Request,
    cat_id: int,
    is_active: int,
):
    try:
        if is_active not in (0, 1):
            raise HTTPException(status_code=400, detail="Invalid status value")

        result = await CategoryService.update_category_status(request, cat_id, is_active)

        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["message"])

        return JSONResponse(content=result)

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")