from .models import Notification


def create_notification(user, title, message):
    """
    Create an in-app notification for a user.
    """
    Notification.objects.create(
        user=user,
        title=title,
        message=message
    )