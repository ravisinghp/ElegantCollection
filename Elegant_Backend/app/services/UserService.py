
from starlette.requests import Request
from fastapi import HTTPException
from app.db.repositories import UserRepo
from typing import List, Dict, Any, Optional
from collections import Counter
import io
import pandas as pd
from app.models.schemas.users import BusinessAdminSearchRequest
from loguru import logger
from fastapi.responses import StreamingResponse

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
    except Exception as e:
        return None


#Fetching Total Numbers of Attachments on User Dashboard
async def get_documents_analyzed_by_user_id(user_id: int, request: Request):
    try:
        return await UserRepo.fetch_documents_analyzed_by_user_id(user_id,  request)
    except Exception as e:
        return None


#Download Missing Report and Mismatch Report
async def download_missing_po_report(
    request: Request,
    user_id: int,
    role_id: int,
    format: str,
    #selected_ids: Optional[List[int]] = None
):
    #selected_ids = selected_ids or []
    data = await UserRepo.download_missing_po_report(request, user_id, role_id)

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
    request: Request,
    user_id: int,
    role_id: int,
    format: str,
    #selected_ids: Optional[List[int]] = None
):
    #selected_ids = selected_ids or []
    data = await UserRepo.download_mismatch_po_report(request, user_id, role_id)

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
    
  
 #For Business admin Dashboard download all missing pos    
async def download_all_missing_po_report(
        request: Request,
        format: str
    ):
        try:
            data = await UserRepo.download_all_missing_po_report(request)

            if not data:
                raise HTTPException(status_code=404, detail="No missing PO data available")

            df = pd.DataFrame(data)
            filename = "all_missing_po_report"

            if format == "excel":
                output = io.BytesIO()
                df.to_excel(output, index=False)
                output.seek(0)
                return (
                    output,
                    f"{filename}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            elif format == "pdf":
                return _generate_po_pdf(df, filename)

            else:
                raise HTTPException(status_code=400, detail="Invalid format")

        except Exception as e:
            raise e
        
  #For Business admin Dashboard download all mismatch pos       
async def download_all_mismatch_po_report(
        request: Request,
        format: str
    ):
        try:
            data = await UserRepo.download_all_mismatch_po_report(request)

            if not data:
                raise HTTPException(status_code=404, detail="No mismatch PO data available")

            df = pd.DataFrame(data)
            filename = "all_mismatch_po_report"

            if format == "excel":
                output = io.BytesIO()
                df.to_excel(output, index=False)
                output.seek(0)
                return (
                    output,
                    f"{filename}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            elif format == "pdf":
                return _generate_po_pdf(df, filename)

            else:
                raise HTTPException(status_code=400, detail="Invalid format")

        except Exception as e:
            raise e
        
async def download_all_selected_po_report(
        request,
        payload: dict,
        format: str
    ):
        try:
            user_id = payload.get("user_id")
            role_id = payload.get("role_id")
            missing_ids = payload.get("missing_po_ids", [])
            mismatch_ids = payload.get("mismatch_po_ids", [])
            matched_ids = payload.get("matched_po_ids", [])
            data = await UserRepo.download_all_selected_po_report(
                request=request,
                user_id=user_id,
                role_id=role_id,
                missing_po_ids=missing_ids,
                mismatch_po_ids=mismatch_ids,
                matched_po_ids=matched_ids
            )

            if not data:
                raise HTTPException(status_code=404, detail="No PO data found")

            df = pd.DataFrame(data)
            filename = "all_selected_email_pos"

            # ---------- EXCEL ----------
            if format == "excel":
                output = io.BytesIO()
                df.to_excel(output, index=False)
                output.seek(0)

                return StreamingResponse(
                    output,
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={
                        "Content-Disposition": f"attachment; filename={filename}.xlsx"
                    }
                )

            # ---------- PDF ----------
            if format == "pdf":
                pdf_stream, pdf_name, media_type = _generate_po_pdf(df, filename)
                return StreamingResponse(
                    pdf_stream,
                    media_type=media_type,
                    headers={
                        "Content-Disposition": f"attachment; filename={pdf_name}"
                    }
                )

            raise HTTPException(status_code=400, detail="Invalid format")

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))      

        
    #On Business admin dashboard    
