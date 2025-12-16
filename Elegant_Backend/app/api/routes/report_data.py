from fastapi import Response, HTTPException, APIRouter, Depends
from pydantic import BaseModel, field_validator, FieldValidationInfo, Field
import csv, io
from fpdf import FPDF
from typing import Optional, List, Dict
import logging
from datetime import datetime
from app.services.report_data_service import ReportDataService
from app.db.repositories.report_data_repo import ReportDataRepo
from app.api.dependencies.database import get_repository
from app.models.schemas.report_schemas import (
    ReportIdsRequest,
    ReportFilter,
    MeetingDataRequest,
    MeetingReportIdsRequest,
)
from fastapi.responses import FileResponse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
# repo = report_data_repo() # Removed direct instantiation
# service = EffortService(repo) # Removed direct instantiation

# ---------------- CSV mail Export ----------------
@router.post("/mail/csv")
async def export_csv(
    request: ReportIdsRequest,
    repo: ReportDataRepo = Depends(get_repository(ReportDataRepo)),
):
    if not request.report_ids:
        raise HTTPException(status_code=400, detail="report_ids is mandatory")

    try:
        rows = await repo.fetch_report_data(request.report_ids)
        logger.info(f"Fetched {len(rows) if rows else 0} rows for CSV export")

        if not rows:
            raise HTTPException(
                status_code=404, detail="No data found for the provided report IDs"
            )

        output = io.StringIO()
        writer = csv.writer(output)

        # ---------------Header---------------
        writer.writerow(
            [
                "Report ID",
                "Date",
                "From",
                "To",
                "Categories",
                "Mail Words",
                "Attach Words",
                "Keywords",
                "Computed Efforts(min)",
                "Revise Efforts(min)",
            ]
        )

        # ---------------Data---------------
        for row in rows:
            try:
                created_date = row.get("created_date")
                if isinstance(created_date, str):
                    try:
                        dt = datetime.strptime(created_date, "%Y-%m-%d")
                    except ValueError:
                        dt = datetime.fromisoformat(created_date)
                    created_date = dt.strftime("%d-%m-%Y")
                elif isinstance(created_date, datetime):
                    created_date = created_date.strftime("%d-%m-%Y")
                else:
                    created_date = str(created_date)
            except Exception:
                created_date = str(row.get("created_date", ""))

            writer.writerow(
                [
                    row.get("report_id"),
                    created_date,
                    row.get("mail_from"),
                    row.get("mail_to"),
                    row.get("cat_name"),
                    row.get("word_count"),
                    row.get("attachment_word_count"),
                    row.get("repeated_keyword_count"),
                    row.get("actual_effort_time"),
                    row.get("planned_effort_time"),
                ]
            )

        response = Response(content=output.getvalue(), media_type="text/csv")
        response.headers["Content-Disposition"] = "attachment; filename=report_data.csv"
        return response

    except Exception as e:
        logger.error(f"Error generating CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating CSV: {str(e)}")


# ---------------- mail PDF Export ----------------
class PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.col_widths = [12, 20, 30, 30, 20, 15, 15, 15, 20, 20]  # adjusted widths
        self.table_width = sum(self.col_widths)
        self.line_height = 5

    def header(self):
        self.set_font("Arial", "BU", 14)
        self.cell(0, 10, "Mails Report Data", ln=True, align="C")
        self.ln(3)
        self.set_font("Arial", "B", 7)

    def add_table_header(self):
        headers = [
            "Report ID",
            "Date",
            "From",
            "To",
            "Categories",
            "Mail Words",
            "Attach Words",
            "Keywords",
            "Computed Efforts(min)",
            "Revise Efforts(min)",
        ]
        self.table_row(headers, is_header=True, is_header_row=True)

    def check_page_break(self, row_height, is_header_row=False):
        if self.get_y() + row_height > self.page_break_trigger:
            self.add_page()
            self.add_table_header()

    def table_row(self, row, is_header=False, is_header_row=False):
        expected_columns = len(self.col_widths)
        if len(row) != expected_columns:
            row = (list(row) + [""] * expected_columns)[:expected_columns]

        # Wrap text
        cell_texts, line_counts = [], []
        for i, text in enumerate(row):
            wrapped = self.multi_cell(
                self.col_widths[i],
                self.line_height,
                str(text),
                border=0,
                align="L",
                split_only=True,
            )
            cell_texts.append(wrapped)
            line_counts.append(len(wrapped))

        row_height = max(line_counts) * self.line_height
        self.check_page_break(row_height, is_header_row=is_header_row)

        start_x = (self.w - self.table_width) / 2
        y = self.get_y()

        for i, lines in enumerate(cell_texts):
            x = start_x + sum(self.col_widths[:i])
            self.set_xy(x, y)
            self.rect(x, y, self.col_widths[i], row_height)
            for line in lines:
                self.multi_cell(
                    self.col_widths[i],
                    self.line_height,
                    line,
                    border=0,
                    align="C" if is_header else "L",
                )
                self.set_x(x)

        self.set_y(y + row_height)


