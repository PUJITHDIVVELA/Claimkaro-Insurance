from flask import Blueprint, render_template, session, request
from utils.decorators import role_required
from services.admin_service import AdminService
from services.auth_service import AuthService
from services.policy_service import PolicyService
from services.claim_service import ClaimService
from services.ticket_service import TicketService
from utils.helpers import api_response

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@role_required('ADMIN')
def dashboard_view():
    return render_template('admin/dashboard.html')

@admin_bp.route('/users')
@role_required('ADMIN')
def users_view():
    return render_template('admin/users.html')

@admin_bp.route('/policy-types')
@role_required('ADMIN')
def policy_types_view():
    return render_template('admin/policy_types.html')

@admin_bp.route('/policies')
@role_required('ADMIN')
def policies_view():
    return render_template('admin/policies.html')

@admin_bp.route('/claims')
@role_required('ADMIN')
def claims_view():
    return render_template('admin/claims.html')

@admin_bp.route('/tickets')
@role_required('ADMIN')
def tickets_view():
    return render_template('admin/tickets.html')

@admin_bp.route('/audit-logs')
@role_required('ADMIN')
def audit_logs_view():
    return render_template('admin/audit_logs.html')

@admin_bp.route('/api/dashboard-summary')
@role_required('ADMIN')
def admin_dashboard_api():
    metrics = AdminService.get_dashboard_metrics()
    return api_response(True, "Admin dashboard metrics fetched", metrics)

@admin_bp.route('/api/users', methods=['GET'])
@role_required('ADMIN')
def list_users_api():
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '')
    users = AdminService.get_all_users(role_filter, status_filter, search)
    return api_response(True, "Users retrieved", users)

@admin_bp.route('/api/users/create-staff', methods=['POST'])
@role_required('ADMIN')
def create_staff_user_api():
    data = request.get_json() or {}
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password')
    role = data.get('role')

    if role not in ['AGENT', 'CLAIMS_OFFICER', 'ADMIN']:
        return api_response(False, "Invalid staff role specified.", status_code=400)

    success, msg, res_data = AuthService.register_user(
        name, email, phone, password, role
    )
    return api_response(success, msg, res_data, status_code=201 if success else 400)

@admin_bp.route('/api/users/<int:target_user_id>/status', methods=['POST'])
@role_required('ADMIN')
def update_user_status_api(target_user_id):
    data = request.get_json() or {}
    new_status = data.get('status')
    success, msg = AdminService.update_user_status(session['user_id'], target_user_id, new_status)
    return api_response(success, msg, status_code=200 if success else 400)

@admin_bp.route('/api/policy-types', methods=['POST'])
@role_required('ADMIN')
def create_policy_type_api():
    data = request.get_json() or {}
    name = data.get('name')
    desc = data.get('description')
    cov = data.get('coverage')
    prem = data.get('premium')
    dur = data.get('duration_months', 12)

    success, msg, res = AdminService.create_policy_type(session['user_id'], name, desc, cov, prem, dur)
    return api_response(success, msg, res, status_code=201 if success else 400)

@admin_bp.route('/api/audit-logs', methods=['GET'])
@role_required('ADMIN')
def get_audit_logs_api():
    logs = AdminService.get_audit_logs(limit=200)
    return api_response(True, "Audit logs retrieved", logs)
