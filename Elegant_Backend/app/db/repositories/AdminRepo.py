from starlette.requests import Request
from sqlalchemy import text
from typing import Optional, List, Dict, Any, Tuple,List,Dict
from app.models.schemas.AdminSchema import UserCreate, UserUpdate
from app.models.domain.AdminDomain import UserInDB
import bcrypt
from fastapi import Query,HTTPException
import aiomysql
from datetime import datetime, timedelta

IST_OFFSET = timedelta(hours=5, minutes=30)


        
        
#--------------------Creating new user---------------------
async def   create_user(request: Request, user: UserInDB) -> int:
    query = """
        INSERT INTO users_master (user_name, mail_id, password, role_id, folder_name, created_by, provider)
        VALUES (%s, %s, %s, %s, %s,%s,%s)
    """
    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, (
                user.user_name,
                user.mail_id,
                user.password,
                user.role_id,
                user.folder_name,
                user.created_by,
                user.provider
            ))
            
            return cursor.lastrowid    
        
async def insert_user_sources(
    request: Request,
    user_id: int,
    sources: list
) -> None:
    query = """
        INSERT INTO user_source_mapping (user_id, source_id)
        VALUES (%s, %s) 
    """

    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            values = [
                (
                    user_id,
                    src.source_id,
                )
                for src in sources
            ]

            await cursor.executemany(query, values)

        
##-------------------Update the user-----------------
async def update_user_in_db(request: Request, user_id: int, user_data: UserUpdate, role_id: Optional[int]):
    fields = []
    values = []

    if user_data.user_name:
        fields.append("user_name = %s")
        values.append(user_data.user_name)
    if user_data.mail_id:
        fields.append("mail_id = %s")
        values.append(user_data.mail_id)
    if user_data.password:
        # Hash password before update
        from app.db.repositories import hash_password
        fields.append("password = %s")
        values.append(hash_password(user_data.password))
    if role_id:
        fields.append("role_id = %s")
        values.append(role_id)
    

    if not fields:
        return

    values.append(user_id)
    query = f"UPDATE users_master SET {', '.join(fields)} WHERE user_id = %s"

    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, tuple(values))
            await conn.commit()
            
            
#--------------Delete User--------------------
async def delete_user(request: Request, user_id: int) -> bool:
    delete_child_query = "DELETE FROM user_source_mapping WHERE user_id = %s"
    query = "DELETE FROM users_master WHERE user_id = %s"

    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            # Delete child rows first
            await cursor.execute(delete_child_query, (user_id,))
            # Then delete parent row
            await cursor.execute(query, (user_id,))
            await conn.commit()

            # cursor.rowcount returns number of deleted rows
            return cursor.rowcount > 0


#---------------Encrypt the password------------------
def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')


#checking with original password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))



#--------------Getting the User by email Id--------------
async def get_user_by_emailId(request: Request, email: str, role_id:int) -> Optional[UserInDB]:
    query = "SELECT * FROM users_master WHERE mail_id = %s AND role_id=%s AND is_active = 1"
    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, (email, role_id))
            row = await cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                result_dict = dict(zip(columns, row))
                return result_dict
            return None


async def get_user_with_org_role_by_email(request: Request, email: str) -> Optional[dict]:
    """
    Get user data from users_master table with organization and role names for login
    """
    query = """
        SELECT 
            u.user_id,
            u.user_name,
            u.mail_id,
            u.password,
            u.org_id,
            u.role_id,
            u.folder_name,
            u.created_on,
            u.updated_on,
            o.org_name,
            r.role_name,
            u.term_condition_flag,
            u.provider
        FROM users_master u
        LEFT JOIN org_master o ON u.org_id = o.org_id
        LEFT JOIN role_master r ON u.role_id = r.role_id
        WHERE u.mail_id = %s AND u.is_active = 1
    """
    
    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, (email,))
            row = await cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                result_dict = dict(zip(columns, row))
                
                # Convert BIT/TINYINT byte to int
                if isinstance(result_dict.get("term_condition_flag"), (bytes, bytearray)):
                    result_dict["term_condition_flag"] = int.from_bytes(result_dict["term_condition_flag"], "big")
                
                return result_dict
            return None


