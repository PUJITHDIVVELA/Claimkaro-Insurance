from database.connection import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
from utils.helpers import log_audit, generate_employee_id
from utils.mail_handler import create_and_send_otp, verify_otp_code
import re

class AuthService:
    @staticmethod
    def send_register_otp(email):
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not email or not re.match(email_regex, email):
            return False, "Please enter a valid email address.", None

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    return False, "User with this email already exists.", None
        finally:
            conn.close()

        success, msg, _ = create_and_send_otp(email, "REGISTRATION")
        return success, msg, None

    @staticmethod
    def send_forgot_password_otp(email):
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not email or not re.match(email_regex, email):
            return False, "Please enter a valid email address.", None

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()
                if not user:
                    return False, "No registered user found with this email.", None
        finally:
            conn.close()

        success, msg, _ = create_and_send_otp(email, "FORGOT_PASSWORD")
        return success, msg, None

    @staticmethod
    def reset_password_with_otp(email, otp_code, new_password):
        if len(new_password) < 6:
            return False, "New password must be at least 6 characters long."

        valid, msg = verify_otp_code(email, otp_code, "FORGOT_PASSWORD")
        if not valid:
            return False, msg

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()
                if not user:
                    return False, "User not found."

                pw_hash = generate_password_hash(new_password)
                cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (pw_hash, user['id']))

            log_audit(user['id'], "FORGOT_PASSWORD_RESET", "AUTH", "Password reset successfully via email OTP")
            return True, "Password reset successfully! You can now log in with your new password."
        finally:
            conn.close()

    @staticmethod
    def register_user(name, email, phone, password, role='CUSTOMER', dob=None, gender=None, address=None, city=None, state=None, pincode=None, otp_code=None):
        if not name or not email or not password or not phone:
            return False, "All required fields must be provided.", None

        if len(password) < 6:
            return False, "Password must be at least 6 characters long.", None

        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_regex, email):
            return False, "Invalid email format.", None

        # Verify OTP if role is CUSTOMER
        if role == 'CUSTOMER':
            if not otp_code:
                return False, "OTP verification code is required.", None
            valid, msg = verify_otp_code(email, otp_code, "REGISTRATION")
            if not valid:
                return False, msg

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    return False, "User with this email already exists.", None

                pw_hash = generate_password_hash(password)
                cursor.execute("""
                    INSERT INTO users (name, email, phone, password_hash, role, status)
                    VALUES (%s, %s, %s, %s, %s, 'ACTIVE')
                """, (name, email, phone, pw_hash, role))
                user_id = cursor.lastrowid

                if role == 'CUSTOMER':
                    cursor.execute("""
                        INSERT INTO customer_profiles (user_id, date_of_birth, gender, address, city, state, pincode)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (user_id, dob, gender, address, city, state, pincode))
                elif role == 'AGENT':
                    emp_id = generate_employee_id('AGENT')
                    cursor.execute("""
                        INSERT INTO agent_profiles (user_id, employee_id, department, experience)
                        VALUES (%s, %s, 'Sales & Advisory', 1)
                    """, (user_id, emp_id))
                elif role == 'CLAIMS_OFFICER':
                    emp_id = generate_employee_id('CLAIMS_OFFICER')
                    cursor.execute("""
                        INSERT INTO claims_officer_profiles (user_id, employee_id, department)
                        VALUES (%s, %s, 'Claims Assessment')
                    """, (user_id, emp_id))

            log_audit(user_id, "REGISTER", "AUTH", f"User registered with role {role}")
            return True, "User registered successfully!", {"user_id": user_id, "role": role}
        except Exception as e:
            return False, f"Registration failed: {str(e)}", None
        finally:
            conn.close()

    @staticmethod
    def authenticate(email, password):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()
                if not user:
                    return False, "Invalid email or password.", None

                if user['status'] != 'ACTIVE':
                    return False, f"Account is currently {user['status'].lower()}. Please contact admin.", None

                if check_password_hash(user['password_hash'], password):
                    log_audit(user['id'], "LOGIN", "AUTH", "User logged in successfully")
                    return True, "Login successful", user
                else:
                    return False, "Invalid email or password.", None
        finally:
            conn.close()

    @staticmethod
    def get_user_profile(user_id):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT u.id, u.name, u.email, u.phone, u.role, u.status, u.created_at,
                           cp.date_of_birth, cp.gender, cp.address, cp.city, cp.state, cp.pincode, cp.profile_photo,
                           ap.employee_id as agent_emp_id, ap.department as agent_dept,
                           cop.employee_id as officer_emp_id, cop.department as officer_dept
                    FROM users u
                    LEFT JOIN customer_profiles cp ON u.id = cp.user_id
                    LEFT JOIN agent_profiles ap ON u.id = ap.user_id
                    LEFT JOIN claims_officer_profiles cop ON u.id = cop.user_id
                    WHERE u.id = %s
                """, (user_id,))
                return cursor.fetchone()
        finally:
            conn.close()

    @staticmethod
    def change_password(user_id, old_password, new_password):
        if len(new_password) < 6:
            return False, "New password must be at least 6 characters long."
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                if not user or not check_password_hash(user['password_hash'], old_password):
                    return False, "Incorrect old password."
                
                new_hash = generate_password_hash(new_password)
                cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, user_id))
            log_audit(user_id, "CHANGE_PASSWORD", "AUTH", "Password updated")
            return True, "Password changed successfully."
        finally:
            conn.close()
