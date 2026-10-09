import unittest
import sys
import os
import io
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from database.connection import get_db_connection
from database.seed import seed_database
from utils.mail_handler import create_and_send_otp, verify_otp_code

class InsuranceSystemComprehensiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Seed database and initialize test client."""
        seed_database()
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def login_user(self, email, password):
        return self.client.post('/login', json={'email': email, 'password': password})

    def test_01_authentication_flow(self):
        """Test user login for all 4 roles and invalid login attempt."""
        res = self.login_user("ravi@example.com", "Customer@123")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['user']['role'], 'CUSTOMER')

        res = self.login_user("officer.rajesh@insurance.com", "Officer@123")
        self.assertEqual(res.status_code, 200)

        res = self.login_user("agent.sunil@insurance.com", "Agent@123")
        self.assertEqual(res.status_code, 200)

        res = self.login_user("admin@insurance.com", "Admin@123")
        self.assertEqual(res.status_code, 200)

    def test_02_otp_and_forgot_password_flow(self):
        """Test OTP generation, validation, and Forgot Password reset."""
        test_email = f"testuser_{int(time.time())}@example.com"

        # 1. Send OTP for Registration
        res = self.client.post('/api/auth/send-register-otp', json={'email': test_email})
        self.assertEqual(res.status_code, 200)

        # 2. Get Generated OTP from DB for testing
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT otp_code FROM email_otps WHERE email = %s ORDER BY id DESC LIMIT 1", (test_email,))
            otp_record = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(otp_record)
        otp = otp_record['otp_code']

        # 3. Register Customer with OTP
        res = self.client.post('/register', json={
            'name': 'Test OTP User',
            'email': test_email,
            'phone': '+919876549999',
            'password': 'Customer@123',
            'role': 'CUSTOMER',
            'otp': otp
        })
        self.assertEqual(res.status_code, 200)

        # 4. Forgot Password Flow
        res = self.client.post('/forgot-password', json={
            'action': 'send_otp',
            'email': test_email
        })
        self.assertEqual(res.status_code, 200)

        # Get Reset OTP
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT otp_code FROM email_otps WHERE email = %s AND purpose = 'FORGOT_PASSWORD' ORDER BY id DESC LIMIT 1", (test_email,))
            fp_record = cursor.fetchone()
        conn.close()
        fp_otp = fp_record['otp_code']

        # Reset Password
        res = self.client.post('/forgot-password', json={
            'action': 'reset_password',
            'email': test_email,
            'otp': fp_otp,
            'new_password': 'NewPassword@123'
        })
        self.assertEqual(res.status_code, 200)

        # Verify Login with New Password
        res = self.login_user(test_email, "NewPassword@123")
        self.assertEqual(res.status_code, 200)

    def test_03_razorpay_payment_order_flow(self):
        """Test Razorpay Order creation API."""
        self.login_user("ravi@example.com", "Customer@123")
        res = self.client.post('/api/policies/create-payment-order', json={'policy_type_id': 1})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()['data']
        self.assertIn('order_id', data)
        self.assertIn('key_id', data)
        self.assertIn('amount', data)

    def test_04_claim_submission_and_document_upload(self):
        """Test filing a new claim and uploading proof document."""
        self.login_user("ravi@example.com", "Customer@123")
        res = self.client.get('/api/policies')
        policies = res.get_json()['data']
        policy_id = policies[0]['id']

        data = {
            'policy_id': policy_id,
            'reason': 'Automated Test Hospitalization',
            'description': 'Submitted via automated test suite',
            'claim_amount': '12500.00',
            'claim_date': '2026-09-28',
            'document': (io.BytesIO(b"Medical Discharge Summary Test Content"), "discharge_summary.pdf")
        }
        res = self.client.post('/api/claims/submit', data=data, content_type='multipart/form-data')
        self.assertEqual(res.status_code, 201)

    def test_05_officer_review_and_approval(self):
        """Test Claims Officer assessing, reviewing, and approving a claim."""
        self.login_user("officer.rajesh@insurance.com", "Officer@123")
        res = self.client.get('/api/claims')
        claims = res.get_json()['data']
        pending_claims = [c for c in claims if c['status'] == 'SUBMITTED']
        self.assertGreater(len(pending_claims), 0)

        target_claim_id = pending_claims[0]['id']
        res = self.client.post(f'/api/claims/{target_claim_id}/review', json={
            'decision': 'APPROVED',
            'remarks': 'Approved after complete verification of medical bills.'
        })
        self.assertEqual(res.status_code, 200)

    def test_06_chatbot_live_db_queries_and_ticket_creation(self):
        """Test AI Chatbot queries against real DB data and direct ticket creation."""
        self.login_user("ravi@example.com", "Customer@123")
        res = self.client.post('/api/chatbot/message', json={'message': 'What is my claim status?'})
        self.assertEqual(res.status_code, 200)
        self.assertIn("Here are your recent claims", res.get_json()['data']['reply'])

        res = self.client.post('/api/chatbot/message', json={
            'message': 'TICKET: Claim | Billing Delay | My claim payout is delayed by 3 days'
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn("Support Ticket Created Successfully", res.get_json()['data']['reply'])

    def test_07_admin_metrics_and_audit_logs(self):
        """Test System Admin metrics dashboard and Audit Log recording."""
        self.login_user("admin@insurance.com", "Admin@123")
        res = self.client.get('/admin/api/dashboard-summary')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()['data']
        self.assertGreater(data['total_users'], 0)

if __name__ == '__main__':
    unittest.main()
