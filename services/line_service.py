import requests
import time
from config import LINE_CHANNEL_ACCESS_TOKEN, LINE_USER_ID, logger

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
                        logger.error(f"LINE function {func.__name__} failed after {retries} attempts: {e}")
                        raise e
                    sleep_time = backoff_in_seconds * (2 ** (attempt - 1))
                    logger.warning(f"Error in {func.__name__}: {e}. Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
        return wrapper
    return decorator

@retry_on_failure(retries=3, backoff_in_seconds=2)
def reply_message(reply_token, text):
    """
    Send a reply message back to the user who triggered the webhook.
    Uses replyToken which is valid only for a short time.
    """
    if not LINE_CHANNEL_ACCESS_TOKEN:
        logger.error("LINE_CHANNEL_ACCESS_TOKEN not configured!")
        return False
        
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    
    payload = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "text",
                "text": text
            }
        ]
    }
    
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    if response.status_code == 200:
        logger.info("Reply message sent successfully.")
        return True
    else:
        logger.error(f"Failed to send reply. Status: {response.status_code}. Response: {response.text}")
        response.raise_for_status()

@retry_on_failure(retries=3, backoff_in_seconds=2)
def push_message(text, target_user_id=None):
    """
    Send an outbound push message to a specific user.
    If target_user_id is not specified, uses the LINE_USER_ID from environment.
    """
    if not LINE_CHANNEL_ACCESS_TOKEN:
        logger.error("LINE_CHANNEL_ACCESS_TOKEN not configured!")
        return False
        
    user_id = target_user_id or LINE_USER_ID
    if not user_id:
        logger.error("No LINE User ID specified for push message.")
        return False
        
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    
    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": text
            }
        ]
    }
    
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    if response.status_code == 200:
        logger.info(f"Push message sent successfully to {user_id}.")
        return True
    else:
        logger.error(f"Failed to send push. Status: {response.status_code}. Response: {response.text}")
        response.raise_for_status()

def push_reminder_message(title, date_str, time_str, location, target_user_id=None):
    """
    Send a pre-formatted push reminder to the user 1.5 hours before the event.
    """
    message_text = (
        f"⏰ 【行程出發提醒】\n"
        f"您的行程將於 1.5 小時後開始，請提前準備並出發！\n\n"
        f"📌 主題：{title}\n"
        f"📅 時間：{date_str} {time_str}\n"
        f"📍 地點：{location if location else '未設定地點'}"
    )
    return push_message(message_text, target_user_id)
