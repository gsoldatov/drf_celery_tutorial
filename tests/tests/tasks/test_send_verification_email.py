import time

import pytest
from django.urls import reverse
from users.models import EmailVerificationToken

REGISTER_URL = reverse("user-registration")

POLL_TIMEOUT = 5  # seconds
POLL_INTERVAL = 0.1  # seconds


def _wait_for_status(token: EmailVerificationToken, status: str) -> None:
    """Poll until *token* reaches *status*, or raise AssertionError on timeout."""
    deadline = time.monotonic() + POLL_TIMEOUT
    while time.monotonic() < deadline:
        token.refresh_from_db()
        if token.status == status:
            return
        time.sleep(POLL_INTERVAL)
    raise AssertionError(
        f"Token {token.id} status is {token.status}, expected {status} "
        f"after {POLL_TIMEOUT}s."
    )


@pytest.mark.django_db(transaction=True)
class TestSuccessfulTask:
    def test_send_email_receives_correct_email_and_token(
        self, api_client, celery_worker, purge_test_queue, mocker
    ):
        mock_send = mocker.patch("users.tasks.send_email")
        payload = {
            "email": "alice@example.com",
            "password": "secret123",
            "password_repeat": "secret123",
            "first_name": "Alice",
            "last_name": "Smith",
        }

        response = api_client.post(REGISTER_URL, payload)

        assert response.status_code == 201
        token = EmailVerificationToken.objects.get()

        # Wait for email sending task to complete
        _wait_for_status(token, EmailVerificationToken.Status.SENT)
        mock_send.assert_called_once_with("alice@example.com", str(token.token))

        # Check if send time was set during the task
        assert token.sent_at is not None
