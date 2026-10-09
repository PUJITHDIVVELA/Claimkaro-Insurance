import os
from flask import Flask, render_template, session, redirect, url_for, request
from flask_cors import CORS
from config import Config
from database.connection import init_db
from database.seed import seed_database

# Import Blueprints
from routes.auth_routes import auth_bp
from routes.customer_routes import customer_bp
from routes.agent_routes import agent_bp
from routes.officer_routes import officer_bp
from routes.admin_routes import admin_bp
from routes.policy_routes import policy_bp
from routes.claim_routes import claim_bp
from routes.ticket_routes import ticket_bp
from routes.chatbot_routes import chatbot_bp
from routes.notification_routes import notif_bp
from utils.helpers import api_response

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable CORS
    CORS(app)

    # Ensure Uploads Directory Exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize Database Schema & Seed Data
    try:
        init_db()
        seed_database()
    except Exception as e:
        print(f"Warning: Database initialization/seed on startup: {e}")

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(agent_bp)
    app.register_blueprint(officer_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(policy_bp)
    app.register_blueprint(claim_bp)
    app.register_blueprint(ticket_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(notif_bp)

    @app.route('/')
    def landing_page():
        return render_template('index.html')

    # Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith('/api/'):
            return api_response(False, "Resource not found", status_code=404)
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        if request.path.startswith('/api/'):
            return api_response(False, "Internal server error", status_code=500)
        return render_template('errors/500.html'), 500

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
