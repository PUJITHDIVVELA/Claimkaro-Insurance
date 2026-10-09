from flask import jsonify, request, session
from database.connection import get_db_connection
import random
import datetime

def api_response(success=True, message="", data=None, status_code=200):
    payload = {
        "success": success,
        "message": message,
        "data": data if data is not None else {}
    }
    return jsonify(payload), status_code

def generate_policy_number():
    year = datetime.datetime.now().year
    rand_num = random.randint(10000, 99999)
    return f"POL{year}{rand_num}"

def generate_claim_number():
    year = datetime.datetime.now().year
    rand_num = random.randint(10000, 99999)
    return f"CLM{year}{rand_num}"

def generate_ticket_number():
    year = datetime.datetime.now().year
    rand_num = random.randint(10000, 99999)
    return f"TKT{year}{rand_num}"

def generate_employee_id(role):
    prefix = "AGT" if role == 'AGENT' else "CO"
    rand_num = random.randint(1000, 9999)
    return f"{prefix}-{rand_num}"

def log_audit(user_id, action, module, description=""):
    try:
        ip = request.remote_addr if request else '127.0.0.1'
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO audit_logs (user_id, action, module, description, ip_address)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, action, module, description, ip))
        conn.close()
    except Exception as e:
        print(f"Error logging audit: {e}")
