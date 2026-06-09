import time
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from users.models import EmailVerificationToken, User
from users.tasks import cleanup_expired_tokens

REGISTER_URL = reverse("user-registration")

VALID_PAYLOAD = {
    "email": "alice@example.com",
    "password": "secret123",
    "password_repeat": "secret123",
    "first_name": "Alice",
    "last_name": "Smith",
}

POLL_TIMEOUT = 5  # seconds
POLL_INTERVAL = 0.1  # seconds


def _wait_for_deletion(token_ids: list[int]) -> None:
    """Poll until all tokens in *token_ids* are deleted, or raise AssertionError."""
    deadline = time.monotonic() + POLL_TIMEOUT
    while time.monotonic() < deadline:
        if not EmailVerificationToken.objects.filter(id__in=token_ids).exists():
            return
        time.sleep(POLL_INTERVAL)
    remaining = EmailVerificationToken.objects.filter(id__in=token_ids).count()
    raise AssertionError(
        f"{remaining} token(s) still present after {POLL_TIMEOUT}s."
    )


@pytest.mark.django_db(transaction=True)
class TestMixedTokens:
    def test_expired_deleted_non_expired_preserved(
        self, api_client, celery_worker, purge_test_queue
    ):
        user = User.objects.create_user(email="test@example.com", password="secret")
        now = timezone.now()
        expired1 = EmailVerificationToken.objects.create(
            user=user, expires_at=now - timedelta(seconds=2)
        )
        expired2 = EmailVerificationToken.objects.create(
            user=user, expires_at=now - timedelta(seconds=1)
        )
        non_expired = EmailVerificationToken.objects.create(
            user=user, expires_at=now + timedelta(seconds=60)
        )

        cleanup_expired_tokens.delay()

        _wait_for_deletion([expired1.id, expired2.id])

        assert not EmailVerificationToken.objects.filter(
            id__in=[expired1.id, expired2.id]
        ).exists()
        assert EmailVerificationToken.objects.filter(id=non_expired.id).exists()


@pytest.mark.django_db(transaction=True)
class TestE2ERegistration:
    def test_token_deleted_after_expiry(
        self, api_client, celery_worker, purge_test_queue, settings
    ):
        settings.EMAIL_VERIFICATION_TOKEN_LIFETIME = 1

        response = api_client.post(REGISTER_URL, VALID_PAYLOAD)
        assert response.status_code == 201

        token = EmailVerificationToken.objects.get()
        assert User.objects.filter(email=VALID_PAYLOAD["email"]).exists()

        # Wait for token to expire.
        time.sleep(1.5)
        cleanup_expired_tokens.delay()

        _wait_for_deletion([token.id])

        assert not EmailVerificationToken.objects.filter(id=token.id).exists()
        assert User.objects.filter(email=VALID_PAYLOAD["email"]).exists()


@pytest.mark.django_db(transaction=True)
class TestZeroTokens:
    def test_no_errors_with_empty_db(
        self, api_client, celery_worker, purge_test_queue
    ):
        cleanup_expired_tokens.delay()
        # Let the worker process the task.
        time.sleep(1)
        assert EmailVerificationToken.objects.count() == 0
