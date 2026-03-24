from datetime import datetime

from pydantic import BaseModel


class NotificationSchema(BaseModel):
    user_id: int
    type: str
    message: str


class CreateNotificationSchema(NotificationSchema):
    pass


class BulkNotificationSchema(BaseModel):
    phone_numbers: list[str]
    message: str
    type: str = "custom"


class BulkReminderSchema(BaseModel):
    phone_numbers: list[str]
    excursion_id: int
    days_before: int = 2


class UpdateNotificationSchema(BaseModel):
    id: int
    user_id: int
    is_read: bool = True


class NotificationBaseSchema(NotificationSchema):
    id: int
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
