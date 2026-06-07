import pytest
from rest_framework.test import APIClient
from users.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user(db):
    def _create_user(**kwargs):
        defaults = {
            "email": "test@example.com",
            "password": "secret123",
        }
        defaults.update(kwargs)
        return User.objects.create_user(**defaults)

    return _create_user