async def get_user_by_email(request: Request, email: str) -> Optional[dict]:
    """
    Get user data from users_master table only, no joins.
    """
    query = """
        SELECT *
        FROM users_master
        WHERE mail_id = %s AND is_active = 1
    """
    
    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, (email,))
            row = await cursor.fetchone()
            
            if row:
                # Get column names
                columns = [col[0] for col in cursor.description]
                result_dict = dict(zip(columns, row))

                # Convert BIT/TINYINT bytes to int if needed
                if isinstance(result_dict.get("term_condition_flag"), (bytes, bytearray)):
                    result_dict["term_condition_flag"] = int.from_bytes(result_dict["term_condition_flag"], "big")
                
                return result_dict
            
            return None


#------------Listing All Users On System Dashboard-----------------
async def get_all_users(request):
    query_users = """
        SELECT 
            um.user_id,
            um.role_id,
            um.user_name,
            um.mail_id,
            rm.role_name
        FROM users_master um
        LEFT JOIN role_master rm ON rm.role_id = um.role_id
        WHERE um.is_active = 1
        ORDER BY um.user_id DESC
    """

    query_count = "SELECT COUNT(*) AS total_count FROM users_master WHERE is_active = 1"

    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:

            await cur.execute(query_users)
            users = await cur.fetchall()

            await cur.execute(query_count)
            total_count = (await cur.fetchone())["total_count"]

    return {
        "users": users,
        "totalCount": total_count
    }


#--------------Fetch all roles----------------   
async def get_all_roles(request: Request) -> list[dict]:
    query = """
        SELECT r.role_id, r.role_name
        FROM role_master r
        where r.is_active = 1
    """
    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query)
            rows = await cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        

#-------------Fetch all Source-----------------  
async def get_all_sources(request: Request) -> list[dict]:
    query = """
        SELECT s.source_id, s.source_name
        FROM source_master s
        where s.is_active = 1
    """
    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query)
            rows = await cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        
# Total Effort (convert minutes to hours)
# async def fetch_total_effort(request: Request) -> float:
#     query = """
#         SELECT ROUND(COALESCE(SUM(planned_effort_time), 0) / 60.0, 2) AS total_hours
#         FROM report_data rd
#         where rd.isActive = 1
#     """
#     async with request.app.state.pool.acquire() as conn:
#         async with conn.cursor() as cursor:
#             await cursor.execute(query)
#             row = await cursor.fetchone()
#             return float(row[0]) if row and row[0] is not None else 0.0




#         return fetch_total_effort
async def fetch_total_effort(request: Request, from_date: str, to_date: str,org_id:int) -> float:
    query = """
        SELECT 
            ROUND(COALESCE(SUM(rd.planned_effort_time), 0) / 60.0, 2) AS total_hours
        FROM report_data rd
        LEFT JOIN mail_details md 
            ON md.mail_dtl_id = rd.mail_dtl_id
        WHERE 
            rd.isActive = 1
            AND rd.org_id = %s
            AND DATE(md.date_time) BETWEEN %s AND %s
    """
    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, (org_id, from_date, to_date))
            row = await cursor.fetchone()
            return float(row[0]) if row and row[0] is not None else 0.0




# async def fetch_active_users(request: Request) -> int:
#     query = """
#         SELECT COUNT(*) FROM users_master u WHERE u.is_active = 1
#     """
#     async with request.app.state.pool.acquire() as conn:
#         async with conn.cursor() as cursor:
#             await cursor.execute("COMMIT")
#             await cursor.execute(query)
#             row = await cursor.fetchone()
#             return int(row[0]) if row else 0


# Active Users Count
async def fetch_active_users(request: Request, from_date: str, to_date: str,userId:int,org_id:int,role_id:int) -> int:
    query = """
        SELECT COUNT(*) 
        FROM users_master u 
        WHERE u.is_active = 1
        AND u.role_id = 2 AND u.org_id = %s 
    """
    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query,(org_id))
            row = await cursor.fetchone()
            return int(row[0]) if row else 0




# async def fetch_emails_processed(request: Request) -> int:
#     query ="""
#         SELECT COUNT(*) FROM mail_details m WHERE m.is_active = 1
#     """
#     async with request.app.state.pool.acquire() as conn:
#         async with conn.cursor() as cursor:
#             await cursor.execute(query)
#             row = await cursor.fetchone()
#             return int(row[0]) if row else 0


