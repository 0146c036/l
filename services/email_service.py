import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_TO, logger

def retry_on_failure(retries=3, backoff_in_seconds=2):
    """Decorator to retry a function upon failure with exponential backoff."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    if attempt == retries:
                        logger.error(f"Function {func.__name__} failed after {retries} attempts: {e}")
                        raise e
                    sleep_time = backoff_in_seconds * (2 ** (attempt - 1))
                    logger.warning(f"Error in {func.__name__}: {e}. Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
        return wrapper
    return decorator

@retry_on_failure(retries=3, backoff_in_seconds=2)
def _send_smtp_email(subject, html_content):
    """Low-level helper to send email over SMTP."""
    if not SMTP_USER or not SMTP_PASSWORD or not EMAIL_TO:
        logger.warning("SMTP configuration is incomplete. Skipping email transmission.")
        return False
        
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"會議提醒系統 <{SMTP_USER}>"
    msg["To"] = EMAIL_TO
    
    # Attach HTML payload
    part = MIMEText(html_content, "html", "utf-8")
    msg.attach(part)
    
    server = None
    try:
        if SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10)
        else:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
            server.starttls()
            
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, [EMAIL_TO], msg.as_string())
        logger.info(f"Email sent successfully to {EMAIL_TO}: '{subject}'")
        return True
    except Exception as e:
        logger.error(f"SMTP error sending email: {e}")
        raise e
    finally:
        if server:
            try:
                server.quit()
            except Exception:
                pass

def send_confirmation_email(title, date_str, time_str, location):
    """Send an immediate confirmation email when a meeting is booked."""
    subject = f"【行程已建立】{title}"
    
    # Elegant HTML design for confirmation
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f6f9fc; padding: 20px; color: #333333;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-top: 4px solid #4CAF50;">
            <h2 style="color: #4CAF50; margin-top: 0;">📅 行程已成功排定！</h2>
            <p>您好：</p>
            <p>系統已為您記錄以下行程，並同步新增至您的 <strong>Google 行事曆</strong>：</p>
            
            <div style="background-color: #f9f9f9; padding: 15px; border-left: 4px solid #e0e0e0; margin: 20px 0; border-radius: 4px;">
                <p style="margin: 5px 0;"><strong>📌 主題：</strong> {title}</p>
                <p style="margin: 5px 0;"><strong>⏰ 時間：</strong> {date_str} {time_str}</p>
                <p style="margin: 5px 0;"><strong>📍 地點：</strong> {location if location else '未設定地點'}</p>
            </div>
            
            <p>系統將會在此行程開始前 <strong>1.5 小時</strong> 發送 LINE 訊息與 Email 提醒您。</p>
            <hr style="border: 0; border-top: 1px solid #eeeeee; margin: 20px 0;">
            <p style="font-size: 12px; color: #888888;">此郵件為自動發送，請勿直接回覆。</p>
        </div>
    </body>
    </html>
    """
    return _send_smtp_email(subject, html_content)

def send_reminder_email(title, date_str, time_str, location):
    """Send a reminder email 1.5 hours before the scheduled meeting."""
    subject = f"【行程提醒】「{title}」將於 1.5 小時後開始！"
    
    # Urgent/attention-grabbing HTML design for reminders
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #fff9f9; padding: 20px; color: #333333;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-top: 4px solid #FF5722;">
            <h2 style="color: #FF5722; margin-top: 0;">⏰ 準備出發！行程提醒</h2>
            <p>您好：</p>
            <p>您排定的行程將於 <strong>1.5 小時（90 分鐘）後</strong> 開始，請提前準備出發！</p>
            
            <div style="background-color: #fff5f2; padding: 15px; border-left: 4px solid #FF5722; margin: 20px 0; border-radius: 4px;">
                <p style="margin: 5px 0; font-size: 16px; font-weight: bold;"><strong>📌 主題：</strong> {title}</p>
                <p style="margin: 5px 0;"><strong>⏰ 時間：</strong> {date_str} {time_str}</p>
                <p style="margin: 5px 0;"><strong>📍 地點：</strong> {location if location else '未設定地點'}</p>
            </div>
            
            <p style="color: #555555; font-size: 14px;">提醒您注意交通狀況，並預留足夠的前往時間。祝您會議/行程順利！</p>
            <hr style="border: 0; border-top: 1px solid #eeeeee; margin: 20px 0;">
            <p style="font-size: 12px; color: #888888;">此郵件為自動發送，請勿直接回覆。</p>
        </div>
    </body>
    </html>
    """
    return _send_smtp_email(subject, html_content)
