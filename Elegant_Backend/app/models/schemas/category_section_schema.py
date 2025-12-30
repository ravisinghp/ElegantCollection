from pydantic import BaseModel
from typing import Optional

class CategoryKeywordRequest(BaseModel):
    category_name: str
    keyword_name: str
    user_id: int


class UserRequest(BaseModel):
    user_id: int
    

class DeleteCategoryKeywordRequest(BaseModel):
    cat_id: int
    keyword_id: int
    user_id: int
