from typing import Optional

from pydantic import BaseModel, EmailStr, HttpUrl

from app.models.domain.users import User
from app.models.schemas.rwschema import RWSchema





class UserInLogin(RWSchema):
    email: EmailStr
    password: str


class UserInCreate(UserInLogin):
    username: str


class UserInUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    # bio: Optional[str] = None
    # image: Optional[HttpUrl] = None


class UserWithToken(User):
    id:int
    token: str
    username: str
    email: EmailStr 
    org_id: Optional[int] = None
    role_id: Optional[int] = None
    



class UserWithoutToken(BaseModel):
    id:int
    username: str
    email: EmailStr 
    org_id: Optional[int] = None
    role_id: Optional[int] = None
    token: Optional[str] = None
    password: str
    # fileName: str
    # fileType: int
    # contractTypeId: int
    # statusId: int
    # status_message: Optional[str] = ""
    # riskScore: float



class UserInResponse(BaseModel):
    #user: UserWithToken
     user: UserWithoutToken


class MailResponse(BaseModel):
    subject: Optional[str]
    body: Optional[str]
    date_time: Optional[str]  # YYYY-MM-DD
    mail_from: Optional[str]
    mail_to: Optional[str]
    mail_cc: Optional[str]
    word_count: Optional[str]
    keyword: Optional[str] = None
    repeated_keyword: Optional[str] = None
    cal_id: Optional[int] = None
    user_id: Optional[int] = None
    keyword_id: Optional[int] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    is_active: int = 1
    graph_mail_id: Optional[str] = None

class BusinessAdminSearchRequest(BaseModel):
    fromDate: Optional[str] = None
    toDate: Optional[str] = None
    userId: Optional[int] = None
    vendorNumber: Optional[str] = None
    

class DeleteUserPayload(BaseModel):
    user_id: int
    action: str  # "inactive" or "delete"