# Emails Processed Count
async def fetch_emails_processed(request: Request, from_date: str, to_date: str,org_id:int) -> int:
    query = """
        SELECT COUNT(*)
            FROM report_data rd
            JOIN mail_details md ON md.mail_dtl_id = rd.mail_dtl_id
            WHERE rd.org_id = %s
            AND rd.isActive = TRUE
            AND DATE(md.date_time) BETWEEN %s AND %s;
    """
    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, (org_id, from_date, to_date))
            row = await cursor.fetchone()
            return int(row[0]) if row else 0
        
        
async def fetch_meetings_processed(request: Request, from_date: str, to_date: str,org_id:int) -> int:
    query="""
    SELECT COUNT(*)
        FROM meeting_report_data mrd
        JOIN cal_master cm ON mrd.cal_id = cm.cal_id
        JOIN users_master u ON mrd.user_id = u.user_id
        WHERE mrd.is_active = TRUE
        AND DATE(cm.event_start_datetime) BETWEEN %s AND %s
        AND u.org_id = %s;
    """
    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, (from_date, to_date,org_id))
            row = await cursor.fetchone()
            return int(row[0]) if row else 0




# async def fetch_documents_analyzed(request: Request) -> int:
#     query = """
#         SELECT COUNT(*) FROM attach_master a WHERE a.is_active = 1
#     """
#     async with request.app.state.pool.acquire() as conn:
#         async with conn.cursor() as cursor:
#             await cursor.execute(query)
#             row = await cursor.fetchone()
#             return int(row[0]) if row else 0


# Documents Analyzed Count
async def fetch_documents_analyzed(request: Request, from_date: str, to_date: str,org_id:int) -> int:
    query = """
    SELECT 
        COUNT(a.mail_dtl_id)
    FROM 
        attach_master a
    JOIN mail_details md ON a.mail_dtl_id = md.mail_dtl_id
    JOIN users_master u ON a.user_id = u.user_id
    WHERE 
        a.is_active = TRUE
        AND DATE(md.date_time) BETWEEN %s AND %s
        AND u.org_id = %s;
    """
    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, (from_date, to_date,org_id))
            row = await cursor.fetchone()
            return int(row[0]) if row else 0
        
        
   
        
#update User Status        
async def update_user_status(request, user_id: int, is_active: int, org_id: int):
    
    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
 
            #Check if user exists in org
            check_query_if_user_present = "SELECT COUNT(*) FROM users_master WHERE user_id = %s AND org_id = %s"
            await cursor.execute(check_query_if_user_present, (user_id, org_id))
            row = await cursor.fetchone()
            if row[0] == 0:
                return False  #User not found or org mismatch
            #Update status
            update_query = """
                UPDATE users_master
                SET is_active = %s
                WHERE user_id = %s AND org_id = %s
            """
            await cursor.execute(update_query, (is_active, user_id, org_id))
            await conn.commit()
            return True
        
  
  
        
#update Keyword Status
async def update_keyword_status(request, keyword_id: int, is_active: int):
    
    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:            
            #Check if user exists in org
            check_query_if_keyword_present = "SELECT COUNT(*) FROM keyword_master WHERE keyword_id = %s"
            await cursor.execute(check_query_if_keyword_present, (keyword_id))
            row = await cursor.fetchone()
            if row[0] == 0:
                return False  #keyword not found or org mismatch
            #Update status
            update_query = """
                UPDATE keyword_master
                SET is_active = %s
                WHERE keyword_id = %s 
            """
            await cursor.execute(update_query, (is_active, keyword_id))
            await conn.commit()
            return True
        
        


        
        
        

# async def get_users(conn, limit: int, offset: int) -> List[Dict]:
#     query = f"""
#         SELECT user_id, user_name, org_id, is_active
#         FROM users_master
#         WHERE is_active = 1
#         ORDER BY user_id DESC
#         LIMIT {limit} OFFSET {offset}
#     """
#     async with conn.cursor(aiomysql.DictCursor) as cursor:  # DictCursor returns rows as dict
#         await cursor.execute(query)
#         rows = await cursor.fetchall()  # ✅ now fetchall on cursor
#     return rows  # already dicts, no need to convert again


# async def get_users_count(conn) -> int:
#     query = "SELECT COUNT(*) as total FROM users_master WHERE is_active = 1"
#     async with conn.cursor() as cursor:
#         await cursor.execute(query)
#         row = await cursor.fetchone()  # single row
#     return row[0]  # first column contains the count

### above code is commented because it not fetches the increse or decreates data but the below code is fetches all data dynamically

