from typing import Optional, List, Dict, Any, Tuple, Union
from app.db.repositories.base import BaseRepository
from datetime import date
import logging
import aiofiles

# Configure logger (do this once, ideally at the top of the module)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# CREATE_USER_QUERY = """
# INSERT INTO report_data
# (user_id, org_id, word_count, keywords_found, keyword_count, actual_effort_time, planned_effort_time, mail_dtl_id)
# VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
# """
CREATE_USER_QUERY = """
INSERT INTO report_data
(user_id, org_id, word_count, keywords_found, keyword_count, repeated_keyword_count,
actual_effort_time, planned_effort_time, mail_dtl_id, cat_id, created_by)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) AS new_data
ON DUPLICATE KEY UPDATE
user_id = new_data.user_id,
org_id = new_data.org_id,
word_count = new_data.word_count,
keywords_found = new_data.keywords_found,
keyword_count = new_data.keyword_count,
repeated_keyword_count = new_data.repeated_keyword_count,
actual_effort_time = new_data.actual_effort_time,
planned_effort_time = new_data.planned_effort_time,
mail_dtl_id = new_data.mail_dtl_id,
cat_id = new_data.cat_id,
created_by = new_data.created_by;
"""


CREATE_MEETING_QUERY = """
INSERT INTO meeting_report_data
(user_id, org_id, cal_id, word_count, keywords_found, keyword_count, meeting_duration, efforts_time, created_by)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) AS new_data
ON DUPLICATE KEY UPDATE
user_id = new_data.user_id,
org_id = new_data.org_id,
word_count = new_data.word_count,
keywords_found = new_data.keywords_found,
keyword_count = new_data.keyword_count,
meeting_duration = new_data.meeting_duration,
efforts_time = new_data.efforts_time,
created_by = new_data.created_by;
"""

FILE_TYPE_LABELS = {
    "application/pdf": "PDF Document",
    "text/plain": "Text File",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "Word Document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "PowerPoint",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "Excel Sheet",
    "application/vnd.ms-excel": "Excel XLS Sheet",
    "text/csv": "CSV File",
    "application/csv": "CSV File",
}