@router.post("/mail/pdf")
async def export_pdf(
    request: ReportIdsRequest,
    repo: ReportDataRepo = Depends(get_repository(ReportDataRepo)),
):
    if not request.report_ids:
        raise HTTPException(status_code=400, detail="report_ids is mandatory")
    try:
        rows = await repo.fetch_report_data(request.report_ids)
        if not rows:
            raise HTTPException(
                status_code=404, detail="No data found for the provided report IDs"
            )

        valid_rows = []
        for row in rows:
            try:
                created_date = row.get("created_date")
                if isinstance(created_date, str):
                    try:
                        dt = datetime.strptime(created_date, "%Y-%m-%d")
                    except ValueError:
                        dt = datetime.fromisoformat(created_date)
                    created_date = dt.strftime("%d-%m-%Y")
                elif isinstance(created_date, datetime):
                    created_date = created_date.strftime("%d-%m-%Y")
                else:
                    created_date = str(created_date)
            except Exception:
                created_date = str(row.get("created_date", ""))

            valid_rows.append(
                [
                    row.get("report_id"),
                    created_date,
                    row.get("mail_from"),
                    row.get("mail_to"),
                    row.get("cat_name"),
                    row.get("word_count"),
                    row.get("attachment_word_count"),
                    row.get("repeated_keyword_count"),
                    row.get("actual_effort_time"),
                    row.get("planned_effort_time"),
                ]
            )

        pdf = PDF()
        pdf.add_page()
        pdf.add_table_header()
        pdf.set_font("Arial", size=7)

        for row in valid_rows:
            pdf.table_row(row)

        pdf_output = pdf.output(dest="S").encode("latin1")
        return Response(
            content=pdf_output,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=report_data.pdf"},
        )

    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")


