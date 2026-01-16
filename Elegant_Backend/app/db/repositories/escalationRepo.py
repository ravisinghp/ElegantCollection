# from datetime import datetime
# from sqlalchemy import text


# class EscalationRepository:
#     def __init__(self, cur):
#         self._cur = cur

#     async def get_reports_for_escalation(self, report_type: str):
#         """
#         DB-driven escalation logic:
#         - Working days only (Mon–Fri)
#         - Excludes holidays
#         - created_on → now
#         - updated_on unchanged
#         - is_active = 1
#         - No duplicate escalation
#         """

#         table_name = (
#             "po_missing_report"
#             if report_type == "MISSING_PO"
#             else "po_mismatch_report"
#         )

#         query = text(f"""
#             SELECT
#                 r.id AS report_id,
#                 em.escalation_level,
#                 em.recipient_role
#             FROM {table_name} r
#             JOIN escalation_matrix em
#                 ON em.report_type = :report_type
#                AND em.is_active = 1
#             LEFT JOIN escalation_log el
#                 ON el.report_id = r.id
#                AND el.report_type = :report_type
#                AND el.escalation_level = em.escalation_level
#             WHERE
#                 r.is_active = 1
#                 AND r.updated_on = r.created_on
#                 AND el.escalation_log_id IS NULL
#                 AND (
#                     SELECT COUNT(*)
#                     FROM (
#                         SELECT DATE_ADD(r.created_on, INTERVAL n DAY) AS d
#                         FROM (
#                             SELECT a.N + b.N * 10 + c.N * 100 AS n
#                             FROM
#                                 (SELECT 0 N UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
#                                  UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) a,
#                                 (SELECT 0 N UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
#                                  UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) b,
#                                 (SELECT 0 N UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
#                                  UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) c
#                         ) numbers
#                         WHERE DATE_ADD(r.created_on, INTERVAL n DAY) <= CURDATE()
#                     ) days
#                     WHERE
#                         WEEKDAY(d) < 5
#                         AND d NOT IN (SELECT holiday_date FROM holiday_calendar)
#                 ) >= em.threshold_working_days
#         """)

#         result = await self._cur.execute(
#             query,
#             {"report_type": report_type}
#         )

#         return result.fetchall()

#     async def get_recipient_email(self, role: str):
#         query = text("""
#             SELECT email
#             FROM users
#             WHERE role = :role
#               AND is_active = 1
#             LIMIT 1
#         """)

#         result = await self._cur.execute(query, {"role": role})
#         row = result.fetchone()
#         return row.email if row else None

#     async def log_escalation(
#         self,
#         report_id: int,
#         report_type: str,
#         escalation_level: int,
#         role: str,
#         email: str
#     ):
#         query = text("""
#             INSERT INTO escalation_log (
#                 report_id,
#                 report_type,
#                 escalation_level,
#                 escalated_to_role,
#                 escalated_to_email,
#                 escalated_at
#             )
#             VALUES (
#                 :report_id,
#                 :report_type,
#                 :level,
#                 :role,
#                 :email,
#                 NOW()
#             )
#         """)

#         await self._cur.execute(
#             query,
#             {
#                 "report_id": report_id,
#                 "report_type": report_type,
#                 "level": escalation_level,
#                 "role": role,
#                 "email": email
#             }
#         )
#         await self._cur.commit()


# mansi 
# -------------------------------------------------------------------------------------------------------- option 2
# class EscalationRepository:
#     def __init__(self, cur):
#         self._cur = cur

#     async def get_reports_for_escalation(self, report_type: str):
#         report_type = report_type.lower()

#         if report_type == "missing":
#             table_name = "po_missing_report"
#         elif report_type == "mismatch":
#             table_name = "po_mismatch_report"
#         else:
#             raise ValueError("Invalid report_type")

#         query = f"""
#         SELECT
#     r.created_on,
#     r.updated_on,
#     r.active,
#     em.escalation_level,
#     em.recipient_role
# FROM {table_name} AS r
# JOIN escalation_matrix em
#     ON em.report_type = %s
#    AND em.is_active = 1
# WHERE
#     r.active = 1
#     AND r.created_on IS NOT NULL
#     AND r.updated_on IS NULL
#     AND (
#         SELECT COUNT(*)
#         FROM (
#             SELECT DATE_ADD(r.created_on, INTERVAL n DAY) AS d
#             FROM (
#                 SELECT a.N + b.N * 10 + c.N * 100 AS n
#                 FROM
#                     (SELECT 0 N UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
#                      UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) a,
#                     (SELECT 0 N UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
#                      UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) b,
#                     (SELECT 0 N UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
#                      UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) c
#             ) numbers
#             WHERE DATE_ADD(r.created_on, INTERVAL n DAY) <= CURDATE()
#         ) days
#         WHERE
#             WEEKDAY(d) < 5
#             AND d NOT IN (SELECT holiday_date FROM holiday_calendar)
#     ) >= em.threshold_working_days
#         """

#         await self._cur.execute(query, (report_type,))
#         return await self._cur.fetchall()


#     async def is_escalation_already_sent(
#         self,
#         report_type: str,
#         escalation_level: int,
#         role: str
#     ):
#         query = """
#             SELECT 1
#             FROM escalation_log
#             WHERE report_type = %s
#             AND escalation_level = %s
#             AND escalated_to_role = %s
#             LIMIT 1
#         """
#         await self._cur.execute(
#             query,
#             (report_type, escalation_level, role)
#         )
#         return await self._cur.fetchone() is not None

#     async def log_escalation(
#         self,
#         report_type: str,
#         escalation_level: int,
#         role: str,
#         email: str
#     ):
#         query = """
#             INSERT INTO escalation_log (
#                 report_type,
#                 escalation_level,
#                 escalated_to_role,
#                 escalated_to_email,
#                 escalated_at
#             )
#             VALUES (%s, %s, %s, %s, NOW())
#         """

#         await self._cur.execute(
#             query,
#             (report_type, escalation_level, role, email)
#     )


class EscalationRepository:
    def __init__(self, cur):
        self._cur = cur

    async def get_missing_reports(self):
        query = """
            SELECT *, 'missing' AS report_type
            FROM po_missing_report
            WHERE active = 1
              AND created_on IS NOT NULL
              AND updated_on IS NULL
        """
        await self._cur.execute(query)
        return await self._cur.fetchall()

    async def get_mismatch_reports(self):
        query = """
            SELECT *, 'mismatch' AS report_type
            FROM po_mismatch_report
            WHERE active = 1
              AND created_on IS NOT NULL
              AND updated_on IS NULL
        """
        await self._cur.execute(query)
        return await self._cur.fetchall()

