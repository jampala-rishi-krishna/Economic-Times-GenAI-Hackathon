import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "nexus.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Add missing columns to notifications table if they don't exist
try:
    cursor.execute("ALTER TABLE notifications ADD COLUMN email_sent BOOLEAN DEFAULT 0")
    print("✅ Added email_sent column")
except Exception as e:
    print(f"ℹ️  email_sent: {e}")

try:
    cursor.execute("ALTER TABLE notifications ADD COLUMN email_sent_at DATETIME")
    print("✅ Added email_sent_at column")
except Exception as e:
    print(f"ℹ️  email_sent_at: {e}")

try:
    cursor.execute("ALTER TABLE notifications ADD COLUMN email_error TEXT")
    print("✅ Added email_error column")
except Exception as e:
    print(f"ℹ️  email_error: {e}")

# Add missing columns to participant_emails table if it doesn't exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS participant_emails (
        id TEXT PRIMARY KEY,
        participant_name TEXT,
        email_address TEXT,
        meeting_id TEXT
    )
""")
print("✅ participant_emails table ready")

conn.commit()
conn.close()
print("✅ Migration complete — restart the server now")
