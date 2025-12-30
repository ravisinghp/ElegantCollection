from typing import Dict
from fastapi import HTTPException
from app.db.repositories.category_section_repo import CategoryRepo


class CategoryService:
    def __init__(self, repo: CategoryRepo):
        self.repo = repo

    # ------------------- create category + keyword-------------------
    async def create_category_keyword(self, request):
        category_name = request.category_name.strip()
        keyword_name = request.keyword_name.strip()
        user_id = request.user_id

        if not category_name:
            raise HTTPException(status_code=400, detail="Category name is required")

        if not keyword_name:
            raise HTTPException(status_code=400, detail="Keyword name is required")

        try:
            # Check category exists
            existing_cat = await self.repo.is_category_exists(category_name, user_id)

            if existing_cat:
                cat_id = existing_cat["cat_id"]

                # Check keyword exists in this category
                existing_keyword = await self.repo.is_keyword_exists(keyword_name, user_id, cat_id)
                if existing_keyword:
                    return{
                        "success": False,
                        "message": "Keyword already exists in this category"
                    }

                # Insert keyword only
                created_by = request.user_id
                keyword_id = await self.repo.create_keyword(keyword_name, user_id, created_by, cat_id)

                return {
                    "success": True,
                    "message": "Keyword added successfully under existing category",
                    "category_id": cat_id,
                    "keyword_id": keyword_id
                }

            # Category does not exist → create category & keyword
            await self.repo.create_category(category_name, user_id, user_id)
            new_cat = await self.repo.get_last_inserted_id()
            cat_id = new_cat["cat_id"]

            created_by = request.user_id
            keyword_id = await self.repo.create_keyword(keyword_name, user_id, created_by, cat_id)

            return {
                "success": True,
                "message": "Category & Keyword created successfully",
                "category_id": cat_id,
                "keyword_id": keyword_id
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


    # ------------------- fetch category keyword list -------------------
    async def get_category_keyword_list(self, user_id: int):
        return await self.repo.fetch_category_keyword_list(user_id)
    
    
    # ------------------- delete category/keyword -------------------
    async def delete_category_keyword(self, request):
        cat_id = request.cat_id
        keyword_id = request.keyword_id
        user_id = request.user_id

        # Delete keyword
        await self.repo.delete_keyword(keyword_id, user_id, cat_id)

        # Check remaining keywords under the same category
        remaining = await self.repo.count_keywords_under_category(cat_id, user_id)

        # No keyword left → delete category automatically
        if remaining == 0:
            await self.repo.delete_category(cat_id, user_id)

        return {
            "success": True,
            "message": "Record deleted successfully."
        }
