import pytest
from users.serializers import RegistrationSerializer


@pytest.mark.django_db
class TestRegistrationSerializer:
    def test_valid_payload_passes(self):
        data = {
            "email": "test@example.com",
            "password": "secret123",
            "password_repeat": "secret123",
            "first_name": "John",
            "last_name": "Doe",
        }

        serializer = RegistrationSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

    def test_password_mismatch(self):
        data = {
            "email": "test@example.com",
            "password": "secret123",
            "password_repeat": "different",
            "first_name": "John",
            "last_name": "Doe",
        }

        serializer = RegistrationSerializer(data=data)

        assert not serializer.is_valid()
        assert "password_repeat" in serializer.errors

    def test_empty_payload_rejects_required_fields(self):
        serializer = RegistrationSerializer(data={})

        assert not serializer.is_valid()
        assert "email" in serializer.errors
        assert "password" in serializer.errors
        assert "password_repeat" in serializer.errors

    def test_first_name_and_last_name_are_optional(self):
        data = {
            "email": "test@example.com",
            "password": "secret123",
            "password_repeat": "secret123",
        }

        serializer = RegistrationSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
