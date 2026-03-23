from datetime import datetime

from pydantic import BaseModel


class NotificatoinSchema(BaseModel):
    user_id: int
    type: str
    message: str


class CreateNotificationSchema(NotificatoinSchema):
    pass


class UpdateNotificationSchema(NotificatoinSchema):
    id: int
    is_read: bool


class NotificationBaseSchema(NotificatoinSchema):
    id: int
    is_read: bool
    created_at: datetime
