from database.connection import get_db_connection
from utils.helpers import generate_ticket_number, log_audit

class TicketService:
    @staticmethod
    def create_ticket(customer_id, category, subject, description, priority='MEDIUM'):
        if not category or not subject or not description:
            return False, "Category, subject, and description are required.", None

        tkt_num = generate_ticket_number()
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO support_tickets (ticket_number, customer_id, category, subject, description, priority, status)
                    VALUES (%s, %s, %s, %s, %s, %s, 'OPEN')
                """, (tkt_num, customer_id, category, subject, description, priority))
                ticket_id = cursor.lastrowid

                # Initial message
                cursor.execute("""
                    INSERT INTO ticket_messages (ticket_id, sender_id, message)
                    VALUES (%s, %s, %s)
                """, (ticket_id, customer_id, description))

                # Create notification
                cursor.execute("""
                    INSERT INTO notifications (user_id, title, message, type)
                    VALUES (%s, %s, %s, 'INFO')
                """, (customer_id, "Support Ticket Raised", f"Ticket {tkt_num} has been created. Our support team will respond shortly."))

            log_audit(customer_id, "TICKET_CREATE", "SUPPORT", f"Created ticket {tkt_num}")
            return True, f"Support ticket {tkt_num} created successfully.", {"ticket_id": ticket_id, "ticket_number": tkt_num}
        except Exception as e:
            return False, f"Failed to create ticket: {str(e)}", None
        finally:
            conn.close()

    @staticmethod
    def get_tickets(user_id=None, role='CUSTOMER', status_filter="", search=""):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                query = """
                    SELECT st.*, c.name as customer_name, c.email as customer_email,
                           ast.name as assigned_name
                    FROM support_tickets st
                    JOIN users c ON st.customer_id = c.id
                    LEFT JOIN users ast ON st.assigned_to = ast.id
                    WHERE 1=1
                """
                params = []

                if role == 'CUSTOMER':
                    query += " AND st.customer_id = %s"
                    params.append(user_id)
                elif role == 'AGENT':
                    query += " AND (st.assigned_to = %s OR st.assigned_to IS NULL)"
                    params.append(user_id)

                if status_filter:
                    query += " AND st.status = %s"
                    params.append(status_filter)

                if search:
                    query += " AND (st.ticket_number LIKE %s OR st.subject LIKE %s OR c.name LIKE %s)"
                    params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

                query += " ORDER BY st.id DESC"
                cursor.execute(query, params)
                return cursor.fetchall()
        finally:
            conn.close()

    @staticmethod
    def get_ticket_details(ticket_id, user_id=None, role='CUSTOMER'):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT st.*, c.name as customer_name, c.email as customer_email,
                           ast.name as assigned_name
                    FROM support_tickets st
                    JOIN users c ON st.customer_id = c.id
                    LEFT JOIN users ast ON st.assigned_to = ast.id
                    WHERE st.id = %s
                """, (ticket_id,))
                ticket = cursor.fetchone()

                if not ticket:
                    return None

                if role == 'CUSTOMER' and ticket['customer_id'] != user_id:
                    return None

                # Fetch chat messages
                cursor.execute("""
                    SELECT tm.*, u.name as sender_name, u.role as sender_role
                    FROM ticket_messages tm
                    JOIN users u ON tm.sender_id = u.id
                    WHERE tm.ticket_id = %s
                    ORDER BY tm.created_at ASC
                """, (ticket_id,))
                messages = cursor.fetchall()
                ticket['messages'] = messages
                return ticket
        finally:
            conn.close()

    @staticmethod
    def add_message(ticket_id, sender_id, message_text):
        if not message_text or not message_text.strip():
            return False, "Message text cannot be empty."

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM support_tickets WHERE id = %s", (ticket_id,))
                tkt = cursor.fetchone()
                if not tkt:
                    return False, "Ticket not found."

                cursor.execute("""
                    INSERT INTO ticket_messages (ticket_id, sender_id, message)
                    VALUES (%s, %s, %s)
                """, (ticket_id, sender_id, message_text))

                # Update ticket timestamp and status if resolved/in_progress
                cursor.execute("UPDATE support_tickets SET updated_at = CURRENT_TIMESTAMP WHERE id = %s", (ticket_id,))

                # If sender is agent/admin, notify customer
                if sender_id != tkt['customer_id']:
                    cursor.execute("""
                        INSERT INTO notifications (user_id, title, message, type)
                        VALUES (%s, %s, %s, 'INFO')
                    """, (tkt['customer_id'], f"Update on Ticket {tkt['ticket_number']}", f"Support responded: '{message_text[:60]}...'"))

            return True, "Message sent successfully."
        except Exception as e:
            return False, f"Failed to send message: {str(e)}"
        finally:
            conn.close()

    @staticmethod
    def update_ticket_status(ticket_id, status, assigned_to=None):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                query = "UPDATE support_tickets SET status = %s"
                params = [status]
                if assigned_to:
                    query += ", assigned_to = %s"
                    params.append(assigned_to)
                query += " WHERE id = %s"
                params.append(ticket_id)

                cursor.execute(query, params)
            return True, "Ticket status updated."
        finally:
            conn.close()
