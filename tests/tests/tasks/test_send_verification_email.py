import time

import pytest
from django.db.utils import OperationalError
from django.urls import reverse
from users.models import EmailVerificationToken
from users.tasks import EmailSendError

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
    """ End-to-end send verification email task happy path. """
    def test_send_email_receives_correct_email_and_token(
        self, api_client, celery_worker, purge_test_queue, mocker
    ):
        mock_send = mocker.patch("users.tasks.send_email")

        response = api_client.post(REGISTER_URL, VALID_PAYLOAD)

        assert response.status_code == 201
        token = EmailVerificationToken.objects.get()

        # Wait for email sending task to complete
        _wait_for_status(token, EmailVerificationToken.Status.SENT)
        mock_send.assert_called_once_with("alice@example.com", str(token.token))

        # Check if send time was set during the task
        assert token.sent_at is not None


@pytest.mark.django_db(transaction=True)
class TestDbDownBeforeEmail:
    """
    DB down in phase 1 of send verifiction email task
    (getting / updating token and corresponding user)
    """
    def test_temporary_failure_retries_and_succeeds(
        self, api_client, celery_worker, purge_test_queue, mocker
    ):
        mock_send = mocker.patch("users.tasks.send_email")
        # select_for_update is only called inside the task, not the
        # serializer, so mocking it here is end-to-end-safe.
        from unittest.mock import DEFAULT

        mocker.patch.object(
            EmailVerificationToken.objects,
            "select_for_update",
            wraps=EmailVerificationToken.objects.select_for_update,
            side_effect=[OperationalError, DEFAULT],
        )

        response = api_client.post(REGISTER_URL, VALID_PAYLOAD)
        assert response.status_code == 201
        token = EmailVerificationToken.objects.get()

        _wait_for_status(token, EmailVerificationToken.Status.SENT)
        mock_send.assert_called_once_with("alice@example.com", str(token.token))

    def test_constant_failure_exhausts_retries(
        self, api_client, celery_worker, purge_test_queue, mocker
    ):
        mock_send = mocker.patch("users.tasks.send_email")
        mocker.patch.object(
            EmailVerificationToken.objects,
            "select_for_update",
            side_effect=OperationalError,
        )

        response = api_client.post(REGISTER_URL, VALID_PAYLOAD)
        assert response.status_code == 201
        token = EmailVerificationToken.objects.get()

        # Wait for max_retries to exhaust.
        time.sleep(2)
        token.refresh_from_db()
        assert token.status == EmailVerificationToken.Status.NOT_SENT
        mock_send.assert_not_called()


@pytest.mark.django_db(transaction=True)
class TestDbDownDuringError:
    """
    DB down in phase 2 of send verifiction email task
    (setting token status to "error" after email send failed)
    """
    def test_temporary_db_failure_retries_and_succeeds(
        self, api_client, celery_worker, purge_test_queue, mocker
    ):
        mock_send = mocker.patch(
            "users.tasks.send_email",
            side_effect=[EmailSendError, None],
        )
        # _update_status_safe: first call (ERROR) no-op (DB down),
        # second call (SENT) does the real update.
        _update_status_safe = mocker.patch("users.tasks._update_status_safe")
        _update_status_safe.side_effect = lambda token_id, status: (
            None
            if status == EmailVerificationToken.Status.ERROR
            else EmailVerificationToken.objects.filter(id=token_id).update(
                status=status
            )
        )

        response = api_client.post(REGISTER_URL, VALID_PAYLOAD)
        assert response.status_code == 201
        token = EmailVerificationToken.objects.get()

        _wait_for_status(token, EmailVerificationToken.Status.SENT)
        assert mock_send.call_count == 2

    def test_constant_db_failure_exhausts_retries(
        self, api_client, celery_worker, purge_test_queue, mocker
    ):
        mock_send = mocker.patch(
            "users.tasks.send_email", side_effect=EmailSendError
        )
        mocker.patch("users.tasks._update_status_safe")  # no-op: DB down

        response = api_client.post(REGISTER_URL, VALID_PAYLOAD)
        assert response.status_code == 201
        token = EmailVerificationToken.objects.get()

        # Wait for max_retries to exhaust.
        time.sleep(2)
        token.refresh_from_db()
        assert token.status == EmailVerificationToken.Status.SENDING
        assert mock_send.call_count == 4  # 1 initial + 3 retries


@pytest.mark.django_db(transaction=True)
class TestDbDownAfterEmail:
    """
    DB down in phase 3 of send verifiction email task
    (marking token as sent)
    """
    def test_status_not_updated_but_email_sent_once(
        self, api_client, celery_worker, purge_test_queue, mocker
    ):
        mock_send = mocker.patch("users.tasks.send_email")
        mocker.patch("users.tasks._update_status_safe")  # no-op: DB down in Phase 3

        response = api_client.post(REGISTER_URL, VALID_PAYLOAD)
        assert response.status_code == 201
        token = EmailVerificationToken.objects.get()

        # Poll until send_email is called (task completes Phase 2).
        deadline = time.monotonic() + POLL_TIMEOUT
        while not mock_send.called and time.monotonic() < deadline:
            time.sleep(POLL_INTERVAL)
        assert mock_send.call_count == 1
        token.refresh_from_db()
        assert token.status == EmailVerificationToken.Status.SENDING


@pytest.mark.django_db(transaction=True)
class TestEmailSendingError:
    """
    Email sending fails during phase 2 of send verifiction email task
    """
    def test_temporary_failure_retries_and_succeeds(
        self, api_client, celery_worker, purge_test_queue, mocker
    ):
        mock_send = mocker.patch(
            "users.tasks.send_email",
            side_effect=[EmailSendError, None],
        )

        response = api_client.post(REGISTER_URL, VALID_PAYLOAD)
        assert response.status_code == 201
        token = EmailVerificationToken.objects.get()

        _wait_for_status(token, EmailVerificationToken.Status.SENT)
        assert mock_send.call_count == 2

    def test_constant_failure_exhausts_retries(
        self, api_client, celery_worker, purge_test_queue, mocker
    ):
        mock_send = mocker.patch(
            "users.tasks.send_email", side_effect=EmailSendError
        )

        response = api_client.post(REGISTER_URL, VALID_PAYLOAD)
        assert response.status_code == 201
        token = EmailVerificationToken.objects.get()

        # Wait for max_retries to exhaust.
        time.sleep(2)
        token.refresh_from_db()
        assert token.status == EmailVerificationToken.Status.ERROR
        assert mock_send.call_count == 4  # 1 initial + 3 retries