async def download_combined_all_po_report(
        request: Request,
        user_id: int,
        role_id: int,
        email_missing_ids: list[int],
        email_mismatch_ids: list[int],
        sharepoint_missing_ids: list[int],
        sharepoint_mismatch_ids: list[int],
        format: str
    ):
        try:
            data = await UserRepo.download_combined_all_po_report(
                request=request,
                user_id=user_id,
                role_id=role_id,
                email_missing_ids=email_missing_ids,
                email_mismatch_ids=email_mismatch_ids,
                sharepoint_missing_ids=sharepoint_missing_ids,
                sharepoint_mismatch_ids=sharepoint_mismatch_ids
            )

            if not data:
                raise HTTPException(status_code=404, detail="No PO data found")

            df = pd.DataFrame(data)
            filename_prefix = "all_selected_purchase_orders"

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
                raise HTTPException(status_code=400, detail="Invalid format")

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


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
    
    #Adding and Update comment for po missing and po mismatch from UI
async def save_po_comment(
    report_type: str,
    record_id: int,
    comment: str,
    request: Request
):
    if report_type == "missing":
        return await UserRepo.save_po_missing_comment(
            record_id, comment, request
        )

    elif report_type == "mismatch":
        return await UserRepo.save_po_mismatch_comment(
            record_id, comment, request
        )


#For Fetching the PO comment ON UI 
async def fetch_po_comment(
        report_type: str,
        record_id: int,
        request: Request
    ) -> str | None:

        if report_type == "missing":
            return await UserRepo.fetch_missing_po_comment(
                record_id, request
            )

        elif report_type == "mismatch":
            return await UserRepo.fetch_mismatch_po_comment(
                record_id, request
            )

        else:
            raise ValueError("Invalid report type")


#For Ignoring the PO in Next Sync On UI
async def ignore_po(
        report_type: str,
        record_id: int,
        request: Request
    ) -> bool:

        if report_type == "missing":
            return await UserRepo.ignore_missing_po(
                record_id, request
            )

        elif report_type == "mismatch":
            return await UserRepo.ignore_mismatch_po(
                record_id, request
            )

        else:
            raise ValueError("Invalid report type")

# async def create_po_comment(
#     report_type: str,
#     record_id: int,
#     comment: str,
#     request: Request
# ):
#     if report_type == "missing":
#         return await UserRepo.create_po_missing_comment(
#             record_id, comment, request
#         )

#     elif report_type == "mismatch":
#         return await UserRepo.create_po_mismatch_comment(
#             record_id, comment, request
#         )
    
# #Update the PO Comment On UI 
# async def update_po_comment(
#     report_type: str,
#     record_id: int,
#     comment: str,
#     request: Request
# ):
#     if report_type == "missing":
#         return await UserRepo.update_po_missing_comment(
#             record_id, comment, request
#         )

#     elif report_type == "mismatch":
#         return await UserRepo.update_po_mismatch_comment(
#             record_id, comment, request
#         )

#     else:
#         raise ValueError("Invalid report type")
    

# async def missing_po_data_fetch(request: Request):
#         data = await UserRepo.fetch_missing_po_data(request)
#         return {
#             "status": "success",
#             "count": len(data),
#             "data": data
#         }
        
# async def mismatch_po_data_fetch(request: Request):
#         data = await UserRepo.fetch_mismatch_po_data(request)
#         return {
#             "status": "success",
#             "count": len(data),
#             "data": data
#         }
        
# async def matched_po_data_fetch(request: Request):
#         data = await UserRepo.fetch_matched_po_data(request)
#         return {
#             "status": "success",
#             "count": len(data),
#             "data": data
#         }

async def missing_po_data_fetch(request: Request, frontendRequest):
    data = await UserRepo.fetch_missing_po_data(request, frontendRequest)
    # FIX: Return empty list if None, and return the LIST directly (no wrapper object)
    return data if data else []
        
async def mismatch_po_data_fetch(request: Request, frontendRequest):
    data = await UserRepo.fetch_mismatch_po_data(request, frontendRequest)
    return data if data else []
        
async def matched_po_data_fetch(request: Request, frontendRequest):
    data = await UserRepo.fetch_matched_po_data(request, frontendRequest)
    return data if data else []
        

#Business admin fetching users list and vendor number list on dashboard
async def get_all_users_by_role_id_business_admin(request):
        try:
            users = await UserRepo.get_all_users_by_role_id_business_admin(request)

            if not users:
                return {
                    "success": False,
                    "message": "No active users found"
                }

            return {
                "success": True,
                "data": users
            }

        except Exception as e:
            raise Exception(f"Service error while fetching users: {str(e)}")

