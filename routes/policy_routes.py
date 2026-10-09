from flask import Blueprint, request, session
from services.policy_service import PolicyService
from utils.helpers import api_response
from utils.decorators import login_required

policy_bp = Blueprint('policy', __name__, url_prefix='/api/policies')

@policy_bp.route('/types', methods=['GET'])
def get_policy_types_api():
    pts = PolicyService.get_all_policy_types()
    return api_response(True, "Policy types fetched", pts)

@policy_bp.route('', methods=['GET'])
@login_required
def get_policies_api():
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    role = session.get('role')
    user_id = session.get('user_id')

    if role == 'CUSTOMER':
        policies = PolicyService.get_customer_policies(user_id, search, status_filter)
    elif role == 'AGENT':
        policies = PolicyService.get_all_policies(search, status_filter, agent_id=user_id)
    else:
        policies = PolicyService.get_all_policies(search, status_filter)

    return api_response(True, "Policies retrieved", policies)

@policy_bp.route('/<int:policy_id>', methods=['GET'])
@login_required
def get_policy_by_id_api(policy_id):
    role = session.get('role')
    user_id = session.get('user_id')
    pol = PolicyService.get_policy_by_id(policy_id, user_id=user_id, role=role)
    if not pol:
        return api_response(False, "Policy not found or access denied.", status_code=404)
    return api_response(True, "Policy retrieved", pol)

@policy_bp.route('/create-payment-order', methods=['POST'])
@login_required
def create_payment_order_api():
    if session.get('role') != 'CUSTOMER':
        return api_response(False, "Only customers can purchase policies.", status_code=403)

    data = request.get_json() or {}
    policy_type_id = data.get('policy_type_id')

    success, msg, res_data = PolicyService.create_razorpay_order(session['user_id'], policy_type_id)
    return api_response(success, msg, res_data, status_code=200 if success else 400)

@policy_bp.route('/verify-payment', methods=['POST'])
@login_required
def verify_payment_api():
    if session.get('role') != 'CUSTOMER':
        return api_response(False, "Only customers can verify policy payments.", status_code=403)

    data = request.get_json() or {}
    policy_type_id = data.get('policy_type_id')
    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_signature = data.get('razorpay_signature')

    success, msg, res_data = PolicyService.verify_razorpay_payment(
        session['user_id'], policy_type_id, razorpay_order_id, razorpay_payment_id, razorpay_signature
    )
    return api_response(success, msg, res_data, status_code=200 if success else 400)
