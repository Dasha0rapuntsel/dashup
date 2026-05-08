from django.contrib import admin
from .models import Course, Enrollment


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "subject_name",
        "level",
        "format",
        "group_name",
        "teacher",
        "is_active",
        "created_at",
    )
    list_filter = ("format", "is_active", "teacher")
    search_fields = ("title", "subject_name", "level", "group_name")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("course", "student", "is_active", "enrolled_at")
    list_filter = ("is_active", "course")
    search_fields = ("course__title", "student__username")