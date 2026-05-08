from django.contrib import admin
from .models import (
    Homework,
    HomeworkStatus,
    HomeworkAttachment,
    HomeworkSubmissionAttachment,
)


class HomeworkAttachmentInline(admin.TabularInline):
    model = HomeworkAttachment
    extra = 1


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "lesson", "due_date", "max_score", "is_active")
    list_filter = ("course", "is_active", "due_date")
    search_fields = ("title", "course__title")
    inlines = [HomeworkAttachmentInline]


@admin.register(HomeworkStatus)
class HomeworkStatusAdmin(admin.ModelAdmin):
    list_display = ("homework", "student", "status", "score", "submitted_at")
    list_filter = ("status", "homework__course")
    search_fields = ("student__username", "homework__title")


@admin.register(HomeworkAttachment)
class HomeworkAttachmentAdmin(admin.ModelAdmin):
    list_display = ("homework", "title", "created_at")
    search_fields = ("title", "homework__title")


@admin.register(HomeworkSubmissionAttachment)
class HomeworkSubmissionAttachmentAdmin(admin.ModelAdmin):
    list_display = ("status", "title", "created_at")
    search_fields = ("title", "status__student__username", "status__homework__title")