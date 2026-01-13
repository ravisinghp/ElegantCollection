from starlette.requests import Request
from typing import List, Tuple
from typing import Any,Dict
from datetime import datetime, timedelta
IST_OFFSET = timedelta(hours=5, minutes=30)


#Total R&D Effort On User Dashboard
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
        
        

#Fetching Total Numbers of Emails on User Dashboard
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
            row = await cursor.fetchone()
            return int(row[0]) if row else 0


#Fetching Total Numbers of Attachments on User Dashboard
async def fetch_documents_analyzed_by_user_id(user_id: int, request: Request) -> int:
    query = """
       SELECT
	COUNT(em.mail_dtl_id)
FROM
	email_attachments em
WHERE
	em.user_id = %s
	AND em.is_active = 1;
    """
    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, (user_id, ))
            row = await cursor.fetchone()
            return int(row[0]) if row else 0
        
        
#For Downloading the PO Missing Report     
async def download_missing_po_report(request: Request, user_id: int, role_id: int):
    base_query  = """
        SELECT
            COALESCE(pd.po_number, s.po_number) AS po_number,
            COALESCE(pd.po_date, s.po_date) AS po_date,
            COALESCE(pd.vendor_number, s.vendor_number) AS vendor_code,
            COALESCE(pd.customer_name, s.customer_name) AS customer_name
        FROM
            po_missing_report pm
        LEFT JOIN po_details pd ON
            pd.po_det_id = pm.po_det_id
        LEFT JOIN system_po_details s ON
            s.system_po_id = pm.system_po_id
        WHERE
            pm.active = 1
    """
    
    params = []
    
    if role_id == 1:
        base_query += " AND pm.user_id = %s"
        params.append(user_id)
        
    base_query += " ORDER BY pm.po_missing_id DESC"

    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(base_query, tuple(params))

            columns = [col[0] for col in cursor.description]
            rows = await cursor.fetchall()

            return [dict(zip(columns, row)) for row in rows]


   #For Doanloading the PO Mismatch Report   
async def download_mismatch_po_report(request: Request, user_id: int, role_id: int):
    base_query  = """
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
    """
    
    params = []
    
    if role_id == 1:
        base_query += " AND mm.user_id = %s"
        params.append(user_id)
        
    base_query += " ORDER BY mm.po_mismatch_id DESC"
    
    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(base_query, tuple(params))

            columns = [col[0] for col in cursor.description]
            rows = await cursor.fetchall()

            return [dict(zip(columns, row)) for row in rows]
        

#Adding and Update comment for po missing  from UI
async def save_po_missing_comment(
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


#Adding and Update comment for po mismatch from UI
async def save_po_mismatch_comment(
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



#For Fetching the missing PO comment ON UI 
async def fetch_missing_po_comment(
        po_missing_id: int,
        request: Request
    ) -> str | None:

        query = """
            SELECT comment
            FROM po_missing_report
            WHERE po_missing_id = %s
              AND active = 1
        """

        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (po_missing_id,))
                row = await cursor.fetchone()
                return row[0] if row else None  
            


#For Fetching the Mismatch PO comment ON UI 
async def fetch_mismatch_po_comment(
        po_mismatch_id: int,
        request: Request
    ) -> str | None:

        query = """
            SELECT comment
            FROM po_mismatch_report
            WHERE po_mismatch_id = %s
              AND active = 1
        """

        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (po_mismatch_id,))
                row = await cursor.fetchone()
                return row[0] if row else None


#For Ignoring the Missing PO in Next Sync On UI
async def ignore_missing_po(
        po_missing_id: int,
        request: Request
    ) -> bool:

        query = """
            UPDATE po_missing_report
            SET active = 0
            WHERE po_missing_id = %s
              AND active = 1
        """

        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (po_missing_id,))
                await conn.commit()
                return cursor.rowcount > 0
            
   
