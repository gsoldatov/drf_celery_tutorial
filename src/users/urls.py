from django.urls import path

from . import views

urlpatterns = [
    path("users/", views.UserRegistrationView.as_view(), name="user-registration"),
    path("users/<int:pk>/", views.UserDetailView.as_view(), name="user-detail"),
    path("activate/", views.UserActivationView.as_view(), name="user-activate"),
]
