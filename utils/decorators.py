from functools import wraps
from flask import session, redirect, url_for, flash, request
from utils.helpers import api_response

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json or '/api/' in request.path:
                return api_response(False, "Unauthorized access. Please log in.", status_code=401)
            flash("Please login to access this page", "warning")
            return redirect(url_for('auth.login_view'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json or '/api/' in request.path:
                    return api_response(False, "Unauthorized access. Please log in.", status_code=401)
                flash("Please login to access this page", "warning")
                return redirect(url_for('auth.login_view'))
            
            user_role = session.get('role')
            if user_role not in allowed_roles:
                if request.is_json or '/api/' in request.path:
                    return api_response(False, f"Access denied for role '{user_role}'.", status_code=403)
                flash("You are not authorized to access this page", "danger")
                # Redirect based on user's actual role
                if user_role == 'ADMIN':
                    return redirect(url_for('admin.dashboard_view'))
                elif user_role == 'CLAIMS_OFFICER':
                    return redirect(url_for('officer.dashboard_view'))
                elif user_role == 'AGENT':
                    return redirect(url_for('agent.dashboard_view'))
                else:
                    return redirect(url_for('customer.dashboard_view'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
