from flask import Blueprint, request, session
from services.notification_service import NotificationService
from utils.helpers import api_response
from utils.decorators import login_required

notif_bp = Blueprint('notification', __name__, url_prefix='/api/notifications')

@notif_bp.route('', methods=['GET'])
@login_required
def get_notifications_api():
    limit = request.args.get('limit', 15, type=int)
    notifs = NotificationService.get_user_notifications(session['user_id'], limit)
    unread_cnt = len([n for n in notifs if not n['is_read']])
    return api_response(True, "Notifications fetched", {"notifications": notifs, "unread_count": unread_cnt})

@notif_bp.route('/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_read_api(notif_id):
    NotificationService.mark_as_read(notif_id, session['user_id'])
    return api_response(True, "Notification marked as read")

@notif_bp.route('/read-all', methods=['POST'])
@login_required
def mark_all_read_api():
    NotificationService.mark_all_read(session['user_id'])
    return api_response(True, "All notifications marked as read")
