import sqlite3
import os
from datetime import datetime
from config import logger

DB_FILE = "reminders.db"

def get_db_connection():
    """Create and return a database connection."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # reminders table: stores active reminders
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        start_time TIMESTAMP NOT NULL, -- Format: YYYY-MM-DD HH:MM:SS
        location TEXT,
        google_event_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        reminder_sent INTEGER DEFAULT 0 -- 0 = No, 1 = Yes
    )
    """)
    
    # sessions table: stores conversational state for LINE dialog
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        user_id TEXT PRIMARY KEY,
        title TEXT,
        date_str TEXT,
        time_str TEXT,
        location TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully.")

# Session Operations
def get_session(user_id):
    """Retrieve active session for a LINE user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def save_session(user_id, title=None, date_str=None, time_str=None, location=None):
    """Create or update the session state for a user."""
    existing = get_session(user_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if existing:
        # Merge new fields with existing fields (only update if not None)
        new_title = title if title is not None else existing["title"]
        new_date = date_str if date_str is not None else existing["date_str"]
        new_time = time_str if time_str is not None else existing["time_str"]
        new_loc = location if location is not None else existing["location"]
        
        cursor.execute("""
            UPDATE sessions 
            SET title = ?, date_str = ?, time_str = ?, location = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (new_title, new_date, new_time, new_loc, user_id))
    else:
        cursor.execute("""
            INSERT INTO sessions (user_id, title, date_str, time_str, location)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, title, date_str, time_str, location))
        
    conn.commit()
    conn.close()

def clear_session(user_id):
    """Delete a session when a schedule is fully recorded."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# Reminder Operations
def add_reminder(title, start_time_str, location, google_event_id):
    """Insert a new reminder event into database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO reminders (title, start_time, location, google_event_id, reminder_sent)
        VALUES (?, ?, ?, ?, 0)
    """, (title, start_time_str, location, google_event_id))
    reminder_id = cursor.lastrowid
    conn.commit()
    conn.close()
    logger.info(f"Added reminder to DB (ID: {reminder_id}): {title} at {start_time_str}")
    return reminder_id

def get_pending_reminders(limit_time_str):
    """Get all reminders where start_time <= limit_time_str and reminder_sent = 0."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Find reminders that start in the future but within the reminder window (<= limit_time_str)
    # AND are not yet sent
    cursor.execute("""
        SELECT * FROM reminders 
        WHERE start_time <= ? AND reminder_sent = 0
    """, (limit_time_str,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_reminder_sent(reminder_id):
    """Update reminder status to sent."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE reminders SET reminder_sent = 1 WHERE id = ?", (reminder_id,))
    conn.commit()
    conn.close()
    logger.info(f"Marked reminder ID {reminder_id} as sent in DB.")
