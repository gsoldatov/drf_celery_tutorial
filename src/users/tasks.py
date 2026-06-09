from celery import shared_task
from django.db import transaction
from django.db.utils import OperationalError
from django.utils import timezone

from .models import EmailVerificationToken


class EmailSendError(Exception):
    """Transient failure during email sending — triggers task retry."""


def send_email(email: str, token: str) -> None:
    """No-op by default. Mockable in tests to raise EmailSendError."""
    pass


def _update_status_safe(token_id: int, status: str) -> None:
    """Update token status, swallowing DB errors so a failed write
    does not mask a prior successful email send or a pending retry."""
    try:
        (
            EmailVerificationToken.objects.filter(id=token_id).update(status=status)
        )
    except OperationalError:
        pass


@shared_task(
    bind=True,
    acks_late=True,
    max_retries=3,
    default_retry_delay=0.1,
    retry_backoff=True,
    retry_jitter=True,
)
def send_verification_email(self, verification_token_id: int) -> None:
    # Per-phase comment: idempotency is enforced by an atomic
    # select_for_update claim in Phase 1, which serialises
    # concurrent deliveries of the same token.  Retries that
    # follow a Phase-2 OperationalError can reclaim a SENDING
    # token; fresh concurrent deliveries cannot.

    # -- Phase 1: atomic claim & status transition ----------
    # Retries may reclaim a SENDING token whose ERROR update failed.
    claimable = {EmailVerificationToken.Status.NOT_SENT, EmailVerificationToken.Status.ERROR}
    if self.request.retries > 0:
        claimable.add(EmailVerificationToken.Status.SENDING)

    try:
        with transaction.atomic():
            # Get token and user
            token = (
                EmailVerificationToken.objects.select_for_update()
                .select_related("user")
                .get(id=verification_token_id)
            )

            # Do nothing, if token expired or not claimable
            # (email sent or is sending)
            if token.status not in claimable:
                return

            if token.expires_at <= timezone.now():
                return

            # Update token status and send time
            token.status = EmailVerificationToken.Status.SENDING
            token.sent_at = timezone.now()
            token.save(update_fields=["status", "sent_at"])

            email = token.user.email
            token_value = str(token.token)
    except EmailVerificationToken.DoesNotExist:
        # Do nothing, if token does not exist
        return
    except OperationalError:
        # Retry if db went down
        raise self.retry()

    # -- Phase 2: send the email ----------------------------
    try:
        send_email(email, token_value)
    except EmailSendError:
        # Mark as ERROR so a retry can reclaim the token.  If the
        # DB is unavailable the exception propagates and acks_late
        # redelivers the message; the retry-path above then allows
        # SENDING tokens to be reclaimed.
        _update_status_safe(verification_token_id, EmailVerificationToken.Status.ERROR)
        raise self.retry()

    # -- Phase 3: mark sent ---------------------------------
    # Email has been sent.  A DB failure here must NOT cause a
    # retry (that would double-send), so swallow the error.
    _update_status_safe(verification_token_id, EmailVerificationToken.Status.SENT)


@shared_task
def cleanup_expired_tokens() -> None:
    EmailVerificationToken.objects.filter(
        expires_at__lte=timezone.now()
    ).delete()
