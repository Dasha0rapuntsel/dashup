from django.contrib import admin
from .models import Grade


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "lesson", "score", "max_score", "created_at")
    list_filter = ("course", "lesson")
    search_fields = ("student__username", "course__title")
