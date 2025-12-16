from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class ReportIdsRequest(BaseModel):
    """Request model for report IDs."""

    report_ids: List[int]


class MeetingReportIdsRequest(BaseModel):
    """Request model for meeting report IDs."""

    meeting_report_ids: List[int]


class MailEffortRequest(BaseModel):
    """Request model for mail effort calculation."""

    mail_dtl_id: int


class ReportResponse(BaseModel):
    """Response model for report data."""

    user_id: int
    user_name: str
    organisation_name: str
    word_count: int
    keywords_found: str
    actual_effort_time: int
    planned_effort_time: int


class MailEffortResponse(BaseModel):
    """Response model for mail effort calculation."""

    message: str
    word_count: int
    keywords_found: List[str]
    actual_effort_time: int
    planned_effort_time: int


class ReportFilter(BaseModel):
    from_date: date
    to_date: date
    user_id: int
    role_id: int
    org_id: int
    keyword: Optional[str] = None
    category: Optional[str] = None
    user: Optional[str] = None
    file_type: Optional[str] = None


class MeetingDataRequest(BaseModel):
    from_date: date | None = None
    to_date: date | None = None
    user_id: int | None = None
    role_id: int | None = None
    org_id: int | None = None
    user: Optional[str] = None
