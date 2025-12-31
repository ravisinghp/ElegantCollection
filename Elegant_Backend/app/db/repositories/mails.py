from datetime import datetime
from typing import Optional, List, Dict, Any
from app.db.repositories.base import BaseRepository


# Insert into your existing mail_details table (including `keyword`, `repeated_keyword`, and `graph_mail_id` columns)
INSERT_MAIL_DETAILS = """
INSERT INTO mail_details (
  user_id, 
  subject, body, date_time,
  mail_from, mail_to, mail_cc,
keyword, created_by, updated_by, is_active, graph_mail_id, folder_name
) VALUES ( %s, %s, %s, %s, %s, %s, %s,  %s, %s, %s, %s, %s, %s)
"""

# Insert into your existing attach_master table (including `keyword` and `repeated_keyword` columns)
INSERT_ATTACHMENT = """
INSERT INTO email_attachments (
  mail_dtl_id, user_id, 
  attach_name, attach_type, attach_path,
  created_by, updated_by, is_active, keyword, file_hash
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,  %s)
"""

# Insert into calendar master table for events matched by keywords
INSERT_CALENDAR_EVENT = """
INSERT INTO cal_master (
  user_id,
  organiser,
  attendees,
  title,
  description,
  word_count,
  keyword,
  repeated_keyword,
  event_start_datetime,
  event_end_datetime,
  duration_minutes,
  event_id,
  created_by,
  updated_by,
  is_active
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


INSERT_PO_DETAILS = """
INSERT INTO po_details (
    mail_dtl_id,
    po_number,
    customer_name,
    vendor_number,
    po_date,
    delivery_date,
    cancel_date,
    gold_karat,
    ec_style_number,
    customer_style_number,
    color,
    quantity,
    description,
    mail_folder,
    created_by
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


# PO REPOSITORY (SAME FILE - MATCHES MAILSREPOSITORY STYLE)
# ---------------------------------------------------------------------

GET_ALL_PO_DETAILS = """
SELECT * FROM po_details WHERE active = 1
"""

GET_ALL_SYSTEM_PO_DETAILS = """
SELECT * FROM system_po_details WHERE active = 1
"""

INSERT_MISMATCH = """
INSERT INTO po_mismatch_report (
    po_det_id,
    system_po_id,
    mismatch_attribute,
    system_value,
    scanned_value,
    comment
) VALUES (%s, %s, %s, %s, %s, %s)
"""

CHECK_PO_EXISTS = """
SELECT 1 FROM po_details 
WHERE po_number = %s 
AND is_active = 1 
LIMIT 1
"""

GET_EXISTING_MISMATCH = """
SELECT 1
FROM po_mismatch_report
WHERE po_det_id = %s
  AND (
        (system_po_id = %s AND mismatch_attribute = %s)
        OR
        (system_po_id IS NULL AND %s IS NULL)
      )
LIMIT 1
"""

GET_EXISTING_PO_MISSING = """
SELECT 1
FROM po_missing_report
WHERE po_det_id = %s
LIMIT 1
"""


INSERT_PO_MISSING = """
INSERT INTO po_missing_report (
    po_det_id,
    system_po_id,
    mismatch_attribute,
    system_value,
    scanned_value,
    comment
) VALUES (%s, %s, %s, %s, %s, %s)
"""

GET_EXISTING_PO_MISSING_BY_SYSTEM_PO = """
SELECT 1
FROM po_missing_report
WHERE system_po_id = %s
  AND mismatch_attribute = 'po_missing'
LIMIT 1
"""
class MailsRepository(BaseRepository):
    async def insert_mail_detail(
        self,
        *,
        subject: Optional[str],
        body: Optional[str],
        date_time: Optional[str],  # YYYY-MM-DD
        mail_from: Optional[str],
        mail_to: Optional[str],
        mail_cc: Optional[str],
        keyword: Optional[str],
        repeated_keyword: Optional[str] = None,
        # cal_id: Optional[int] = None,
        user_id: Optional[int] = None,
        keyword_id: Optional[int] = None,
        created_by: Optional[int] = None,
        updated_by: Optional[int] = None,
        is_active: int = 1,
        graph_mail_id: Optional[str] = None,
        folder_name: Optional[str] = None,
    ) -> int:
        await self._log_and_execute(
            INSERT_MAIL_DETAILS,
            [
                 user_id, 
                subject, body, date_time,
                mail_from, mail_to, mail_cc,
                keyword,  created_by, updated_by, is_active,
                graph_mail_id, folder_name
            ],
        )
        last_id = self._cur.lastrowid  # type: ignore[attr-defined]
        await self._cur.connection.commit()
        if not last_id:
            raise RuntimeError("Failed to retrieve inserted mail_details id")
        return int(last_id)
    
    


    async def insert_attachment(
        self,
        *,
        mail_dtl_id: int,
        attach_name: Optional[str],
        attach_type: Optional[str],
        attach_path: Optional[str],
        word_count: Optional[str] = None,
        user_id: Optional[int] = None,
        cal_id: Optional[int] = None,
        created_by: Optional[int] = None,
        updated_by: Optional[int] = None,
        is_active: int = 1,
        keyword: Optional[str] = None,
        repeated_keyword: Optional[str] = None,
        file_hash: Optional[str] = None,
    ) -> None:
        await self._log_and_execute(
            INSERT_ATTACHMENT,
            [
                mail_dtl_id, user_id, 
                attach_name, attach_type, attach_path,
                created_by, updated_by, is_active, keyword,  file_hash
            ],
        )
        await self._cur.connection.commit() 

    async def update_mail_detail(
        self,
        *,
        mail_dtl_id: int,
        repeated_keyword: Optional[str] = None,
    ) -> None:
        """Update repeated_keyword field in mail_details table"""
        UPDATE_MAIL_DETAILS = """
        UPDATE mail_details 
        SET repeated_keyword = %s
        WHERE id = %s
        """
        await self._log_and_execute(
            UPDATE_MAIL_DETAILS,
            [repeated_keyword, mail_dtl_id],
        )
        await self._cur.connection.commit() 


    async def mail_exists(self, graph_mail_id: str, user_id: str) -> bool:
        """Check if a mail with the given graph_mail_id already exists"""
        query = "SELECT 1 FROM mail_details WHERE graph_mail_id = %s AND user_id = %s AND is_active = 1 LIMIT 1"
        await self._log_and_execute(query, [graph_mail_id,user_id])
        result = await self._cur.fetchone()
        return result is not None
    
    
    


    # async def save_event(self, event_data: Dict[str, Any]):
    #     query = """
    #     INSERT INTO events (user_id, event_id, subject, start_time, end_time, body_preview, keywords_count)
    #     VALUES (%s, %s, %s, %s, %s, %s, %s)
    #     """
    #     async with self.conn.cursor() as cur:
    #         await cur.execute(
    #             query,
    #             (
    #                 event_data["user_id"],
    #                 event_data["event_id"],
    #                 event_data["subject"],
    #                 event_data["start"],
    #                 event_data["end"],
    #                 event_data["body_preview"],
    #                 event_data["keywords_count"],
    #             ),
    #         )
    #         await self.conn.commit()


    async def fetch_keywords(self, orgid: int) -> List[str]:
        """
        Fetch active keywords for a given orgid from keyword_master table.
        """
        query = """
            SELECT keyword_name 
            FROM keyword_master 
            WHERE org_id = %s AND is_active = 1
        """
        
        await self._log_and_execute(query, (orgid,))
        result = await self._cur.fetchall()
        return [row['keyword_name'].lower() for row in result] if result else []

    async def insert_calendar_event(
        self,
        *,
        user_id: int,
        organiser: Optional[str],
        attendees: Optional[str],
        title: Optional[str],
        description: Optional[str],
        word_count: Optional[int],
        keyword: Optional[str],
        repeated_keyword: Optional[str],
        event_start_datetime: Optional[str],
        event_end_datetime: Optional[str],
        duration_minutes: Optional[int],
        event_id: Optional[str],
        created_by: Optional[int] = None,
        updated_by: Optional[int] = None,
        is_active: int = 1,
    ) -> int:
        await self._log_and_execute(
            INSERT_CALENDAR_EVENT,
            [
                user_id,
                organiser,
                attendees,
                title,
                description,
                word_count,
                keyword,
                repeated_keyword,
                event_start_datetime,
                event_end_datetime,
                duration_minutes,
                event_id,
                created_by,
                updated_by,
                is_active,
            ],
        )
        last_id = self._cur.lastrowid  # type: ignore[attr-defined]
        await self._cur.connection.commit()
        if not last_id:
            raise RuntimeError("Failed to retrieve inserted cal_master id")
        return int(last_id)
    
    async def user_token_exists(self, user_id: int) -> bool:
     query = "SELECT COUNT(*) AS cnt FROM outlook_tokens WHERE user_id = %s"
     await self._log_and_execute(query, (user_id,))
     result = await self._cur.fetchone()
     return result['cnt'] > 0 
    

    async def insert_outlook_token(
        self,
        user_id: int,
        access_token: str,
        refresh_token: str,
        token_expiry: datetime,
    ):
        query = """
            INSERT INTO outlook_tokens (user_id, access_token, refresh_token, token_expiry)
            VALUES (%s, %s, %s, %s)
        """
        await self._log_and_execute(query, (user_id, access_token, refresh_token,token_expiry))
        


    async def update_outlook_token(
        self,
        user_id: int,
        access_token: str,
        refresh_token: str,
        token_expiry: datetime,
    ):
        query = """
            UPDATE outlook_tokens
            SET access_token = %s,
                refresh_token = %s,
                token_expiry = %s,
                updated_at = NOW()
            WHERE user_id = %s
        """
        await self._log_and_execute(query, (access_token, refresh_token, token_expiry, user_id))


    async def update_first_login_flag(self, user_id: int):
     query = """
        UPDATE users_master
        SET is_first_login = 0,
            updated_on = NOW()
        WHERE user_id = %s
        """
     await self._log_and_execute(query, (user_id,))

    async def insert_po_details(
        self,
        *,
        mail_dtl_id: int,
        po_number: Optional[str],
        customer_name: Optional[str],
        vendor_number: Optional[str],
        po_date: Optional[str],
        delivery_date: Optional[str],
        cancel_date: Optional[str],
        gold_karat: Optional[str],
        ec_style_number: Optional[str],
        customer_style_number: Optional[str],
        color: Optional[str],
        quantity: Optional[str],
        description: Optional[str],
        mail_folder: Optional[str],
        created_by: Optional[int],
    ) -> int:
        
        await self._log_and_execute(
            INSERT_PO_DETAILS,
            [
                mail_dtl_id,
                po_number,
                customer_name,
                vendor_number,
                po_date,
                delivery_date,
                cancel_date,
                gold_karat,
                ec_style_number,
                customer_style_number,
                color,
                quantity,
                description,
                mail_folder,
                created_by,
            ],
        )

        last_id = self._cur.lastrowid
        await self._cur.connection.commit()

        if not last_id:
            raise RuntimeError("Failed to retrieve inserted po_details id")

        return int(last_id)
    
    
    async def check_event_exists(self, event_id: str) -> bool:
        """Check if a calendar event with the given event_id already exists"""
        query = "SELECT 1 FROM cal_master WHERE event_id = %s AND is_active = 1 LIMIT 1"
        await self._log_and_execute(query, [event_id])
        result = await self._cur.fetchone()
        return result is not None
    

    async def attachment_exists(self, file_hash: str) -> bool:
        query = "SELECT 1 FROM email_attachments WHERE file_hash = %s AND is_active = 1 LIMIT 1"
        await self._log_and_execute(query, [file_hash])
        result = await self._cur.fetchone()
        return result is not None
    



# ---------------------------------------------------------------------
# REPOSITORY SECTION (IN SAME FILE)
# ---------------------------------------------------------------------
    async def get_all_po_details(self):
        """Used in your PO mismatch service"""
        await self._log_and_execute(GET_ALL_PO_DETAILS, [])
        return await self._cur.fetchall()

    async def get_all_system_po_details(self):
        """Used in your PO mismatch service"""
        await self._log_and_execute(GET_ALL_SYSTEM_PO_DETAILS, [])
        return await self._cur.fetchall()

    async def check_po_exists(self, po_number: str) -> bool:
        """Optional helper if you need PO existence checking"""
        await self._log_and_execute(CHECK_PO_EXISTS, [po_number])
        result = await self._cur.fetchone()
        return result is not None
    
    
    async def get_existing_mismatch(self, po_det_id, system_po_id, mismatch_attribute=None):
        await self._log_and_execute(
            GET_EXISTING_MISMATCH,
        [po_det_id, system_po_id,  mismatch_attribute,system_po_id,]
    )
        return await self._cur.fetchone()
    
    async def get_existing_po_missing_by_system_po(self, system_po_id: int):
        await self._log_and_execute(
            GET_EXISTING_PO_MISSING_BY_SYSTEM_PO,
        [system_po_id],
    )
        return await self._cur.fetchone()
    
    async def get_existing_po_missing(self, po_det_id: int):
        await self._log_and_execute(
        GET_EXISTING_PO_MISSING,
        [po_det_id],
    )
        return await self._cur.fetchone()



    async def insert_mismatch(
        self,
        *,
        po_det_id: Optional[int],
        system_po_id: Optional[int],
        field: str,
        system_value: str,
        scanned_value: str,
        comment: str,
    ) -> int:
        """Inserts a mismatch into po_mismatch_report"""

        await self._log_and_execute(
            INSERT_MISMATCH,
            [
                po_det_id,
                system_po_id,
                field,
                system_value,
                scanned_value,
                comment,
            ],
        )

        last_id = self._cur.lastrowid
        await self._cur.connection.commit()

        if not last_id:
            raise RuntimeError("Failed to insert mismatch report")

        return int(last_id)
    
 
    
    async def insert_po_missing(
        self,
        *,
        po_det_id: int,
        system_po_id: Optional[int],
        attribute: str,
        system_value: str,
        scanned_value: str,
        comment: str,
    ) -> int:

        await self._log_and_execute(
            INSERT_PO_MISSING,
            [
                po_det_id,
                system_po_id,
                attribute,
                system_value,
                scanned_value,
                comment,
            ],
        )

        last_id = self._cur.lastrowid
        await self._cur.connection.commit()

        if not last_id:
            raise RuntimeError("Failed to insert PO missing report")

        return int(last_id)

    
    

        
