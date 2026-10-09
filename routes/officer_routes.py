from flask import Blueprint, render_template, session, request
from utils.decorators import role_required
from services.claim_service import ClaimService
from utils.helpers import api_response

officer_bp = Blueprint('officer', __name__, url_prefix='/officer')

@officer_bp.route('/dashboard')
@role_required('CLAIMS_OFFICER')
def dashboard_view():
    return render_template('officer/dashboard.html')

@officer_bp.route('/pending-claims')
@role_required('CLAIMS_OFFICER')
def pending_claims_view():
    return render_template('officer/pending_claims.html')

@officer_bp.route('/claims')
@role_required('CLAIMS_OFFICER')
def all_claims_view():
    return render_template('officer/all_claims.html')

@officer_bp.route('/claims/<int:claim_id>/review')
@role_required('CLAIMS_OFFICER')
def review_claim_view(claim_id):
    claim = ClaimService.get_claim_details(claim_id, user_id=session['user_id'], role='CLAIMS_OFFICER')
    return render_template('officer/claim_review.html', claim=claim)

@officer_bp.route('/api/dashboard-summary')
@role_required('CLAIMS_OFFICER')
def officer_dashboard_api():
    all_claims = ClaimService.get_officer_claims()

    total_cnt = len(all_claims)
    pending_cnt = len([c for c in all_claims if c['status'] == 'SUBMITTED'])
    reviewing_cnt = len([c for c in all_claims if c['status'] == 'UNDER_REVIEW'])
    doc_req_cnt = len([c for c in all_claims if c['status'] == 'DOCUMENT_REQUIRED'])
    approved_cnt = len([c for c in all_claims if c['status'] == 'APPROVED'])
    rejected_cnt = len([c for c in all_claims if c['status'] == 'REJECTED'])

    summary = {
        "total_claims": total_cnt,
        "pending_review": pending_cnt,
        "under_review": reviewing_cnt,
        "documents_required": doc_req_cnt,
        "approved": approved_cnt,
        "rejected": rejected_cnt,
        "recent_pending_claims": [c for c in all_claims if c['status'] in ('SUBMITTED', 'UNDER_REVIEW', 'DOCUMENT_REQUIRED')][:10]
    }
    return api_response(True, "Officer dashboard summary fetched", summary)