# async def fetch_total_effort(request: Request) -> dict:
#     query = """
#         SELECT 
#             ROUND(COALESCE(SUM(CASE WHEN MONTH(created_date) = MONTH(CURRENT_DATE()) 
#                                     AND YEAR(created_date) = YEAR(CURRENT_DATE())
#                                THEN planned_effort_time ELSE 0 END), 0) / 60.0, 2) AS current_month,
#             ROUND(COALESCE(SUM(CASE WHEN MONTH(created_date) = MONTH(CURRENT_DATE() - INTERVAL 1 MONTH) 
#                                     AND YEAR(created_date) = YEAR(CURRENT_DATE() - INTERVAL 1 MONTH)
#                                THEN planned_effort_time ELSE 0 END), 0) / 60.0, 2) AS last_month
#         FROM report_data
#         WHERE isActive = 1
#     """
#     async with request.app.state.pool.acquire() as conn:
#         async with conn.cursor() as cursor:
#             await cursor.execute(query)
#             row = await cursor.fetchone()

#             current, last = row
#             difference = round(current - last, 2)
#             percent_change = round(((current - last) / last * 100), 2) if last > 0 else 100.0

#             return {
#                 "current": current,
#                 "difference": difference,
#                 "percent_change": percent_change,
#                 "status": "increase" if difference > 0 else "decrease" if difference < 0 else "no change"
#             }


# async def fetch_active_users(request: Request) -> dict:
#     query = """
#         SELECT 
#             COUNT(CASE WHEN MONTH(created_on) = MONTH(CURRENT_DATE()) 
#                         AND YEAR(created_on) = YEAR(CURRENT_DATE()) THEN 1 END) AS current_month,
#             COUNT(CASE WHEN MONTH(created_on) = MONTH(CURRENT_DATE() - INTERVAL 1 MONTH) 
#                         AND YEAR(created_on) = YEAR(CURRENT_DATE() - INTERVAL 1 MONTH) THEN 1 END) AS last_month
#         FROM users_master
#         WHERE is_active = 1
#     """
#     async with request.app.state.pool.acquire() as conn:
#         async with conn.cursor() as cursor:
#             await cursor.execute(query)
#             row = await cursor.fetchone()

#             current, last = row
#             difference = current - last

#             return {
#                 "current": current,
#                 "difference": difference,
#                 "status": "increase" if difference > 0 else "decrease" if difference < 0 else "no change"
#             }


# async def fetch_emails_processed(request: Request) -> dict:
#     query = """
#         SELECT 
#             COUNT(CASE WHEN MONTH(created_on) = MONTH(CURRENT_DATE()) 
#                         AND YEAR(created_on) = YEAR(CURRENT_DATE()) THEN 1 END) AS current_month,
#             COUNT(CASE WHEN MONTH(created_on) = MONTH(CURRENT_DATE() - INTERVAL 1 MONTH) 
#                         AND YEAR(created_on) = YEAR(CURRENT_DATE() - INTERVAL 1 MONTH) THEN 1 END) AS last_month
#         FROM mail_details
#         WHERE is_active = 1
#     """
#     async with request.app.state.pool.acquire() as conn:
#         async with conn.cursor() as cursor:
#             await cursor.execute(query)
#             row = await cursor.fetchone()

#             current, last = row
#             difference = current - last

#             return {
#                 "current": current,
#                 "difference": difference,
#                 "status": "increase" if difference > 0 else "decrease" if difference < 0 else "no change"
#             }


# async def fetch_documents_analyzed(request: Request) -> dict:
#     query = """
#         SELECT 
#             COUNT(CASE WHEN MONTH(created_on) = MONTH(CURRENT_DATE()) 
#                         AND YEAR(created_on) = YEAR(CURRENT_DATE()) THEN 1 END) AS current_month,
#             COUNT(CASE WHEN MONTH(created_on) = MONTH(CURRENT_DATE() - INTERVAL 1 MONTH) 
#                         AND YEAR(created_on) = YEAR(CURRENT_DATE() - INTERVAL 1 MONTH) THEN 1 END) AS last_month
#         FROM attach_master
#         WHERE is_active = 1
#     """
#     async with request.app.state.pool.acquire() as conn:
#         async with conn.cursor() as cursor:
#             await cursor.execute(query)
#             row = await cursor.fetchone()

#             current, last = row
#             difference = current - last

#             return {
#                 "current": current,
#                 "difference": difference,
#                 "status": "increase" if difference > 0 else "decrease" if difference < 0 else "no change"
#             }


