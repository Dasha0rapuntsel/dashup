from datetime import date

from django import forms
from django.utils import timezone

from courses.models import Course
from lessons.models import Lesson
from .models import Homework, HomeworkAttachment, HomeworkSubmissionAttachment


class HomeworkCreateForm(forms.ModelForm):
    attachment_title = forms.CharField(required=False, label="Название файла")
    attachment_file = forms.FileField(required=False, label="Файл к заданию")

    class Meta:
        model = Homework
        fields = ["course", "lesson", "title", "description", "due_date", "max_score"]

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)

        if teacher is not None:
            self.fields["course"].queryset = Course.objects.filter(
                teacher=teacher,
                is_active=True,
            ).order_by("title")

            self.fields["lesson"].queryset = Lesson.objects.filter(
                course__teacher=teacher,
                course__is_active=True,
            ).select_related("course").order_by("-lesson_date", "start_time")
        else:
            self.fields["course"].queryset = Course.objects.none()
            self.fields["lesson"].queryset = Lesson.objects.none()

        self.fields["lesson"].required = False
        self.fields["description"].widget = forms.Textarea(attrs={"rows": 8, "cols": 70})
        self.fields["due_date"].widget = forms.DateInput(attrs={"type": "date"})

    def clean(self):
        cleaned_data = super().clean()
        course = cleaned_data.get("course")
        lesson = cleaned_data.get("lesson")

        if lesson and course and lesson.course != course:
            raise forms.ValidationError("Выбранное занятие не относится к выбранному курсу.")

        return cleaned_data

    def save(self, teacher, commit=True):
        homework = super().save(commit=False)

        if homework.course.teacher != teacher:
            raise forms.ValidationError("Нельзя создавать ДЗ для чужого курса.")

        if commit:
            homework.save()

            uploaded_file = self.cleaned_data.get("attachment_file")
            attachment_title = self.cleaned_data.get("attachment_title", "").strip()

            if uploaded_file:
                HomeworkAttachment.objects.create(
                    homework=homework,
                    title=attachment_title,
                    file=uploaded_file,
                )

        return homework


class HomeworkSubmissionForm(forms.Form):
    answer_text = forms.CharField(
        required=False,
        label="Текст ответа",
        widget=forms.Textarea(attrs={"rows": 8, "cols": 70}),
    )
    attachment_title = forms.CharField(required=False, label="Название файла")
    submission_file = forms.FileField(required=False, label="Файл / фото решения")

    def save(self, status_obj):
        status_obj.answer_text = self.cleaned_data.get("answer_text", "").strip()
        status_obj.status = "submitted"
        status_obj.submitted_at = timezone.now()
        status_obj.save()

        uploaded_file = self.cleaned_data.get("submission_file")
        attachment_title = self.cleaned_data.get("attachment_title", "").strip()

        if uploaded_file:
            HomeworkSubmissionAttachment.objects.create(
                status=status_obj,
                title=attachment_title,
                file=uploaded_file,
            )

        return status_obj


class HomeworkReviewForm(forms.Form):
    score = forms.IntegerField(required=False, label="Балл", min_value=0)
    teacher_comment = forms.CharField(
        required=False,
        label="Комментарий",
        widget=forms.Textarea(attrs={"rows": 4, "cols": 60}),
    )

    def __init__(self, *args, max_score=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_score = max_score

    def clean_score(self):
        score = self.cleaned_data.get("score")

        if score is not None and self.max_score is not None and score > self.max_score:
            raise forms.ValidationError(f"Балл не может быть больше {self.max_score}.")
        return score

    def save(self, status_obj):
        status_obj.score = self.cleaned_data.get("score")
        status_obj.teacher_comment = self.cleaned_data.get("teacher_comment", "").strip()
        status_obj.status = "checked"
        status_obj.save()
        return status_obj