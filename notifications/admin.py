from django.contrib import admin
from .models import TelegramProfile, NotificationLog


@admin.register(TelegramProfile)
class TelegramProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "chat_id", "username", "is_linked", "linked_at")
    list_filter = ("is_linked",)
    search_fields = ("user__username", "username", "chat_id")


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ("recipient", "notification_type", "status", "sent_at", "created_at")
    list_filter = ("notification_type", "status")
    search_fields = ("recipient__username", "message")
