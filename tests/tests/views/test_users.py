from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from users.models import User, UserActivationToken

REGISTER_URL = reverse("user-registration")
ACTIVATE_URL = reverse("user-activate")


def _detail_url(pk):
    return reverse("user-detail", kwargs={"pk": pk})


@pytest.mark.django_db(transaction=True)
class TestUserRegistrationView:
    def test_successful_registration(self, api_client, mocker):
        mock_delay = mocker.patch("users.tasks.send_activation_email.delay")
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
        assert UserActivationToken.objects.filter(user=user).exists()
        mock_delay.assert_called_once_with(user.id)

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
        mock_delay = mocker.patch("users.tasks.send_activation_email.delay")
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


@pytest.mark.django_db
class TestUserActivationView:
    def test_valid_token(self, api_client, create_user):
        user = create_user(email_verified=False)
        token = UserActivationToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(seconds=300),
        )

        response = api_client.post(ACTIVATE_URL, {"token": str(token.token)})

        assert response.status_code == 200
        user.refresh_from_db()
        assert user.email_verified is True

    def test_invalid_uuid_format(self, api_client):
        response = api_client.post(ACTIVATE_URL, {"token": "not-a-uuid"})

        assert response.status_code == 400
        assert "token" in response.data

    def test_nonexistent_token(self, api_client):
        response = api_client.post(
            ACTIVATE_URL, {"token": "00000000-0000-0000-0000-000000000000"}
        )

        assert response.status_code == 400
        assert "token" in response.data

    def test_expired_token_unverified_user(self, api_client, create_user):
        user = create_user(email_verified=False)
        token = UserActivationToken.objects.create(
            user=user,
            expires_at=timezone.now() - timedelta(seconds=1),
        )

        response = api_client.post(ACTIVATE_URL, {"token": str(token.token)})

        assert response.status_code == 400
        user.refresh_from_db()
        assert user.email_verified is False

    def test_expired_token_already_verified(self, api_client, create_user):
        user = create_user(email_verified=True)
        token = UserActivationToken.objects.create(
            user=user,
            expires_at=timezone.now() - timedelta(seconds=1),
        )

        response = api_client.post(ACTIVATE_URL, {"token": str(token.token)})

        assert response.status_code == 200
        user.refresh_from_db()
        assert user.email_verified is True

    def test_missing_token_field(self, api_client):
        response = api_client.post(ACTIVATE_URL, {})

        assert response.status_code == 400
        assert "token" in response.data
