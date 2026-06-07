from django.db import transaction
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import (
    ActivationSerializer,
    RegistrationSerializer,
    UserDetailSerializer,
)


class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegistrationSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer


class UserActivationView(APIView):
    @transaction.atomic
    def post(self, request):
        serializer = ActivationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Email was successfully verified."})
