from starlette.requests import Request
from typing import List, Tuple
from typing import Any,Dict
from datetime import datetime, timedelta
IST_OFFSET = timedelta(hours=5, minutes=30)


#Total R&D Effort On User Dashboard
<<<<<<< HEAD
async def fetch_total_user_effort_by_id(user_id: int, from_date: str, to_date: str, request: Request) -> float:
    query = """
        SELECT ROUND(COALESCE(SUM(rd.planned_effort_time), 0) / 60.0, 2) AS total_hours
        FROM report_data rd, mail_details md
        WHERE md.mail_dtl_id=rd.mail_dtl_id and rd.user_id = %s
          AND DATE(md.date_time) BETWEEN %s AND %s
    """
    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, (user_id, from_date, to_date))
            row = await cursor.fetchone()
            return float(row[0]) if row and row[0] is not None else 0.0
=======
# async def fetch_total_user_effort_by_id(user_id: int, from_date: str, to_date: str, request: Request) -> float:
#     query = """
#         SELECT ROUND(COALESCE(SUM(rd.planned_effort_time), 0) / 60.0, 2) AS total_hours
#         FROM report_data rd, mail_details md
#         WHERE md.mail_dtl_id=rd.mail_dtl_id and rd.user_id = %s
#           AND DATE(md.date_time) BETWEEN %s AND %s
#     """
#     async with request.app.state.pool.acquire() as conn:
#         async with conn.cursor() as cursor:
#             await cursor.execute(query, (user_id, from_date, to_date))
#             row = await cursor.fetchone()
#             return float(row[0]) if row and row[0] is not None else 0.0
>>>>>>> 90466875ac1d9c50955449637aa13f6f4f1da8c7
        
        

#Fetching Total Numbers of Emails on User Dashboard
<<<<<<< HEAD
async def fetch_emails_processed_by_user_id(user_id: int, from_date: str, to_date: str, request: Request) -> int:
    query = """
        SELECT COUNT(*) 
        FROM report_data rd,mail_details md
        WHERE md.mail_dtl_id=rd.mail_dtl_id and rd.user_id = %s 
          AND rd.isActive = TRUE
          AND DATE(md.date_time) BETWEEN %s AND %s
    """
    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, (user_id, from_date, to_date))
=======
async def fetch_emails_processed_by_user_id(user_id: int,  request: Request) -> int:
    query = """
       SELECT COUNT(*)
        FROM mail_details m
        WHERE m.is_active = 1
        AND m.user_id = %s;
    """
    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, (user_id,))
>>>>>>> 90466875ac1d9c50955449637aa13f6f4f1da8c7
            row = await cursor.fetchone()
            return int(row[0]) if row else 0


#Fetching Total Numbers of Attachments on User Dashboard
<<<<<<< HEAD
async def fetch_documents_analyzed_by_user_id(user_id: int, from_date: str, to_date: str, request: Request) -> int:
    query = """
        SELECT COUNT(md.mail_dtl_id) 
        FROM attach_master am,mail_details md
        WHERE am.mail_dtl_id=md.mail_dtl_id and am.user_id = %s 
          AND am.is_active = TRUE
          AND DATE(md.date_time) BETWEEN %s AND %s
    """
    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, (user_id, from_date, to_date))
=======
async def fetch_documents_analyzed_by_user_id(user_id: int, request: Request) -> int:
    query = """
       SELECT COUNT(m.mail_dtl_id) 
        FROM email_attachments em,POlyticsAI.mail_details m
        WHERE em.mail_dtl_id=m.mail_dtl_id and m.user_id = %s 
          AND m.is_active = TRUE
    """
    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, (user_id, ))
>>>>>>> 90466875ac1d9c50955449637aa13f6f4f1da8c7
            row = await cursor.fetchone()
            return int(row[0]) if row else 0
        
        
<<<<<<< HEAD
#Fetching Total Numbers of Meeting on User Dashboard
async def fetch_meetings_processed_by_user_id(user_id: int, from_date: str, to_date: str, request: Request) -> int:
    query = """
        SELECT COUNT(*) 
        FROM meeting_report_data mrd,cal_master cm
        WHERE mrd.cal_id=cm.cal_id and mrd.user_id = %s 
          AND mrd.is_active = TRUE
          AND DATE(cm.event_start_datetime) BETWEEN %s AND %s
    """
    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, (user_id, from_date, to_date))
            row = await cursor.fetchone()
            return int(row[0]) if row else 0
=======
   #For Doanloading the PO Missing Report     
async def fetch_po_missing_report(request: Request):
    query = """
        SELECT
            pd.po_number,
            pd.po_date,
            pd.vendor_number AS vendor_code,
            pd.customer_name,
            pm.comment
        FROM po_missing_report pm
        JOIN po_details pd ON pd.po_det_id = pm.po_det_id
        WHERE pm.active = 1
        ORDER BY pm.created_on DESC
    """

    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query)

            columns = [col[0] for col in cursor.description]
            rows = await cursor.fetchall()

            return [dict(zip(columns, row)) for row in rows]


   #For Doanloading the PO Mismatch Report   
