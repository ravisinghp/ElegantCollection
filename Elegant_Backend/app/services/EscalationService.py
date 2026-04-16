import os
from collections import defaultdict
from app.utils.email_sender import send_employee_email

class EscalationService:
    def __init__(self, repo):
        self.repo = repo
        self.admin_email = os.getenv("ADMIN_EMAIL") 

    async def run_escalation(self):
        missing = await self.repo.get_missing_reports()
        mismatch = await self.repo.get_mismatch_reports()

        #-----------Send mail------------
        # self._send_emails(missing, mismatch)
        await self._send_emails(missing, mismatch)

        return {
            "missing": self._group_by_user(missing),
            "mismatch": self._group_by_user(mismatch)
        }

    def _group_by_user(self, reports: list):
        grouped = defaultdict(list)
        for report in reports:
            grouped[report["user_id"]].append(report)
        return dict(grouped)


    async def _send_emails(self, missing, mismatch):
        EMPLOYEE_DAYS = 3
        SYSTEM_USER_ID = 1  # system / scheduler user

        # Group records by user (only valid SLA breaches)
        missing_by_user = self._group_by_user(
            [r for r in missing if r.get("working_days") == EMPLOYEE_DAYS]
        )
        mismatch_by_user = self._group_by_user(
            [r for r in mismatch if r.get("working_days") == EMPLOYEE_DAYS]
        )

        user_ids = set(missing_by_user.keys()) | set(mismatch_by_user.keys())
        if not user_ids:
            return

        # Fetch user emails
        user_emails = await self.repo.get_user_emails(list(user_ids))
        email_map = dict(zip(user_ids, user_emails))

        # Send ONE mail per user
        for user_id in user_ids:
            email = email_map.get(user_id)
            if not email:
                continue

            body = (
                "Dear User,\n\n"
                "This is an automated escalation notification.\n"
                "The following Purchase Order (PO) reports assigned to you were not "
                "actioned within the defined SLA and have been escalated for your "
                "immediate attention.\n\n"
                "--------------------------------------------------\n\n"
            )

            #  MISSING PO (only if exists)
            if user_id in missing_by_user:
                body += "MISSING PURCHASE ORDERS\n"
                for r in missing_by_user[user_id]:
                    body += (
                        f"PO ID: {r['po_missing_id']} | "
                        f"Pending: {r['working_days']} working days\n"
                    )
                body += "\n"

            #  MISMATCH PO (ONLY IF EXISTS)
            if user_id in mismatch_by_user:
                body += "MISMATCH PURCHASE ORDERS\n"
                for r in mismatch_by_user[user_id]:
                    body += (
                        f"PO ID: {r['po_mismatch_id']} | "
                        f"Pending: {r['working_days']} working days\n"
                    )
                body += "\n"

            body += (
                "--------------------------------------------------\n\n"
                "If you have already addressed any of these items, please ignore this message.\n\n"
                "Regards,\n"
                "PO Escalation System\n"
                "(This is a system-generated email. Please do not reply.)"
            )

            # Send email
            try:
                send_employee_email(
                    subject="Action Required: PO Escalation",
                    body=body,
                    recipients=[email]
                )
                mail_sent = 1
            except Exception:
                mail_sent = 0

            # Log escalations
            for r in missing_by_user.get(user_id, []):
                await self.repo.insert_escalation_log(
                    report_id=r["po_missing_id"],
                    report_type="MISSING_PO",
                    escalation_level=r["escalation_level"],
                    escalated_to_role=r["recipient_role"],
                    escalated_to_email=email,
                    created_by=SYSTEM_USER_ID,
                    mail_sent=mail_sent
                )

            for r in mismatch_by_user.get(user_id, []):
                await self.repo.insert_escalation_log(
                    report_id=r["po_mismatch_id"],
                    report_type="MISMATCH_PO",
                    escalation_level=r["escalation_level"],
                    escalated_to_role=r["recipient_role"],
                    escalated_to_email=email,
                    created_by=SYSTEM_USER_ID,
                    mail_sent=mail_sent
                )

        # ================= ADMIN ESCALATION (5+ DAYS OR DB ROLE) =================
        admin_missing = [
            r for r in missing
            if r.get("working_days", 0) >= 5 or r.get("recipient_role") == "ADMIN"
        ]

        admin_mismatch = [
            r for r in mismatch
            if r.get("working_days", 0) >= 5 or r.get("recipient_role") == "ADMIN"
        ]

        if (admin_missing or admin_mismatch) and self.admin_email:

            body = (
                "Dear Admin,\n\n"
                "The following Purchase Orders have crossed SLA and require attention.\n\n"
                "--------------------------------------------------\n\n"
            )

            if admin_missing:
                body += "MISSING PURCHASE ORDERS\n"
                for r in admin_missing:
                    body += (
                        f"PO Number: {r.get('po_number', 'N/A')} | "
                        f"Pending: {r['working_days']} working days\n"
                    )
                body += "\n"

            if admin_mismatch:
                body += "MISMATCH PURCHASE ORDERS\n"
                for r in admin_mismatch:
                    body += (
                        f"PO Number: {r.get('po_number', 'N/A')} | "
                        f"Pending: {r['working_days']} working days\n"
                    )
                body += "\n"

            body += (
                "--------------------------------------------------\n\n"
                "Regards,\nPO Escalation System"
            )

            try:
                send_employee_email(
                    subject="URGENT: Admin Escalation - PO Pending Beyond SLA",
                    body=body,
                    recipients=[self.admin_email]
                )
            except Exception:
                pass