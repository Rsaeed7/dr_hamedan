def send_notification(user, title, message, link=None, notification_type='info', priority='medium', metadata=None, expires_at=None):
    """
    Send a notification to a user
    
    Args:
        user: The user to send the notification to
        title: Notification title
        message: Notification message content
        link: Optional URL to direct the user to
        notification_type: Type of notification (info, success, warning, error, appointment, message, system)
        priority: Priority level (low, medium, high, urgent)
        metadata: Optional dictionary of additional data
        expires_at: Optional expiration datetime
        
    Returns:
        Notification object
    """
    try:
        from doctors.models import Notification
        
        # Create notification in database
        notification = Notification.create_notification(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            link=link,
            metadata=metadata or {},
            expires_at=expires_at
        )
        
        # Log for debugging (can be removed in production)
        print(f"Notification created for {user.email}: {title} - {message}")
        
        return notification
        
    except Exception as e:
        # Fallback to console logging if database save fails
        print(f"Failed to create notification for {user.email}: {title} - {message}. Error: {str(e)}")
        return None 