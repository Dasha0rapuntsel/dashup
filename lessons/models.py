from datetime import datetime, timedelta, date
import uuid

from django.db import models
from courses.models import Course


class Lesson(models.Model):
    STATUS_CHOICES = (
        ("planned", "Запланировано"),
        ("completed", "Проведено"),
        ("cancelled", "Отменено"),
    )

    TYPE_CHOICES = (
        ("one_time", "Разовое"),
        ("recurring", "Постоянное"),
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="lessons",
        verbose_name="Курс",
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        default="",
        verbose_name="Название занятия",
    )
    lesson_date = models.DateField(verbose_name="Дата занятия")
    start_time = models.TimeField(verbose_name="Время начала")
    duration_minutes = models.PositiveIntegerField(default=60, verbose_name="Длительность (мин)")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="planned",
        verbose_name="Статус",
    )
    lesson_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default="one_time",
        verbose_name="Тип занятия",
    )
    series_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Серия занятий",
    )
    original_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Изначальная дата",
    )
    original_start_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Изначальное время",
    )
    notes = models.TextField(blank=True, verbose_name="Комментарий")

    class Meta:
        ordering = ["lesson_date", "start_time"]
        verbose_name = "Занятие"
        verbose_name_plural = "Занятия"

    @property
    def end_time(self):
        dt = datetime.combine(date.today(), self.start_time) + timedelta(minutes=self.duration_minutes)
        return dt.time()

    @property
    def time_range(self):
        return f"{self.start_time.strftime('%H:%M')}–{self.end_time.strftime('%H:%M')}"

    @property
    def is_rescheduled(self):
        return bool(self.original_date or self.original_start_time)

    def __str__(self):
        label = self.title if self.title else self.course.title
        return f"{label} ({self.lesson_date} {self.time_range})"