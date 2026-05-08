from django.conf import settings
from django.db import models


class Course(models.Model):
    FORMAT_CHOICES = (
        ("group", "Групповой"),
        ("individual", "Индивидуальный"),
    )

    # Оставляем title, чтобы не ломать текущие страницы
    title = models.CharField(max_length=200, verbose_name="Название")

    subject_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        verbose_name="Предмет",
    )
    level = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Класс / уровень",
    )
    format = models.CharField(
        max_length=20,
        choices=FORMAT_CHOICES,
        default="group",
        verbose_name="Формат",
    )
    group_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        verbose_name="Группа / ученик",
    )

    description = models.TextField(blank=True, verbose_name="Описание")
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teaching_courses",
        verbose_name="Преподаватель",
    )
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        # Если новые поля заполнены — автоматически собираем красивое название
        if self.subject_name:
            parts = [self.subject_name]

            if self.level:
                parts.append(self.level)

            if self.format == "group":
                if self.group_name:
                    parts.append(f"группа {self.group_name}")
                else:
                    parts.append("группа")
            else:
                if self.group_name:
                    parts.append(f"индивидуально ({self.group_name})")
                else:
                    parts.append("индивидуально")

            self.title = " — ".join(parts)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Enrollment(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="course_enrollments",
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("course", "student")
        verbose_name = "Запись на курс"
        verbose_name_plural = "Записи на курс"

    def __str__(self):
        return f"{self.student.username} -> {self.course.title}"