from flask import Blueprint, request, session
from services.ticket_service import TicketService
from utils.helpers import api_response
from utils.decorators import login_required

ticket_bp = Blueprint('ticket', __name__, url_prefix='/api/tickets')

@ticket_bp.route('', methods=['GET'])
@login_required
def get_tickets_api():
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '')
    role = session.get('role')
    user_id = session.get('user_id')

    tickets = TicketService.get_tickets(user_id=user_id, role=role, status_filter=status_filter, search=search)
    return api_response(True, "Tickets fetched", tickets)

@ticket_bp.route('', methods=['POST'])
@login_required
def create_ticket_api():
    if session.get('role') != 'CUSTOMER':
        return api_response(False, "Only customers can raise support tickets.", status_code=403)

    data = request.get_json() or {}
    category = data.get('category')
    subject = data.get('subject')
    description = data.get('description')
    priority = data.get('priority', 'MEDIUM')

    success, msg, res_data = TicketService.create_ticket(
        session['user_id'], category, subject, description, priority
    )
    return api_response(success, msg, res_data, status_code=201 if success else 400)

@ticket_bp.route('/<int:ticket_id>', methods=['GET'])
@login_required
def get_ticket_details_api(ticket_id):
    role = session.get('role')
    user_id = session.get('user_id')
    tkt = TicketService.get_ticket_details(ticket_id, user_id=user_id, role=role)
    if not tkt:
        return api_response(False, "Ticket not found or unauthorized.", status_code=404)
    return api_response(True, "Ticket details fetched", tkt)

@ticket_bp.route('/<int:ticket_id>/messages', methods=['POST'])
@login_required
def add_ticket_message_api(ticket_id):
    data = request.get_json() or {}
    message_text = data.get('message')

    success, msg = TicketService.add_message(ticket_id, session['user_id'], message_text)
    return api_response(success, msg, status_code=200 if success else 400)

@ticket_bp.route('/<int:ticket_id>/status', methods=['POST'])
@login_required
def update_ticket_status_api(ticket_id):
    data = request.get_json() or {}
    status = data.get('status')
    assigned_to = data.get('assigned_to')

    success, msg = TicketService.update_ticket_status(ticket_id, status, assigned_to)
    return api_response(success, msg, status_code=200 if success else 400)
