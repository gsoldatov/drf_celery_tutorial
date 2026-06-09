from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from users.models import User, EmailVerificationToken

REGISTER_URL = reverse("user-registration")


def _detail_url(pk):
    return reverse("user-detail", kwargs={"pk": pk})


def _verify_url(token):
    return reverse("user-verify-email", kwargs={"token": token})


@pytest.mark.django_db(transaction=True)
class TestUserRegistrationView:
    def test_successful_registration(self, api_client, mocker):
        mock_delay = mocker.patch("users.tasks.send_verification_email.delay")
        payload = {
            "email": "new@example.com",
            "password": "secret123",
            "password_repeat": "secret123",
            "first_name": "Alice",
            "last_name": "Smith",
        }

        response = api_client.post(REGISTER_URL, payload)

        assert response.status_code == 201
        user = User.objects.get(email="new@example.com")
        assert user.email_verified is False
        assert user.check_password("secret123")
        token = EmailVerificationToken.objects.get(user=user)
        mock_delay.assert_called_once_with(token.id)

    def test_password_mismatch(self, api_client):
        payload = {
            "email": "new@example.com",
            "password": "secret123",
            "password_repeat": "different",
            "first_name": "Alice",
            "last_name": "Smith",
        }

        response = api_client.post(REGISTER_URL, payload)

        assert response.status_code == 400
        assert "password_repeat" in response.data

    def test_missing_required_fields(self, api_client):
        response = api_client.post(REGISTER_URL, {})

        assert response.status_code == 400
        assert "email" in response.data
        assert "password" in response.data
        assert "password_repeat" in response.data

    def test_duplicate_email(self, api_client, create_user):
        create_user(email="taken@example.com")
        payload = {
            "email": "taken@example.com",
            "password": "secret123",
            "password_repeat": "secret123",
            "first_name": "Alice",
            "last_name": "Smith",
        }

        response = api_client.post(REGISTER_URL, payload)

        assert response.status_code == 400
        assert "email" in response.data

    def test_task_not_called_on_failure(self, api_client, create_user, mocker):
        mock_delay = mocker.patch("users.tasks.send_verification_email.delay")
        create_user(email="taken@example.com")
        payload = {
            "email": "taken@example.com",
            "password": "secret123",
            "password_repeat": "secret123",
            "first_name": "Alice",
            "last_name": "Smith",
        }

        api_client.post(REGISTER_URL, payload)

        mock_delay.assert_not_called()

    def test_db_unavailable(self, api_client, db_unavailable, mocker):
        mock_delay = mocker.patch("users.tasks.send_verification_email.delay")
        payload = {
            "email": "new@example.com",
            "password": "secret123",
            "password_repeat": "secret123",
            "first_name": "Alice",
            "last_name": "Smith",
        }

        response = api_client.post(REGISTER_URL, payload)

        assert response.status_code == 503
        assert response.data == {"detail": "Service temporarily unavailable"}
        mock_delay.assert_not_called()


@pytest.mark.django_db
class TestUserDetailView:
    def test_existing_user(self, api_client, create_user):
        user = create_user()

        response = api_client.get(_detail_url(user.pk))

        assert response.status_code == 200
        assert response.data["email"] == user.email
        assert response.data["first_name"] == user.first_name
        assert response.data["last_name"] == user.last_name
        assert response.data["email_verified"] == user.email_verified
        assert "password" not in response.data

    def test_nonexistent_user(self, api_client):
        response = api_client.get(_detail_url(9999))

        assert response.status_code == 404

    def test_db_unavailable(self, api_client, db_unavailable):
        response = api_client.get(_detail_url(9999))

        assert response.status_code == 503
        assert response.data == {"detail": "Service temporarily unavailable"}


@pytest.mark.django_db
class TestEmailVerificationView:
    def test_valid_token(self, api_client, create_user):
        user = create_user(email_verified=False)
        token = EmailVerificationToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(seconds=300),
        )

        response = api_client.post(_verify_url(token.token))

        assert response.status_code == 200
        user.refresh_from_db()
        assert user.email_verified is True

    def test_malformed_uuid(self, api_client):
        response = api_client.post("/api/verify-email/not-a-uuid/")

        assert response.status_code == 404

    def test_nonexistent_token(self, api_client):
        url = _verify_url("00000000-0000-0000-0000-000000000000")

        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Invalid or expired token."}

    def test_expired_token_unverified_user(self, api_client, create_user):
        user = create_user(email_verified=False)
        token = EmailVerificationToken.objects.create(
            user=user,
            expires_at=timezone.now() - timedelta(seconds=1),
        )

        response = api_client.post(_verify_url(token.token))

        assert response.status_code == 404
        assert response.data == {"detail": "Invalid or expired token."}
        user.refresh_from_db()
        assert user.email_verified is False

    def test_expired_token_already_verified(self, api_client, create_user):
        user = create_user(email_verified=True)
        token = EmailVerificationToken.objects.create(
            user=user,
            expires_at=timezone.now() - timedelta(seconds=1),
        )

        response = api_client.post(_verify_url(token.token))

        assert response.status_code == 200
        user.refresh_from_db()
        assert user.email_verified is True

    def test_db_unavailable(self, api_client, db_unavailable):
        url = _verify_url("00000000-0000-0000-0000-000000000000")

        response = api_client.post(url)

        assert response.status_code == 503
        assert response.data == {"detail": "Service temporarily unavailable"}


@pytest.mark.django_db(transaction=True)
class TestBrokerDown:
    def test_registration_succeeds_when_broker_down(
        self, api_client, broker_unavailable
    ):
        payload = {
            "email": "alice@example.com",
            "password": "secret123",
            "password_repeat": "secret123",
            "first_name": "Alice",
            "last_name": "Smith",
        }

        response = api_client.post(REGISTER_URL, payload)

        assert response.status_code == 201
        assert User.objects.filter(email="alice@example.com").exists()
