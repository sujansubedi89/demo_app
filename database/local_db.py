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
    password_hash=password
    rows=run_query("""SELECT id, username, full_name, role
FROM officers
WHERE username=%s
AND password_hash=%s
AND is_active=1""",(username,password_hash),fetch=True)
    return rows[0] if rows else None

# NSERT INTO officers (username, password_hash, full_name, role, checkpost_id, is_active) VALUES
# ('admin', 'admin123', 'System Admin', 'admin', NULL, 1),
# ('ktm_1', 'ktm1pass', 'Kathmandu Counter 1', 'issuer', 1, 1),
# ('ktm_2', 'ktm2pass', 'Kathmandu Counter 2', 'issuer', 1, 1),
# ('ktm_3', 'ktm3pass', 'Kathmandu Counter 3', 'issuer', 1, 1),
# ('sim_1', 'sim1pass', 'Simpani Counter 1', 'issuer', 2, 1),
# ('sim_2', 'sim2pass', 'Simpani Counter 2', 'issuer', 2, 1),
# ('sim_3', 'sim3pass', 'Simpani Counter 3', 'issuer', 2, 1),
# ('pkr_1', 'pkr1pass', 'Pokhara Counter 1', 'issuer', 3, 1),
# ('pkr_2', 'pkr2pass', 'Pokhara Counter 2', 'issuer', 3, 1),
# ('pkr_3', 'pkr3pass', 'Pokhara Counter 3', 'issuer', 3, 1),
# ('gas_1', 'gas1pass', 'Gassa Counter 1', 'issuer', 4, 1),
# ('gas_2', 'gas2pass', 'Gassa Counter 2', 'issuer', 4, 1),
# ('gas_3', 'gas3pass', 'Gassa Counter 3', 'issuer', 4, 1);
