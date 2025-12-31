from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from pydantic import ConfigDict
from starlette.config import Config

config = Config(".env")


class UserCreate(BaseModel):
    user_name: str
    mail_id: EmailStr
    password: str
    role_id: int
    provider:str
    folder_name: str
    created_by: int


class UserUpdate(BaseModel):
    user_name: Optional[str] = None
    mail_id: Optional[EmailStr] = None
    password: Optional[str] = None
    role_id: Optional[int] = None



class KeywordResponse(BaseModel):
    keyword_id: int
    keyword_text: str
    ref_word_id: int
    created_on: datetime
    updated_on: Optional[datetime] = None
    is_active: bool


class RWModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, validate_by_name=True  # replaces orm_mode
    )


class UserResponse(BaseModel):
    user_id: int
    user_name: Optional[str] = None
    mail_id: EmailStr
    org_id: Optional[int] = None
    role_id: Optional[int] = None
    org_name: Optional[str] = None
    role_name: Optional[str] = None
    token: Optional[str] = None
    provider: Optional[str] = None
    created_on: datetime
    updated_on: Optional[datetime] = None


# New schema that matches your exact requirements
class LoginResponse(BaseModel):
    userid: int
    username: str
    email: str
    roleid: Optional[int] = None
    rolename: Optional[str] = None
    token: str
    provider: Optional[str] = None 
    term_condition_flag: Optional[int] = 0
    is_first_login: bool = True


# replaces allow_population_by_field_name


class UserListResponse(BaseModel):
    user_name: str
    org_name: str
    user_id: int
    org_id: int
    email_count: int


class PaginatedUsersResponse(BaseModel):
    users: List[UserListResponse]
    totalCount: int


class KeywordListResponse(BaseModel):
    keyword_name: str
    keyword_id: int
    org_id: int
    user_id: Optional[int] = None


class PaginatedKeywordsResponse(BaseModel):
    keywords: List[KeywordListResponse]
    totalCount: int


class RoleResponse(BaseModel):
    role_id: int
    role_name: str


class CategoryResponse(BaseModel):
    cat_id: int
    cat_name: str


##This is for email configuration
from pydantic import BaseModel, EmailStr


class EmailSettings(BaseModel):
    MAIL_USERNAME: str = config("MAIL_USERNAME", default="")
    MAIL_PASSWORD: str = config("MAIL_PASSWORD", default="")
    MAIL_FROM: EmailStr = config("MAIL_FROM", default="no-reply@example.com")
    MAIL_FROM_NAME: str = config("MAIL_FROM_NAME", default="iCapture")
    MAIL_PORT: int = int(config("MAIL_PORT", default=587))
    MAIL_SERVER: str = config("MAIL_SERVER", default="smtp.gmail.com")
    # New flags expected by fastapi-mail (replacing TLS/SSL)
    MAIL_STARTTLS: bool = bool(config("MAIL_STARTTLS", default=True))
    MAIL_SSL_TLS: bool = bool(config("MAIL_SSL_TLS", default=False))
    # Backward compatibility (not used directly in ConnectionConfig)
    MAIL_TLS: bool = bool(config("MAIL_TLS", default=True))
    MAIL_SSL: bool = bool(config("MAIL_SSL", default=False))
    USE_CREDENTIALS: bool = bool(config("USE_CREDENTIALS", default=True))