async def fetch_po_mismatch_report(request: Request):
    query = """
        SELECT
            pd.po_number,
            pd.po_date,
            pd.vendor_number AS vendor_code,
            pd.customer_name,
            pd.delivery_date,
            pd.cancel_date,
            pd.gold_karat,
            pd.ec_style_number,
            pd.customer_style_number,
            pd.color,
            pd.quantity,
            pd.description,
            mm.mismatch_attribute,
            mm.scanned_value,
            mm.system_value,
            mm.comment
        FROM po_mismatch_report mm
        JOIN po_details pd ON pd.po_det_id = mm.po_det_id
        WHERE mm.active = 1
        ORDER BY mm.created_on DESC
    """

    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query)

            columns = [col[0] for col in cursor.description]
            rows = await cursor.fetchall()

            return [dict(zip(columns, row)) for row in rows]
        
        
        
    #Update the Comment For PO Missing 
async def update_po_missing_comment(
    po_missing_id: int,
    comment: str,
    request: Request
) -> bool:

    query = """
        UPDATE po_missing_report
        SET comment = %s
        WHERE po_missing_id = %s
          AND active = 1
    """

    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, (comment, po_missing_id))
            await conn.commit()
            return cursor.rowcount > 0 
        


#Update the Comment For PO Mismatch
async def update_po_mismatch_comment(
    po_mismatch_id: int,
    comment: str,
    request: Request
) -> bool:

    query = """
        UPDATE po_mismatch_report
        SET comment = %s
        WHERE po_mismatch_id = %s
          AND active = 1
    """

    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, (comment, po_mismatch_id))
            await conn.commit()
            return cursor.rowcount > 0      
#Fetching Total Numbers of Meeting on User Dashboard
# async def fetch_meetings_processed_by_user_id(user_id: int, from_date: str, to_date: str, request: Request) -> int:
#     query = """
#         SELECT COUNT(*) 
#         FROM meeting_report_data mrd,cal_master cm
#         WHERE mrd.cal_id=cm.cal_id and mrd.user_id = %s 
#           AND mrd.is_active = TRUE
#           AND DATE(cm.event_start_datetime) BETWEEN %s AND %s
#     """
#     async with request.app.state.pool.acquire() as conn:
#         async with conn.cursor() as cursor:
#             await cursor.execute(query, (user_id, from_date, to_date))
#             row = await cursor.fetchone()
#             return int(row[0]) if row else 0
>>>>>>> 90466875ac1d9c50955449637aa13f6f4f1da8c7




<<<<<<< HEAD
### This code is used to fetch calculateing one month to current date data week wise
async def get_weekly_hours_previous_month(request, from_date:str,to_date:str,org_id: int, user_id: int,) -> List[Dict[str, Any]]:
    try:
        query = """
        WITH date_range AS (
            SELECT
                CAST(%s AS DATE) AS start_date,
                CAST(DATE_ADD(%s, INTERVAL 1 DAY) AS DATE) AS end_date
                                        )
                                        SELECT
                DATE_FORMAT(MIN(md.date_time), '%%b %%Y') AS month_name,
                CONCAT('Week ', FLOOR(DATEDIFF(md.date_time, p.start_date) / 7) + 1) AS week_index,
                ROUND(SUM(r.planned_effort_time) / 60, 2) AS total_hours
            FROM
                report_data r
            LEFT JOIN 
                            mail_details md ON
                md.mail_dtl_id = r.mail_dtl_id
            JOIN 
                date_range p
                                            ON
                md.date_time >= p.start_date
                AND md.date_time < p.end_date
            WHERE
                r.org_id = %s
                AND r.user_id = %s
            GROUP BY
                week_index
            ORDER BY
                MIN(md.date_time);
        """

        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                #pass both org_id and user_id as parameters
                await cursor.execute(query, (from_date,to_date,org_id,user_id,))
                rows = await cursor.fetchall()

                result = [
                    {
                        "month_name": row[0],
                        "week_of_month": row[1],
                        "total_hours": float(row[2]) if row[2] is not None else 0.0,
                    }
                    for row in rows
                ]

                return result
    except Exception as e:
        return []


#Fetching Top Keywords On User Dashboard 
async def fetch_keywords_by_userId(request, org_id: int, user_id: int,from_date:str,to_date:str) -> List[Tuple[str]]:
    try:
        query = """
           SELECT
            rd.keywords_found
        FROM
            report_data rd
        JOIN users_master u ON
            rd.user_id = u.user_id
        Join mail_details m on m.mail_dtl_id =rd.mail_dtl_id
        WHERE
            u.user_id = %s
            AND u.is_active = 1
            AND m.date_time between %s and %s;
        """
        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (user_id,from_date,to_date))
                return await cursor.fetchall()
    except Exception as e:
        return []
    
 #Last Sync On User Dashboard