async def get_vendors_business_admin(request):
        try:
            vendors = await UserRepo.get_vendors_business_admin(request)

            if not vendors:
                return {
                    "success": False,
                    "message": "No active vendors found"
                }

            return {
                "success": True,
                "data": vendors
            }

        except Exception as e:
            raise Exception(f"Service error while fetching vendors: {str(e)}")  
        
#----------------Search PO for Business Admin Dashboard-----------------#
async def search_pos_business_admin(request: Request, filters: BusinessAdminSearchRequest):
        
        # Validation: fromDate requires toDate
        if filters.fromDate and not filters.toDate:
            return "toDate is required when fromDate is provided"

        result = await UserRepo.search_pos_business_admin(request, filters)
        return result

 #Fetching Total Numbers of Meeting on User Dashboard   
# async def get_meetings_processed_by_user_id(user_id: int, from_date: str, to_date: str, request: Request):
#     try:
#         return await UserRepo.fetch_meetings_processed_by_user_id(user_id, from_date, to_date, request)
#     except Exception as e:
#         return None



### This code is used to fetch calculateing one month to current date data week wise
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
async def get_last_sync_by_user_id(user_id: int,role_id: int,request: Request):
    try:
        last_sync_data = await UserRepo.get_last_sync_by_user_id(user_id,role_id,request)
        return last_sync_data
    except Exception as e:
        raise Exception(f"Error fetching last sync data: {str(e)}")


#Last sync On business and system admin
async def get_last_sync(request: Request):
    try:
        last_sync_data = await UserRepo.get_last_sync(request)
        return last_sync_data
    except Exception as e:
        raise Exception(f"Error fetching last sync data: {str(e)}")
    

#save the folders in folder mapping table for scheduler 
async def save_folder_mapping_service(
    request: Request,
    user_id: int,
    folder_name: str
) -> dict:
    try:
        folder_name = folder_name.strip()

        if not folder_name:
            return {
                "success": False,
                "message": "Folder name cannot be empty"
            }

        # 🔍 Check duplicate
        exists = await UserRepo.check_folder_mapping_exists_repo(
            request=request,
            user_id=user_id,
            folder_name=folder_name
        )

        if exists:
            return {
                "success": False,
                "message": "Folder already exists for this user"
            }

        #Insert
        inserted = await UserRepo.insert_folder_mapping_repo(
            request=request,
            user_id=user_id,
            folder_name=folder_name
        )

        return {
            "success": inserted,
            "message": "Folder mapping saved successfully"
        }

    except Exception as e:
        raise Exception(f"Service error while saving folder mapping: {str(e)}")
    
# #Update Term Condition Fleg When User login once
# async def update_term_condition_flag(user_id: int, role_id: int, org_id: int, request: Request):
#     try:
#         return await UserRepo.update_term_condition_flag(user_id, role_id, org_id, request)
#     except Exception as e:
#         raise Exception(f"Error updating terms flag: {str(e)}")



#---------------Soft Delete and Hard Delete User and all related tables-----------------#
async def deactivate_or_delete_user(request_obj, user_id: int, action: str):
    """
    Delete or inactivate user based on action
    action: 'inactive' or 'delete'
    """
    if action == "inactive":
        success = await UserRepo.soft_delete_user(request_obj, user_id)
        msg = "User inactivated successfully" if success else "Failed to inactivate user"
    elif action == "delete":
        success = await UserRepo.hard_delete_user(request_obj, user_id)
        msg = "User deleted successfully" if success else "Failed to delete user"
    else:
        raise ValueError("Invalid action. Must be 'inactive' or 'delete'.")

    logger.info(f"Action '{action}' on user {user_id}: {msg}")
    return {"user_id": user_id, "action": action, "success": success, "message": msg}



#---------------Soft Delete and Hard Delete PO By Business Admin-----------------#
async def delete_or_deactivate_po_by_business_admin(request_obj, record_id: int, action: str, source: str, record_type: str):
    """
    Delete or inactivate user based on action
    action: 'inactive' or 'delete'
    """
    if action == "inactive":
        success = await UserRepo.soft_delete_po_by_business_admin(request_obj, record_id, source, record_type)
        msg = "PO inactivated successfully" if success else "Failed to inactivate PO"
    elif action == "delete":
        success = await UserRepo.hard_delete_po_by_business_admin(request_obj, record_id, source, record_type)
        msg = "PO deleted successfully" if success else "Failed to delete PO"
    else:
        raise ValueError("Invalid action. Must be 'inactive' or 'delete'.")

    logger.info(f"Action '{action}' on user {record_id}: {msg}")
    return {"user_id": record_id, "action": action, "success": success, "message": msg}