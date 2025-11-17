from datetime import date
from typing import Optional
from app.models.domain.rwmodel import RWModel


class ReportData(RWModel):
    report_id: int
    user_id: int
    org_id: int
    word_count: int
    keywords_found: str
    actual_effort_time: int
    planned_effort_time: int


class MailDetails(RWModel):
    mail_dtl_id: int
    user_id: int
    date_time: date
    subject: Optional[str]
    body: Optional[str]
    attachments_text: Optional[str] = None
