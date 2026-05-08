from django import forms
from django.contrib.auth import get_user_model

from courses.models import Course, Enrollment
from .models import Payment

User = get_user_model()


class PaymentCreateForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["student", "course", "amount", "due_date", "period_label", "note"]
        labels = {
            "course": "Направление",
            "period_label": "За что оплата / период",
        }
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "note": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)

        if teacher is not None:
            teacher_courses = Course.objects.filter(
                teacher=teacher,
                is_active=True,
            ).order_by("title")

            self.fields["course"].queryset = teacher_courses

            student_ids = Enrollment.objects.filter(
                course__in=teacher_courses,
                is_active=True,
                student__role="student",
            ).values_list("student_id", flat=True)

            self.fields["student"].queryset = User.objects.filter(id__in=student_ids).order_by("username")

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get("student")
        course = cleaned_data.get("course")

        if student and course:
            is_enrolled = Enrollment.objects.filter(
                student=student,
                course=course,
                is_active=True,
            ).exists()

            if not is_enrolled:
                raise forms.ValidationError("Этот ученик не записан на выбранное направление.")

        return cleaned_data


class PaymentMarkPaidForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["method", "paid_at", "note"]
        widgets = {
            "paid_at": forms.DateInput(attrs={"type": "date"}),
            "note": forms.Textarea(attrs={"rows": 4}),
        }