from django import forms
from django.contrib.auth import get_user_model

from .models import Course, Enrollment

User = get_user_model()


class CourseCreateForm(forms.ModelForm):
    students = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(role="student").order_by("username"),
        required=False,
        label="Ученики",
        widget=forms.SelectMultiple(attrs={"size": 8}),
    )

    class Meta:
        model = Course
        fields = [
            "subject_name",
            "level",
            "format",
            "group_name",
            "description",
            "is_active",
        ]
        labels = {
            "subject_name": "Предмет",
            "level": "Класс / уровень",
            "format": "Формат",
            "group_name": "Группа / имя ученика",
            "description": "Описание",
            "is_active": "Активно",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        format_value = cleaned_data.get("format")
        students = cleaned_data.get("students")

        if format_value == "individual":
            if not students or students.count() != 1:
                raise forms.ValidationError("Для индивидуального направления нужно выбрать ровно одного ученика.")

        if format_value == "group":
            if not students or students.count() < 1:
                raise forms.ValidationError("Для группового направления нужно выбрать хотя бы одного ученика.")

        return cleaned_data

    def save(self, teacher):
        course = super().save(commit=False)
        course.teacher = teacher

        students = self.cleaned_data.get("students")

        if course.format == "individual" and not course.group_name and students:
            student = students.first()
            full_name = f"{student.first_name} {student.last_name}".strip()
            course.group_name = full_name if full_name else student.username

        course.save()

        for student in students:
            Enrollment.objects.get_or_create(
                course=course,
                student=student,
                defaults={"is_active": True},
            )

        return course