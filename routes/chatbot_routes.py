from flask import Blueprint, request, session
from services.chatbot_service import ChatbotService
from utils.helpers import api_response
from utils.decorators import login_required

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/chatbot')

@chatbot_bp.route('/message', methods=['POST'])
@login_required
def chatbot_message_api():
    if session.get('role') != 'CUSTOMER':
        return api_response(False, "Chatbot is available for customers.", status_code=403)

    data = request.get_json() or {}
    user_message = data.get('message', '')

    if not user_message.strip():
        return api_response(False, "Message cannot be empty.", status_code=400)

    bot_reply = ChatbotService.process_user_message(session['user_id'], user_message)
    return api_response(True, "Response generated", {"reply": bot_reply})

@chatbot_bp.route('/history', methods=['GET'])
@login_required
def chatbot_history_api():
    if session.get('role') != 'CUSTOMER':
        return api_response(False, "Chatbot history is available for customers.", status_code=403)

    history = ChatbotService.get_conversation_history(session['user_id'])
    return api_response(True, "History fetched", history)
