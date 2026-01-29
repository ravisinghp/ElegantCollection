
from collections import defaultdict
from app.utils.email_sender import send_employee_email

class EscalationService:
    def __init__(self, repo):
        self.repo = repo

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


# for ignore --------------------------------------------------------------------------------------

    # def _send_emails(self, missing, mismatch):
    #     EMPLOYEE_DAYS = 3
    #     has_valid_data = False

    #     body = "ESCALATION REPORT\n\n"

    #     if missing:
    #         body += "MISSING PO\n"
    #         for r in missing:
    #             if r.get("working_days") != EMPLOYEE_DAYS:
    #                 continue

    #             has_valid_data = True   # MARK VALID DATA
    #             body += (
    #                 f"User ID: {r['user_id']} | "
    #                 f"Level: {r['escalation_level']} | "
    #                 f"Working Days: {r['working_days']}\n"
    #             )

    #     if mismatch:
    #         body += "\n MISMATCH PO\n"
    #         for r in mismatch:
    #             if r.get("working_days") != EMPLOYEE_DAYS:
    #                 continue

    #             has_valid_data = True   #  MARK VALID DATA
    #             body += (
    #                 f"User ID: {r['user_id']} | "
    #                 f"Level: {r['escalation_level']} | "
    #                 f"Working Days: {r['working_days']}\n"
    #             )

    #     #  NO VALID RECORD → NO EMAIL
    #     if not has_valid_data:
    #         return

    #     send_employee_email(
    #         subject="PO Escalation Alert",
    #         body=body
    #     )

   

# fixed the email are send group by  this is working proper
# ----------------------------------------------------------------------
    # async def _send_emails(self, missing, mismatch):
    #     EMPLOYEE_DAYS = 3

    #     #  Group records by user
    #     missing_by_user = self._group_by_user(
    #         [r for r in missing if r.get("working_days") == EMPLOYEE_DAYS]
    #     )
    #     mismatch_by_user = self._group_by_user(
    #         [r for r in mismatch if r.get("working_days") == EMPLOYEE_DAYS]
    #     )

    #     # All users involved
    #     user_ids = set(missing_by_user.keys()) | set(mismatch_by_user.keys())

    #     if not user_ids:
    #         return

    #     #  Fetch emails
    #     user_emails = await self.repo.get_user_emails(list(user_ids))
    #     email_map = dict(zip(user_ids, user_emails))  # user_id → email

    #     #  Send ONE MAIL PER USER
    #     for user_id in user_ids:
    #         email = email_map.get(user_id)
    #         if not email:
    #             continue

    #         body = "ESCALATION REPORT\n\n"

    #         if user_id in missing_by_user:
    #             body += " MISSING PO\n"
    #             for r in missing_by_user[user_id]:
    #                 body += (
    #                     f"PO ID: {r.get('po_missing_id')} | "
    #                     f"Level: {r['escalation_level']} | "
    #                     f"Working Days: {r['working_days']}\n"
    #                 )

    #         if user_id in mismatch_by_user:
    #             body += "\n MISMATCH PO\n"
    #             for r in mismatch_by_user[user_id]:
    #                 body += (
    #                     f"PO ID: {r.get('po_mismatch_id')} | "
    #                     f"Level: {r['escalation_level']} | "
    #                     f"Working Days: {r['working_days']}\n"
    #                 )

    #         send_employee_email(
    #             subject="PO Escalation Alert",
    #             body=body,
    #             recipients=[email]   # ONLY THIS USER
    #         )

    # async def _send_emails(self, missing, mismatch):
    #     EMPLOYEE_DAYS = 3
    #     SYSTEM_USER_ID = 1  # system / scheduler user

    #     # Group records by user
    #     missing_by_user = self._group_by_user(
    #         [r for r in missing if r.get("working_days") == EMPLOYEE_DAYS]
    #     )
    #     mismatch_by_user = self._group_by_user(
    #         [r for r in mismatch if r.get("working_days") == EMPLOYEE_DAYS]
    #     )

    #     user_ids = set(missing_by_user.keys()) | set(mismatch_by_user.keys())
    #     if not user_ids:
    #         return

    #     # Fetch emails
    #     user_emails = await self.repo.get_user_emails(list(user_ids))
    #     email_map = dict(zip(user_ids, user_emails))

    #     # ONE MAIL PER USER
    #     for user_id in user_ids:
    #         email = email_map.get(user_id)
    #         if not email:
    #             continue

    #         body = "ESCALATION REPORT\n\n"

    #         if user_id in missing_by_user:
    #             body += " MISSING PO\n"
    #             for r in missing_by_user[user_id]:
    #                 body += (
    #                     f"PO ID: {r.get('po_missing_id')} | "
    #                     f"Level: {r['escalation_level']} | "
    #                     f"Working Days: {r['working_days']}\n"
    #                 )

    #         if user_id in mismatch_by_user:
    #             body += "\n MISMATCH PO\n"
    #             for r in mismatch_by_user[user_id]:
    #                 body += (
    #                     f"PO ID: {r.get('po_mismatch_id')} | "
    #                     f"Level: {r['escalation_level']} | "
    #                     f"Working Days: {r['working_days']}\n"
    #                 )

    #         # SEND MAIL (TRY / EXCEPT HERE 👇)
    #         try:
    #             send_employee_email(
    #                 subject="PO Escalation Alert",
    #                 body=body,
    #                 recipients=[email]
    #             )
    #             mail_sent = 1
    #             mail_error = None
    #         except Exception as e:
    #             mail_sent = 0
    #             mail_error = str(e)

    #         # LOG EACH ESCALATED REPORT (DB)
    #         for r in missing_by_user.get(user_id, []):
    #             await self.repo.insert_escalation_log(
    #                 report_id=r["po_missing_id"],
    #                 report_type="MISSING_PO",
    #                 escalation_level=r["escalation_level"],
    #                 escalated_to_role=r["recipient_role"],
    #                 escalated_to_email=email,
    #                 created_by=SYSTEM_USER_ID,
    #                 mail_sent=mail_sent
    #             )

    #         for r in mismatch_by_user.get(user_id, []):
    #             await self.repo.insert_escalation_log(
    #                 report_id=r["po_mismatch_id"],
    #                 report_type="MISMATCH_PO",
    #                 escalation_level=r["escalation_level"],
    #                 escalated_to_role=r["recipient_role"],
    #                 escalated_to_email=email,
    #                 created_by=SYSTEM_USER_ID,
    #                 mail_sent=mail_sent
    #             )

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

