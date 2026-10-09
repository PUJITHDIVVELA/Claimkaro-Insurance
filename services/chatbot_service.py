from database.connection import get_db_connection
from services.ticket_service import TicketService
import re

class ChatbotService:
    @staticmethod
    def get_or_create_conversation(customer_id):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM chatbot_conversations WHERE customer_id = %s ORDER BY id DESC LIMIT 1", (customer_id,))
                conv = cursor.fetchone()
                if conv:
                    return conv['id']
                
                cursor.execute("INSERT INTO chatbot_conversations (customer_id) VALUES (%s)", (customer_id,))
                return cursor.lastrowid
        finally:
            conn.close()

    @staticmethod
    def get_conversation_history(customer_id):
        conv_id = ChatbotService.get_or_create_conversation(customer_id)
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT sender_type, message, created_at
                    FROM chatbot_messages
                    WHERE conversation_id = %s
                    ORDER BY id ASC
                """, (conv_id,))
                return cursor.fetchall()
        finally:
            conn.close()

    @staticmethod
    def process_user_message(customer_id, user_text, session_state=None):
        conv_id = ChatbotService.get_or_create_conversation(customer_id)
        user_msg = user_text.strip()
        lower_msg = user_msg.lower()

        # Save user message to database
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO chatbot_messages (conversation_id, sender_type, message) VALUES (%s, 'user', %s)",
                               (conv_id, user_msg))
        finally:
            conn.close()

        bot_reply = ""

        # Priority 1: Handle Ticket Creation syntax
        if lower_msg.startswith("ticket:") or lower_msg.startswith("ticket :"):
            parts = [p.strip() for p in user_msg[7:].split("|")]
            if len(parts) >= 3:
                cat, subj, desc = parts[0], parts[1], parts[2]
                success, msg, data = TicketService.create_ticket(customer_id, cat, subj, desc)
                if success:
                    bot_reply = f"✅ **Support Ticket Created Successfully!**\n\nTicket Number: **{data['ticket_number']}**\nCategory: {cat}\nSubject: {subj}\n\nOur support team will respond shortly under **Support Tickets**."
                else:
                    bot_reply = f"❌ Could not create ticket: {msg}"
            else:
                bot_reply = "Invalid ticket format. Please use: `TICKET: Category | Subject | Description`"

        # Priority 2: Check ticket creation trigger phrase
        elif "raise a ticket" in lower_msg or "create ticket" in lower_msg or "support ticket" in lower_msg or "raise ticket" in lower_msg:
            bot_reply = ("I can assist you in creating a support ticket immediately! 🎫\n\n"
                         "Please reply with your issue details in this format:\n"
                         "**Category: Claim** (or Policy, Payment, Documents, Technical, Other)\n"
                         "**Subject: [Short Title]**\n"
                         "**Details: [Describe your issue]**\n\n"
                         "Or simply type: `TICKET: Category | Subject | Details`")

        # Priority 3: Handle live DB queries for authenticated customer claims
        elif "claim status" in lower_msg or "my claim" in lower_msg or "status of claim" in lower_msg:
            conn = get_db_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT c.claim_number, c.status, c.claim_amount, c.reason, pt.name as policy_name
                        FROM claims c
                        JOIN policies p ON c.policy_id = p.id
                        JOIN policy_types pt ON p.policy_type_id = pt.id
                        WHERE c.customer_id = %s
                        ORDER BY c.id DESC LIMIT 3
                    """, (customer_id,))
                    claims = cursor.fetchall()
                    if claims:
                        reply_lines = ["📋 **Here are your recent claims:**"]
                        for clm in claims:
                            reply_lines.append(f"• **Claim #{clm['claim_number']}** ({clm['policy_name']}): Status is **{clm['status']}** for Rs {float(clm['claim_amount']):,.2f}.")
                        reply_lines.append("\nYou can click on **My Claims** in your dashboard for complete tracking!")
                        bot_reply = "\n".join(reply_lines)
                    else:
                        bot_reply = "You currently have no claims submitted under your account. You can submit a new claim directly from your dashboard."
            finally:
                conn.close()

        # Priority 4: Handle live DB queries for customer policies
        elif "my policy" in lower_msg or "policies" in lower_msg or "active policy" in lower_msg or "expiry" in lower_msg:
            conn = get_db_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT p.policy_number, p.status, p.end_date, p.coverage_amount, pt.name as policy_name
                        FROM policies p
                        JOIN policy_types pt ON p.policy_type_id = pt.id
                        WHERE p.customer_id = %s
                        ORDER BY p.id DESC
                    """, (customer_id,))
                    pols = cursor.fetchall()
                    if pols:
                        reply_lines = ["🛡️ **Your Enrolled Policies:**"]
                        for p in pols:
                            reply_lines.append(f"• **{p['policy_name']}** ({p['policy_number']}): Status **{p['status']}**, Coverage Rs {float(p['coverage_amount']):,.2f}, Expires: {p['end_date']}.")
                        bot_reply = "\n".join(reply_lines)
                    else:
                        bot_reply = "You do not have any active policies yet. Check out **Available Policies** in your menu to purchase coverage!"
            finally:
                conn.close()

        # Priority 5: Guidance & FAQ answers
        elif "submit claim" in lower_msg or "how to claim" in lower_msg or "file claim" in lower_msg:
            bot_reply = ("To file a new claim:\n"
                         "1. Go to **Submit Claim** from your Customer Dashboard sidebar.\n"
                         "2. Select your active policy.\n"
                         "3. Enter claim reason, description, and claim amount.\n"
                         "4. Upload supporting documents (Hospital bills, damage photos, invoice - PDF/PNG/JPG).\n"
                         "5. Click **Submit Claim**.")

        elif "document" in lower_msg or "upload" in lower_msg:
            bot_reply = ("Supported document formats: **PDF, PNG, JPG, JPEG** (Max size: 16MB).\n"
                         "You can upload documents during claim submission or upload missing documents directly on your **Claim Details** page.")

        elif "contact" in lower_msg or "phone" in lower_msg or "email" in lower_msg or "human" in lower_msg:
            bot_reply = ("You can reach our customer support team 24/7:\n"
                         "📞 **Helpline:** +91 1800-123-4567\n"
                         "📧 **Support Email:** support@insurance-enterprise.com\n"
                         "Or raise a support ticket directly using the chat!")

        else:
            bot_reply = (f"Hello! I am your AI Insurance Assistant. 🛡️\n\n"
                         "Here is what I can help you with:\n"
                         "• Type **'my claim status'** to view your recent claims\n"
                         "• Type **'my policies'** to view your active policies & expiries\n"
                         "• Type **'how to submit claim'** for step-by-step guidance\n"
                         "• Type **'raise a ticket'** to create a support ticket directly\n\n"
                         "How can I assist you right now?")

        # Save bot response to database
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO chatbot_messages (conversation_id, sender_type, message) VALUES (%s, 'bot', %s)",
                               (conv_id, bot_reply))
        finally:
            conn.close()

        return bot_reply
