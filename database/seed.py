import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db_connection, init_db
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

def seed_database():
    print("Initializing Database Schema...")
    init_db()
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Check if users already seeded
            cursor.execute("SELECT COUNT(*) as cnt FROM users")
            if cursor.fetchone()['cnt'] > 0:
                print("Database already contains data. Skipping seed.")
                return

            print("Seeding Users and Profiles...")
            # 1. Admin
            admin_pw = generate_password_hash("Admin@123")
            cursor.execute("""
                INSERT INTO users (name, email, phone, password_hash, role, status)
                VALUES (%s, %s, %s, %s, 'ADMIN', 'ACTIVE')
            """, ("System Admin", "admin@insurance.com", "+919876543210", admin_pw))
            admin_id = cursor.lastrowid

            # 2. Agents
            agent_pw = generate_password_hash("Agent@123")
            cursor.execute("""
                INSERT INTO users (name, email, phone, password_hash, role, status)
                VALUES (%s, %s, %s, %s, 'AGENT', 'ACTIVE')
            """, ("Sunil Verma", "agent.sunil@insurance.com", "+919811122233", agent_pw))
            agent1_id = cursor.lastrowid
            cursor.execute("INSERT INTO agent_profiles (user_id, employee_id, department, experience) VALUES (%s, %s, %s, %s)",
                           (agent1_id, "AGT-1001", "Health & Retail Sales", 5))

            cursor.execute("""
                INSERT INTO users (name, email, phone, password_hash, role, status)
                VALUES (%s, %s, %s, %s, 'AGENT', 'ACTIVE')
            """, ("Anita Roy", "agent.anita@insurance.com", "+919822233344", agent_pw))
            agent2_id = cursor.lastrowid
            cursor.execute("INSERT INTO agent_profiles (user_id, employee_id, department, experience) VALUES (%s, %s, %s, %s)",
                           (agent2_id, "AGT-1002", "Motor & Corporate Sales", 7))

            # 3. Claims Officers
            officer_pw = generate_password_hash("Officer@123")
            cursor.execute("""
                INSERT INTO users (name, email, phone, password_hash, role, status)
                VALUES (%s, %s, %s, %s, 'CLAIMS_OFFICER', 'ACTIVE')
            """, ("Rajesh Kumar", "officer.rajesh@insurance.com", "+919833344455", officer_pw))
            officer1_id = cursor.lastrowid
            cursor.execute("INSERT INTO claims_officer_profiles (user_id, employee_id, department) VALUES (%s, %s, %s)",
                           (officer1_id, "CO-5001", "Medical Claims Assessment"))

            cursor.execute("""
                INSERT INTO users (name, email, phone, password_hash, role, status)
                VALUES (%s, %s, %s, %s, 'CLAIMS_OFFICER', 'ACTIVE')
            """, ("Meena Swaminathan", "officer.meena@insurance.com", "+919844455566", officer_pw))
            officer2_id = cursor.lastrowid
            cursor.execute("INSERT INTO claims_officer_profiles (user_id, employee_id, department) VALUES (%s, %s, %s)",
                           (officer2_id, "CO-5002", "Motor & Property Assessment"))

            # 4. Customers
            cust_pw = generate_password_hash("Customer@123")
            cursor.execute("""
                INSERT INTO users (name, email, phone, password_hash, role, status)
                VALUES (%s, %s, %s, %s, 'CUSTOMER', 'ACTIVE')
            """, ("Ravi Sharma", "ravi@example.com", "+919988776655", cust_pw))
            cust1_id = cursor.lastrowid
            cursor.execute("""
                INSERT INTO customer_profiles (user_id, date_of_birth, gender, address, city, state, pincode)
                VALUES (%s, '1990-05-15', 'MALE', '42 Green Park Avenue', 'New Delhi', 'Delhi', '110016')
            """, (cust1_id,))

            cursor.execute("""
                INSERT INTO users (name, email, phone, password_hash, role, status)
                VALUES (%s, %s, %s, %s, 'CUSTOMER', 'ACTIVE')
            """, ("Priya Patel", "priya@example.com", "+919877665544", cust_pw))
            cust2_id = cursor.lastrowid
            cursor.execute("""
                INSERT INTO customer_profiles (user_id, date_of_birth, gender, address, city, state, pincode)
                VALUES (%s, '1994-08-22', 'FEMALE', '108 Bandra West', 'Mumbai', 'Maharashtra', '400050')
            """, (cust2_id,))

            print("Seeding Policy Types...")
            policy_types = [
                ("Health Guard Comprehensive", "Complete family health insurance including cashless hospitalization and ICU cover.", 500000.00, 12500.00, 12),
                ("Super Auto Secure", "Comprehensive motor insurance covering third-party liability and self vehicle damage.", 300000.00, 8500.00, 12),
                ("Life Protect Term Plan", "High sum assured term life insurance providing total financial stability.", 5000000.00, 24000.00, 12),
                ("Home & Property Shield", "Coverage against fire, burglary, flood, and natural disaster structural damage.", 2000000.00, 9500.00, 12),
                ("Global Travel Care", "Medical emergency and loss of baggage coverage for international travel.", 100000.00, 3200.00, 6)
            ]
            pt_ids = []
            for name, desc, cov, prem, dur in policy_types:
                cursor.execute("""
                    INSERT INTO policy_types (name, description, coverage, premium, duration_months, status)
                    VALUES (%s, %s, %s, %s, %s, 'ACTIVE')
                """, (name, desc, cov, prem, dur))
                pt_ids.append(cursor.lastrowid)

            print("Seeding Active Customer Policies...")
            today = datetime.today().date()
            start_date_1 = today - timedelta(days=60)
            end_date_1 = start_date_1 + timedelta(days=365)

            start_date_2 = today - timedelta(days=340)
            end_date_2 = today + timedelta(days=25) # Expiring soon!

            start_date_3 = today - timedelta(days=30)
            end_date_3 = start_date_3 + timedelta(days=365)

            # Policy 1: Ravi - Health Guard
            cursor.execute("""
                INSERT INTO policies (policy_number, policy_type_id, customer_id, agent_id, start_date, end_date, premium, coverage_amount, status)
                VALUES ('POL202600001', %s, %s, %s, %s, %s, 12500.00, 500000.00, 'ACTIVE')
            """, (pt_ids[0], cust1_id, agent1_id, start_date_1, end_date_1))
            pol1_id = cursor.lastrowid

            # Policy 2: Ravi - Super Auto (Expiring in 25 days)
            cursor.execute("""
                INSERT INTO policies (policy_number, policy_type_id, customer_id, agent_id, start_date, end_date, premium, coverage_amount, status)
                VALUES ('POL202600002', %s, %s, %s, %s, %s, 8500.00, 300000.00, 'ACTIVE')
            """, (pt_ids[1], cust1_id, agent2_id, start_date_2, end_date_2))
            pol2_id = cursor.lastrowid

            # Policy 3: Priya - Life Protect
            cursor.execute("""
                INSERT INTO policies (policy_number, policy_type_id, customer_id, agent_id, start_date, end_date, premium, coverage_amount, status)
                VALUES ('POL202600003', %s, %s, %s, %s, %s, 24000.00, 5000000.00, 'ACTIVE')
            """, (pt_ids[2], cust2_id, agent1_id, start_date_3, end_date_3))
            pol3_id = cursor.lastrowid

            print("Seeding Claims...")
            # Claim 1: Ravi Sharma - Health Policy Emergency Hospitalization (SUBMITTED)
            cursor.execute("""
                INSERT INTO claims (claim_number, policy_id, customer_id, reason, description, claim_amount, claim_date, status, assigned_officer_id)
                VALUES ('CLM202600001', %s, %s, 'Emergency Hospitalization', 'Admitted for acute gastroenteritis treatment at Max Healthcare for 3 days.', 45000.00, %s, 'SUBMITTED', %s)
            """, (pol1_id, cust1_id, today - timedelta(days=5), officer1_id))
            clm1_id = cursor.lastrowid

            # Claim 2: Priya Patel - Auto Bumper Repair (UNDER_REVIEW)
            cursor.execute("""
                INSERT INTO claims (claim_number, policy_id, customer_id, reason, description, claim_amount, claim_date, status, assigned_officer_id)
                VALUES ('CLM202600002', %s, %s, 'Accidental Vehicle Damage', 'Front bumper damaged due to collision with parking pillar.', 18500.00, %s, 'UNDER_REVIEW', %s)
            """, (pol2_id, cust2_id, today - timedelta(days=10), officer2_id))
            clm2_id = cursor.lastrowid

            # Claim 3: Ravi Sharma - Approved claim
            cursor.execute("""
                INSERT INTO claims (claim_number, policy_id, customer_id, reason, description, claim_amount, claim_date, status, assigned_officer_id)
                VALUES ('CLM202600003', %s, %s, 'Diagnostic & Pharmacy Reimbursement', 'Routine health checkup and specialized blood test labs.', 6200.00, %s, 'APPROVED', %s)
            """, (pol1_id, cust1_id, today - timedelta(days=20), officer1_id))
            clm3_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO claim_reviews (claim_id, officer_id, decision, remarks)
                VALUES (%s, %s, 'APPROVED', 'All original hospital medical bills and discharge summary verified successfully.')
            """, (clm3_id, officer1_id))

            print("Seeding Support Tickets & Messages...")
            # Ticket 1: Ravi Sharma
            cursor.execute("""
                INSERT INTO support_tickets (ticket_number, customer_id, category, subject, description, priority, status, assigned_to)
                VALUES ('TKT202600001', %s, 'Claim', 'Inquiry regarding hospital bill reimbursement status', 'Hi, I submitted claim CLM202600001 5 days ago and need an update on review.', 'HIGH', 'OPEN', %s)
            """, (cust1_id, agent1_id))
            tkt1_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO ticket_messages (ticket_id, sender_id, message)
                VALUES (%s, %s, 'Hi, I submitted claim CLM202600001 5 days ago and need an update on review.')
            """, (tkt1_id, cust1_id))

            cursor.execute("""
                INSERT INTO ticket_messages (ticket_id, sender_id, message)
                VALUES (%s, %s, 'Hello Ravi, our Claims Officer Rajesh Kumar is currently reviewing your medical documents. We will update the status shortly.')
            """, (tkt1_id, agent1_id))

            print("Seeding Notifications...")
            cursor.execute("""
                INSERT INTO notifications (user_id, title, message, type)
                VALUES (%s, 'Policy Renewal Alert', 'Your Super Auto Secure policy POL202600002 expires in 25 days. Renew now to avoid lapse!', 'WARNING')
            """, (cust1_id,))

            cursor.execute("""
                INSERT INTO notifications (user_id, title, message, type)
                VALUES (%s, 'Claim CLM202600003 Approved', 'Your claim for Diagnostic Reimbursement of Rs 6,200 has been approved!', 'SUCCESS')
            """, (cust1_id,))

            print("Seeding Audit Logs...")
            cursor.execute("""
                INSERT INTO audit_logs (user_id, action, module, description)
                VALUES (%s, 'SYSTEM_INIT', 'DATABASE', 'Initial database seed executed successfully.')
            """, (admin_id,))

            print("Database Seeding Completed Successfully!")
    except Exception as e:
        print(f"Error during database seed: {e}")
        raise e

if __name__ == "__main__":
    seed_database()