#For Ignoring the Mismatch PO in Next Sync On UI         
async def ignore_mismatch_po(
        po_mismatch_id: int,
        request: Request
    ) -> bool:

        query = """
            UPDATE po_mismatch_report
            SET active = 0
            WHERE po_mismatch_id = %s
              AND active = 1
        """

        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (po_mismatch_id,))
                await conn.commit()
                return cursor.rowcount > 0
     
            
#Business admin fetching users list and vendor number list on dashboard
async def get_all_users_by_role_id_business_admin(
    request
):
    #Business admin can see all users
    query = """
        SELECT user_id, user_name
        FROM users_master
        WHERE is_active = 1
        AND role_id = 1
        ORDER BY user_name ASC
    """

    try:
        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query)
                rows = await cursor.fetchall()

                return [
                    {
                        "user_id": row[0],
                        "user_name": row[1]
                    }
                    for row in rows
                ]
    except Exception as e:
        raise Exception(f"DB error while fetching users: {str(e)}")


async def get_vendors_business_admin(request):
        query = """
            SELECT DISTINCT vendor_number
            FROM (
                SELECT vendor_number FROM po_details WHERE vendor_number IS NOT NULL
                UNION
                SELECT vendor_number FROM system_po_details WHERE vendor_number IS NOT NULL
            ) vendor_list
            ORDER BY vendor_number;
        """

        try:
            async with request.app.state.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query)
                    rows = await cursor.fetchall()

                    return [
                        {
                            "vendor_number": row[0]
                        }
                        for row in rows
                    ]

        except Exception as e:
            raise Exception(f"DB error while fetching vendors: {str(e)}")
# async def create_po_missing_comment(
#     po_missing_id: int,
#     comment: str,
#     request: Request
# ) -> bool:

#     query = """
#         UPDATE po_missing_report
#         SET comment = %s
#         WHERE po_missing_id = %s
#           AND active = 1
#           AND (comment IS NULL OR comment = '')
#     """

#     async with request.app.state.pool.acquire() as conn:
#         async with conn.cursor() as cursor:
#             await cursor.execute(query, (comment, po_missing_id))
#             await conn.commit()
#             return cursor.rowcount > 0
        
        
# async def create_po_mismatch_comment(
#     po_mismatch_id: int,
#     comment: str,
#     request: Request
# ) -> bool:

#     query = """
#         UPDATE po_mismatch_report
#         SET comment = %s
#         WHERE po_mismatch_id = %s
#           AND active = 1
#           AND (comment IS NULL OR comment = '')
#     """

#     async with request.app.state.pool.acquire() as conn:
#         async with conn.cursor() as cursor:
#             await cursor.execute(query, (comment, po_mismatch_id))
#             await conn.commit()
#             return cursor.rowcount > 0

        
   
#     #Update the Comment For PO Missing 
# async def update_po_missing_comment(
#     po_missing_id: int,
#     comment: str,
#     request: Request
# ) -> bool:

#     query = """
#         UPDATE po_missing_report
#         SET comment = %s
#         WHERE po_missing_id = %s
#           AND active = 1
#     """

#     async with request.app.state.pool.acquire() as conn:
#         async with conn.cursor() as cursor:
#             await cursor.execute(query, (comment, po_missing_id))
#             await conn.commit()
#             return cursor.rowcount > 0 
        


# #Update the Comment For PO Mismatch
# async def update_po_mismatch_comment(
#     po_mismatch_id: int,
#     comment: str,
#     request: Request
# ) -> bool:

#     query = """
#         UPDATE po_mismatch_report
#         SET comment = %s
#         WHERE po_mismatch_id = %s
#           AND active = 1
#     """

