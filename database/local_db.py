import mysql.connector
from mysql.connector import Error
import sys
import os

# Permanently fix the import path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from config import LOCAL_DB
def get_connection():
    try:
        conn=mysql.connector.connect(
            host=LOCAL_DB["host"]
            ,port=LOCAL_DB["port"]
            ,user=LOCAL_DB["user"]
            ,password=LOCAL_DB["password"]
            ,database=LOCAL_DB["database"]

        )
        return conn
    except Error as e:
        print(f"[DB ERROR] Could not connect to local database:{e}")
        return None
def run_query(sql,params=None,fetch=False):
    conn=get_connection()
    if conn is None:
        return None
    try:
        cursor=conn.cursor(dictionary=True)
        cursor.execute(sql,params or ())
        if fetch:
            result=cursor.fetchall()
            return result
        else:
            conn.commit()
            return True
    except Error as e:
        print(f"[DB ERROR] Query failed: {e}")
        print(f"SQL:{sql}")
        print(f"Params:{params}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()
def test_connection():
    conn=get_connection()
    if conn:
        print("[DB TEST] Connection successful!")
        conn.close()
        return True
    else:
        print("[DB TEST] Connection failed.")
        return False
if __name__=="__main__":
    test_connection()
    rows=run_query("SELECT * FROM checkposts",fetch=True)
    if rows:
        print(f"\nCheckposts in database ({len(rows)} found):")
        for row in rows:
            print(f"  - {row['name']}  ({row['location']})")
def verify_officer(username,password):
    import hashlib
    password_hash=hashlib.sha256(password.encode()).hexdigest()
    rows=run_query("""SELECT id,username,full_name,checkpost FROM officers WHERE username=%s AND password_hash=%s AND is_active=1""",(username,password_hash),fetch=True)
    return rows[0] if rows else None

