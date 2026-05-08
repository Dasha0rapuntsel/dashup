from django.conf import settings
from django.db import models

from courses.models import Course
from lessons.models import Lesson


class Homework(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="homeworks",
        verbose_name="Курс",
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="homeworks",
        verbose_name="Занятие",
    )
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    due_date = models.DateField(null=True, blank=True, verbose_name="Срок сдачи")
    max_score = models.PositiveIntegerField(default=10, verbose_name="Максимальный балл")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Домашнее задание"
        verbose_name_plural = "Домашние задания"

    def __str__(self):
        return f"{self.course.title} — {self.title}"


class HomeworkStatus(models.Model):
    STATUS_CHOICES = (
        ("not_started", "Не начато"),
        ("submitted", "Отправлено"),
        ("checked", "Проверено"),
    )

    homework = models.ForeignKey(
        Homework,
        on_delete=models.CASCADE,
        related_name="statuses",
        verbose_name="Домашнее задание",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="homework_statuses",
        verbose_name="Ученик",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="not_started",
        verbose_name="Статус",
    )
    answer_text = models.TextField(blank=True, verbose_name="Ответ ученика")
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата отправки")
    teacher_comment = models.TextField(blank=True, verbose_name="Комментарий преподавателя")
    score = models.PositiveIntegerField(null=True, blank=True, verbose_name="Балл")

    class Meta:
        unique_together = ("homework", "student")
        ordering = ["student__username"]
        verbose_name = "Статус домашнего задания"
        verbose_name_plural = "Статусы домашних заданий"

    def __str__(self):
        return f"{self.student.username} — {self.homework.title}"


class HomeworkAttachment(models.Model):
    homework = models.ForeignKey(
        Homework,
        on_delete=models.CASCADE,
        related_name="attachments",
        verbose_name="Домашнее задание",
    )
    title = models.CharField(max_length=200, blank=True, verbose_name="Название файла")
    file = models.FileField(
        upload_to="homework_attachments/%Y/%m/%d/",
        verbose_name="Файл преподавателя",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Файл преподавателя"
        verbose_name_plural = "Файлы преподавателя"

    def __str__(self):
        return self.title or self.file.name


class HomeworkSubmissionAttachment(models.Model):
    status = models.ForeignKey(
        HomeworkStatus,
        on_delete=models.CASCADE,
        related_name="submission_attachments",
        verbose_name="Статус домашнего задания",
    )
    title = models.CharField(max_length=200, blank=True, verbose_name="Название файла")
    file = models.FileField(
        upload_to="homework_submissions/%Y/%m/%d/",
        verbose_name="Файл ученика",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Файл ответа ученика"
        verbose_name_plural = "Файлы ответов учеников"

    def __str__(self):
        return self.title or self.file.name