#     async with request.app.state.pool.acquire() as conn:
#         async with conn.cursor() as cursor:
#             await cursor.execute(query, (comment, po_mismatch_id))
#             await conn.commit()
#             return cursor.rowcount > 0    

        
async def fetch_missing_po_data(request: Request, frontendRequest):

    base_query = """
        SELECT
            pm.po_missing_id,
            pm.po_det_id,
            pm.system_po_id,

            COALESCE(pd.po_number, sp.po_number) AS po_number,
            COALESCE(pd.po_date, sp.po_date) AS po_date,
            COALESCE(pd.vendor_number, sp.vendor_number) AS vendor_code,
            COALESCE(pd.customer_name, sp.customer_name) AS customer_name,
            um.user_name AS username,

            pm.comment,
            'MISSING' AS po_status,

            CASE
                WHEN pm.po_det_id IS NOT NULL THEN 'SCANNED'
                ELSE 'SYSTEM'
            END AS source
        FROM po_missing_report pm
        LEFT JOIN po_details pd ON pm.po_det_id = pd.po_det_id
        LEFT JOIN system_po_details sp ON pm.system_po_id = sp.system_po_id
        LEFT JOIN users_master um ON pm.user_id = um.user_id
        WHERE pm.active = 1
    """

    params = []

    # Apply condition only when user_id == 1
    if frontendRequest.role_id == 1:
        base_query += " AND pm.user_id = %s"
        params.append(frontendRequest.user_id)

    base_query += " ORDER BY pm.po_missing_id DESC"

    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(base_query, tuple(params))
            cols = [c[0] for c in cursor.description]
            rows = await cursor.fetchall()

    return [dict(zip(cols, r)) for r in rows]
        
        
async def fetch_mismatch_po_data(request: Request, frontendRequest):

    base_query = """
        SELECT
            mm.po_mismatch_id,
            mm.po_det_id,
            mm.system_po_id,

            pd.po_number,
            pd.po_date,
            pd.vendor_number AS vendor_code,
            pd.customer_name,
            um.user_name AS username,

            mm.mismatch_attribute,
            mm.scanned_value,
            mm.system_value,
           

            'MISMATCH' AS po_status
        FROM po_mismatch_report mm
        LEFT JOIN po_details pd 
            ON mm.po_det_id = pd.po_det_id
        LEFT JOIN system_po_details sp
            ON mm.system_po_id = sp.system_po_id
        LEFT JOIN users_master um ON mm.user_id = um.user_id
        WHERE mm.active = 1
    """

    params = []

    if frontendRequest.role_id == 1:
        base_query += " AND mm.user_id = %s"
        params.append(frontendRequest.user_id)

    base_query += " ORDER BY mm.po_mismatch_id DESC"

    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(base_query, tuple(params))
            cols = [c[0] for c in cursor.description]
            rows = await cursor.fetchall()

    return [dict(zip(cols, r)) for r in rows]
        

async def fetch_matched_po_data(request: Request, frontendRequest):

    base_query = """
       SELECT
            pd.*,
            pd.vendor_number AS vendor_code,
            u.user_name AS username
        FROM po_details pd
        LEFT JOIN po_missing_report pm
            ON pm.po_det_id = pd.po_det_id
        AND pm.active = 1
        LEFT JOIN po_mismatch_report mm
            ON mm.po_det_id = pd.po_det_id
        AND mm.active = 1
        LEFT JOIN mail_details md
            ON md.mail_dtl_id = pd.mail_dtl_id
        LEFT JOIN users_master u
            ON u.user_id = md.user_id
        WHERE pm.po_det_id IS NULL
        AND mm.po_det_id IS NULL
    """

    params = []

    # Apply user filter only when user_id == 1
    if frontendRequest.role_id == 1:
        base_query += " AND pd.user_id = %s"
        params.append(frontendRequest.user_id)

    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(base_query, tuple(params))
            cols = [c[0] for c in cursor.description]
            rows = await cursor.fetchall()

    return [dict(zip(cols, r)) for r in rows]
        
        #for schedular we are getting all users 
async def get_active_users(request: Request):
    query = """
        SELECT user_id
        FROM user_master
        WHERE role_id = 1
          AND is_active = 1
    """

    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query)
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
        
