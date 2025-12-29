from fastapi import APIRouter, Depends, Query
from app.db.repositories.category_section_repo import CategoryRepo
from app.services.category_section_service import CategoryService
from app.api.dependencies.database import get_repository
from app.models.schemas.category_section_schema import (
    CategoryKeywordRequest,
    DeleteCategoryKeywordRequest,
    UserRequest
)

router = APIRouter()


# ------------------- create category -------------------
@router.post("/create_category_keyword")
async def create_category_keyword(
    request: CategoryKeywordRequest,
    repo: CategoryRepo = Depends(get_repository(CategoryRepo))
):
    service = CategoryService(repo)
    result = await service.create_category_keyword(request)
    return result


# ------------------- fetch category keyword list -------------------
@router.get("/category_keyword_list")
async def category_keyword_list(
    request: UserRequest,
    repo: CategoryRepo = Depends(get_repository(CategoryRepo))
):
    service = CategoryService(repo)
    result = await service.get_category_keyword_list(request.user_id)
    return {"success": True, "data": result}


# ------------------- delete category/keyword -------------------
@router.post("/delete_category_keyword")
async def delete_category_keyword(
    request: DeleteCategoryKeywordRequest,
    repo: CategoryRepo = Depends(get_repository(CategoryRepo))
):
    service = CategoryService(repo)
    result = await service.delete_category_keyword(request)
    return result

