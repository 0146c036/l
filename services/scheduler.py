import time
import threading
from datetime import datetime, timedelta
from config import TAIPEI_TZ, logger
from database import get_db_connection, mark_reminder_sent
from services.line_service import push_reminder_message
from services.email_service import send_reminder_email

def scheduler_loop():
    """
    Main loop running in a background thread.
    Checks the database every 60 seconds for reminders scheduled in the next 1.5 hours (90 minutes)
    that have not been processed.
    """
    logger.info("Background scheduler loop initialized.")
    while True:
        try:
            # Current time in Asia/Taipei timezone
            now = datetime.now(TAIPEI_TZ)
            
            # Reminder trigger window: events starting within next 90 minutes
            limit_dt = now + timedelta(minutes=90)
            # Grace period window: don't notify for events that started more than 30 minutes ago
            grace_dt = now - timedelta(minutes=30)
            
            limit_str = limit_dt.strftime("%Y-%m-%d %H:%M:%S")
            grace_str = grace_dt.strftime("%Y-%m-%d %H:%M:%S")
            
            # Connect to database and query pending reminders
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM reminders 
                WHERE start_time <= ? AND start_time >= ? AND reminder_sent = 0
            """, (limit_str, grace_str))
            
            rows = cursor.fetchall()
            reminders = [dict(r) for r in rows]
            conn.close()
            
            for r in reminders:
                reminder_id = r["id"]
                title = r["title"]
                start_time_str = r["start_time"]
                location = r["location"]
                
                logger.info(f"Scheduler found target reminder: '{title}' starting at {start_time_str}")
                
                # Parse strings for presentation
                dt_obj = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
                date_str = dt_obj.strftime("%Y-%m-%d")
                time_str = dt_obj.strftime("%H:%M")
                
                # Send LINE Push
                line_success = False
                try:
                    line_success = push_reminder_message(title, date_str, time_str, location)
                except Exception as e:
                    logger.error(f"Error sending LINE push reminder: {e}")
                    
                # Send Email
                email_success = False
                try:
                    email_success = send_reminder_email(title, date_str, time_str, location)
                except Exception as e:
                    logger.error(f"Error sending SMTP email reminder: {e}")
                    
                # Mark as sent if either channel succeeded
                if line_success or email_success:
                    mark_reminder_sent(reminder_id)
                    logger.info(f"Reminder ID {reminder_id} notification successfully triggered.")
                else:
                    logger.error(f"Failed to send both LINE and email reminders for ID {reminder_id}.")
                    
        except Exception as e:
            logger.error(f"Exception in scheduler loop: {e}", exc_info=True)
            
        # Check every minute
        time.sleep(60)

def start_scheduler():
    """Start the scheduler loop in a background daemon thread."""
    t = threading.Thread(target=scheduler_loop, name="SchedulerThread")
    t.daemon = True
    t.start()
    logger.info("Background scheduler thread started.")
