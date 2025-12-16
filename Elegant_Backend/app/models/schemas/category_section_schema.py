from pydantic import BaseModel
from typing import List,Optional

class Category(BaseModel):
    category_id: int
    category_name: str
    is_active: int
    keywords: Optional[str] = None 


class CategoryRequest(BaseModel):
    category_name: str
    user_id: int
    org_id: int


class UpdateCategoryRequest(BaseModel):
    category_id: int
    user_id: int
    category_name: str
    
class PaginatedCategoriesResponse(BaseModel):
    categories: List[Category]
    totalCount: int
