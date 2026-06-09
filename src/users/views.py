from django.db import transaction
from django.utils import timezone
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import EmailVerificationToken, User
from .serializers import RegistrationSerializer, UserDetailSerializer


class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegistrationSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer


class EmailVerificationView(APIView):
    @transaction.atomic
    def post(self, request, token):
        try:
            token_obj = EmailVerificationToken.objects.select_related("user").get(
                token=token
            )
        except EmailVerificationToken.DoesNotExist:
            return Response(
                {"detail": "Invalid or expired token."},
                status=404,
            )

        if (
            token_obj.expires_at < timezone.now()
            and not token_obj.user.email_verified
        ):
            return Response(
                {"detail": "Invalid or expired token."},
                status=404,
            )

        user = token_obj.user
        user.email_verified = True
        user.save(update_fields=["email_verified"])
        return Response({"detail": "Email was successfully verified."})
