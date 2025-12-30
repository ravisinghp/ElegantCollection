
from starlette.requests import Request
from fastapi import HTTPException
from app.db.repositories import UserRepo
from typing import List, Dict, Any
from collections import Counter
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> c91285d3e10beced0bc4f53193cdf2f4f500bcd7

#Total R&D Effort On User Dashboard
async def get_total_user_effort_by_user_id(user_id: int, from_date: str, to_date: str, request: Request):
    try:
        return await UserRepo.fetch_total_user_effort_by_id(user_id, from_date, to_date, request)
    except Exception as e:
        return None


#Fetching Total Numbers of Emails on User Dashboard
async def get_emails_processed_by_user_id(user_id: int, from_date: str, to_date: str, request: Request):
    try:
        return await UserRepo.fetch_emails_processed_by_user_id(user_id, from_date, to_date, request)
<<<<<<< HEAD
=======
=======
import io
import pandas as pd

#Total R&D Effort On User Dashboard
# async def get_total_user_effort_by_user_id(user_id: int, from_date: str, to_date: str, request: Request):
#     try:
#         return await UserRepo.fetch_total_user_effort_by_id(user_id, from_date, to_date, request)
#     except Exception as e:
#         return None


#Fetching Total Numbers of Emails on User Dashboard
async def get_emails_processed_by_user_id(user_id: int, request: Request):
    try:
        return await UserRepo.fetch_emails_processed_by_user_id(user_id, request)
>>>>>>> 90466875ac1d9c50955449637aa13f6f4f1da8c7
>>>>>>> c91285d3e10beced0bc4f53193cdf2f4f500bcd7
    except Exception as e:
        return None


#Fetching Total Numbers of Attachments on User Dashboard
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> c91285d3e10beced0bc4f53193cdf2f4f500bcd7
async def get_documents_analyzed_by_user_id(user_id: int, from_date: str, to_date: str, request: Request):
    try:
        return await UserRepo.fetch_documents_analyzed_by_user_id(user_id, from_date, to_date, request)
    except Exception as e:
        return None
    
    
 #Fetching Total Numbers of Meeting on User Dashboard   
async def get_meetings_processed_by_user_id(user_id: int, from_date: str, to_date: str, request: Request):
    try:
        return await UserRepo.fetch_meetings_processed_by_user_id(user_id, from_date, to_date, request)
    except Exception as e:
        return None
<<<<<<< HEAD
=======
=======
async def get_documents_analyzed_by_user_id(user_id: int, request: Request):
    try:
        return await UserRepo.fetch_documents_analyzed_by_user_id(user_id,  request)
    except Exception as e:
        return None


