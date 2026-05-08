import uuid

from django.conf import settings
from django.db import models


class TelegramProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="telegram_profile",
        verbose_name="Пользователь",
    )
    chat_id = models.BigIntegerField(
        null=True, blank=True, unique=True, verbose_name="Telegram chat_id"
    )
    username = models.CharField(
        max_length=200, blank=True, verbose_name="Telegram username"
    )
    link_code = models.CharField(
        max_length=64, blank=True, verbose_name="Код привязки",
        help_text="Код, который ученик отправляет боту для привязки",
    )
    is_linked = models.BooleanField(default=False, verbose_name="Привязан")
    linked_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата привязки")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Telegram-профиль"
        verbose_name_plural = "Telegram-профили"

    def __str__(self):
        status = "привязан" if self.is_linked else "не привязан"
        return f"{self.user.username} — {status}"

    def generate_link_code(self):
        self.link_code = uuid.uuid4().hex[:8]
        self.save(update_fields=["link_code"])
        return self.link_code


class NotificationLog(models.Model):
    TYPE_CHOICES = (
        ("lesson_reminder", "Напоминание о занятии"),
        ("homework_new", "Новое домашнее задание"),
        ("homework_deadline", "Дедлайн ДЗ"),
        ("homework_overdue", "Просроченное ДЗ"),
        ("payment_reminder", "Напоминание об оплате"),
        ("quiz_assigned", "Назначен тест"),
        ("custom", "Сообщение от преподавателя"),
    )

    STATUS_CHOICES = (
        ("pending", "Ожидает отправки"),
        ("sent", "Отправлено"),
        ("failed", "Ошибка"),
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_logs",
        verbose_name="Получатель",
    )
    notification_type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES,
        verbose_name="Тип уведомления",
    )
    message = models.TextField(verbose_name="Текст сообщения")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name="Статус",
    )
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата отправки")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Журнал уведомлений"
        verbose_name_plural = "Журнал уведомлений"

    def __str__(self):
        return f"{self.recipient.username} — {self.get_notification_type_display()} — {self.get_status_display()}"
