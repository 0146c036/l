import os
import logging
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# App Configuration
PORT = int(os.environ.get("PORT", 5000))
TIMEZONE_NAME = "Asia/Taipei"
TAIPEI_TZ = pytz.timezone(TIMEZONE_NAME)

# LINE Bot Credentials
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
# The LINE_USER_ID is the specific user to whom reminders and notifications will be sent
LINE_USER_ID = os.environ.get("LINE_USER_ID")

# Email Configurations
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 465))  # Use 465 for SSL by default
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")  # Gmail App Password
EMAIL_TO = os.environ.get("EMAIL_TO")  # Destination email for notifications

# Gemini API Credentials
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Google API Credentials
# These can be loaded as JSON strings directly from env vars (useful for cloud deploys like Render/Railway)
GOOGLE_CREDENTIALS_JSON = os.environ.get("GOOGLE_CREDENTIALS_JSON")
GOOGLE_TOKEN_JSON = os.environ.get("GOOGLE_TOKEN_JSON")

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("reminder_system")

def validate_config():
    """Verify that all required environment variables are set."""
    missing = []
    if not LINE_CHANNEL_ACCESS_TOKEN:
        missing.append("LINE_CHANNEL_ACCESS_TOKEN")
    if not LINE_CHANNEL_SECRET:
        missing.append("LINE_CHANNEL_SECRET")
    if not LINE_USER_ID:
        missing.append("LINE_USER_ID")
    if not SMTP_USER:
        missing.append("SMTP_USER")
    if not SMTP_PASSWORD:
        missing.append("SMTP_PASSWORD")
    if not EMAIL_TO:
        missing.append("EMAIL_TO")
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
        
    if missing:
        logger.warning(f"Missing environment variables: {', '.join(missing)}")
        logger.warning("The application may fail to send notifications or parse inputs correctly.")
        return False
    return True
