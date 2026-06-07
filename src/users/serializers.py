from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
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
        EmailVerificationToken.objects.create(
            user=user,
            expires_at=timezone.now()
            + timedelta(seconds=settings.EMAIL_VERIFICATION_TOKEN_LIFETIME),
        )
        transaction.on_commit(lambda: send_verification_email.delay(user.id))
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


class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.UUIDField()

    def validate_token(self, value):
        try:
            token_obj = EmailVerificationToken.objects.select_related("user").get(
                token=value
            )
        except EmailVerificationToken.DoesNotExist:
            raise serializers.ValidationError("Invalid token.")

        if token_obj.expires_at < timezone.now() and not token_obj.user.email_verified:
            raise serializers.ValidationError("Token has expired.")

        self._token_obj = token_obj
        return value

    def save(self, **kwargs):
        user = self._token_obj.user
        user.email_verified = True
        user.save(update_fields=["email_verified"])
