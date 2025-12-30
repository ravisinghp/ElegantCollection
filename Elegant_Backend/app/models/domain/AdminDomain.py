from app.models.domain.rwmodel import RWModel
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict


class UserInDB(BaseModel):
    user_id: int = Field(alias="userId")
    user_name: str = Field(alias="userName")
    mail_id: str = Field(alias="mailId")
    role_id: int
    password: str
    folder_name: str = Field(alias="folderName")
    created_by: Optional[int] = None
    provider :str

    model_config = ConfigDict(
        populate_by_name=True,  # allow both snake_case and camelCase
        from_attributes=True,  # replaces orm_mode
    )


class RoleMaster(BaseModel):
    role_id: int
    role_name: str


# class PaginatedUsers(BaseModel):
#     users: List[UserInDB]
#     total: int
#     page: int
#     limit: int
#     total_pages: 


#Update the PO Comment On UI 
class UpdatePoCommentRequest(BaseModel):
    po_missing_id: Optional[int] = None
    po_mismatch_id: Optional[int] = None
    comment: str
