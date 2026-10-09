"""Background scheduler for automated daily vocabulary lessons."""

import logging
from datetime import datetime
from telegram.ext import ContextTypes, Application

from src.database import Database
from src.handlers.daily import send_daily_lesson

logger = logging.getLogger(__name__)


async def scheduled_daily_check(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Repeating job running every 60 seconds.
    Checks if current local time (HH:MM) matches any user's scheduled daily lesson time.
    """
    db: Database = context.bot_data.get("db")
    if not db:
        return

    now_str = datetime.now().strftime("%H:%M")

    try:
        user_ids = await db.get_users_for_daily_notification(now_str)
        if not user_ids:
            return

        logger.info(f"Delivering automated daily lessons to {len(user_ids)} user(s) at {now_str}")
        for uid in user_ids:
            try:
                await send_daily_lesson(uid, db, context.bot, force_new=False)
            except Exception as user_err:
                logger.warning(f"Failed to deliver scheduled lesson to user {uid}: {user_err}")

    except Exception as e:
        logger.error(f"Error in scheduled daily check: {e}")


def setup_scheduler(application: Application) -> None:
    """Register scheduled job with PTB JobQueue."""
    if application.job_queue:
        # Run check every 60 seconds, starting after 10 seconds
        application.job_queue.run_repeating(
            scheduled_daily_check,
            interval=60,
            first=10,
            name="daily_vocabulary_delivery"
        )
        logger.info("Daily vocabulary delivery scheduler registered successfully.")
    else:
        logger.warning("JobQueue not available. Automated scheduling disabled.")
