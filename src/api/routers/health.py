import sqlite3
import time
import os
from fastapi import APIRouter

router = APIRouter()
START_TIME = time.time()
DB_PATH = os.path.join(os.getcwd(), "data", "nifty100.db")

@router.get("/health")
def health_check():
    uptime = round(time.time() - START_TIME, 2)
    db_row_counts = {}
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Dynamically fetch all tables in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            db_row_counts[table_name] = cursor.fetchone()[0]
            
        conn.close()
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "ok",
        "version": "1.0.0",
        "uptime_seconds": uptime,
        "database": db_status,
        "db_row_counts": db_row_counts
    }