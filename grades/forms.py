from django import forms
from django.contrib.auth import get_user_model

from courses.models import Course, Enrollment
from lessons.models import Lesson
from .models import Grade

User = get_user_model()


class GradeCreateForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ["student", "course", "lesson", "score", "max_score", "comment"]
        labels = {
            "student": "Ученик",
            "course": "Направление",
            "lesson": "Занятие (необязательно)",
            "score": "Балл",
            "max_score": "Максимальный балл",
            "comment": "Комментарий",
        }
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["lesson"].required = False

        if teacher is not None:
            teacher_courses = Course.objects.filter(
                teacher=teacher, is_active=True
            ).order_by("title")

            self.fields["course"].queryset = teacher_courses

            student_ids = Enrollment.objects.filter(
                course__in=teacher_courses,
                is_active=True,
                student__role="student",
            ).values_list("student_id", flat=True)

            self.fields["student"].queryset = User.objects.filter(
                id__in=student_ids
            ).order_by("last_name", "first_name", "username")

            self.fields["lesson"].queryset = Lesson.objects.filter(
                course__teacher=teacher,
                course__is_active=True,
            ).select_related("course").order_by("-lesson_date", "start_time")

    def clean(self):
        cleaned_data = super().clean()
        score = cleaned_data.get("score")
        max_score = cleaned_data.get("max_score")

        if score is not None and max_score is not None and score > max_score:
            raise forms.ValidationError("Балл не может быть больше максимального.")

        student = cleaned_data.get("student")
        course = cleaned_data.get("course")
        if student and course:
            enrolled = Enrollment.objects.filter(
                student=student, course=course, is_active=True
            ).exists()
            if not enrolled:
                raise forms.ValidationError("Ученик не записан на это направление.")

        lesson = cleaned_data.get("lesson")
        if lesson and course and lesson.course != course:
            raise forms.ValidationError("Занятие не относится к выбранному направлению.")

        return cleaned_data
