from database.connection import get_db_connection
from datetime import datetime, timedelta

class NotificationService:
    @staticmethod
    def get_user_notifications(user_id, limit=10):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM notifications
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (user_id, limit))
                return cursor.fetchall()
        finally:
            conn.close()

    @staticmethod
    def mark_as_read(notification_id, user_id):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE notifications SET is_read = TRUE WHERE id = %s AND user_id = %s", (notification_id, user_id))
            return True
        finally:
            conn.close()

    @staticmethod
    def mark_all_read(user_id):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE notifications SET is_read = TRUE WHERE user_id = %s", (user_id,))
            return True
        finally:
            conn.close()

    @staticmethod
    def check_and_create_expiry_alerts(user_id):
        """Scans policies for impending expiry (30, 7, 1 days) and creates notifications."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                today = datetime.today().date()
                cursor.execute("""
                    SELECT p.id, p.policy_number, p.end_date, pt.name as policy_type_name
                    FROM policies p
                    JOIN policy_types pt ON p.policy_type_id = pt.id
                    WHERE p.customer_id = %s AND p.status = 'ACTIVE'
                """, (user_id,))
                policies = cursor.fetchall()

                for pol in policies:
                    end_date = pol['end_date']
                    days_remaining = (end_date - today).days

                    if days_remaining in [30, 7, 1]:
                        title = f"Policy Expiry Warning: {pol['policy_number']}"
                        msg = f"Your {pol['policy_type_name']} ({pol['policy_number']}) will expire in {days_remaining} day(s) on {end_date}. Renew today!"
                        
                        # Prevent duplicate notifications on same day
                        cursor.execute("""
                            SELECT id FROM notifications
                            WHERE user_id = %s AND title = %s AND DATE(created_at) = CURRENT_DATE()
                        """, (user_id, title))
                        if not cursor.fetchone():
                            cursor.execute("""
                                INSERT INTO notifications (user_id, title, message, type)
                                VALUES (%s, %s, %s, 'WARNING')
                            """, (user_id, title, msg))
        finally:
            conn.close()
