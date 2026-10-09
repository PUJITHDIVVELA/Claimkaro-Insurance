from database.connection import get_db_connection
from utils.helpers import generate_policy_number, log_audit
from config import Config
from datetime import datetime, timedelta
import razorpay
import time

class PolicyService:
    @staticmethod
    def get_all_policy_types():
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM policy_types WHERE status = 'ACTIVE' ORDER BY id ASC")
                return cursor.fetchall()
        finally:
            conn.close()

    @staticmethod
    def create_razorpay_order(customer_id, policy_type_id):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM policy_types WHERE id = %s AND status = 'ACTIVE'", (policy_type_id,))
                pt = cursor.fetchone()
                if not pt:
                    return False, "Selected policy plan is not available.", None

                cursor.execute("SELECT name, email, phone FROM users WHERE id = %s", (customer_id,))
                user = cursor.fetchone()

                # Initialize Razorpay SDK Client
                client = razorpay.Client(auth=(Config.RAZORPAY_KEY_ID, Config.RAZORPAY_KEY_SECRET))

                amount_in_paise = int(float(pt['premium']) * 100)
                receipt_id = f"rcpt_pol_{customer_id}_{int(time.time())}"

                order_data = {
                    "amount": amount_in_paise,
                    "currency": "INR",
                    "receipt": receipt_id,
                    "notes": {
                        "policy_type_id": policy_type_id,
                        "customer_id": customer_id
                    }
                }
                order = client.order.create(data=order_data)

                # Insert Pending Payment Record
                cursor.execute("""
                    INSERT INTO policy_payments (customer_id, razorpay_order_id, amount, status)
                    VALUES (%s, %s, %s, 'PENDING')
                """, (customer_id, order['id'], pt['premium']))

                return True, "Razorpay order generated", {
                    "order_id": order['id'],
                    "key_id": Config.RAZORPAY_KEY_ID,
                    "amount": order['amount'],
                    "currency": "INR",
                    "policy_type_id": pt['id'],
                    "policy_name": pt['name'],
                    "premium": float(pt['premium']),
                    "coverage": float(pt['coverage']),
                    "user_name": user['name'],
                    "user_email": user['email'],
                    "user_phone": user['phone']
                }
        except Exception as e:
            return False, f"Failed to initialize Razorpay payment: {str(e)}", None
        finally:
            conn.close()

    @staticmethod
    def verify_razorpay_payment(customer_id, policy_type_id, razorpay_order_id, razorpay_payment_id, razorpay_signature):
        client = razorpay.Client(auth=(Config.RAZORPAY_KEY_ID, Config.RAZORPAY_KEY_SECRET))
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }

        try:
            client.utility.verify_payment_signature(params_dict)
        except Exception as e:
            return False, "Razorpay payment signature verification failed.", None

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM policy_types WHERE id = %s", (policy_type_id,))
                pt = cursor.fetchone()
                if not pt:
                    return False, "Policy type not found.", None

                pol_num = generate_policy_number()
                start_date = datetime.today().date()
                end_date = start_date + timedelta(days=pt['duration_months'] * 30)

                # Issue ACTIVE Policy
                cursor.execute("""
                    INSERT INTO policies (policy_number, policy_type_id, customer_id, start_date, end_date, premium, coverage_amount, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'ACTIVE')
                """, (pol_num, policy_type_id, customer_id, start_date, end_date, pt['premium'], pt['coverage']))
                policy_id = cursor.lastrowid

                # Update Payment Record status to SUCCESS
                cursor.execute("""
                    UPDATE policy_payments 
                    SET policy_id = %s, razorpay_payment_id = %s, razorpay_signature = %s, status = 'SUCCESS'
                    WHERE razorpay_order_id = %s
                """, (policy_id, razorpay_payment_id, razorpay_signature, razorpay_order_id))

                # Create Notification
                cursor.execute("""
                    INSERT INTO notifications (user_id, title, message, type)
                    VALUES (%s, %s, %s, 'SUCCESS')
                """, (customer_id, "Policy Issued Successfully", f"Payment verified! Policy {pol_num} ({pt['name']}) is now ACTIVE."))

            log_audit(customer_id, "RAZORPAY_PAYMENT_SUCCESS", "POLICY", f"Verified payment {razorpay_payment_id} for policy {pol_num}")
            return True, f"Payment verified & Policy {pol_num} activated successfully!", {"policy_id": policy_id, "policy_number": pol_num}
        except Exception as e:
            return False, f"Error completing policy purchase: {str(e)}", None
        finally:
            conn.close()

    @staticmethod
    def get_customer_policies(customer_id, search="", status_filter=""):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                query = """
                    SELECT p.*, pt.name as policy_type_name, pt.description as policy_description,
                           ag.name as agent_name, ag.email as agent_email
                    FROM policies p
                    JOIN policy_types pt ON p.policy_type_id = pt.id
                    LEFT JOIN users ag ON p.agent_id = ag.id
                    WHERE p.customer_id = %s
                """
                params = [customer_id]

                if search:
                    query += " AND (p.policy_number LIKE %s OR pt.name LIKE %s)"
                    params.extend([f"%{search}%", f"%{search}%"])
                
                if status_filter:
                    query += " AND p.status = %s"
                    params.append(status_filter)

                query += " ORDER BY p.id DESC"
                cursor.execute(query, params)
                return cursor.fetchall()
        finally:
            conn.close()

    @staticmethod
    def get_policy_by_id(policy_id, user_id=None, role='CUSTOMER'):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                query = """
                    SELECT p.*, pt.name as policy_type_name, pt.description as policy_description, pt.duration_months,
                           c.name as customer_name, c.email as customer_email, c.phone as customer_phone,
                           ag.name as agent_name, ag.email as agent_email
                    FROM policies p
                    JOIN policy_types pt ON p.policy_type_id = pt.id
                    JOIN users c ON p.customer_id = c.id
                    LEFT JOIN users ag ON p.agent_id = ag.id
                    WHERE p.id = %s
                """
                cursor.execute(query, (policy_id,))
                pol = cursor.fetchone()
                
                if not pol:
                    return None
                
                # Check authorization
                if role == 'CUSTOMER' and pol['customer_id'] != user_id:
                    return None
                if role == 'AGENT' and pol['agent_id'] != user_id:
                    return None
                    
                return pol
        finally:
            conn.close()

    @staticmethod
    def get_all_policies(search="", status_filter="", agent_id=None):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                query = """
                    SELECT p.*, pt.name as policy_type_name, c.name as customer_name, c.email as customer_email,
                           ag.name as agent_name
                    FROM policies p
                    JOIN policy_types pt ON p.policy_type_id = pt.id
                    JOIN users c ON p.customer_id = c.id
                    LEFT JOIN users ag ON p.agent_id = ag.id
                    WHERE 1=1
                """
                params = []

                if agent_id:
                    query += " AND p.agent_id = %s"
                    params.append(agent_id)

                if search:
                    query += " AND (p.policy_number LIKE %s OR c.name LIKE %s OR pt.name LIKE %s)"
                    params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
                
                if status_filter:
                    query += " AND p.status = %s"
                    params.append(status_filter)

                query += " ORDER BY p.id DESC"
                cursor.execute(query, params)
                return cursor.fetchall()
        finally:
            conn.close()
