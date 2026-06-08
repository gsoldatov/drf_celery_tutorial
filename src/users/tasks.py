from celery import shared_task

from .models import User


class EmailSendError(Exception):
    """Transient failure during email sending — triggers task retry."""


def _send_email(user_id: int) -> None:
    """No-op by default. Mockable in tests to raise EmailSendError."""
    pass


@shared_task(
    acks_late=True,
    autoretry_for=(EmailSendError,),
    max_retries=3,
    default_retry_delay=0.1,
    retry_backoff=True,
    retry_jitter=True,
)
def send_verification_email(user_id: int) -> None:
    user = User.objects.get(id=user_id)
    _send_email(user.id)
