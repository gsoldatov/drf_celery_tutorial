from django.contrib import admin
from .models import User, EmailVerificationToken


class UserAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "first_name",
        "last_name",
        "email_verified",
        "is_staff",
        "is_active",
        "date_joined",
    )


class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "token", "status", "expires_at", "sent_at")


admin.site.register(User, UserAdmin)
admin.site.register(EmailVerificationToken, EmailVerificationTokenAdmin)
