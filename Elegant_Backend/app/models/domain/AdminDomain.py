from app.models.domain.rwmodel import RWModel
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict
from datetime import date
from typing import List, Optional



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
    
class UpdateSharepointPoCommentRequest(BaseModel):
    sharepoint_po_missing_id: Optional[int] = None
    sharepoint_po_mismatch_id: Optional[int] = None
    comment: str

#Scheduler Information from frontend it coming
class SchedulerRequest(BaseModel):
    user_id:int
    #date: date
    days: List[str]
    hour: int
    minute: int


class DownloadMissingMismatchRequest(BaseModel):
    user_id: int
    role_id: int
    #selected_ids: Optional[List[int]] = None
    
class DownloadCombinedAllPORequest(BaseModel):
    user_id: int
    role_id: int
    email_missing_ids: list[int] = []
    email_mismatch_ids: list[int] = []
    sharepoint_missing_ids: list[int] = []
    sharepoint_mismatch_ids: list[int] = []
    
class DownloadAllMissingMismatchRequest(BaseModel):
    user_id: int
    role_id: int

class DownloadSharepointMissingMismatchRequest(BaseModel):
    user_id : int
    role_id : int
    selected_ids: Optional[List[int]] = None
    
class DownloadAllSelectedSharepointPORequest(BaseModel):
    user_id: int
    role_id: int
    sharepoint_missing_ids: Optional[List[int]] = []
    sharepoint_mismatch_ids: Optional[List[int]] = []
    
    
class DownloadCombinedMissingMismatchRequest(BaseModel):
    user_id: int
    role_id: int
    system_selected_ids: Optional[List[int]] = []
    sharepoint_selected_ids: Optional[List[int]] = []
class GenerateMissingPoReport(BaseModel):
    user_id : int
    po_det_ids: List[int]
    
class GenerateMissingSharepointPoReport(BaseModel):
    user_id : int
    
class FetchMissingMismatchReport(BaseModel):
    user_id : int
    role_id:int
   
class SharepointFetchMissingMismatchReport(BaseModel):
    user_id : int
    role_id:int
class FolderMappingRequest(BaseModel):
    user_id: int
    folder_name: str
    