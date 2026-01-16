# from datetime import datetime
# from app.db.repositories.escalationRepo import EscalationRepository
# # from app.utils.email_sender import send_email


# class EscalationService:
#     def __init__(self, repo: EscalationRepository):
#         self.repo = repo

#     async def run_escalation(self, report_type: str):
#         """
#         Run escalation fully DB-driven.
#         """

#         escalations = await self.repo.get_reports_for_escalation(report_type)

#         for row in escalations:
#             report_id = row.report_id
#             level = row.escalation_level
#             role = row.recipient_role

#             email = await self.repo.get_recipient_email(role)
#             if not email:
#                 continue

#             # Send mail ONLY at 8 AM
#             if datetime.now().hour == 8:
#                 pass
#                 # send_email(
#                 #     email,
#                 #     subject=f"{report_type} escalation alert",
#                 #     body=f"Report {report_id} has no response."
#                 # )

#             await self.repo.log_escalation(
#                 report_id=report_id,
#                 report_type=report_type,
#                 escalation_level=level,
#                 role=role,
#                 email=email
#             )



# mansi option 2
# -----------------------------------------------------------------


# from datetime import datetime
# from app.db.repositories.escalationRepo import EscalationRepository
# # from app.utils.email_sender import send_email


# class EscalationService:
#     def __init__(self, repo: EscalationRepository):
#         self.repo = repo

#     async def run_escalation(self, report_type: str):
#         report_type = report_type.lower()

#         if report_type not in ("missing", "mismatch"):
#             raise ValueError("Invalid report_type")
        
#         results = []

#         escalations = await self.repo.get_reports_for_escalation(report_type)

#         for row in escalations:
#             # report_id = row.report_id
#             # level = row.escalation_level
#             # role = row.recipient_role
#             report_id = row["report_id"]
#             level = row["escalation_level"]
#             role = row["recipient_role"]


#             if await self.repo.is_escalation_already_sent(
#                 report_id,
#                 report_type,
#                 level,
#                 role
#             ):
#                 continue

#             email = await self.repo.get_recipient_email(role)
#             if not email:
#                 continue

          
#             # 📧 Send email (enable later)
#             # send_email(
#             #     to=email,
#             #     subject=f"{report_type.upper()} escalation alert",
#             #     body=f"Report ID {report_id} has no response at level {level}"
#             # )

#             await self.repo.log_escalation(
#                 report_id=report_id,
#                 report_type=report_type,
#                 escalation_level=level,
#                 role=role,
#                 email=email,
#                 sent_on=datetime.utcnow()
#             )

#             results.append({
#             "report_id": report_id,
#             "level": level,
#             "role": role,
#             "email": email
#         })
            
#         return results


from datetime import datetime
from app.db.repositories.escalationRepo import EscalationRepository
# from app.utils.email_sender import send_email

class EscalationService:
    def __init__(self, repo: EscalationRepository):
        self.repo = repo

    async def run_escalation(self):
        missing = await self.repo.get_missing_reports()
        mismatch = await self.repo.get_mismatch_reports()

        return {
            "missing": missing,
            "mismatch": mismatch
        }

