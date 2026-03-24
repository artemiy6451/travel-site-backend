from app.exceptions import ServiceError


class NotificationNotFoundError(ServiceError):
    """Notification not found."""

    status_code = 404
    message = "Notification not found"
