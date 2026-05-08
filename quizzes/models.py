from django.conf import settings
from django.db import models

from courses.models import Course


class Quiz(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="quizzes",
        verbose_name="Направление",
    )
    title = models.CharField(max_length=200, verbose_name="Название теста")
    description = models.TextField(blank=True, verbose_name="Описание")
    time_limit_minutes = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Ограничение по времени (мин)"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True)

    # Если задан — тест назначается только этим ученикам
    assigned_students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="assigned_quizzes",
        verbose_name="Назначить ученикам",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Тест"
        verbose_name_plural = "Тесты"

    def __str__(self):
        return f"{self.course.title} — {self.title}"

    @property
    def question_count(self):
        return self.questions.count()

    @property
    def max_score(self):
        return sum(q.points for q in self.questions.all())


class Question(models.Model):
    TYPE_CHOICES = (
        ("single", "Один правильный ответ"),
        ("multiple", "Несколько правильных ответов"),
        ("text", "Текстовый ответ"),
    )

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="Тест",
    )
    text = models.TextField(verbose_name="Текст вопроса")
    question_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default="single",
        verbose_name="Тип вопроса",
    )
    points = models.PositiveIntegerField(default=1, verbose_name="Баллы за правильный ответ")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"

    def __str__(self):
        return f"Вопрос {self.order}: {self.text[:60]}"


class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="choices",
        verbose_name="Вопрос",
    )
    text = models.CharField(max_length=500, verbose_name="Вариант ответа")
    is_correct = models.BooleanField(default=False, verbose_name="Правильный")

    class Meta:
        ordering = ["id"]
        verbose_name = "Вариант ответа"
        verbose_name_plural = "Варианты ответов"

    def __str__(self):
        mark = "✓" if self.is_correct else "✗"
        return f"{mark} {self.text[:40]}"


class QuizAttempt(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name="Тест",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quiz_attempts",
        verbose_name="Ученик",
    )
    score = models.PositiveIntegerField(default=0, verbose_name="Набрано баллов")
    max_score = models.PositiveIntegerField(default=0, verbose_name="Максимум баллов")
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    is_finished = models.BooleanField(default=False, verbose_name="Завершён")

    class Meta:
        ordering = ["-started_at"]
        verbose_name = "Попытка"
        verbose_name_plural = "Попытки"

    def __str__(self):
        return f"{self.student.username} — {self.quiz.title} — {self.score}/{self.max_score}"


class AttemptAnswer(models.Model):
    attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="Попытка",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="attempt_answers",
        verbose_name="Вопрос",
    )
    selected_choices = models.ManyToManyField(
        Choice,
        blank=True,
        related_name="attempt_answers",
        verbose_name="Выбранные варианты",
    )
    text_answer = models.TextField(blank=True, verbose_name="Текстовый ответ")
    is_correct = models.BooleanField(default=False, verbose_name="Правильно")
    points_earned = models.PositiveIntegerField(default=0, verbose_name="Баллы")

    class Meta:
        unique_together = ("attempt", "question")
        verbose_name = "Ответ ученика"
        verbose_name_plural = "Ответы учеников"

    def __str__(self):
        return f"Ответ на: {self.question.text[:40]}"
