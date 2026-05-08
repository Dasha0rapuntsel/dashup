from datetime import date, timedelta

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render

User = get_user_model()

from courses.models import Course, Enrollment
from homework.models import HomeworkStatus
from lessons.models import Lesson
from quizzes.models import Quiz, QuizAttempt


def home(request):
    return redirect("portal")


def portal(request):
    return render(request, "users/portal.html")


def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.role == "teacher":
                return redirect("teacher_dashboard")
            return redirect("student_dashboard")

        return render(request, "users/login.html", {"error": "Неверный логин или пароль"})

    return render(request, "users/login.html")


def user_logout(request):
    logout(request)
    return redirect("login")


@login_required
def student_dashboard(request):
    if request.user.role != "student":
        return HttpResponseForbidden("Доступ только для учеников")

    enrollments = (
        Enrollment.objects
        .filter(student=request.user, is_active=True, course__is_active=True)
        .select_related("course")
        .order_by("-enrolled_at")
    )
    courses = [e.course for e in enrollments]

    today = date.today()
    week_end = today + timedelta(days=7)
    course_ids = [c.id for c in courses]

    upcoming_lessons_count = Lesson.objects.filter(
        course_id__in=course_ids,
        lesson_date__gte=today,
        lesson_date__lte=week_end,
        status="planned",
    ).count()

    pending_hw_count = HomeworkStatus.objects.filter(
        student=request.user,
        homework__is_active=True,
        status="not_started",
    ).count()

    quiz_count = Quiz.objects.filter(
        course_id__in=course_ids,
        is_active=True,
    ).filter(
        Q(assigned_students__isnull=True) | Q(assigned_students=request.user)
    ).distinct().count()

    return render(request, "users/student_dashboard.html", {
        "courses": courses,
        "upcoming_lessons_count": upcoming_lessons_count,
        "pending_hw_count": pending_hw_count,
        "quiz_count": quiz_count,
    })


@login_required
def teacher_dashboard(request):
    if request.user.role != "teacher":
        return HttpResponseForbidden("Доступ только для преподавателя")

    courses = Course.objects.filter(teacher=request.user).order_by("-created_at")

    student_count = (
        Enrollment.objects
        .filter(course__teacher=request.user, is_active=True, student__role="student")
        .values("student_id")
        .distinct()
        .count()
    )

    today = date.today()
    week_end = today + timedelta(days=7)
    upcoming_lessons_count = Lesson.objects.filter(
        course__teacher=request.user,
        lesson_date__gte=today,
        lesson_date__lte=week_end,
        status="planned",
    ).count()

    pending_hw_count = HomeworkStatus.objects.filter(
        homework__course__teacher=request.user,
        homework__is_active=True,
        status="submitted",
    ).count()

    return render(request, "users/teacher_dashboard.html", {
        "courses": courses,
        "student_count": student_count,
        "upcoming_lessons_count": upcoming_lessons_count,
        "pending_hw_count": pending_hw_count,
    })


def register(request):
    if request.user.is_authenticated:
        return redirect("portal")

    errors = []
    form_data = {}

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")
        role = request.POST.get("role", "student")

        form_data = {
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "email": email,
        }

        if not first_name:
            errors.append("Введите имя.")
        if not last_name:
            errors.append("Введите фамилию.")
        if not username:
            errors.append("Введите логин.")
        elif User.objects.filter(username=username).exists():
            errors.append("Этот логин уже занят.")
        if len(password) < 6:
            errors.append("Пароль должен содержать минимум 6 символов.")
        if password != password2:
            errors.append("Пароли не совпадают.")
        if role not in ("student", "teacher"):
            role = "student"

        if not errors:
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=role,
            )
            login(request, user)
            if role == "teacher":
                return redirect("teacher_dashboard")
            return redirect("student_dashboard")

    return render(request, "users/register.html", {
        "errors": errors,
        "form_data": form_data,
    })