#----------------Search PO for Business Admin Dashboard-----------------#
async def search_pos_business_admin(request: Request, filters):
    base_query = """
        SELECT * FROM (

            -- ================= MISSING =================
            SELECT
                pm.po_missing_id AS record_id,
                COALESCE(pd.po_number, sp.po_number) AS po_number,
                COALESCE(pd.po_date, sp.po_date) AS po_date,
                COALESCE(pd.vendor_number, sp.vendor_number) AS vendor_code,
                COALESCE(pd.customer_name, sp.customer_name) AS customer_name,
                um.user_id,
                um.user_name AS username,
                'missing' AS record_type
            FROM po_missing_report pm
            LEFT JOIN po_details pd ON pm.po_det_id = pd.po_det_id
            LEFT JOIN system_po_details sp ON pm.system_po_id = sp.system_po_id
            LEFT JOIN users_master um ON pm.user_id = um.user_id
            WHERE pm.active = 1

            UNION ALL

            -- ================= MISMATCH =================
            SELECT
                mm.po_mismatch_id AS record_id,
                pd.po_number,
                pd.po_date,
                pd.vendor_number AS vendor_code,
                pd.customer_name,
                um.user_id,
                um.user_name AS username,
                'mismatch' AS record_type
            FROM po_mismatch_report mm
            JOIN po_details pd ON mm.po_det_id = pd.po_det_id
            LEFT JOIN users_master um ON mm.user_id = um.user_id
            WHERE mm.active = 1

            UNION ALL

            -- ================= NORMAL =================
            SELECT
                pd.po_det_id AS record_id,
                pd.po_number,
                pd.po_date,
                pd.vendor_number AS vendor_code,
                pd.customer_name,
                um.user_id,
                um.user_name AS username,
                'normal' AS record_type
            FROM po_details pd
            LEFT JOIN po_missing_report pm
                ON pm.po_det_id = pd.po_det_id AND pm.active = 1
            LEFT JOIN po_mismatch_report mm
                ON mm.po_det_id = pd.po_det_id AND mm.active = 1
            LEFT JOIN users_master um ON um.user_id = pd.user_id
            WHERE pm.po_det_id IS NULL
              AND mm.po_det_id IS NULL

        ) t
        WHERE 1=1
    """

    params = []

    # ---------- Filters ----------
    if filters.fromDate:
        base_query += " AND t.po_date >= %s"
        params.append(filters.fromDate)

    if filters.toDate:
        base_query += " AND t.po_date <= %s"
        params.append(filters.toDate)

    if filters.userId:
        base_query += " AND t.user_id = %s"
        params.append(int(filters.userId))

    if filters.vendorNumber:
        base_query += " AND t.vendor_code = %s"
        params.append(filters.vendorNumber)

    base_query += " ORDER BY t.po_date DESC"

    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(base_query, tuple(params))
            cols = [c[0] for c in cursor.description]
            rows = await cursor.fetchall()

    return [dict(zip(cols, row)) for row in rows]


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
async def get_last_sync_by_user_id(
    user_id: int,
    role_id: int,
    request: Request
) -> List[Dict[str, Any]]:
    try:
        # 🔹 Role-based query selection
        if role_id in (2, 3):
            query = """
                SELECT m.user_id, m.created_on AS last_sync
                FROM mail_details m
                ORDER BY m.created_on DESC
                LIMIT 1
            """
            params = ()
        else:
            query = """
                SELECT m.user_id, MAX(m.created_on) AS last_sync
                FROM mail_details m
                WHERE m.user_id = %s
            """
            params = (user_id,)

        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, params)
                row = await cursor.fetchone()

                if not row or not row[1]:
                    return []

                return [{
                    "user_id": row[0],
                    "last_sync": row[1].strftime('%Y-%m-%d %H:%M:%S')
                }]

    except Exception as e:
        return []

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