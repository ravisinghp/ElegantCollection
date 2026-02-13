from datetime import datetime
from app.utils.date_utils import working_days_between

class EscalationRepository:
    def __init__(self, cur):
        self._cur = cur

    async def _get_reports_with_escalation(self, table_name: str, report_type: str):
        # Fetch reports
        query = f"""
            SELECT *
            FROM {table_name}
            WHERE active = 1
              AND created_on IS NOT NULL
        """
        await self._cur.execute(query)
        rows = await self._cur.fetchall()

        # Fetch escalation rules
        escalation_rules = await self.get_escalation_rules(report_type)

        holidays = await self.get_holidays()
        now = datetime.now()

        escalated_reports = []

        for row in rows:
            updated_on = row.get("updated_on") or now
            working_days = working_days_between(
                row["created_on"], updated_on, holidays
            )

            # Determine escalation level dynamically
            for rule in escalation_rules:
                if working_days >= rule["threshold_working_days"]:
                    escalated_reports.append({
                        **row,
                        "escalation_level": rule["escalation_level"],
                        "recipient_role": rule["recipient_role"],
                        "working_days": working_days
                    })

        return escalated_reports

    #  ADD THESE METHODS RIGHT HERE 
    async def get_missing_reports(self):
        return await self._get_reports_with_escalation(
            "po_missing_report",
            "MISSING_PO"
        )

    async def get_mismatch_reports(self):
        return await self._get_reports_with_escalation(
            "po_mismatch_report",
            "MISMATCH_PO"
        )
    
    

    # supporting DB methods (should already exist)
    async def get_escalation_rules(self, report_type: str):
        query = """
            SELECT escalation_level,
                   threshold_working_days,
                   recipient_role
            FROM escalation_matrix
            WHERE report_type = %s
              AND is_active = 1
            ORDER BY threshold_working_days ASC
        """
        await self._cur.execute(query, (report_type,))
        return await self._cur.fetchall()

    async def get_holidays(self):
        query = "SELECT holiday_date FROM holiday_calendar"
        await self._cur.execute(query)
        rows = await self._cur.fetchall()
        return [row["holiday_date"] for row in rows]
    

    async def get_user_emails(self, user_ids: list[int]):
        if not user_ids:
            return []

        placeholders = ",".join(["%s"] * len(user_ids))
        query = f"""
            SELECT DISTINCT mail_id
            FROM users_master
            WHERE user_id IN ({placeholders})
            AND mail_id IS NOT NULL
        """

        await self._cur.execute(query, user_ids)
        rows = await self._cur.fetchall()

        return [row["mail_id"] for row in rows]
    
    # to insert in DB-----------------------------------------------------------------------------------
    
    async def insert_escalation_log(
    self,
    report_id: int,
    report_type: str,
    escalation_level: int,
    escalated_to_role: str,
    escalated_to_email: str,
    created_by: int,
    mail_sent: int
):
        query = """
            INSERT INTO escalation_log
            (
                report_id,
                report_type,
                escalation_level,
                escalated_to_role,
                escalated_to_email,
                escalated_at,
                created_by,
                created_on,
                mail_sent,
                active
            )
            VALUES
            (
                %s, %s, %s, %s, %s,
                NOW(),
                %s,
                NOW(),
                %s,
                1
            )
        """
        await self._cur.execute(
            query,
            (
                report_id,
                report_type,
                escalation_level,
                escalated_to_role,
                escalated_to_email,
                created_by,
                mail_sent
            )
        )


