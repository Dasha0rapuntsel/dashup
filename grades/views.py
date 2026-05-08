from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Max
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from courses.models import Course, Enrollment
from .forms import GradeCreateForm
from .models import Grade


@login_required
def grade_list(request):
    if request.user.role == "teacher":
        # Build a per-course student table with stats
        courses = (
            Course.objects
            .filter(teacher=request.user, is_active=True)
            .prefetch_related("enrollments__student")
            .order_by("title")
        )

        students_data = {}

        for course in courses:
            student_list = []
            for enrollment in course.enrollments.filter(is_active=True, student__role="student"):
                student = enrollment.student
                grades = Grade.objects.filter(student=student, course=course)

                avg_data = grades.aggregate(
                    avg_score=Avg("score"),
                    avg_max=Avg("max_score"),
                    count=Count("id"),
                )

                last_grade = grades.order_by("-created_at").first()

                full_name = f"{student.first_name} {student.last_name}".strip()
                name = full_name if full_name else student.username
                initial = name[0].upper() if name else "?"

                student_list.append({
                    "id": student.id,
                    "course_id": course.id,
                    "username": student.username,
                    "name": name,
                    "initial": initial,
                    "avg_score": round(avg_data["avg_score"], 1) if avg_data["avg_score"] else None,
                    "avg_max": round(avg_data["avg_max"], 1) if avg_data["avg_max"] else None,
                    "grade_count": avg_data["count"],
                    "last_grade": last_grade,
                })

            if student_list:
                students_data[course.title] = student_list

        return render(request, "grades/teacher_grade_list.html", {
            "students_data": students_data,
        })

    # Student view
    grades = (
        Grade.objects
        .filter(student=request.user)
        .select_related("course", "lesson")
        .order_by("-created_at")
    )
    return render(request, "grades/student_grade_list.html", {"grades": grades})


@login_required
def create_grade(request):
    if request.user.role != "teacher":
        return HttpResponseForbidden("Только преподаватель может ставить оценки")

    initial = {}
    if request.GET.get("student"):
        initial["student"] = request.GET["student"]
    if request.GET.get("course"):
        initial["course"] = request.GET["course"]

    if request.method == "POST":
        form = GradeCreateForm(request.POST, teacher=request.user)
        if form.is_valid():
            grade = form.save(commit=False)
            if grade.course.teacher != request.user:
                return HttpResponseForbidden("Нельзя ставить оценки чужим ученикам")
            grade.save()
            return redirect("grade_list")
    else:
        form = GradeCreateForm(teacher=request.user, initial=initial)

    return render(request, "grades/create_grade.html", {"form": form})


@login_required
def grade_detail(request, grade_id):
    grade = get_object_or_404(
        Grade.objects.select_related("student", "course", "lesson", "course__teacher"),
        id=grade_id,
    )

    if request.user.role == "teacher":
        if grade.course.teacher != request.user:
            return HttpResponseForbidden("Вы не можете просматривать эту оценку")
    else:
        if grade.student != request.user:
            return HttpResponseForbidden("Вы не можете просматривать эту оценку")

    return render(request, "grades/grade_detail.html", {"grade": grade})
