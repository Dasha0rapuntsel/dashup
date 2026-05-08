from django.contrib import admin
from .models import Lesson


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "lesson_date", "start_time", "duration_minutes", "status")
    list_filter = ("status", "course", "lesson_date")
    search_fields = ("title", "course__title")