#Download Missing Report and Mismatch Report
async def download_missing_po_report(
    format: str,
    request: Request
):
    data = await UserRepo.fetch_po_missing_report(request)

    if not data:
        raise HTTPException(status_code=404, detail="No missing PO data available")

    df = pd.DataFrame(data)
    filename_prefix = "po_missing_report"

    if format == "excel":
        output = io.BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)

        return (
            output,
            f"{filename_prefix}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    elif format == "pdf":
        return _generate_po_pdf(df, filename_prefix)

    else:
        raise HTTPException(status_code=400, detail="Invalid file format")




async def download_mismatch_po_report(
    format: str,
    request: Request
):
    data = await UserRepo.fetch_po_mismatch_report(request)

    if not data:
        raise HTTPException(status_code=404, detail="No mismatch PO data available")

    df = pd.DataFrame(data)
    filename_prefix = "po_mismatch_report"

    if format == "excel":
        output = io.BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)

        return (
            output,
            f"{filename_prefix}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    elif format == "pdf":
        return _generate_po_pdf(df, filename_prefix)

    else:
        raise HTTPException(status_code=400, detail="Invalid file format")


# ===============================
# PDF GENERATION (HELPER)
def _generate_po_pdf(df, filename_prefix):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    output = io.BytesIO()
    pdf = canvas.Canvas(output, pagesize=A4)

    width, height = A4
    x_start = 30
    y = height - 40

    # Header
    for col in df.columns:
        pdf.drawString(x_start, y, str(col))
        x_start += 100

    y -= 20
    x_start = 30

    # Rows
    for _, row in df.iterrows():
        for val in row:
            pdf.drawString(x_start, y, str(val))
            x_start += 100

        y -= 20
        x_start = 30

        if y < 40:
            pdf.showPage()
            y = height - 40

    pdf.save()
    output.seek(0)

    return (
        output,
        f"{filename_prefix}.pdf",
        "application/pdf"
    )
    
    
    
#Update the PO Comment On UI 
async def update_po_comment(
    report_type: str,
    record_id: int,
    comment: str,
    request: Request
):
    if report_type == "missing":
        return await UserRepo.update_po_missing_comment(
            record_id, comment, request
        )

    elif report_type == "mismatch":
        return await UserRepo.update_po_mismatch_comment(
            record_id, comment, request
        )

    else:
        raise ValueError("Invalid report type")
    
 #Fetching Total Numbers of Meeting on User Dashboard   
# async def get_meetings_processed_by_user_id(user_id: int, from_date: str, to_date: str, request: Request):
#     try:
#         return await UserRepo.fetch_meetings_processed_by_user_id(user_id, from_date, to_date, request)
#     except Exception as e:
#         return None
>>>>>>> 90466875ac1d9c50955449637aa13f6f4f1da8c7
>>>>>>> c91285d3e10beced0bc4f53193cdf2f4f500bcd7



### This code is used to fetch calculateing one month to current date data week wise
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> c91285d3e10beced0bc4f53193cdf2f4f500bcd7
async def get_weekly_hours_previous_month(

    request,from_date:str,to_date:str,org_id: int, user_id: int
) -> List[Dict[str, Any]]:
    try:
        return await UserRepo.get_weekly_hours_previous_month(request, from_date,to_date,org_id, user_id,)
    except Exception as e:
        return None



#Fetching Top Keywords On User Dashboard 
async def get_top_keywords(request, org_id: int, user_id: int,from_date:str,to_date:str, limit: int = 5):
    try:
        rows = await UserRepo.fetch_keywords_by_userId(request, org_id, user_id,from_date,to_date)

        # Flatten keywords (split by comma, strip spaces)
        all_keywords = []
        for (kw,) in rows:
            if kw:
                parts = [k.strip().lower() for k in kw.split(",")]
                all_keywords.extend(parts)

        # Count top N
        counter = Counter(all_keywords)
        return counter.most_common(limit)
    except Exception as e:
        return []
    

#Last Sync On User Dashboard
async def get_last_sync_by_user_id(user_id: int,request: Request):
    try:
        last_sync_data = await UserRepo.get_last_sync_by_user_id(user_id,request)
        return last_sync_data
    except Exception as e:
        raise Exception(f"Error fetching last sync data: {str(e)}")
    
    
#Update Term Condition Fleg When User login once
async def update_term_condition_flag(user_id: int, role_id: int, org_id: int, request: Request):
    try:
        return await UserRepo.update_term_condition_flag(user_id, role_id, org_id, request)
    except Exception as e:
<<<<<<< HEAD
        raise Exception(f"Error updating terms flag: {str(e)}")
=======
        raise Exception(f"Error updating terms flag: {str(e)}")
=======
# async def get_weekly_hours_previous_month(

#     request,from_date:str,to_date:str,org_id: int, user_id: int
# ) -> List[Dict[str, Any]]:
#     try:
#         return await UserRepo.get_weekly_hours_previous_month(request, from_date,to_date,org_id, user_id,)
#     except Exception as e:
#         return None



# #Fetching Top Keywords On User Dashboard 
# async def get_top_keywords(request, org_id: int, user_id: int,from_date:str,to_date:str, limit: int = 5):
#     try:
#         rows = await UserRepo.fetch_keywords_by_userId(request, org_id, user_id,from_date,to_date)

#         # Flatten keywords (split by comma, strip spaces)
#         all_keywords = []
#         for (kw,) in rows:
#             if kw:
#                 parts = [k.strip().lower() for k in kw.split(",")]
#                 all_keywords.extend(parts)

#         # Count top N
#         counter = Counter(all_keywords)
#         return counter.most_common(limit)
#     except Exception as e:
#         return []
    

# #Last Sync On User Dashboard
# async def get_last_sync_by_user_id(user_id: int,request: Request):
#     try:
#         last_sync_data = await UserRepo.get_last_sync_by_user_id(user_id,request)
#         return last_sync_data
#     except Exception as e:
#         raise Exception(f"Error fetching last sync data: {str(e)}")
    
    
# #Update Term Condition Fleg When User login once
# async def update_term_condition_flag(user_id: int, role_id: int, org_id: int, request: Request):
#     try:
#         return await UserRepo.update_term_condition_flag(user_id, role_id, org_id, request)
#     except Exception as e:
#         raise Exception(f"Error updating terms flag: {str(e)}")
>>>>>>> 90466875ac1d9c50955449637aa13f6f4f1da8c7
>>>>>>> c91285d3e10beced0bc4f53193cdf2f4f500bcd7
