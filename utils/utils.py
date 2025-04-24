def send_notification(user, title, message, link=None, notification_type='info'):
    """
    Send a notification to a user
    
    Args:
        user: The user to send the notification to
        title: Notification title
        message: Notification message content
        link: Optional URL to direct the user to
        notification_type: Type of notification (info, success, warning, error)
        
    Returns:
        Notification object
    """
    # This is a placeholder implementation
    # In a real app, you would save this to a database model and/or
    # send it via a notification service, email, SMS, etc.
    print(f"Notification sent to {user.email}: {title} - {message}")
    
    # Return a dummy successful result
    return {"success": True} 