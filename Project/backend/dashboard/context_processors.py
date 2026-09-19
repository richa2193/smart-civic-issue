from complaints.models import Notification

def global_notifications(request):
    if not request.user.is_authenticated:
        return {}
    
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    return {
        'recent_notifications': notifications,
        'unread_notifications_count': unread_count,
    }
