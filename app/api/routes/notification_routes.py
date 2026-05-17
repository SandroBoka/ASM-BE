from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_customer
from app.db.database import get_db
from app.repositories.notification_repository import NotificationRepository
from app.schemas import AuthUserResponse
from app.schemas.notification_schema import NotificationResponse
from app.services.email_service import EmailService
from app.services.notification_service import NotificationService

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)


def get_notification_service(db: Session = Depends(get_db)) -> NotificationService:
    repository = NotificationRepository(db)
    email_service = EmailService()
    return NotificationService(repository=repository, email_service=email_service)


@router.get("", response_model=list[NotificationResponse])
def get_my_notifications(
        service: NotificationService = Depends(get_notification_service),
        current_user: AuthUserResponse = Depends(require_customer),
):
    return service.get_notifications_for_customer(current_user.IdOsobe)


@router.get("/unread", response_model=list[NotificationResponse])
def get_my_unread_notifications(
        service: NotificationService = Depends(get_notification_service),
        current_user: AuthUserResponse = Depends(require_customer),
):
    return service.get_unread_for_customer(current_user.IdOsobe)


@router.post("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_as_read(
        notification_id: int,
        service: NotificationService = Depends(get_notification_service),
        current_user: AuthUserResponse = Depends(require_customer),
):
    return service.mark_as_read(notification_id, current_user.IdOsobe)
