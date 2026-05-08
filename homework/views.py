from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import HomeworkCreateForm, HomeworkSubmissionForm, HomeworkReviewForm
from .models import Homework, HomeworkStatus


@login_required
def homework_list(request):
    if request.user.role == "teacher":
        homeworks = (
            Homework.objects
            .filter(course__teacher=request.user, is_active=True)
            .select_related("course", "lesson")
            .order_by("-created_at")
        )
        return render(
            request,
            "homework/teacher_homework_list.html",
            {"homeworks": homeworks},
        )

    statuses = (
        HomeworkStatus.objects
        .filter(student=request.user, homework__is_active=True)
        .select_related("homework", "homework__course", "homework__lesson")
        .order_by("-homework__created_at")
    )
    return render(
        request,
        "homework/student_homework_list.html",
        {"statuses": statuses},
    )


@login_required
def create_homework(request):
    if request.user.role != "teacher":
        return HttpResponseForbidden("Только преподаватель может создавать ДЗ")

    if request.method == "POST":
        form = HomeworkCreateForm(request.POST, request.FILES, teacher=request.user)
        if form.is_valid():
            homework = form.save(teacher=request.user)
            return redirect("homework_detail", homework_id=homework.id)
    else:
        form = HomeworkCreateForm(teacher=request.user)

    return render(
        request,
        "homework/create_homework.html",
        {"form": form},
    )


@login_required
def homework_detail(request, homework_id):
    homework = get_object_or_404(
        Homework.objects.select_related("course", "lesson", "course__teacher"),
        id=homework_id,
        is_active=True,
    )

    if request.user.role == "teacher":
        if homework.course.teacher != request.user:
            return HttpResponseForbidden("Вы не можете просматривать это ДЗ")

        statuses = (
            HomeworkStatus.objects
            .filter(homework=homework)
            .select_related("student")
            .order_by("student__username")
        )

        return render(
            request,
            "homework/teacher_homework_detail.html",
            {
                "homework": homework,
                "statuses": statuses,
            },
        )

    status_obj = get_object_or_404(
        HomeworkStatus.objects.select_related("homework", "student"),
        homework=homework,
        student=request.user,
    )

    form = HomeworkSubmissionForm(
        initial={"answer_text": status_obj.answer_text}
    )

    return render(
        request,
        "homework/student_homework_detail.html",
        {
            "homework": homework,
            "status_obj": status_obj,
            "form": form,
        },
    )


@login_required
def submit_homework(request, homework_id):
    if request.user.role != "student":
        return HttpResponseForbidden("Только ученик может отправить ДЗ")

    homework = get_object_or_404(Homework, id=homework_id, is_active=True)
    status_obj = get_object_or_404(
        HomeworkStatus,
        homework=homework,
        student=request.user,
    )

    if request.method == "POST":
        form = HomeworkSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            form.save(status_obj)
            return redirect("homework_detail", homework_id=homework.id)

    return redirect("homework_detail", homework_id=homework.id)


@login_required
def review_submission(request, status_id):
    if request.user.role != "teacher":
        return HttpResponseForbidden("Только преподаватель может проверять ДЗ")

    status_obj = get_object_or_404(
        HomeworkStatus.objects.select_related("homework", "homework__course", "student"),
        id=status_id,
    )

    if status_obj.homework.course.teacher != request.user:
        return HttpResponseForbidden("Вы не можете проверять это ДЗ")

    if request.method == "POST":
        form = HomeworkReviewForm(
            request.POST,
            max_score=status_obj.homework.max_score,
        )
        if form.is_valid():
            form.save(status_obj)
            return redirect("homework_detail", homework_id=status_obj.homework.id)
    else:
        form = HomeworkReviewForm(
            initial={
                "score": status_obj.score,
                "teacher_comment": status_obj.teacher_comment,
            },
            max_score=status_obj.homework.max_score,
        )

    return render(
        request,
        "homework/review_submission.html",
        {
            "status_obj": status_obj,
            "homework": status_obj.homework,
            "form": form,
        },
    )