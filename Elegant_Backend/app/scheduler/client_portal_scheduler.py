from apscheduler.schedulers.background import BackgroundScheduler
from app.db.repositories import UserRepo
import asyncio
from fastapi import Request
from app.db.repositories.mails import MailsRepository
from asyncmy.cursors import DictCursor
from loguru import logger
from app.core.websocket_manager import manager
from app.services import usersmailservice
from app.core.config import CLIENT_SCHEDULER_HOUR, CLIENT_SCHEDULER_MINUTE

scheduler = BackgroundScheduler()


class client_portal_scheduler:
    app = None
    loop = None

    # =====================================================================
    # -------------------- Bridge: APScheduler → Async --------------------
    # =====================================================================
    @staticmethod
    def job_wrapper():
        try:
            fake_request = create_scheduler_request(client_portal_scheduler.app)
            asyncio.run_coroutine_threadsafe(
                client_portal_scheduler.run_job(fake_request),
                client_portal_scheduler.loop
            )
        except Exception as e:
            logger.exception(f"[CLIENT_SCHEDULER] job_wrapper failed to dispatch: {e}")
    
    # =============================================================== 
    # -------------------- Register the cron job --------------------
    # ===============================================================
    @staticmethod
    def configure(app, loop):
        try:
            client_portal_scheduler.app = app
            client_portal_scheduler.loop = loop

            scheduler.add_job(
                client_portal_scheduler.job_wrapper,
                trigger="cron",
                hour=CLIENT_SCHEDULER_HOUR,      # ← from .env
                minute=CLIENT_SCHEDULER_MINUTE,  # ← from .env
                id="client_portal_daily_job",
                replace_existing=True,
            )

            if not scheduler.running:
                scheduler.start()

            logger.info(f"[CLIENT_SCHEDULER] Registered — runs daily at " f"{CLIENT_SCHEDULER_HOUR:02d}:{CLIENT_SCHEDULER_MINUTE:02d}")

        except Exception as e:
            logger.exception(f"[CLIENT_SCHEDULER] Failed to configure scheduler: {e}")
            raise

    # ================================================================
    # -------------------- Core Job Logic ----------------------------
    # ================================================================
    @staticmethod
    async def run_job(request: Request):
        logger.info("[CLIENT_SCHEDULER] Job triggered")

        # ── Enrich po_details with domain_name FIRST ──
        try:
            await UserRepo.enrich_po_details_with_domain(request)
            logger.info("[CLIENT_SCHEDULER] Domain enrichment completed")
        except Exception as e:
            logger.warning(f"[CLIENT_SCHEDULER] Domain enrichment failed (non-fatal): {e}")
            # non-fatal — continue even if enrichment fails

        # ── Step 1: Fetch all uncompared client PO records ──
        try:
            po_records = await UserRepo.get_existing_client_po_det_ids(request)
        except Exception as e:
            logger.exception(f"[CLIENT_SCHEDULER] Failed to fetch PO records, aborting job: {e}")
            return

        if not po_records:
            logger.info("[CLIENT_SCHEDULER] No uncompared client PO records. Job exiting early.")
            return

        logger.info(f"[CLIENT_SCHEDULER] Processing {len(po_records)} PO records")

        # ── Step 2: Fetch system POs once (shared across all records) ──
        system_pos = []
        try:
            async with request.app.state.pool.acquire() as conn:
                async with conn.cursor(DictCursor) as cur:
                    repo = MailsRepository(cur)
                    system_pos = await usersmailservice.fetch_system_pos_with_oldest_date(
                        repo, request.app
                    )
            logger.info(f"[CLIENT_SCHEDULER] Fetched {len(system_pos)} system POs")
        except Exception as e:
            logger.warning(f"[CLIENT_SCHEDULER] fetch_system_pos failed — reconcile will be skipped: {e}")

        # ── Step 3: Group by user_id and split by is_compared ──
        from collections import defaultdict

        user_fresh_map = defaultdict(list)       # is_compared=0 → compare
        user_compared_map = defaultdict(list)    # is_compared=1 → reconcile only

        for record in po_records:
            uid = record["user_id"]
            if not uid:
                logger.warning(
                    f"[CLIENT_SCHEDULER] po_det_id {record['po_det_id']} "
                    f"has no matching user_id — skipping"
                )
                continue

            if record["is_compared"] == 0:       
                user_fresh_map[uid].append(record["po_det_id"])
            elif record["is_compared"] == 1:    
                user_compared_map[uid].append(record["po_det_id"])

        if not user_fresh_map and not user_compared_map:
            logger.warning("[CLIENT_SCHEDULER] No records had a valid user_id. Job exiting.")
            return

        all_users = set(user_fresh_map.keys()) | set(user_compared_map.keys())
        logger.info(f"[CLIENT_SCHEDULER] Processing {len(all_users)} distinct users")

        # ── Step 4: Process per user ──
        for user_id in all_users:
            fresh_ids = user_fresh_map.get(user_id, [])
            compared_ids = user_compared_map.get(user_id, [])

            logger.info(
                f"[CLIENT_SCHEDULER][User {user_id}] "
                f"Fresh → compare: {len(fresh_ids)} | "
                f"Already compared → reconcile: {len(compared_ids)}"
            )

            try:
                async with request.app.state.pool.acquire() as conn:
                    async with conn.cursor(DictCursor) as cur:
                        repo = MailsRepository(cur)

                        # ── Path A: Fresh → Compare ──
                        if fresh_ids:
                            try:
                                await usersmailservice.compare_scanned_and_system_pos(
                                    request=request,
                                    user_id=user_id,
                                    po_det_ids=fresh_ids,
                                    mails_repo=repo,
                                    system_pos=system_pos
                                )
                                logger.info(f"[CLIENT_SCHEDULER][User {user_id}] " f"Compare completed for {len(fresh_ids)} records")

                                # Mark as compared only if inserted into po_matched_report
                                await UserRepo.mark_po_as_compared(request, fresh_ids)

                            except Exception as e:
                                logger.error(f"[CLIENT_SCHEDULER][User {user_id}] compare failed: {e}", exc_info=True)

                        # ── Path B: Already compared → Reconcile only ──
                        if compared_ids and system_pos:
                            try:
                                reconcile_stats = await usersmailservice.reconcile_all_pos(
                                    user_id=user_id,
                                    mails_repo=repo,
                                    system_pos=system_pos
                                )
                                logger.info(f"[CLIENT_SCHEDULER][User {user_id}] " f"Reconcile completed: {reconcile_stats}")

                                # ── Check if any moved to matched → mark as 2 ──
                                await UserRepo.mark_po_as_reconciled(request, compared_ids)

                            except Exception as e:
                                logger.error(f"[CLIENT_SCHEDULER][User {user_id}] reconcile failed: {e}", exc_info=True)

            except Exception as user_err:
                logger.exception(f"[CLIENT_SCHEDULER][User {user_id}] Unexpected error: {user_err}")
                continue


def create_scheduler_request(app):
    scope = {"type": "http", "app": app}
    return Request(scope)