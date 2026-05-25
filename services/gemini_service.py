import json
from datetime import datetime
import google.generativeai as genai
from config import GEMINI_API_KEY, TAIPEI_TZ, logger

# Configure Gemini API
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.error("GEMINI_API_KEY is not configured!")

def parse_schedule_message(message_text):
    """
    Parse a user message to extract meeting details: title, date, time, location.
    Resolves relative terms (e.g., 'tomorrow', 'this afternoon 3pm') using Taipei timezone.
    """
    if not GEMINI_API_KEY:
        logger.error("Cannot parse message, Gemini API Key is missing.")
        return {"title": None, "date": None, "time": None, "location": None}
    
    # Get current time in Taipei timezone
    now = datetime.now(TAIPEI_TZ)
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    day_of_week = now.strftime("%A") # e.g. Monday
    
    prompt = f"""
You are an expert NLP assistant specialized in schedule extraction.
Your task is to parse a user's text message and extract the scheduling details for a calendar event.

Please resolve relative dates and times (such as "today", "tomorrow", "this Monday", "next Friday", "this afternoon at 4", "3:00 PM") into exact calendar formats.
Use the following reference time information as the base for calculations:
- Current Local Date: {current_date}
- Current Local Time: {current_time}
- Day of the Week: {day_of_week}
- Timezone: Asia/Taipei

You must extract:
1. "title": A short description of the meeting, activity, or what to do.
2. "date": The resolved date in "YYYY-MM-DD" format.
3. "time": The resolved time in "HH:MM" format (24-hour).
4. "location": The location of the event (e.g. room number, building, address).

Rules:
- If a detail is missing from the message and cannot be inferred, set its value to null.
- Resolve relative terms correctly. For example, if today is 2026-05-25 (Monday):
  - "本週一下午 4:00" -> Date: 2026-05-25, Time: 16:00
  - "明天下午三點" -> Date: 2026-05-26, Time: 15:00
  - "下星期三早上9點" -> Date: 2026-06-03, Time: 09:00
- If the user provides only one part of the information (e.g. "延平技術大樓817"), return only that part (e.g., location="延平技術大樓817", others=null).

You must return a valid JSON object matching the JSON Schema. Do NOT wrap the JSON output in markdown formatting (like ```json).

JSON Schema:
{{
  "title": string or null,
  "date": string or null,
  "time": string or null,
  "location": string or null
}}

User Input Message:
"{message_text}"
"""
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        result_text = response.text.strip()
        logger.info(f"Gemini raw response: {result_text}")
        
        parsed_json = json.loads(result_text)
        
        # Ensure keys exist
        extracted = {
            "title": parsed_json.get("title"),
            "date": parsed_json.get("date"),
            "time": parsed_json.get("time"),
            "location": parsed_json.get("location")
        }
        logger.info(f"Successfully extracted: {extracted}")
        return extracted
        
    except Exception as e:
        logger.error(f"Error parsing message with Gemini: {e}", exc_info=True)
        return {"title": None, "date": None, "time": None, "location": None}
