import random
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config
from database.connection import get_db_connection
import logging

logger = logging.getLogger(__name__)

def generate_otp_code():
    return str(random.randint(100000, 999999))

def send_email_smtp(recipient_email, subject, body_html):
    """Sends HTML email using configured SMTP credentials with fallback ports."""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"ClaimKaro Insurance <{Config.MAIL_USERNAME}>"
        msg['To'] = recipient_email

        html_part = MIMEText(body_html, 'html')
        msg.attach(html_part)

        # Try Primary SMTP configuration
        try:
            if Config.MAIL_PORT == 465:
                server = smtplib.SMTP_SSL(Config.MAIL_SERVER, Config.MAIL_PORT, timeout=10)
            else:
                server = smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT, timeout=10)
                if Config.MAIL_USE_TLS:
                    server.starttls()
            server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
            server.sendmail(Config.MAIL_USERNAME, recipient_email, msg.as_string())
            server.quit()
        except Exception as e_primary:
            logger.warning(f"Primary SMTP port failed: {e_primary}, trying fallback SSL port 465...")
            # Fallback to SSL port 465
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10)
            server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
            server.sendmail(Config.MAIL_USERNAME, recipient_email, msg.as_string())
            server.quit()

        logger.info(f"Email sent successfully to {recipient_email}")
        return True, "Email sent successfully"
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_email}: {e}")
        return False, str(e)

def create_and_send_otp(email, purpose):
    otp_code = generate_otp_code()
    expires_at = datetime.datetime.now() + datetime.timedelta(minutes=10)

    # Save to Database
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE email_otps SET is_verified = TRUE 
                WHERE email = %s AND purpose = %s
            """, (email, purpose))

            cursor.execute("""
                INSERT INTO email_otps (email, otp_code, purpose, expires_at)
                VALUES (%s, %s, %s, %s)
            """, (email, otp_code, purpose, expires_at))
    finally:
        conn.close()

    # Compose HTML Email
    purpose_title = "Account Registration" if purpose == "REGISTRATION" else "Password Reset Request"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 550px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
        <h2 style="color: #0f172a; text-align: center;">🛡️ ClaimKaro Insurance</h2>
        <h3 style="color: #2563eb; text-align: center;">{purpose_title} Verification Code</h3>
        <p>Hello,</p>
        <p>Your 6-digit OTP verification code is:</p>
        <div style="background: #f1f5f9; font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #0f172a; text-align: center; padding: 15px; border-radius: 6px; margin: 20px 0;">
            {otp_code}
        </div>
        <p>This code is valid for <strong>10 minutes</strong>. Please do not share this OTP with anyone.</p>
        <p style="color: #64748b; font-size: 12px; margin-top: 30px; text-align: center;">ClaimKaro Enterprise Insurance Platform</p>
    </div>
    """

    success, msg = send_email_smtp(email, f"ClaimKaro OTP Verification: {otp_code}", html_content)
    return success, msg, otp_code

def verify_otp_code(email, otp_code, purpose):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM email_otps
                WHERE email = %s AND otp_code = %s AND purpose = %s AND is_verified = FALSE AND expires_at >= NOW()
                ORDER BY id DESC LIMIT 1
            """, (email, otp_code, purpose))
            record = cursor.fetchone()

            if not record:
                return False, "Invalid or expired OTP verification code."

            # Mark OTP as verified
            cursor.execute("UPDATE email_otps SET is_verified = TRUE WHERE id = %s", (record['id'],))
            return True, "OTP verified successfully!"
    finally:
        conn.close()
