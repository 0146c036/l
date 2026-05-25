import os
import json
import hmac
import hashlib
import base64
from datetime import datetime
from flask import Flask, request, jsonify, abort

from config import (
    PORT, LINE_CHANNEL_SECRET, TAIPEI_TZ, logger, validate_config
)
from database import (
    init_db, get_session, save_session, clear_session, add_reminder
)
from services.gemini_service import parse_schedule_message
from services.calendar_service import create_calendar_event
from services.email_service import send_confirmation_email
from services.line_service import reply_message
from services.scheduler import start_scheduler

app = Flask(__name__)

def verify_line_signature(body_data, signature):
    """Verify that the webhook request signature matches the Line Channel Secret."""
    if not signature or not LINE_CHANNEL_SECRET:
        return False
    hash_val = hmac.new(
        LINE_CHANNEL_SECRET.encode("utf-8"),
        body_data,
        hashlib.sha256
    ).digest()
    computed_sig = base64.b64encode(hash_val).decode("utf-8")
    return hmac.compare_digest(computed_sig, signature)

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for Render/Railway monitoring."""
    return jsonify({"status": "healthy", "timezone": "Asia/Taipei"}), 200

@app.route("/webhook", methods=["POST"])
def webhook():
    """Webhook endpoint for LINE Messaging API."""
    signature = request.headers.get("X-Line-Signature")
    body_data = request.get_data()
    
    # Verify signature
    if not verify_line_signature(body_data, signature):
        logger.warning("Invalid LINE webhook signature detected.")
        abort(400, "Invalid signature")
        
    try:
        payload = json.loads(body_data.decode("utf-8"))
        events = payload.get("events", [])
        
        for event in events:
            # Handle text messages
            if event.get("type") == "message" and event.get("message", {}).get("type") == "text":
                reply_token = event.get("replyToken")
                user_id = event.get("source", {}).get("userId")
                message_text = event.get("message", {}).get("text", "").strip()
                
                logger.info(f"Received webhook message from {user_id}: '{message_text}'")
                
                # Command: Reset session
                if message_text.lower() in ["取消", "重設", "clear", "reset", "cancel"]:
                    clear_session(user_id)
                    reply_message(reply_token, "已為您清除暫存的對話狀態。您可以隨時輸入新行程，例如：「明天下午3:00在817教室與組員開會」")
                    continue
                
                # Retrieve existing session details
                session = get_session(user_id) or {
                    "title": None,
                    "date_str": None,
                    "time_str": None,
                    "location": None
                }
                
                # Call Gemini parser to extract fields from the current message
                extracted = parse_schedule_message(message_text)
                
                # Merge newly extracted fields with existing session
                new_title = extracted["title"] or session.get("title")
                new_date = extracted["date"] or session.get("date_str")
                new_time = extracted["time"] or session.get("time_str")
                new_location = extracted["location"] or session.get("location")
                
                # Save merged details back to SQLite
                save_session(
                    user_id=user_id,
                    title=new_title,
                    date_str=new_date,
                    time_str=new_time,
                    location=new_location
                )
                
                # Check for missing parameters
                missing_fields = []
                if not new_title:
                    missing_fields.append("「要做什麼（主題）」")
                if not new_date:
                    missing_fields.append("「日期」")
                if not new_time:
                    missing_fields.append("「時間」")
                if not new_location:
                    missing_fields.append("「地點」")
                    
                if missing_fields:
                    # Provide helpful feedback to the user on what is stored and what is missing
                    status_msg = "已記錄部分行程資訊：\n"
                    if new_title:
                        status_msg += f"📌 主題：{new_title}\n"
                    if new_date:
                        status_msg += f"📅 日期：{new_date}\n"
                    if new_time:
                        status_msg += f"⏰ 時間：{new_time}\n"
                    if new_location:
                        status_msg += f"📍 地點：{new_location}\n"
                        
                    status_msg += f"\n👉 還缺少以下資訊：{', '.join(missing_fields)}\n請告訴我遺漏的項目（例如：「下午 4:00」或「地點在延平技術大樓817」），或輸入「取消」重新設定。"
                    reply_message(reply_token, status_msg)
                else:
                    # All parameters are present! Write to Calendar, DB and send email confirmation
                    try:
                        # Standardize meeting time
                        start_time_str = f"{new_date} {new_time}:00"
                        # Verify it is a valid date format
                        datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
                        
                        logger.info("All fields collected. Scheduling event...")
                        
                        # 1. Google Calendar Integration
                        event_id = create_calendar_event(
                            title=new_title,
                            date_str=new_date,
                            time_str=new_time,
                            location=new_location
                        )
                        
                        # 2. SMTP Confirmation Email
                        email_sent = send_confirmation_email(
                            title=new_title,
                            date_str=new_date,
                            time_str=new_time,
                            location=new_location
                        )
                        
                        # 3. Add to SQLite db for reminder scheduling
                        add_reminder(
                            title=new_title,
                            start_time_str=start_time_str,
                            location=new_location,
                            google_event_id=event_id
                        )
                        
                        # 4. Clear user session state
                        clear_session(user_id)
                        
                        # 5. Reply confirmation message on LINE
                        reply_text = (
                            f"🎉 行程已成功排定並同步！\n\n"
                            f"📌 主題：{new_title}\n"
                            f"📅 時間：{new_date} {new_time}\n"
                            f"📍 地點：{new_location}\n\n"
                            f"已將行程寫入 Google 行事曆，並發送確認信件。\n"
                            f"系統將於行程開始前 1.5 小時透過 LINE 與 Email 再次提醒您！"
                        )
                        reply_message(reply_token, reply_text)
                        
                    except ValueError:
                        reply_message(reply_token, "⚠️ 日期或時間格式解析出錯，請輸入「取消」重新嘗試，例如：「本週一下午4:00在延平817開會」")
                        
    @app.route("/", methods=["GET", "HEAD"])
def index():
    return "Hello, Meeting Reminder System is running!", 200

@app.route("/callback", methods=["POST"])
def callback():
    return "OK", 200



if __name__ == "__main__":
    logger.info("Initializing system dependencies...")
    init_db()
    validate_config()
    start_scheduler()
    
    logger.info(f"Starting server on port {PORT}...")
    app.run(host="0.0.0.0", port=PORT)
