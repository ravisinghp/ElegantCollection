from typing import Dict
from app.db.repositories.category_section_repo import CategoryRepo
from app.models.schemas.category_section_schema import (
    CategoryRequest,
    UpdateCategoryRequest,
)


class CategoryService:
    def __init__(self, repo: CategoryRepo):
        self.repo = repo

    # ------------------- create category -------------------
    async def create_category(self, request: CategoryRequest) -> Dict:
        if not request.org_id or not request.user_id:
            return {"success": False, "message": "Invalid org_id or user_id"}

        try:
            # lean category name (remove spaces at start/end)
            clean_name = request.category_name.strip()

            if not clean_name:
                return {"success": False, "message": "Category name cannot be empty"}

            # Check if category already exists (case-insensitive, same org_id)
            existing = await self.repo.find_by_name(clean_name, request.org_id)
            if existing:
                return {"Duplicate Category": False, "message": "Category already exists with this name, please try with a different name."}

            # Insert if not exists
            await self.repo.insert_category(
                category_name=clean_name,
                org_id=request.org_id,
                user_id=request.user_id,
                created_by=request.user_id,
            )

            await self.repo._cur.connection.commit()
            row = await self.repo.get_last_inserted_id()

            return {
                "success": True,
                "message": "Category created successfully",
                "category_id": row["cat_id"],
            }
        except Exception as e:
            await self.repo._cur.connection.rollback()
            return {"success": False, "message": str(e)}

    # ------------------- update category -------------------
    async def update_category(self, request: UpdateCategoryRequest) -> Dict:
        if not request.category_id:
            return {"success": False, "message": "category_id required"}

        try:
            await self.repo.update_category_record(
                category_id=request.category_id,
                category_name=request.category_name,
                updated_by=request.user_id,
            )

            await self.repo._cur.connection.commit()
            return {
                "success": True,
                "message": "Category updated successfully",
                "category_id": request.category_id,
            }
        except Exception as e:
            await self.repo._cur.connection.rollback()
            return {"success": False, "message": str(e)}

    # ------------------- fetch categories -------------------
    # async def fetch_categories(self, org_id: int, user_id: int, page: int, limit: int):
    #     rows = await self.repo.fetch_categories(org_id, user_id, page, limit)

    #     if not rows or len(rows) == 0:
    #         return {"success": True, "message": "No categories found", "categories": []}

    #     return {
    #         "success": True,
    #         "message": "Categories fetched successfully",
    #         "categories": rows,
    #     }
    
    
    async def fetch_categories(self, org_id: int, user_id: int, page: int, limit: int):
        result = await self.repo.fetch_categories(org_id, user_id, page, limit)
        if not result["categories"]:
            return {
                "categories": [],
                "totalCount": 0
                }
            
        return result
        
        
#--------------------Update the Category Status----------------
    async def update_category_status(request, cat_id: int, is_active: int):
        try:
            result = await CategoryRepo.update_category_status(request, cat_id, is_active)

            if not result["success"]:
                return {"success": False, "message": result["message"]}

            return {"success": True, "message": "Category status updated successfully"}
        except Exception as e:
            return {"success": False, "message": f"Service error: {str(e)}"}

