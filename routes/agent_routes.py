from flask import Blueprint, render_template, session
from utils.decorators import role_required
from services.policy_service import PolicyService
from services.claim_service import ClaimService
from services.admin_service import AdminService
from utils.helpers import api_response

agent_bp = Blueprint('agent', __name__, url_prefix='/agent')

@agent_bp.route('/dashboard')
@role_required('AGENT')
def dashboard_view():
    return render_template('agent/dashboard.html')

@agent_bp.route('/customers')
@role_required('AGENT')
def customers_view():
    return render_template('agent/customers.html')

@agent_bp.route('/policies')
@role_required('AGENT')
def policies_view():
    return render_template('agent/policies.html')

@agent_bp.route('/claims')
@role_required('AGENT')
def claims_view():
    return render_template('agent/claims.html')

@agent_bp.route('/api/dashboard-summary')
@role_required('AGENT')
def agent_dashboard_api():
    agent_id = session['user_id']
    policies = PolicyService.get_all_policies(agent_id=agent_id)
    customers = AdminService.get_all_users(role_filter='CUSTOMER')
    claims = ClaimService.get_officer_claims()

    active_cnt = len([p for p in policies if p['status'] == 'ACTIVE'])
    expired_cnt = len([p for p in policies if p['status'] == 'EXPIRED'])

    summary = {
        "assigned_policies_count": len(policies),
        "active_policies_count": active_cnt,
        "expired_policies_count": expired_cnt,
        "total_customers_count": len(customers),
        "policies": policies[:10],
        "recent_claims": claims[:5]
    }
    return api_response(True, "Agent summary fetched", summary)
