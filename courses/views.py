from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CourseCreateForm
from .models import Course, Enrollment


@login_required
def course_list(request):
    if request.user.role == "teacher":
        return redirect("teacher_course_list")

    enrollments = (
        Enrollment.objects
        .filter(student=request.user, is_active=True, course__is_active=True)
        .select_related("course")
        .order_by("-enrolled_at")
    )
    courses = [e.course for e in enrollments]

    return render(
        request,
        "courses/student_course_list.html",
        {"courses": courses},
    )


@login_required
def teacher_course_list(request):
    if request.user.role != "teacher":
        return HttpResponseForbidden("Только преподаватель может видеть этот раздел")

    courses = (
        Course.objects
        .filter(teacher=request.user)
        .prefetch_related("enrollments__student")
        .order_by("-created_at")
    )

    return render(
        request,
        "courses/teacher_course_list.html",
        {"courses": courses},
    )


@login_required
def create_course(request):
    if request.user.role != "teacher":
        return HttpResponseForbidden("Только преподаватель может создавать направления")

    if request.method == "POST":
        form = CourseCreateForm(request.POST)
        if form.is_valid():
            course = form.save(teacher=request.user)
            return redirect("course_detail", course_id=course.id)
    else:
        form = CourseCreateForm()

    return render(
        request,
        "courses/create_course.html",
        {"form": form},
    )


@login_required
def course_detail(request, course_id):
    course = get_object_or_404(
        Course.objects.prefetch_related("enrollments__student"),
        id=course_id,
        is_active=True,
    )

    if request.user.role == "teacher":
        if course.teacher != request.user:
            return HttpResponseForbidden("Это не ваше направление")
    else:
        is_enrolled = Enrollment.objects.filter(
            course=course,
            student=request.user,
            is_active=True,
        ).exists()
        if not is_enrolled:
            return HttpResponseForbidden("У вас нет доступа к этому направлению")

    students = [
        enrollment.student
        for enrollment in course.enrollments.all()
        if enrollment.is_active
    ]

    return render(
        request,
        "courses/course_detail.html",
        {
            "course": course,
            "students": students,
        },
    )