from typing import Optional, List, Dict, Any
from app.db.repositories.base import BaseRepository


# Insert into your existing mail_details table (including `keyword`, `repeated_keyword`, and `graph_mail_id` columns)
INSERT_MAIL_DETAILS = """
INSERT INTO mail_details (
  cal_id, user_id, keyword_id,
  subject, body, date_time,
  mail_from, mail_to, mail_cc,
  word_count, keyword, repeated_keyword, created_by, updated_by, is_active, graph_mail_id, folder_name
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

# Insert into your existing attach_master table (including `keyword` and `repeated_keyword` columns)
INSERT_ATTACHMENT = """
INSERT INTO attach_master (
  mail_dtl_id, user_id, cal_id, word_count,
  attach_name, attach_type, attach_path,
  created_by, updated_by, is_active, keyword, repeated_keyword, file_hash
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
        word_count: Optional[str],
        keyword: Optional[str] = None,
        repeated_keyword: Optional[str] = None,
        cal_id: Optional[int] = None,
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
                cal_id, user_id, keyword_id,
                subject, body, date_time,
                mail_from, mail_to, mail_cc,
                word_count, keyword, repeated_keyword, created_by, updated_by, is_active,
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
                mail_dtl_id, user_id, cal_id, word_count,
                attach_name, attach_type, attach_path,
                created_by, updated_by, is_active, keyword, repeated_keyword, file_hash
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
    
    async def check_event_exists(self, event_id: str) -> bool:
        """Check if a calendar event with the given event_id already exists"""
        query = "SELECT 1 FROM cal_master WHERE event_id = %s AND is_active = 1 LIMIT 1"
        await self._log_and_execute(query, [event_id])
        result = await self._cur.fetchone()
        return result is not None
    

    async def attachment_exists(self, file_hash: str) -> bool:
        query = "SELECT 1 FROM attach_master WHERE file_hash = %s AND is_active = 1 LIMIT 1"
        await self._log_and_execute(query, [file_hash])
        result = await self._cur.fetchone()
        return result is not None