##### This code is used to fetch week wise data of previous month
# async def get_weekly_hours_previous_month(request, org_id: int, user_id: int) -> List[Dict[str, Any]]:
#     try:
#         query = """
#             WITH prev_month AS (
#                 SELECT 
#                     DATE_FORMAT(CURRENT_DATE - INTERVAL 1 MONTH, '%%Y-%%m-01') AS start_date,
#                     LAST_DAY(CURRENT_DATE - INTERVAL 1 MONTH) AS end_date
#             )
#             SELECT 
#                 DATE_FORMAT(p.start_date, '%%M %%Y') AS month_name,
#                 CONCAT('Week ', CEIL(DAYOFMONTH(r.created_date) / 7)) AS week_of_month,
#                 ROUND(SUM(r.planned_effort_time) / 60, 2) AS total_hours
#             FROM report_data r
#             JOIN prev_month p
#             WHERE r.created_date BETWEEN p.start_date AND p.end_date
#             AND r.org_id = %s     
#             GROUP BY month_name, week_of_month
#             ORDER BY week_of_month;
#         """

#         async with request.app.state.pool.acquire() as conn:
#             async with conn.cursor() as cursor:
#                 await cursor.execute(query, (org_id))
#                 rows = await cursor.fetchall()

#                 # ✅ Convert to list of dicts
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
#         # raise HTTPException(status_code=500, detail=str(e))
#         # AND r.org_id = %s

## This code is used to fetch calculateing one month to current date data week wise
async def get_weekly_hours_previous_month(request, org_id: int,  from_date: str, to_date: str) -> List[Dict[str, Any]]:
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
                ROUND(SUM(rd.planned_effort_time) / 60, 2) AS total_hours
            FROM
                report_data rd
            LEFT JOIN 
                mail_details md ON md.mail_dtl_id = rd.mail_dtl_id
            JOIN 
                date_range p ON md.date_time >= p.start_date AND md.date_time < p.end_date
            WHERE
                rd.org_id = %s
                AND rd.isActive = 1
            GROUP BY
                week_index
            ORDER BY
                MIN(md.date_time);
        """

        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (from_date, to_date, org_id))
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

#Fetching Top Keywords On Admin Dahsboard
async def fetch_keywords_by_org(request, org_id: int, user_id: int,from_date:str,to_date:str) -> List[Tuple[str]]:
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
            u.org_id = %s
            AND u.is_active = 1
            AND m.date_time between %s and %s;
        """
        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (org_id,from_date,to_date))
                return await cursor.fetchall()
    except Exception as e:
        return []  
    
    
    #find Last sync of each user
async def fetch_last_sync_by_users(org_id: int,request:Request) -> List[Dict[str, Any]]:
    try:
        query = """
            SELECT r.user_id, MAX(r.created_date) AS last_sync
            FROM report_data r
            JOIN mail_details m ON r.mail_dtl_id = m.mail_dtl_id
            WHERE r.org_id = %s
            GROUP BY r.user_id
            ORDER BY last_sync DESC
        """
        
        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (org_id,))
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
    
# Get user by email & org_id
async def get_user_by_email_id(email: str, request: Request) -> Dict[str, Any]:
    try:
        query = "SELECT user_id, mail_id FROM users_master WHERE mail_id=%s"
        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (email))
                row = await cursor.fetchone()
                if row:
                    return {
                        "user_id": row[0],
                        "mail_id": row[1]
                    }
                return None
    except Exception as e:
        # raise Exception(f"Error fetching user: {str(e)}")
        print(f"Error fetching user: {str(e)}")
        return None


# Update user password
# async def update_user_password(user_id: int, org_id: int, new_password: str, request: Request) -> bool:
#     try:
#         query = "UPDATE users_master SET password=%s WHERE user_id=%s AND org_id=%s"
#         async with request.app.state.pool.acquire() as conn:
#             async with conn.cursor() as cursor:
#                 await cursor.execute(query, (new_password, user_id, org_id))
#                 await conn.commit()
#                 print(f"Rows updated: {cursor.rowcount}")
#                 return cursor.rowcount > 0  # True if any row updated
#     except Exception as e:
#         raise Exception(f"Error updating password: {str(e)}")

