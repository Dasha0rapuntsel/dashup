from django import forms
from django.contrib.auth import get_user_model

from courses.models import Course, Enrollment
from .models import Quiz, Question, Choice

User = get_user_model()


class QuizCreateForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ["course", "title", "description", "time_limit_minutes", "is_active"]
        labels = {
            "course": "Направление",
            "title": "Название теста",
            "description": "Описание",
            "time_limit_minutes": "Ограничение по времени (мин, необязательно)",
            "is_active": "Активен",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields["course"].queryset = Course.objects.filter(
                teacher=teacher, is_active=True
            ).order_by("title")


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["text", "question_type", "points"]
        labels = {
            "text": "Текст вопроса",
            "question_type": "Тип вопроса",
            "points": "Баллы",
        }
        widgets = {
            "text": forms.Textarea(attrs={"rows": 3}),
        }


class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ["text", "is_correct"]
        labels = {
            "text": "Вариант ответа",
            "is_correct": "Правильный",
        }


# Formset для вариантов ответа
ChoiceFormSet = forms.inlineformset_factory(
    Question,
    Choice,
    form=ChoiceForm,
    extra=4,
    max_num=8,
    can_delete=True,
)
