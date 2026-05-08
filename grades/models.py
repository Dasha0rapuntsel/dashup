from django.conf import settings
from django.db import models

from courses.models import Course
from lessons.models import Lesson


class Grade(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="grades",
        verbose_name="Ученик",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="grades",
        verbose_name="Направление",
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="grades",
        verbose_name="Занятие",
    )
    score = models.PositiveIntegerField(verbose_name="Балл")
    max_score = models.PositiveIntegerField(default=10, verbose_name="Максимальный балл")
    comment = models.TextField(blank=True, verbose_name="Комментарий преподавателя")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Оценка"
        verbose_name_plural = "Оценки"

    def __str__(self):
        label = self.lesson.title if self.lesson and self.lesson.title else str(self.lesson)
        return f"{self.student.username} — {self.score}/{self.max_score} — {label}"