# Update user password and fetch updated user details
async def update_user_password(user_id: int, new_password: str, request: Request) -> dict:
    try:
        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # ✅ Update password
                update_query = """
                    UPDATE users_master 
                    SET password = %s 
                    WHERE user_id = %s 
                """
                await cursor.execute(update_query, (new_password, user_id))
                await conn.commit()

                if cursor.rowcount == 0:
                    return {}  # No rows updated (user not found)

                # ✅ Fetch updated user details
                fetch_query = """
                    SELECT user_id, org_id, user_name, mail_id, password
                    FROM users_master 
                    WHERE user_id = %s  AND is_active = 1
                """
                await cursor.execute(fetch_query, (user_id))
                updated_user = await cursor.fetchone()

                return updated_user or {}
    except Exception as e:
        raise Exception(f"Error updating password: {str(e)}")
    
    
    
#Search Filter On User
async def search_user(request: Request, org_id: int, query: str, page: int, limit: int):
    try:
        offset = (page - 1) * limit

        # Add wildcards around search term
        search_param = f"%{query}%"

        search_query = """
        SELECT 
            u.user_id, 
            u.user_name, 
            o.org_name,
            CAST(u.is_active AS UNSIGNED) AS is_active,  
            COALESCE(email_counts.email_count, 0) AS email_count
        FROM users_master u
        JOIN org_master o ON u.org_id = o.org_id
        LEFT JOIN (
            SELECT user_id, COUNT(*) AS email_count
            FROM mail_details
            WHERE is_active = 1
            GROUP BY user_id
        ) email_counts ON email_counts.user_id = u.user_id
        WHERE u.org_id = %s
          AND u.user_name LIKE %s
        ORDER BY u.user_name ASC
        LIMIT %s OFFSET %s;
        """

        count_query = """
        SELECT COUNT(*) as total
        FROM users_master
        WHERE org_id = %s AND user_name LIKE %s
        """

        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                # Pass arguments exactly matching placeholders
                await cursor.execute(search_query, (org_id, search_param, limit, offset))
                users = await cursor.fetchall()

                await cursor.execute(count_query, (org_id, search_param))
                total = await cursor.fetchone()

        return users, total["total"]

    except Exception as e:
        print("Error in search_user repo:", e)
        raise




# Search Filter On Keywords
async def search_keyword(request: Request, org_id: int, query: str, page: int, limit: int):
    try:
        offset = (page - 1) * limit
        search_query = """
            SELECT 
                k.keyword_id,
                k.keyword_name,
                k.is_active,
                c.cat_id AS category_id,
                c.cat_name AS category_name
            FROM keyword_master AS k
            JOIN category_master AS c
                ON k.cat_id = c.cat_id
            WHERE k.org_id = %s AND k.keyword_name LIKE CONCAT('%%', %s, '%%')
            ORDER BY k.keyword_name ASC
            LIMIT %s OFFSET %s
        """
        count_query = """
            SELECT COUNT(*) as total
            FROM keyword_master
            WHERE org_id = %s AND keyword_name LIKE %s
        """

        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                search_param = f"{query}%"
                await cursor.execute(search_query, (org_id, search_param, limit, offset))
                keywords = await cursor.fetchall()

                await cursor.execute(count_query, (org_id, search_param))
                total = await cursor.fetchone()

        return keywords, total["total"]

    except Exception as e:
        print("Error in search_keyword repo:", e)
        raise


# Search Filetr On Categories
async def search_category(request: Request, org_id: int, query: str, page: int, limit: int):
    try:
        offset = (page - 1) * limit
        search_query = """
           SELECT 
                c.cat_id AS category_id,
                c.cat_name AS category_name,
                c.is_active,
                GROUP_CONCAT(k.keyword_name ORDER BY k.keyword_name SEPARATOR ', ') AS keywords
            FROM category_master AS c
            LEFT JOIN keyword_master AS k
                ON c.cat_id = k.cat_id
            WHERE c.org_id = %s AND c.cat_name LIKE CONCAT('%%', %s, '%%')
            GROUP BY c.cat_id, c.cat_name, c.is_active
            ORDER BY c.cat_name ASC
            LIMIT %s OFFSET %s
        """
        count_query = """
            SELECT COUNT(*) as total
            FROM category_master
            WHERE org_id = %s AND cat_name LIKE %s
        """

        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                search_param = f"{query}%"
                await cursor.execute(search_query, (org_id, search_param, limit, offset))
                categories = await cursor.fetchall()

                await cursor.execute(count_query, (org_id, search_param))
                total = await cursor.fetchone()

        return categories, total["total"]

    except Exception as e:
        print("Error in search_category repo:", e)
        raise