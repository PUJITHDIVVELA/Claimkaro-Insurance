from flask import Blueprint, request, session
from services.claim_service import ClaimService
from utils.file_handler import save_uploaded_file
from utils.helpers import api_response
from utils.decorators import login_required

claim_bp = Blueprint('claim', __name__, url_prefix='/api/claims')

@claim_bp.route('', methods=['GET'])
@login_required
def get_claims_api():
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    role = session.get('role')
    user_id = session.get('user_id')

    if role == 'CUSTOMER':
        claims = ClaimService.get_customer_claims(user_id, search, status_filter)
    else:
        claims = ClaimService.get_officer_claims(status_filter=status_filter, search=search)

    return api_response(True, "Claims fetched", claims)

@claim_bp.route('/<int:claim_id>', methods=['GET'])
@login_required
def get_claim_detail_api(claim_id):
    role = session.get('role')
    user_id = session.get('user_id')
    claim = ClaimService.get_claim_details(claim_id, user_id=user_id, role=role)
    if not claim:
        return api_response(False, "Claim not found or unauthorized.", status_code=404)
    return api_response(True, "Claim details fetched", claim)

@claim_bp.route('/submit', methods=['POST'])
@login_required
def submit_claim_api():
    if session.get('role') != 'CUSTOMER':
        return api_response(False, "Only customers can submit claims.", status_code=403)

    # Check for form data vs json
    if request.files:
        policy_id = request.form.get('policy_id')
        reason = request.form.get('reason')
        description = request.form.get('description')
        claim_amount = request.form.get('claim_amount')
        claim_date = request.form.get('claim_date')
        
        file_obj = request.files.get('document')
        doc_info = None
        if file_obj:
            doc_info, err = save_uploaded_file(file_obj, subfolder='claims')
            if err:
                return api_response(False, f"File upload error: {err}", status_code=400)
    else:
        data = request.get_json() or {}
        policy_id = data.get('policy_id')
        reason = data.get('reason')
        description = data.get('description')
        claim_amount = data.get('claim_amount')
        claim_date = data.get('claim_date')
        doc_info = None

    success, msg, res_data = ClaimService.submit_claim(
        session['user_id'], policy_id, reason, description, claim_amount, claim_date, doc_info
    )
    return api_response(success, msg, res_data, status_code=201 if success else 400)

@claim_bp.route('/<int:claim_id>/review', methods=['POST'])
@login_required
def review_claim_api(claim_id):
    if session.get('role') not in ('CLAIMS_OFFICER', 'ADMIN'):
        return api_response(False, "Unauthorized action.", status_code=403)

    data = request.get_json() or {}
    decision = data.get('decision')
    remarks = data.get('remarks', '')

    success, msg = ClaimService.review_claim(claim_id, session['user_id'], decision, remarks)
    return api_response(success, msg, status_code=200 if success else 400)

@claim_bp.route('/<int:claim_id>/documents', methods=['POST'])
@login_required
def upload_claim_document_api(claim_id):
    if 'document' not in request.files:
        return api_response(False, "No document file uploaded.", status_code=400)

    file_obj = request.files['document']
    doc_info, err = save_uploaded_file(file_obj, subfolder='claims')
    if err:
        return api_response(False, err, status_code=400)

    success, msg = ClaimService.upload_document(claim_id, session['user_id'], doc_info)
    return api_response(success, msg, status_code=200 if success else 400)