# ---------------- MEETING CSV Export ----------------
@router.post("/meeting/csv")
async def export_meeting_csv(
    request: MeetingReportIdsRequest,
    repo: ReportDataRepo = Depends(get_repository(ReportDataRepo)),
):
    if not request.meeting_report_ids:
        raise HTTPException(status_code=400, detail="meeting_report_ids is mandatory")

    try:
        rows = await repo.fetch_meeting_report_data(request.meeting_report_ids)
        if not rows:
            raise HTTPException(
                status_code=404, detail="No meeting data found for the provided IDs"
            )

        output = io.StringIO()
        writer = csv.writer(output)

        # ✅ Header
        writer.writerow(
            [
                "Meeting Report ID",
                "Date",
                "From",
                "To",
                "Meeting Duration(min)",
                "Efforts(min)",
            ]
        )

        # ✅ Data
        for row in rows:
            # --- Date formatting ---
            try:
                date_val = row["date_time"]
                if isinstance(date_val, str):
                    try:
                        dt = datetime.strptime(date_val, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        dt = datetime.fromisoformat(date_val.split("T")[0])
                    date_val = dt.strftime("%d-%m-%Y")
                elif isinstance(date_val, datetime):
                    date_val = date_val.strftime("%d-%m-%Y")
                else:
                    date_val = str(date_val)
            except Exception:
                date_val = str(row["date_time"])

            writer.writerow(
                [
                    row["report_id"],  # meeting_report_id
                    date_val,
                    row["from"],  # From
                    row["to"],  # To
                    row["meeting_duration"],  # Efforts(min)
                    row["efforts_time"],  # Efforts(min)
                ]
            )

        response = Response(content=output.getvalue(), media_type="text/csv")
        response.headers["Content-Disposition"] = (
            "attachment; filename=meeting_report.csv"
        )
        return response

    except Exception as e:
        logger.error(f"Error generating Meeting CSV: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error generating Meeting CSV: {str(e)}"
        )


# ---------------- MEETING PDF Export ----------------
class MeetingPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.col_widths = [25, 30, 45, 45, 25, 25]
        self.table_width = sum(self.col_widths)
        self.line_height = 5

    def header(self):
        self.set_font("Arial", "BU", 14)
        self.cell(0, 10, "Meeting Report Data", ln=True, align="C")
        self.ln(3)
        self.set_font("Arial", "B", 7)

    def add_table_header(self):
        headers = [
            "Meeting Report ID",
            "Date",
            "From",
            "To",
            "Meeting Duration(min)",
            "Efforts(min)",
        ]
        self.table_row(headers, is_header=True, is_header_row=True)

    def check_page_break(self, row_height, is_header_row=False):
        if self.get_y() + row_height > self.page_break_trigger:
            self.add_page()
            self.add_table_header()

    def table_row(self, row, is_header=False, is_header_row=False):
        expected_columns = len(self.col_widths)
        if len(row) != expected_columns:
            row = (list(row) + [""] * expected_columns)[:expected_columns]

        cell_texts, line_counts = [], []
        for i, text in enumerate(row):
            wrapped = self.multi_cell(
                self.col_widths[i],
                self.line_height,
                str(text),
                border=0,
                align="L",
                split_only=True,
            )
            cell_texts.append(wrapped)
            line_counts.append(len(wrapped))

        row_height = max(line_counts) * self.line_height
        self.check_page_break(row_height, is_header_row=is_header_row)

        start_x = (self.w - self.table_width) / 2
        y = self.get_y()

        for i, lines in enumerate(cell_texts):
            x = start_x + sum(self.col_widths[:i])
            self.set_xy(x, y)
            top_padding = (row_height - len(lines) * self.line_height) / 2
            self.rect(x, y, self.col_widths[i], row_height)
            self.set_xy(x, y + top_padding)
            for line in lines:
                self.multi_cell(
                    self.col_widths[i],
                    self.line_height,
                    line,
                    border=0,
                    align="C" if is_header else "L",
                )
                self.set_x(x)

        self.set_y(y + row_height)


@router.post("/meeting/pdf")
async def export_meeting_pdf(
    request: MeetingReportIdsRequest,
    repo: ReportDataRepo = Depends(get_repository(ReportDataRepo)),
):
    if not request.meeting_report_ids:
        raise HTTPException(status_code=400, detail="meeting_report_ids is mandatory")

    try:
        rows = await repo.fetch_meeting_report_data(request.meeting_report_ids)
        if not rows:
            raise HTTPException(status_code=404, detail="No meeting data found")

        valid_rows = []
        for row in rows:
            try:
                date_val = row["date_time"]
                if isinstance(date_val, str):
                    try:
                        dt = datetime.strptime(date_val, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        dt = datetime.fromisoformat(date_val.split("T")[0])
                    date_val = dt.strftime("%d-%m-%Y")
                elif isinstance(date_val, datetime):
                    date_val = date_val.strftime("%d-%m-%Y")
                else:
                    date_val = str(date_val)
            except Exception:
                date_val = str(row["date_time"])

            valid_rows.append(
                [
                    row["report_id"],
                    date_val,
                    row["from"],
                    row["to"],
                    row["meeting_duration"],
                    row["efforts_time"],
                ]
            )

        pdf = MeetingPDF()
        pdf.add_page()
        pdf.add_table_header()  # header on first page
        pdf.set_font("Arial", size=7)

        for row in valid_rows:
            pdf.table_row(row)

        pdf_output = pdf.output(dest="S").encode("latin1")
        return Response(
            content=pdf_output,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=meeting_report.pdf"},
        )

    except Exception as e:
        logger.error(f"Error generating Meeting PDF: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error generating Meeting PDF: {str(e)}"
        )


# ---------------- Effort by Mail ----------------
class MailEffortRequest(BaseModel):
    user_id: int
    org_id: int
    mail_dtl_id: int | None = None
    report_id: int | None = None
    # Fields allowed for update
    efforts: Optional[float] = None
    keyword_efforts: Optional[int] = None


@router.post("/mail")
async def add_mail_effort(
    request: MailEffortRequest,
    report_repo: ReportDataRepo = Depends(get_repository(ReportDataRepo)),
):
    service = ReportDataService(report_repo)
    result = await service.process_mail_effort(
        user_id=request.user_id,
        org_id=request.org_id,
        mail_dtl_id=request.mail_dtl_id,
        report_id=request.report_id,
        efforts=request.efforts,
        keyword_efforts=request.keyword_efforts,
    )
    return result


# ---------------- Fetch Report Data ----------------
@router.post("/fetch_report_data_filtered")
async def fetch_report_data_filtered(
    filter_request: ReportFilter,
    repo: ReportDataRepo = Depends(get_repository(ReportDataRepo)),
):
    service = ReportDataService(repo)

    # optional fields can be None if not sent
    result = await service.fetch_mail_report_data(
        from_date=filter_request.from_date,
        to_date=filter_request.to_date,
        user_id=filter_request.user_id,
        role_id=filter_request.role_id,
        org_id=filter_request.org_id,
        keyword=filter_request.keyword,
        category=filter_request.category,
        user=filter_request.user,
        file_type=filter_request.file_type,
    )
    return result


# ---------------- Fetch Email subject, body and attachment ----------------
class MailDetailRequest(BaseModel):
    mail_dtl_id: int


@router.post("/fetch_mail_details_by_id")
async def fetch_mail_details_by_id(
    request: MailDetailRequest,
    report_repo: ReportDataRepo = Depends(get_repository(ReportDataRepo)),
):
    """
    fetch mail details by mail_dtl_id.
    Only mail_dtl_id is required from frontend.
    """
    service = ReportDataService(report_repo)
    result = await service.fetch_mail_details_by_id(mailDtl_id=request.mail_dtl_id)
    return result


# ---------------- Fetch Meeting subject, body and attachment ----------------
class MeetingDetailRequest(BaseModel):
    cal_id: int


@router.post("/fetch_meeting_details_by_id")
async def fetch_meeting_details_by_id(
    request: MeetingDetailRequest,
    report_repo: ReportDataRepo = Depends(get_repository(ReportDataRepo)),
):
    """
    fetch meeting details by cal_id.
    Only cal_id is required from frontend.
    """
    service = ReportDataService(report_repo)
    result = await service.fetch_meeting_details_by_id(cal_id=request.cal_id)
    return result


# ---------------- Preview Attachment ----------------
class AttachmentPreviewRequest(BaseModel):
    mail_dtl_id: int
    user_id: int
    attachment_name: str


@router.post("/attachments/preview")
async def preview_attachment(
    request: AttachmentPreviewRequest,
    repo: ReportDataRepo = Depends(get_repository(ReportDataRepo)),
):
    service = ReportDataService(repo)
    file_info = await service.preview_attachment(
        request.mail_dtl_id, request.user_id, request.attachment_name
    )

    if not file_info:
        raise HTTPException(status_code=404, detail="Attachment not found")

    return FileResponse(
        path=file_info["path"], media_type=file_info["type"], filename=file_info["name"]
    )


# --------------Business Rules save----------------
class SingleRule(BaseModel):
    org_id: int
    rule_key: str
    rule_value: float


class EffortRuleRequest(BaseModel):
    rules: List[SingleRule]  # <-- Accept multiple rules


@router.post("/save_business_rules")
async def insert_effort_rules(
    request: EffortRuleRequest,
    repo: ReportDataRepo = Depends(get_repository(ReportDataRepo)),
):
    service = ReportDataService(repo)
    results = []

    for rule in request.rules:
        # Validate org_id
        if not rule.org_id or rule.org_id == 0:
            results.append({"rule_key": rule.rule_key, "message": "Invalid org_id"})
            continue

        msg = await service.insert_rule(rule.org_id, rule.rule_key, rule.rule_value)
        results.append({"rule_key": rule.rule_key, "message": msg})

    return {"success": True, "results": results}


# ----------------Fetch Business Rules----------------
class BusinessRulesRequest(BaseModel):
    org_id: int
    user_id: int

    @field_validator("org_id", "user_id")
    def not_null_or_zero(cls, v, info: FieldValidationInfo):
        if v is None or v == 0:
            raise ValueError(f"{info.field_name} must not be null or 0")
        return v


@router.post("/fetch_business_rules_by_org_id")
async def fetch_business_rules_by_org_id(
    request: BusinessRulesRequest,
    repo: ReportDataRepo = Depends(get_repository(ReportDataRepo)),
) -> Dict:
    service = ReportDataService(repo)
    rules = await service.fetch_business_rules(request.org_id, request.user_id)

    if not rules:
        return {
            "success": False,
            "message": "No business rules found",
            "rules": [],
        }

    return {
        "success": True,
        "message": "Business rules fetched successfully",
        "rules": rules,
    }


# ----------------Update Business Rules----------------
class UpdateBusinessRuleRequest(BaseModel):
    org_id: int = Field(..., gt=0)  # must be > 0
    rule_id: int = Field(..., gt=0)  # must be > 0
    rule_value: int = Field(..., gt=0)  # must be > 0


@router.post("/business_rules/update")
async def update_business_rule(
    request: UpdateBusinessRuleRequest,
    repo: ReportDataRepo = Depends(get_repository(ReportDataRepo)),
) -> Dict:
    service = ReportDataService(repo)

    updated = await service.update_rule(
        rule_id=request.rule_id, value=request.rule_value, org_id=request.org_id
    )

    if not updated:
        raise HTTPException(status_code=404, detail="Rule not found")

    return {"message": "Rule updated successfully"}


# -------------------- Fetch Meeting Data --------------------
@router.post("/fetch_meeting_data")
async def fetch_meeting_data(
    meeting_data_request: MeetingDataRequest,
    repo: ReportDataRepo = Depends(get_repository(ReportDataRepo)),
):
    service = ReportDataService(repo)
    result = await service.fetch_meeting_data(
        meeting_data_request.org_id,
        meeting_data_request.from_date,
        meeting_data_request.to_date,
        meeting_data_request.user_id,
        meeting_data_request.page if hasattr(meeting_data_request, "page") else 1,
        meeting_data_request.limit if hasattr(meeting_data_request, "limit") else 10,
        meeting_data_request.role_id,
        user=meeting_data_request.user,
    )
    return result


# -------------------- Fetch Entity Types --------------------
@router.get("/fetch_entity_types")
async def fetch_entity_types(
    repo: ReportDataRepo = Depends(get_repository(ReportDataRepo)),
):
    service = ReportDataService(repo)
    result = await service.fetch_entity_types()
    return result


# ------------------------update meeting effort----------------------
class UpdateMeetingRequest(BaseModel):
    meeting_report_id: int
    efforts: Optional[float] = None


@router.post("/update_meeting")
async def update_meeting_effort(
    request: UpdateMeetingRequest,
    report_repo: ReportDataRepo = Depends(get_repository(ReportDataRepo)),
):
    service = ReportDataService(report_repo)
    result = await service.update_meeting_effort(
        meeting_report_id=request.meeting_report_id,
        efforts=request.efforts,
    )
    return result


# # ---------------------fetch Folder for filter data----------------
# @router.get("/fetch_folders_name")
# async def fetch_folders_name(
#     repo: ReportDataRepo = Depends(get_repository(ReportDataRepo)),
# ):
#     service = ReportDataService(repo)
#     result = await service.fetch_folders_name()
#     return result


# -----------------------Recalculate effort times for all reports------------------------------
class RecalcEffortRequest(BaseModel):
    org_id: int = Field(..., gt=0, description="Organization ID must be positive")
    user_id: Optional[int] = Field(
        None, gt=0, description="Optional user ID, must be positive if provided"
    )


@router.post("/recalculate_efforts")
async def recalc_report_efforts(
    request: RecalcEffortRequest,
    report_repo: ReportDataRepo = Depends(get_repository(ReportDataRepo)),
):
    """
    Recalculate effort times for all reports of an org_id.
    Optionally, filter by user_id.
    """
    service = ReportDataService(report_repo)
    try:
        result = await service.recalc_effort_for_existing_reports(
            org_id=request.org_id, user_id=request.user_id
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error recalculating efforts: {str(e)}"
        )


# ---------------------fetch Keywords List for filter data----------------
class FilterRequest(BaseModel):
    org_id: int = Field(..., gt=0, description="Organization ID must be positive")
    role_id:int | None = None


# --------------------- Fetch Keywords List ----------------
@router.post("/fetch_keywords_list")
async def fetch_keywords_list(
    request: FilterRequest,
    repo: ReportDataRepo = Depends(get_repository(ReportDataRepo)),
):
    service = ReportDataService(repo)
    try:
        result = await service.fetch_keywords_list(org_id=request.org_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching keywords list: {str(e)}"
        )


# --------------------- Fetch Category List ----------------
@router.post("/fetch_category_list")
async def fetch_category_list(
    request: FilterRequest,
    repo: ReportDataRepo = Depends(get_repository(ReportDataRepo)),
):
    service = ReportDataService(repo)
    try:
        result = await service.fetch_category_list(org_id=request.org_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching category list: {str(e)}"
        )


# --------------------- Fetch Users List ----------------
@router.post("/fetch_users_list")
async def fetch_users_list(
    request: FilterRequest,
    repo: ReportDataRepo = Depends(get_repository(ReportDataRepo)),
):
    service = ReportDataService(repo)
    try:
        result = await service.fetch_users_list(org_id=request.org_id, role_id=request.role_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching users list: {str(e)}"
        )


# --------------------- Fetch File Type List ----------------
@router.get("/fetch_fileType_list")
async def fetch_fileType_list(
    repo: ReportDataRepo = Depends(get_repository(ReportDataRepo)),
):
    service = ReportDataService(repo)
    try:
        result = await service.fetch_fileType_list()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching file type list: {str(e)}"
        )
