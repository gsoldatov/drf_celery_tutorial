from django.contrib import admin
from .models import User, EmailVerificationToken

admin.site.register(User)


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "token", "status", "expires_at", "sent_at")