async def get_last_sync_by_user_id(user_id: int,request:Request) -> List[Dict[str, Any]]:
    try:
        query = """
            SELECT r.user_id, MAX(r.created_date) AS last_sync
            FROM report_data r
            JOIN mail_details m ON r.mail_dtl_id = m.mail_dtl_id
            WHERE r.user_id = %s
            
            ORDER BY last_sync DESC
        """
        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (user_id,))
                result = await cursor.fetchall()
                return [
                    {
                        "user_id": row[0],
                        "last_sync": (row[1] + IST_OFFSET).strftime('%Y-%m-%dT%H:%M:%S+05:30') if row[1] else None
                    }
                    for row in result
                ]
    except Exception as e:
        return []
    

#Update Term Condition Fleg When User login once
async def update_term_condition_flag(user_id: int, role_id: int, org_id: int, request: Request, flag: int = 1):
    query = """
        UPDATE users_master
        SET term_condition_flag = %s
        WHERE user_id = %s
          AND role_id = %s
          AND org_id = %s
    """
    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, (flag, user_id, role_id, org_id))
            await conn.commit() 
            return cursor.rowcount > 0   #  True if row updated
=======
# ### This code is used to fetch calculateing one month to current date data week wise
# async def get_weekly_hours_previous_month(request, from_date:str,to_date:str,org_id: int, user_id: int,) -> List[Dict[str, Any]]:
#     try:
#         query = """
#         WITH date_range AS (
#             SELECT
#                 CAST(%s AS DATE) AS start_date,
#                 CAST(DATE_ADD(%s, INTERVAL 1 DAY) AS DATE) AS end_date
#                                         )
#                                         SELECT
#                 DATE_FORMAT(MIN(md.date_time), '%%b %%Y') AS month_name,
#                 CONCAT('Week ', FLOOR(DATEDIFF(md.date_time, p.start_date) / 7) + 1) AS week_index,
#                 ROUND(SUM(r.planned_effort_time) / 60, 2) AS total_hours
#             FROM
#                 report_data r
#             LEFT JOIN 
#                             mail_details md ON
#                 md.mail_dtl_id = r.mail_dtl_id
#             JOIN 
#                 date_range p
#                                             ON
#                 md.date_time >= p.start_date
#                 AND md.date_time < p.end_date
#             WHERE
#                 r.org_id = %s
#                 AND r.user_id = %s
#             GROUP BY
#                 week_index
#             ORDER BY
#                 MIN(md.date_time);
#         """

#         async with request.app.state.pool.acquire() as conn:
#             async with conn.cursor() as cursor:
#                 #pass both org_id and user_id as parameters
#                 await cursor.execute(query, (from_date,to_date,org_id,user_id,))
#                 rows = await cursor.fetchall()

#                 result = [
#                     {
#                         "month_name": row[0],
#                         "week_of_month": row[1],
#                         "total_hours": float(row[2]) if row[2] is not None else 0.0,
#                     }
#                     for row in rows
#                 ]

#                 return result
#     except Exception as e:
#         return []


# #Fetching Top Keywords On User Dashboard 
# async def fetch_keywords_by_userId(request, org_id: int, user_id: int,from_date:str,to_date:str) -> List[Tuple[str]]:
#     try:
#         query = """
#            SELECT
#             rd.keywords_found
#         FROM
#             report_data rd
#         JOIN users_master u ON
#             rd.user_id = u.user_id
#         Join mail_details m on m.mail_dtl_id =rd.mail_dtl_id
#         WHERE
#             u.user_id = %s
#             AND u.is_active = 1
#             AND m.date_time between %s and %s;
#         """
#         async with request.app.state.pool.acquire() as conn:
#             async with conn.cursor() as cursor:
#                 await cursor.execute(query, (user_id,from_date,to_date))
#                 return await cursor.fetchall()
#     except Exception as e:
#         return []
    
#  #Last Sync On User Dashboard
# async def get_last_sync_by_user_id(user_id: int,request:Request) -> List[Dict[str, Any]]:
#     try:
#         query = """
#             SELECT r.user_id, MAX(r.created_date) AS last_sync
#             FROM report_data r
#             JOIN mail_details m ON r.mail_dtl_id = m.mail_dtl_id
#             WHERE r.user_id = %s
            
#             ORDER BY last_sync DESC
#         """
#         async with request.app.state.pool.acquire() as conn:
#             async with conn.cursor() as cursor:
#                 await cursor.execute(query, (user_id,))
#                 result = await cursor.fetchall()
#                 return [
#                     {
#                         "user_id": row[0],
#                         "last_sync": (row[1] + IST_OFFSET).strftime('%Y-%m-%dT%H:%M:%S+05:30') if row[1] else None
#                     }
#                     for row in result
#                 ]
#     except Exception as e:
#         return []
    

# #Update Term Condition Fleg When User login once
# async def update_term_condition_flag(user_id: int, role_id: int, org_id: int, request: Request, flag: int = 1):
#     query = """
#         UPDATE users_master
#         SET term_condition_flag = %s
#         WHERE user_id = %s
#           AND role_id = %s
#           AND org_id = %s
#     """
#     async with request.app.state.pool.acquire() as conn:
#         async with conn.cursor() as cursor:
#             await cursor.execute(query, (flag, user_id, role_id, org_id))
#             await conn.commit() 
#             return cursor.rowcount > 0   #  True if row updated
>>>>>>> 90466875ac1d9c50955449637aa13f6f4f1da8c7
