from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from services.auth_service import AuthService
from utils.helpers import api_response
from utils.decorators import login_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login_view():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
        else:
            email = request.form.get('email')
            password = request.form.get('password')

        success, message, user = AuthService.authenticate(email, password)
        if success:
            session['user_id'] = user['id']
            session['name'] = user['name']
            session['email'] = user['email']
            session['role'] = user['role']

            # Determine redirect URL based on role
            redirect_url = url_for('customer.dashboard_view')
            if user['role'] == 'ADMIN':
                redirect_url = url_for('admin.dashboard_view')
            elif user['role'] == 'CLAIMS_OFFICER':
                redirect_url = url_for('officer.dashboard_view')
            elif user['role'] == 'AGENT':
                redirect_url = url_for('agent.dashboard_view')

            if request.is_json:
                return api_response(True, message, {"user": user, "redirect_url": redirect_url})
            flash(message, "success")
            return redirect(redirect_url)
        else:
            if request.is_json:
                return api_response(False, message, status_code=401)
            flash(message, "danger")

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register_view():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone')
        password = data.get('password')
        role = data.get('role', 'CUSTOMER')
        dob = data.get('date_of_birth')
        gender = data.get('gender')
        address = data.get('address')
        city = data.get('city')
        state = data.get('state')
        pincode = data.get('pincode')
        otp_code = data.get('otp')

        success, message, res_data = AuthService.register_user(
            name, email, phone, password, role, dob, gender, address, city, state, pincode, otp_code
        )

        if success:
            if request.is_json:
                return api_response(True, message, res_data)
            flash(message + " Please login with your credentials.", "success")
            return redirect(url_for('auth.login_view'))
        else:
            if request.is_json:
                return api_response(False, message, status_code=400)
            flash(message, "danger")

    return render_template('auth/register.html')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password_view():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = data.get('email')
        otp_code = data.get('otp')
        new_password = data.get('new_password')
        action = data.get('action', 'send_otp')

        if action == 'send_otp':
            success, msg, _ = AuthService.send_forgot_password_otp(email)
            if request.is_json:
                return api_response(success, msg, status_code=200 if success else 400)
            flash(msg, "info" if success else "danger")
        elif action == 'reset_password':
            success, msg = AuthService.reset_password_with_otp(email, otp_code, new_password)
            if request.is_json:
                return api_response(success, msg, status_code=200 if success else 400)
            if success:
                flash(msg, "success")
                return redirect(url_for('auth.login_view'))
            flash(msg, "danger")

    return render_template('auth/forgot_password.html')

@auth_bp.route('/api/auth/send-register-otp', methods=['POST'])
def send_register_otp_api():
    data = request.get_json() or {}
    email = data.get('email')
    success, msg, _ = AuthService.send_register_otp(email)
    return api_response(success, msg, status_code=200 if success else 400)

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('auth.login_view'))

@auth_bp.route('/api/auth/profile', methods=['GET'])
@login_required
def get_profile_api():
    profile = AuthService.get_user_profile(session['user_id'])
    return api_response(True, "Profile fetched", profile)

@auth_bp.route('/api/auth/change-password', methods=['POST'])
@login_required
def change_password_api():
    data = request.get_json() or {}
    old_pw = data.get('old_password')
    new_pw = data.get('new_password')
    success, message = AuthService.change_password(session['user_id'], old_pw, new_pw)
    return api_response(success, message, status_code=200 if success else 400)
