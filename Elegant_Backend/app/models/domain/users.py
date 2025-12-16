from typing import Optional

from app.models.common import DateTimeModelMixin, IDModelMixin
from app.models.domain.rwmodel import RWModel
from app.services import security


class User(RWModel):
    username:str
    email:str

class file_list(RWModel):
    id:int
    fileName: str
    fileType: int
    contractTypeId: int
    statusId: int
    status_message: Optional[str] = ""
    riskScore: float


class UserInDB(IDModelMixin, DateTimeModelMixin, User):
   
    def check_password(self, password: str) -> bool:
        return security.verify_password(self.salt + password, self.hashed_password)

    def change_password(self, password: str) -> None:
        self.salt = security.generate_salt()
        self.hashed_password = security.get_password_hash(self.salt + password)



class MailResponse(RWModel):
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
