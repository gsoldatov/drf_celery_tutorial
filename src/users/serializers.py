from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from kombu.exceptions import OperationalError as KombuOperationalError
from rest_framework import serializers

from .models import EmailVerificationToken, User
from .tasks import send_verification_email


class RegistrationSerializer(serializers.ModelSerializer):
    password_repeat = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "password", "password_repeat", "first_name", "last_name"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, attrs):
        if attrs["password"] != attrs["password_repeat"]:
            raise serializers.ValidationError(
                {"password_repeat": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_repeat")
        user = User.objects.create_user(**validated_data)
        token = EmailVerificationToken.objects.create(
            user=user,
            expires_at=timezone.now()
            + timedelta(seconds=settings.EMAIL_VERIFICATION_TOKEN_LIFETIME),
        )

        def _dispatch():
            try:
                send_verification_email.delay(token.id)
            except KombuOperationalError:
                # Broker unreachable -> move on
                # (can add logging or additional processing here)
                pass

        transaction.on_commit(_dispatch)
        return user


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "email_verified",
            "date_joined",
        ]
        read_only_fields = fields
