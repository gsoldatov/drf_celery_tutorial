import uuid

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()


class UserActivationToken(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="activation_tokens",
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    expires_at = models.DateTimeField()
