from django import forms

from courses.models import Course
from .models import Lesson


class LessonCreateForm(forms.ModelForm):
    create_mode = forms.ChoiceField(
        choices=(
            ("one_time", "Разовое занятие"),
            ("recurring", "Постоянное занятие"),
        ),
        label="Тип создания",
        initial="one_time",
    )

    repeat_every_weeks = forms.ChoiceField(
        choices=(
            ("1", "Каждую неделю"),
            ("2", "Раз в 2 недели"),
        ),
        label="Повтор",
        required=False,
        initial="1",
    )

    repeat_until = forms.DateField(
        required=False,
        label="Повторять до",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    class Meta:
        model = Lesson
        fields = [
            "course",
            "title",
            "lesson_date",
            "start_time",
            "duration_minutes",
            "status",
            "notes",
        ]
        widgets = {
            "lesson_date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "notes": forms.Textarea(attrs={"rows": 4, "cols": 60}),
        }
        labels = {
            "title": "Название занятия (необязательно)",
        }

    def __init__(self, *args, teacher=None, initial_date=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["title"].required = False

        if teacher is not None:
            self.fields["course"].queryset = Course.objects.filter(
                teacher=teacher,
                is_active=True,
            ).order_by("title")

        if initial_date is not None:
            self.fields["lesson_date"].initial = initial_date

    def clean(self):
        cleaned_data = super().clean()

        create_mode = cleaned_data.get("create_mode")
        lesson_date = cleaned_data.get("lesson_date")
        repeat_until = cleaned_data.get("repeat_until")

        if create_mode == "recurring":
            if not repeat_until:
                raise forms.ValidationError("Для постоянного занятия укажите дату, до которой повторять.")
            if lesson_date and repeat_until < lesson_date:
                raise forms.ValidationError("Дата окончания повторения не может быть раньше даты первого занятия.")

        return cleaned_data


class LessonEditForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = [
            "title",
            "lesson_date",
            "start_time",
            "duration_minutes",
            "status",
            "notes",
        ]
        widgets = {
            "lesson_date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "notes": forms.Textarea(attrs={"rows": 4, "cols": 60}),
        }
        labels = {
            "title": "Название занятия (необязательно)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].required = False