import sqlite3
from datetime import datetime
from datetime import datetime as dt
from collections import Counter


def init_db():
    conn = sqlite3.connect("civic_complaints.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            location TEXT NOT NULL,
            image_path TEXT,
            category TEXT,
            date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Open',
            resolved_date TEXT
        )
    """)
    conn.commit()
    conn.close()


def add_complaint(description, location, image_path=None, category=None):
    conn = sqlite3.connect("civic_complaints.db")
    cursor = conn.cursor()
    submitted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO complaints (description, location, image_path, category, date, status)
        VALUES (?, ?, ?, ?, ?, 'Open')
    """, (description, location, image_path, category, submitted_at))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_all_complaints():
    conn = sqlite3.connect("civic_complaints.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM complaints ORDER BY complaint_id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_complaint_by_id(complaint_id):
    conn = sqlite3.connect("civic_complaints.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM complaints WHERE complaint_id = ?", (complaint_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def update_status(complaint_id, new_status):
    conn = sqlite3.connect("civic_complaints.db")
    cursor = conn.cursor()

    if new_status == "Resolved":
        resolved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "UPDATE complaints SET status = ?, resolved_date = ? WHERE complaint_id = ?",
            (new_status, resolved_at, complaint_id)
        )
    else:
        cursor.execute(
            "UPDATE complaints SET status = ? WHERE complaint_id = ?",
            (new_status, complaint_id)
        )

    conn.commit()
    updated = cursor.rowcount
    conn.close()
    return updated > 0


def get_category_counts():
    conn = sqlite3.connect("civic_complaints.db")
    cursor = conn.cursor()
    cursor.execute("SELECT category FROM complaints WHERE category IS NOT NULL")
    categories = [row[0] for row in cursor.fetchall()]
    conn.close()
    return Counter(categories)


def get_status_counts():
    conn = sqlite3.connect("civic_complaints.db")
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM complaints")
    statuses = [row[0] for row in cursor.fetchall()]
    conn.close()
    return Counter(statuses)


def filter_complaints(category=None, status=None):
    conn = sqlite3.connect("civic_complaints.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = "SELECT * FROM complaints WHERE 1=1"
    params = []

    if category:
        query += " AND category = ?"
        params.append(category)

    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY complaint_id DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_resolution_times():
    conn = sqlite3.connect("civic_complaints.db")
    cursor = conn.cursor()
    cursor.execute("SELECT date, resolved_date FROM complaints WHERE resolved_date IS NOT NULL")
    rows = cursor.fetchall()
    conn.close()

    hours_list = []
    for submitted, resolved in rows:
        t1 = dt.strptime(submitted, "%Y-%m-%d %H:%M:%S")
        t2 = dt.strptime(resolved, "%Y-%m-%d %H:%M:%S")
        hours = (t2 - t1).total_seconds() / 3600
        hours_list.append(hours)

    return hours_list