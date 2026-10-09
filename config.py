import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "default_insurance_secret_key_2026")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "Abhi@123")
    DB_NAME = os.getenv("DB_NAME", "insurance_management")
    
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

    # Flask-Mail Settings
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "abhidivvela4@gmail.com")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "ratw lrjs olym bcda")
    MAIL_DEFAULT_SENDER = ('ClaimKaro Insurance', os.getenv("MAIL_USERNAME", "abhidivvela4@gmail.com"))

    # Razorpay Settings
    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_TcZ7s5ijrUZvyX")
    RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "FCSUx8KbVxFs8fN0l7EZ2ebM")
