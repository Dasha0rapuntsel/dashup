from django.conf import settings
from django.db import models

from courses.models import Course


class Payment(models.Model):
    STATUS_CHOICES = (
        ("pending", "Ожидается"),
        ("paid", "Оплачено"),
        ("overdue", "Просрочено"),
    )

    METHOD_CHOICES = (
        ("sbp", "СБП"),
        ("card", "Карта"),
        ("cash", "Наличные"),
        ("transfer", "Перевод"),
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Ученик",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Направление",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")
    due_date = models.DateField(verbose_name="Срок оплаты")
    paid_at = models.DateField(null=True, blank=True, verbose_name="Дата оплаты")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="Статус")
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, blank=True, default="", verbose_name="Способ оплаты")
    period_label = models.CharField(max_length=200, blank=True, default="", verbose_name="За что оплата / период")
    note = models.TextField(blank=True, verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-due_date", "-created_at"]
        verbose_name = "Оплата"
        verbose_name_plural = "Оплаты"

    def __str__(self):
        return f"{self.student.username} — {self.amount} — {self.get_status_display()}"