from django.contrib import admin
from .models import Quiz, Question, Choice, QuizAttempt, AttemptAnswer


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "question_count", "is_active", "created_at")
    list_filter = ("course", "is_active")
    search_fields = ("title", "course__title")
    inlines = [QuestionInline]
    filter_horizontal = ("assigned_students",)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("quiz", "text", "question_type", "points", "order")
    list_filter = ("quiz", "question_type")
    inlines = [ChoiceInline]


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "quiz", "score", "max_score", "is_finished", "started_at")
    list_filter = ("quiz", "is_finished")
    search_fields = ("student__username", "quiz__title")


@admin.register(AttemptAnswer)
class AttemptAnswerAdmin(admin.ModelAdmin):
    list_display = ("attempt", "question", "is_correct", "points_earned")
