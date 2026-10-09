from flask import Blueprint, render_template, session, request
from utils.decorators import role_required
from services.policy_service import PolicyService
from services.claim_service import ClaimService
from services.ticket_service import TicketService
from services.notification_service import NotificationService
from utils.helpers import api_response

customer_bp = Blueprint('customer', __name__, url_prefix='/customer')

@customer_bp.route('/dashboard')
@role_required('CUSTOMER')
def dashboard_view():
    user_id = session['user_id']
    # Trigger expiry notifications scan
    NotificationService.check_and_create_expiry_alerts(user_id)
    return render_template('customer/dashboard.html')

@customer_bp.route('/policies')
@role_required('CUSTOMER')
def policies_view():
    return render_template('customer/policies.html')

@customer_bp.route('/policies/<int:policy_id>')
@role_required('CUSTOMER')
def policy_detail_view(policy_id):
    pol = PolicyService.get_policy_by_id(policy_id, user_id=session['user_id'], role='CUSTOMER')
    return render_template('customer/policy_detail.html', policy=pol)

@customer_bp.route('/policies/<int:policy_id>/invoice')
@role_required('CUSTOMER')
def policy_invoice_view(policy_id):
    pol = PolicyService.get_policy_by_id(policy_id, user_id=session['user_id'], role='CUSTOMER')
    if not pol:
        return "Policy not found or access unauthorized", 444
    return render_template('customer/policy_invoice.html', policy=pol)

@customer_bp.route('/claims/submit')
@role_required('CUSTOMER')
def submit_claim_view():
    return render_template('customer/submit_claim.html')

@customer_bp.route('/claims')
@role_required('CUSTOMER')
def claims_view():
    return render_template('customer/my_claims.html')

@customer_bp.route('/claims/<int:claim_id>')
@role_required('CUSTOMER')
def claim_detail_view(claim_id):
    claim = ClaimService.get_claim_details(claim_id, user_id=session['user_id'], role='CUSTOMER')
    return render_template('customer/claim_detail.html', claim=claim)

@customer_bp.route('/tickets')
@role_required('CUSTOMER')
def tickets_view():
    return render_template('customer/tickets.html')

@customer_bp.route('/tickets/<int:ticket_id>')
@role_required('CUSTOMER')
def ticket_detail_view(ticket_id):
    tkt = TicketService.get_ticket_details(ticket_id, user_id=session['user_id'], role='CUSTOMER')
    return render_template('customer/ticket_detail.html', ticket=tkt)

# API Endpoint for Customer Dashboard Real DB Data
@customer_bp.route('/api/dashboard-summary')
@role_required('CUSTOMER')
def dashboard_summary_api():
    user_id = session['user_id']
    policies = PolicyService.get_customer_policies(user_id)
    claims = ClaimService.get_customer_claims(user_id)
    tickets = TicketService.get_tickets(user_id, role='CUSTOMER')
    notifications = NotificationService.get_user_notifications(user_id, limit=5)

    active_policies_cnt = len([p for p in policies if p['status'] == 'ACTIVE'])
    pending_claims_cnt = len([c for c in claims if c['status'] in ('SUBMITTED', 'UNDER_REVIEW', 'DOCUMENT_REQUIRED')])
    approved_claims_cnt = len([c for c in claims if c['status'] == 'APPROVED'])
    rejected_claims_cnt = len([c for c in claims if c['status'] == 'REJECTED'])
    open_tickets_cnt = len([t for t in tickets if t['status'] in ('OPEN', 'IN_PROGRESS')])

    summary = {
        "active_policies": active_policies_cnt,
        "total_claims": len(claims),
        "pending_claims": pending_claims_cnt,
        "approved_claims": approved_claims_cnt,
        "rejected_claims": rejected_claims_cnt,
        "open_tickets": open_tickets_cnt,
        "recent_claims": claims[:5],
        "policies": policies,
        "notifications": notifications
    }
    return api_response(True, "Customer summary fetched", summary)