class ReportDataRepo(BaseRepository):
    async def save_report_data(
        self,
        user_id: int,
        org_id: int,
        word_count: int,
        keywords_found: str,
        keyword_count: int,
        repeated_keyword_count: int,
        actual_effort_time: float,
        planned_effort_time: float,
        cat_id: int,
        mail_dtl_id: Optional[int] = None,
        created_by: Optional[int] = None,
    ) -> None:
        # if mail_dtl_id is None:
        #     return

        try:
            await self._log_and_execute(
                CREATE_USER_QUERY,
                (
                    user_id,
                    org_id,
                    word_count,
                    keywords_found,
                    keyword_count,
                    repeated_keyword_count,
                    actual_effort_time,
                    planned_effort_time,
                    mail_dtl_id,
                    cat_id,
                    created_by,
                ),
            )
            await self._cur.connection.commit()
        except Exception as e:
            # This will now catch real DB errors like duplicate key (just in case)
            logger.error(f"DB Error on save_report_data: {e}")
            raise

    # ----------------------insert data in meeting_report_data table----------------------
    async def save_meeting_report_data(
        self,
        user_id: int,
        org_id: int,
        cal_id: int,
        word_count: int,
        keywords_found: str,
        keyword_count: int,
        meeting_duration: float,
        efforts_time: float,
        created_by: Optional[int] = None,
    ) -> None:
        try:
            await self._log_and_execute(
                CREATE_MEETING_QUERY,
                (
                    user_id,
                    org_id,
                    cal_id,
                    word_count,
                    keywords_found,
                    keyword_count,
                    meeting_duration,
                    efforts_time,
                    created_by,
                ),
            )
            await self._cur.connection.commit()
        except Exception as e:
            # This will now catch real DB errors like duplicate key (just in case)
            logger.error(f"DB Error on save_report_data: {e}")
            raise

    async def get_existing_mail_ids(self, mail_ids: List[int]) -> List[int]:
        """
        Fetch all mail_dtl_ids from DB that already exist.
        This is a bulk check to avoid inserting duplicates.
        """
        if not mail_ids:
            return []

        # Generate a placeholder string for the IN clause
        placeholders = ",".join(["%s"] * len(mail_ids))
        query = (
            f"SELECT mail_dtl_id FROM report_data WHERE mail_dtl_id IN ({placeholders})"
        )

        await self._log_and_execute(query, tuple(mail_ids))
        rows = await self._cur.fetchall()
        # Return as a list of integers
        return [row["mail_dtl_id"] for row in rows]

    async def update_report_data(
        self,
        report_id: int,
        efforts: Optional[float] = None,
        keyword_efforts: Optional[int] = None,
    ) -> None:
        """
        Update only allowed fields in report_data (no recalculation).
        """
        fields, params = [], []

        if efforts is not None:
            fields.append("planned_effort_time = %s")
            params.append(efforts)

        # if keyword_efforts is not None:
        #     fields.append("keyword_efforts = %s")
        #     params.append(keyword_efforts)

        if not fields:
            return  # nothing to update

        query = f"""
            UPDATE report_data
            SET {", ".join(fields)}
            WHERE report_id = %s
        """
        params.append(report_id)

        await self._log_and_execute(query, tuple(params))
        await self._cur.connection.commit()

    async def get_rules(self, org_id: int) -> Dict[str, float]:
        """
        Fetch all effort estimation rules for the given org_id.
        """
        query = """
            SELECT rule_key, rule_value
            FROM effort_estimation_rules
            WHERE org_id = %s
        """
        await self._log_and_execute(query, (org_id,))
        rows = await self._cur.fetchall()

        if not rows:
            return {}

        return {row["rule_key"]: float(row["rule_value"]) for row in rows}

    async def get_mail_details(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Fetch mail details by user_id.
        """
        try:
            query = """
                SELECT mail_dtl_id, user_id, subject, body, created_by
                FROM mail_details
                WHERE user_id = %s AND is_active = 1
            """
            return await self._log_and_fetch_all(query, (user_id,))
        except Exception as e:
            logger.error(f"DB Error on get_mail_details: {e}")
            raise

    async def get_keywords(self, org_id: int) -> List[Dict[str, Any]]:
        """
        Fetch all keywords for the given org_id from keyword_master.
        Returns a list of dicts: [{ "keyword_id": 1, "keyword_name": "analysis" }, ...]
        """
        query = """
            SELECT keyword_id, keyword_name, cat_id
            FROM keyword_master
            WHERE org_id = %s AND is_active = 1
        """
        await self._log_and_execute(query, (org_id,))
        rows = await self._cur.fetchall()

        if not rows:
            return []

        # Normalize and clean
        keywords = []
        for row in rows:
            if isinstance(row, dict):
                keywords.append(
                    {
                        "keyword_id": row["keyword_id"],
                        "keyword_name": row["keyword_name"].strip().lower(),
                        "cat_id": row["cat_id"],
                    }
                )
            else:
                keywords.append(
                    {
                        "keyword_id": row[0],
                        "keyword_name": str(row[1]).strip().lower(),
                        "cat_id": row[2],
                    }
                )

        return keywords

    # ------------------- Fetch Report Data for CSV/PDF Export -------------------
    async def fetch_report_data(
        self, report_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch report_data (mail reports) rows for CSV/PDF export.
        Uses DISTINCT and joins category_master.
        """
        try:
            base_query = """
                SELECT DISTINCT
                    rd.report_id,
                    md.mail_dtl_id,
                    DATE(md.date_time) AS created_date,
                    md.mail_from,
                    md.mail_to,
                    md.word_count,
                    rd.actual_effort_time,
                    rd.planned_effort_time,
                    rd.repeated_keyword_count,
                    cm.cat_id,
                    cm.cat_name,
                    rd.word_count AS attachment_word_count
                FROM report_data rd
                INNER JOIN mail_details md ON md.mail_dtl_id = rd.mail_dtl_id
                LEFT JOIN category_master cm ON cm.cat_id = rd.cat_id
            """

            params: List[Any] = []
            if report_ids and len(report_ids) > 0:
                placeholders = ", ".join(["%s"] * len(report_ids))
                base_query += f" WHERE rd.report_id IN ({placeholders})"
                params = report_ids

            base_query += " ORDER BY rd.report_id DESC;"

            await self._log_and_execute(base_query, tuple(params) if params else ())
            return await self._cur.fetchall()

        except Exception as e:
            logger.error(f"DB Error on fetch_report_data: {e}")
            return []


    # ------------------- Fetch Meeting Report Data for CSV/PDF Export -------------------
    async def fetch_meeting_report_data(
        self, report_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch meeting_report_data rows for CSV/PDF export.
        Maps organiser -> From and attendees -> To for consistency with mail reports.
        """
        try:
            base_query = """
                SELECT 
                    mrd.meeting_report_id AS report_id,
                    DATE(cm.event_start_datetime) AS date_time,
                    cm.organiser AS "from",
                    cm.attendees AS "to",
                    mrd.meeting_duration,
                    mrd.efforts_time
                FROM meeting_report_data mrd
                JOIN cal_master cm ON cm.cal_id = mrd.cal_id
            """

            params: List[Any] = []
            if report_ids and len(report_ids) > 0:
                placeholders = ", ".join(["%s"] * len(report_ids))
                base_query += f" WHERE mrd.meeting_report_id IN ({placeholders})"
                params = report_ids

            base_query += """
                ORDER BY mrd.meeting_report_id DESC
            """

            await self._log_and_execute(base_query, tuple(params) if params else ())
            return await self._cur.fetchall()
        except Exception as e:
            logger.error(f"DB Error on fetch_meeting_report_data: {e}")
            return []

    async def get_report_data_by_date(
        self,
        from_date: date,
        to_date: date,
        filters: Dict[str, Optional[str]] = None,
    ) -> Tuple[List[Dict[str, Union[str, int]]], int]:
        """
        Fetch report data for all users with optional filters.
        """
        try:
            filters = filters or {}
            keyword = filters.get("keyword")
            category = filters.get("category")
            user = filters.get("user")
            file_type = filters.get("file_type")

            params = [from_date, to_date]
            conditions = ["DATE(md.date_time) BETWEEN %s AND %s"]

            if keyword:
                conditions.append("FIND_IN_SET(%s, rd.keywords_found)")
                params.append(keyword)

            if category:
                conditions.append("cm.cat_id = %s")
                params.append(category)

            if user:
                conditions.append("md.user_id = %s")
                params.append(user)

            file_join = ""
            if file_type:
                file_join = "JOIN attach_master am ON am.mail_dtl_id = rd.mail_dtl_id"
                conditions.append("am.attach_type = %s")
                params.append(file_type)

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            query = f"""
                SELECT DISTINCT
                    rd.report_id,
                    md.mail_dtl_id,
                    DATE(md.date_time) AS created_date,
                    md.mail_from,
                    md.mail_to,
                    md.word_count,
                    rd.actual_effort_time,
                    rd.planned_effort_time,
                    rd.repeated_keyword_count,
                    cm.cat_id,
                    cm.cat_name,
                    rd.word_count AS attachment_word_count
                FROM report_data rd
                LEFT JOIN mail_details md ON md.mail_dtl_id = rd.mail_dtl_id
                LEFT JOIN category_master cm ON cm.cat_id = rd.cat_id
                {file_join}
                WHERE {where_clause}
                ORDER BY rd.report_id DESC
            """
            await self._log_and_execute(query, tuple(params))
            results = await self._cur.fetchall()

            count_query = f"""
                SELECT COUNT(DISTINCT rd.report_id) AS total
                FROM report_data rd
                LEFT JOIN mail_details md ON md.mail_dtl_id = rd.mail_dtl_id
                LEFT JOIN category_master cm ON cm.cat_id = rd.cat_id
                {file_join}
                WHERE {where_clause}
            """
            await self._log_and_execute(count_query, tuple(params))
            total_count = (await self._cur.fetchone())["total"]

            return results or [], total_count

        except Exception as e:
            logger.error(f"DB Error on get_report_data_by_date: {e}")
            raise

    async def get_report_data_by_date_userId(
        self,
        from_date: date,
        to_date: date,
        user_id: int,
        filters: Dict[str, Optional[str]] = None,
    ) -> Tuple[List[Dict], int]:
        """
        Fetch report data for a specific user with optional filters.
        """
        try:
            filters = filters or {}
            keyword = filters.get("keyword")
            category = filters.get("category")
            user_filter = filters.get("user")
            file_type = filters.get("file_type")

            params = [from_date, to_date, user_id, user_id]
            conditions = [
                "DATE(md.date_time) BETWEEN %s AND %s",
                "(md.user_id = %s OR rd.created_by = %s)",
            ]

            if keyword:
                conditions.append("FIND_IN_SET(%s, rd.keywords_found)")
                params.append(keyword)

            if category:
                conditions.append("cm.cat_id = %s")
                params.append(category)

            if user_filter:
                conditions.append("md.user_id = %s")
                params.append(user_filter)

            file_join = ""
            if file_type:
                file_join = "JOIN attach_master am ON am.mail_dtl_id = rd.mail_dtl_id"
                conditions.append("am.attach_type = %s")
                params.append(file_type)

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            query = f"""
                SELECT DISTINCT
                    rd.report_id,
                    md.mail_dtl_id,
                    DATE(md.date_time) AS created_date,
                    md.mail_from,
                    md.mail_to,
                    md.word_count,
                    rd.actual_effort_time,
                    rd.planned_effort_time,
                    rd.repeated_keyword_count,
                    cm.cat_id,
                    cm.cat_name,
                    rd.word_count AS attachment_word_count
                FROM report_data rd
                LEFT JOIN mail_details md ON md.mail_dtl_id = rd.mail_dtl_id
                LEFT JOIN category_master cm ON cm.cat_id = rd.cat_id
                {file_join}
                WHERE {where_clause}
                ORDER BY rd.report_id DESC
            """
            await self._log_and_execute(query, tuple(params))
            results = await self._cur.fetchall()

            count_query = f"""
                SELECT COUNT(DISTINCT rd.report_id) AS total
                FROM report_data rd
                LEFT JOIN mail_details md ON md.mail_dtl_id = rd.mail_dtl_id
                LEFT JOIN category_master cm ON cm.cat_id = rd.cat_id
                {file_join}
                WHERE {where_clause}
            """
            await self._log_and_execute(count_query, tuple(params))
            total_count = (await self._cur.fetchone())["total"]

            return results, total_count

        except Exception as e:
            logger.error(f"DB Error on get_report_data_by_date_userId: {e}")
            raise

    async def get_report_data_by_date_admin(
        self,
        from_date: date,
        to_date: date,
        user_id: int,
        org_id: int,
        filters: Dict[str, Optional[str]] = None,
    ) -> Tuple[List[Dict], int]:
        """
        Fetch report data for an admin with optional filters.
        """
        try:
            filters = filters or {}
            keyword = filters.get("keyword")
            category = filters.get("category")
            user_filter = filters.get("user")
            file_type = filters.get("file_type")

            params = [from_date, to_date, org_id]
            conditions = ["DATE(md.date_time) BETWEEN %s AND %s", "rd.org_id = %s"]

            if keyword:
                conditions.append("FIND_IN_SET(%s, rd.keywords_found)")
                params.append(keyword)

            if category:
                conditions.append("cm.cat_id = %s")
                params.append(category)

            if user_filter:
                conditions.append("md.user_id = %s")
                params.append(user_filter)

            file_join = ""
            if file_type:
                file_join = "JOIN attach_master am ON am.mail_dtl_id = rd.mail_dtl_id"
                conditions.append("am.attach_type = %s")
                params.append(file_type)

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            query = f"""
                SELECT DISTINCT
                    rd.report_id,
                    md.mail_dtl_id,
                    DATE(md.date_time) AS created_date,
                    md.mail_from,
                    md.mail_to,
                    md.word_count,
                    rd.actual_effort_time,
                    rd.planned_effort_time,
                    rd.repeated_keyword_count,
                    cm.cat_id,
                    cm.cat_name,
                    rd.word_count AS attachment_word_count
                FROM report_data rd
                INNER JOIN mail_details md ON md.mail_dtl_id = rd.mail_dtl_id
                LEFT JOIN category_master cm ON cm.cat_id = rd.cat_id
                {file_join}
                WHERE {where_clause}
                ORDER BY rd.report_id DESC
            """
            await self._log_and_execute(query, tuple(params))
            results = await self._cur.fetchall()

            count_query = f"""
                SELECT COUNT(DISTINCT rd.report_id) AS total
                FROM report_data rd
                LEFT JOIN mail_details md ON md.mail_dtl_id = rd.mail_dtl_id
                LEFT JOIN category_master cm ON cm.cat_id = rd.cat_id
                {file_join}
                WHERE {where_clause}
            """
            await self._log_and_execute(count_query, tuple(params))
            total_count = (await self._cur.fetchone())["total"]

            return results, total_count

        except Exception as e:
            logger.error(f"DB Error on get_report_data_by_date_admin: {e}")
            raise

    # async def get_report_data_by_date(
    #     self,
    #     from_date: date,
    #     to_date: date,
    #     folder_names: Optional[List[str]] = None,
    # ) -> Tuple[List[Dict[str, Union[str, int]]], int]:
    #     """
    #     Fetch report data with pagination by date range.
    #     """
    #     try:
    #         params = [from_date, to_date]
    #         folder_filter = ""
    #         if folder_names:
    #             folder_filter = "AND md.folder_name IN (%s)" % ",".join(
    #                 ["%s"] * len(folder_names)
    #             )
    #             params.extend(folder_names)

    #         query = f"""
    #             SELECT rd.report_id,
    #                 md.mail_dtl_id,
    #                 DATE(md.date_time) AS created_date,
    #                 md.mail_from,
    #                 md.mail_to,
    #                 md.word_count,
    #                 rd.actual_effort_time,
    #                 rd.planned_effort_time,
    #                 cm.cat_id,
    #                 cm.cat_name,
    #                 rd.repeated_keyword_count,
    #                 rd.word_count as attachment_word_count
    #             FROM report_data rd
    #             LEFT JOIN mail_details md ON md.mail_dtl_id = rd.mail_dtl_id
    #             LEFT JOIN category_master cm ON cm.cat_id = rd.cat_id
    #             WHERE DATE(md.date_time) BETWEEN %s AND %s
    #             {folder_filter}
    #             ORDER BY rd.report_id DESC
    #         """
    #         await self._log_and_execute(query, tuple(params))
    #         results = await self._cur.fetchall()

    #         # Count query
    #         count_query = f"""
    #             SELECT COUNT(DISTINCT rd.report_id) AS total
    #             FROM report_data rd
    #             LEFT JOIN mail_details md ON md.mail_dtl_id = rd.mail_dtl_id
    #             WHERE DATE(md.date_time) BETWEEN %s AND %s
    #             {folder_filter}
    #         """
    #         await self._log_and_execute(count_query, tuple(params[: len(params) - 2]))
    #         row = await self._cur.fetchone()
    #         total_count = row["total"] if row and "total" in row else 0

    #         return results or [], total_count

    #     except Exception as e:
    #         logger.error(f"DB Error on get_report_data_by_date: {e}")
    #         raise

    # async def get_report_data_by_date_userId(
    #     self,
    #     from_date: date,
    #     to_date: date,
    #     user_id: int,
    #     folder_names: Optional[List[str]] = None,
    # ) -> Tuple[List[Dict], int]:
    #     """
    #     Fetch report data with pagination for a specific user.
    #     """
    #     try:
    #         params = [from_date, to_date, user_id, user_id]
    #         folder_filter = ""
    #         if folder_names:
    #             folder_filter = "AND md.folder_name IN (%s)" % ",".join(
    #                 ["%s"] * len(folder_names)
    #             )
    #             params.extend(folder_names)

    #         query = f"""
    #             SELECT rd.report_id,
    #                 md.mail_dtl_id,
    #                 DATE(md.date_time) AS created_date,
    #                 md.mail_from,
    #                 md.mail_to,
    #                 md.word_count,
    #                 rd.actual_effort_time,
    #                 rd.planned_effort_time,
    #                 rd.repeated_keyword_count,
    #                 cm.cat_id,
    #                 cm.cat_name,
    #                 rd.word_count as attachment_word_count
    #             FROM report_data rd
    #             LEFT JOIN mail_details md ON md.mail_dtl_id = rd.mail_dtl_id
    #             LEFT JOIN category_master cm ON cm.cat_id = rd.cat_id
    #             WHERE DATE(md.date_time) BETWEEN %s AND %s
    #             AND (md.user_id = %s OR rd.created_by = %s)
    #             {folder_filter}
    #             ORDER BY rd.report_id DESC
    #         """
    #         await self._log_and_execute(query, tuple(params))
    #         results = await self._cur.fetchall()

    #         # Count query
    #         count_query = f"""
    #             SELECT COUNT(*) AS total
    #             FROM report_data rd
    #             LEFT JOIN mail_details md ON md.mail_dtl_id = rd.mail_dtl_id
    #             WHERE DATE(md.date_time) BETWEEN %s AND %s
    #             AND md.user_id = %s
    #             {folder_filter}
    #         """
    #         await self._log_and_execute(
    #             count_query,
    #             tuple(params[: 3 + len(folder_names) if folder_names else 3]),
    #         )
    #         total = (await self._cur.fetchone())["total"]

    #         return results, total

    #     except Exception as e:
    #         logger.error(f"DB Error on get_report_data_by_date_userId: {e}")
    #         raise

    # async def get_report_data_by_date_admin(
    #     self,
    #     from_date: date,
    #     to_date: date,
    #     user_id: int,
    #     org_id: int,
    #     folder_names: Optional[List[str]] = None,
    # ) -> Tuple[List[Dict], int]:
    #     """
    #     Fetch report data with pagination for a specific admin.
    #     """
    #     try:
    #         params = [from_date, to_date, org_id]
    #         folder_filter = ""
    #         if folder_names:
    #             folder_filter = "AND md.folder_name IN (%s)" % ",".join(
    #                 ["%s"] * len(folder_names)
    #             )
    #             params.extend(folder_names)

    #         query = f"""
    #             SELECT rd.report_id,
    #                 md.mail_dtl_id,
    #                 DATE(md.date_time) AS created_date,
    #                 md.mail_from,
    #                 md.mail_to,
    #                 md.word_count,
    #                 rd.actual_effort_time,
    #                 rd.planned_effort_time,
    #                 rd.repeated_keyword_count,
    #                 cm.cat_id,
    #                 cm.cat_name,
    #                 rd.word_count AS attachment_word_count
    #             FROM report_data rd
    #             INNER JOIN mail_details md ON md.mail_dtl_id = rd.mail_dtl_id
    #             LEFT JOIN category_master cm ON cm.cat_id = rd.cat_id
    #             WHERE DATE(md.date_time) BETWEEN %s AND %s
    #             AND rd.org_id = %s
    #             {folder_filter}
    #             ORDER BY rd.report_id DESC
    #         """
    #         await self._log_and_execute(query, tuple(params))
    #         results = await self._cur.fetchall()

    #         # Count query
    #         count_query = f"""
    #             SELECT COUNT(*) AS total
    #             FROM report_data rd
    #             LEFT JOIN mail_details md ON md.mail_dtl_id = rd.mail_dtl_id
    #             WHERE DATE(md.date_time) BETWEEN %s AND %s
    #             AND rd.org_id = %s
    #             {folder_filter}
    #         """
    #         await self._log_and_execute(
    #             count_query,
    #             tuple(params[: 3 + len(folder_names) if folder_names else 3]),
    #         )
    #         total = (await self._cur.fetchone())["total"]

    #         return results, total

    #     except Exception as e:
    #         logger.error(f"DB Error on get_report_data_by_date_admin: {e}")
    #         raise

    async def mail_id_exists(self, mail_dtl_id: str) -> bool:
        """
        Check if a mail with the given mail_dtl_id already exists.
        """
        query = (
            "SELECT 1 FROM report_data WHERE mail_dtl_id = %s and isActive = 1 LIMIT 1"
        )
        await self._log_and_execute(query, [mail_dtl_id])
        result = await self._cur.fetchone()
        return bool(result)

    async def fetch_mail_details_by_id(self, mail_dtl_id: int) -> List[Dict[str, Any]]:
        """
        Fetch mail details and attachment names by mail_dtl_id.
        """
        try:
            query = """
                SELECT
                    md.user_id,
                    md.mail_dtl_id,
                    md.subject,
                    md.body,
                    am.attach_name,
                    md.created_by 
                FROM mail_details md
                LEFT JOIN attach_master am ON am.mail_dtl_id = md.mail_dtl_id
                WHERE md.mail_dtl_id = %s
            """
            await self._log_and_execute(query, (mail_dtl_id,))
            rows = await self._cur.fetchall()
            return rows or []
        except Exception as e:
            logger.error(f"DB Error on fetch_mail_details_by_id: {e}")
            raise

    # -------------------- fetch meeting details by id(preview)--------------------
    async def fetch_meeting_details_by_id(self, cal_id: int) -> List[Dict[str, Any]]:
        """
        Fetch mail details and attachment names by cal_id.
        """
        try:
            query = """
                SELECT
                    cm.cal_id,
                    cm.user_id,
                    cm.title,
                    cm.description,
                    am.attach_name,
                    cm.created_by 
                FROM
                    cal_master cm
                LEFT JOIN attach_master am ON
                    am.cal_id  = cm.cal_id 
                WHERE cm.cal_id = %s
            """
            await self._log_and_execute(query, (cal_id,))
            rows = await self._cur.fetchall()
            return rows or []
        except Exception as e:
            logger.error(f"DB Error on fetch_meeting_details_by_id: {e}")
            raise

    async def get_attachments_by_mail_id(
        self, mail_dtl_id: int
    ) -> List[Dict[str, Any]]:
        query = """
            SELECT attach_id, mail_dtl_id, attach_name, attach_type, attach_path
            FROM attach_master
            WHERE mail_dtl_id = %s AND is_active = 1
        """
        await self._log_and_execute(query, (mail_dtl_id,))
        rows = await self._cur.fetchall()

        results = []
        for row in rows or []:
            record = dict(row)
            file_path = record.get("attach_path")
            if file_path:
                try:
                    async with aiofiles.open(file_path, "rb") as f:
                        record["content"] = await f.read()
                except Exception as e:
                    logger.error(
                        f"Error reading attachment {file_path} for mail {mail_dtl_id}: {str(e)}"
                    )
                    record["content"] = None
            results.append(record)
        return results

    async def get_attachment(
        self, mail_dtl_id: int, user_id: int, attachment_name: str
    ):
        query = """
            SELECT attach_name, attach_type, attach_path
            FROM attach_master
            WHERE mail_dtl_id = %s
            AND attach_name = %s
            AND is_active = 1
            LIMIT 1
        """
        await self._log_and_execute(query, (mail_dtl_id, attachment_name))
        return await self._cur.fetchone()

    # -------------------- Business Rules --------------------
    async def insert_rule(self, org_id: int, rule_key: str, rule_value: float) -> str:
        # Check if rule exists for this org
        query_check = """
            SELECT 1 FROM effort_estimation_rules
            WHERE org_id = %s AND rule_key = %s AND is_active = 1
            LIMIT 1
        """
        await self._log_and_execute(query_check, (org_id, rule_key))
        exists = await self._cur.fetchone()
        if exists:
            return f"Rule '{rule_key}' already exists for org {org_id}"  # Prevent duplicate

        # Insert new rule
        query_insert = """
            INSERT INTO effort_estimation_rules (org_id, rule_key, rule_value)
            VALUES (%s, %s, %s)
        """
        await self._log_and_execute(query_insert, (org_id, rule_key, rule_value))
        await self._cur.connection.commit()
        return f"Rule '{rule_key}' inserted successfully for org {org_id}"

    async def get_business_rules_by_org_id(self, org_id: int):
        """
        Fetch all business rules for a given org_id from DB.
        """
        query = """
                SELECT rule_id, rule_key, rule_value, org_id
                FROM effort_estimation_rules
                WHERE org_id = %s
                ORDER BY rule_id
            """
        await self._log_and_execute(query, (org_id,))
        rows = await self._cur.fetchall()
        return rows or []

    async def update_rule_value(self, rule_id: int, value: float, org_id: int) -> int:
        query = """
            UPDATE effort_estimation_rules
            SET rule_value = %s
            WHERE rule_id = %s
            AND org_id = %s
            AND is_active = 1
        """
        await self._cur.execute(query, (value, rule_id, org_id))
        await self._cur.connection.commit()
        return self._cur.rowcount  # returns number of affected rows

    # --------------------fetch meeting details by id--------------------
    async def fetch_meetings_by_user_id(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Fetch all meeting records for a given user_id.
        """
        try:
            query = """
                SELECT *
                FROM cal_master cm
                WHERE cm.user_id = %s
                AND cm.is_active = 1
                ORDER BY cm.event_start_datetime DESC
            """
            await self._log_and_execute(query, (user_id,))
            rows = await self._cur.fetchall()
            return [dict(row) for row in rows] if rows else []
        except Exception as e:
            logger.error(f"DB Error on fetch_meetings_by_user_id: {e}")
            raise

    # --------------------check meeting id exist--------------------
    async def meeting_id_exists(self, cal_id: int) -> bool:
        """
        Check if a meeting effort already exists for given cal_id.
        """
        try:
            query = "SELECT 1 FROM meeting_report_data WHERE cal_id = %s LIMIT 1"
            await self._log_and_execute(query, (cal_id,))
            row = await self._cur.fetchone()
            return bool(row)
        except Exception as e:
            logger.error(f"DB Error on meeting_id_exists: {e}")
            raise

    # -------------------- Meeting Data --------------------
    async def fetch_meeting_data(
        self,
        org_id: int | None,
        from_date: Union[date, str, None],
        to_date: Union[date, str, None],
        user_id: int | None,
        limit: int | None = None,
        offset: int | None = None,
        is_admin: bool = False,
        user: str | None = None,  # this is the frontend search filter
    ) -> Tuple[List[Dict], int]:
        try:
            base_query = """
                SELECT 
                    mrd.meeting_report_id,
                    cm.cal_id,
                    cm.user_id,
                    cm.created_by,
                    cm.organiser,
                    cm.attendees,
                    mrd.meeting_duration,
                    mrd.efforts_time,
                    DATE(cm.event_start_datetime) as event_start_datetime,
                    CASE WHEN cm.user_id = cm.created_by THEN 1 ELSE 0 END AS same_flag
                FROM cal_master cm
                JOIN meeting_report_data mrd ON mrd.cal_id = cm.cal_id
                WHERE mrd.org_id = %s
                AND DATE(cm.event_start_datetime) BETWEEN %s AND %s
                AND cm.is_active = 1
            """

            count_query = """
                SELECT COUNT(DISTINCT mrd.meeting_report_id) as total
                FROM meeting_report_data mrd
                LEFT JOIN cal_master cm ON cm.cal_id = mrd.cal_id
                WHERE mrd.org_id = %s
                AND DATE(cm.event_start_datetime) BETWEEN %s AND %s
                AND cm.is_active = 1
            """

            params = [org_id, from_date, to_date]
            count_params = [org_id, from_date, to_date]

            # Logged-in user restriction if not admin
            if not is_admin and user_id is not None:
                base_query += " AND (cm.user_id = %s OR cm.created_by = %s)"
                count_query += " AND (cm.user_id = %s OR cm.created_by = %s)"
                params.extend([user_id, user_id])
                count_params.extend([user_id, user_id])

            # Apply frontend search filter only if provided
            if user:  # if user search value exists
                base_query += " AND cm.user_id = %s"
                count_query += " AND cm.user_id = %s"
                params.append(user)
                count_params.append(user)

            base_query += """
                GROUP BY cm.cal_id, cm.user_id, cm.created_by, cm.organiser, cm.attendees,
                        mrd.meeting_duration, DATE(cm.event_start_datetime),
                        mrd.meeting_report_id
                ORDER BY mrd.meeting_report_id DESC
            """

            # Execute queries
            await self._log_and_execute(base_query, tuple(params))
            results = await self._cur.fetchall()

            await self._log_and_execute(count_query, tuple(count_params))
            row = await self._cur.fetchone()
            total = row["total"] if row else 0

            return results, total

        except Exception as e:
            logger.error(f"DB Error on fetch_meeting_data: {e}")
            raise

    # -------------------- Fetch Entity Types --------------------
    async def get_all_entity_types(self):
        query = """
            SELECT entity_id, entity_name
            FROM entity_master
            WHERE is_active = 1
            ORDER BY entity_name
        """
        await self._cur.execute(query)
        return await self._cur.fetchall()

    # -------------------- Update Meeting Report Data --------------------
    async def update_meeting_effort(
        self,
        meeting_report_id: int,
        efforts: Optional[float] = None,
    ) -> None:
        fields, params = [], []

        if efforts is not None:
            fields.append("efforts_time = %s")
            params.append(efforts)

        if not fields:
            return  # nothing to update

        query = f"""
            UPDATE meeting_report_data
            SET {", ".join(fields)}
            WHERE meeting_report_id = %s
            AND is_active = 1
        """
        params.append(meeting_report_id)

        await self._log_and_execute(query, tuple(params))
        await self._cur.connection.commit()

    # -------------------- Fetch All Active Categories --------------------
    async def get_all_active_categories(self, org_id: int) -> List[Dict]:
        """
        Fetch all active categories for a given org dynamically.
        """
        try:
            query = """
                SELECT cat_id, cat_name, priority
                FROM category_master
                WHERE is_active = 1 AND org_id = %s
                ORDER BY cat_id
            """
            await self._log_and_execute(query, (org_id,))
            categories = await self._cur.fetchall()
            return categories or []
        except Exception as e:
            logger.error(f"DB Error in get_all_active_categories: {e}")
            raise

    # ---------------------fetch Folder for filter data----------------
    async def fetch_folders_name(self) -> List[str]:
        query = """
            SELECT DISTINCT folder_name
            FROM mail_details
            WHERE is_active = 1 AND folder_name IS NOT NULL
            ORDER BY folder_name
        """
        await self._log_and_execute(query)
        rows = await self._cur.fetchall()
        return [
            {"id": row["folder_name"], "name": row["folder_name"]}
            for row in rows
            if row["folder_name"]
        ]

    # ---------------------Fetch all reports for recalculation-------------------------
    async def get_all_reports(self, org_id: int, user_id: Optional[int] = None):
        """
        Fetch all report rows to recalc effort.
        Returns list of dicts with at least: report_id, mail_dtl_id, body
        """
        query = """
            SELECT rd.report_id, rd.mail_dtl_id, md.body
            FROM report_data rd
            LEFT JOIN mail_details md ON md.mail_dtl_id = rd.mail_dtl_id
            WHERE rd.org_id = %s
        """
        params = [org_id]

        result = await self._log_and_fetch_all(query, *params)
        return [dict(row) for row in result] if result else []

    # ----------------------Update only effort fields------------------------
    async def update_report_efforts_only(
        self, report_id: int, actual_effort_time: float, planned_effort_time: float
    ):
        """
        Update only actual_effort_time and planned_effort_time in report_data.
        """
        query = """
            UPDATE report_data
            SET actual_effort_time = %s,
                planned_effort_time = %s,
                updated_date = NOW()
            WHERE report_id = %s
        """
        await self._log_and_execute(
            query, (actual_effort_time, planned_effort_time, report_id)
        )
        await self._cur.connection.commit()

    # --------------------- Fetch Keywords List ------------------------
    async def fetch_keywords_list(self, org_id: int) -> List[str]:
        query = """
            SELECT keyword_id, keyword_name 
            FROM keyword_master 
            WHERE org_id = %s AND is_active = 1
            ORDER BY keyword_name ASC
        """
        try:
            await self._log_and_execute(query, (org_id,))
            rows = await self._cur.fetchall()
            return [
                {"id": row["keyword_id"], "name": row["keyword_name"]}
                for row in rows
                if row["keyword_name"]
            ]
        except Exception as e:
            logger.error(f"Error fetching keywords for org_id {org_id}: {str(e)}")
            return []

    # --------------------- Fetch Categories List ------------------------
    async def fetch_category_list(self, org_id: int) -> List[str]:
        query = """
            SELECT cat_id, cat_name 
            FROM category_master 
            WHERE org_id = %s AND is_active = 1
            ORDER BY cat_name ASC;
        """
        try:
            await self._log_and_execute(query, (org_id,))
            rows = await self._cur.fetchall()
            return [
                {"id": row["cat_id"], "name": row["cat_name"]}
                for row in rows
                if row["cat_name"]
            ]
        except Exception as e:
            logger.error(f"Error fetching categories for org_id {org_id}: {str(e)}")
            return []

    # --------------------- Fetch Users List ------------------------
    async def fetch_users_list(self, org_id: int, role_id:int) -> List[str]:
        query = """
            SELECT user_id, user_name 
            FROM users_master 
            WHERE org_id = %s AND role_id = 2 AND is_active = 1
            ORDER BY user_name ASC;
        """
        try:
            await self._log_and_execute(query, (org_id))
            rows = await self._cur.fetchall()
            return [
                {"id": row["user_id"], "name": row["user_name"]}
                for row in rows
                if row["user_name"]
            ]
        except Exception as e:
            logger.error(f"Error fetching users for org_id {org_id}: {str(e)}")
            return []

    # --------------------- Fetch File Type List ------------------------
    async def fetch_fileType_list(self) -> List[str]:
        query = "SELECT DISTINCT attach_type FROM attach_master WHERE is_active = 1 ORDER BY attach_type ASC"
        try:
            await self._log_and_execute(query)
            rows = await self._cur.fetchall()
            return [
                {
                    "id": row["attach_type"],
                    "name": FILE_TYPE_LABELS.get(
                        row["attach_type"], row["attach_type"]
                    ),
                }
                for row in rows
                if row["attach_type"]
            ]
        except Exception as e:
            logger.error(f"Error fetching file types: {str(e)}")
            return []
