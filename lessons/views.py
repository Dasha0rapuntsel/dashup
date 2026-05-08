from calendar import monthcalendar, monthrange
from collections import defaultdict
from datetime import date, timedelta
import json
import uuid

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from courses.models import Course, Enrollment
from .forms import LessonCreateForm, LessonEditForm
from .models import Lesson


def _get_user_lessons_queryset(user):
    if user.role == "teacher":
        return (
            Lesson.objects
            .filter(course__teacher=user, course__is_active=True)
            .select_related("course")
            .order_by("lesson_date", "start_time")
        )

    enrolled_course_ids = Enrollment.objects.filter(
        student=user,
        is_active=True,
        course__is_active=True,
    ).values_list("course_id", flat=True)

    return (
        Lesson.objects
        .filter(course_id__in=enrolled_course_ids)
        .select_related("course")
        .order_by("lesson_date", "start_time")
    )


def _build_course_participants_data(teacher):
    teacher_courses = (
        Course.objects
        .filter(teacher=teacher, is_active=True)
        .prefetch_related("enrollments__student")
        .order_by("title")
    )

    result = {}

    for course in teacher_courses:
        students = []
        for enrollment in course.enrollments.all():
            if enrollment.is_active:
                student = enrollment.student
                full_name = f"{student.first_name} {student.last_name}".strip()
                students.append(full_name if full_name else student.username)

        result[str(course.id)] = {
            "title": course.title,
            "format": getattr(course, "format", ""),
            "group_name": getattr(course, "group_name", ""),
            "students": students,
        }

    return result


@login_required
def lesson_schedule(request):
    today = date.today()
    return redirect("lesson_schedule_month", year=today.year, month=today.month)


@login_required
def lesson_schedule_month(request, year, month):
    first_day = date(year, month, 1)
    last_day_num = monthrange(year, month)[1]
    last_day = date(year, month, last_day_num)

    lessons = _get_user_lessons_queryset(request.user).filter(
        lesson_date__range=(first_day, last_day)
    )

    lessons_by_day = defaultdict(list)
    for lesson in lessons:
        lessons_by_day[lesson.lesson_date.day].append(lesson)

    cal = monthcalendar(year, month)

    if month == 1:
        prev_year = year - 1
        prev_month = 12
    else:
        prev_year = year
        prev_month = month - 1

    if month == 12:
        next_year = year + 1
        next_month = 1
    else:
        next_year = year
        next_month = month + 1

    month_names = {
        1: "Январь",
        2: "Февраль",
        3: "Март",
        4: "Апрель",
        5: "Май",
        6: "Июнь",
        7: "Июль",
        8: "Август",
        9: "Сентябрь",
        10: "Октябрь",
        11: "Ноябрь",
        12: "Декабрь",
    }

    calendar_data = []
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append(None)
            else:
                week_data.append({
                    "day": day,
                    "lessons": lessons_by_day.get(day, []),
                })
        calendar_data.append(week_data)

    return render(
        request,
        "lessons/calendar_month.html",
        {
            "calendar_data": calendar_data,
            "year": year,
            "month": month,
            "month_name": month_names[month],
            "prev_year": prev_year,
            "prev_month": prev_month,
            "next_year": next_year,
            "next_month": next_month,
        },
    )


@login_required
def lesson_schedule_day(request, year, month, day):
    selected_date = date(year, month, day)

    lessons = _get_user_lessons_queryset(request.user).filter(
        lesson_date=selected_date
    )

    return render(
        request,
        "lessons/calendar_day.html",
        {
            "selected_date": selected_date,
            "lessons": lessons,
        },
    )


@login_required
def create_lesson_on_date(request, year, month, day):
    if request.user.role != "teacher":
        return HttpResponseForbidden("Только преподаватель может создавать занятия")

    selected_date = date(year, month, day)
    course_participants_data = _build_course_participants_data(request.user)

    if request.method == "POST":
        form = LessonCreateForm(
            request.POST,
            teacher=request.user,
            initial_date=selected_date,
        )
        if form.is_valid():
            course = form.cleaned_data["course"]
            title = form.cleaned_data["title"]
            lesson_date = form.cleaned_data["lesson_date"]
            start_time = form.cleaned_data["start_time"]
            duration_minutes = form.cleaned_data["duration_minutes"]
            status = form.cleaned_data["status"]
            notes = form.cleaned_data["notes"]

            create_mode = form.cleaned_data["create_mode"]

            if create_mode == "one_time":
                Lesson.objects.create(
                    course=course,
                    title=title,
                    lesson_date=lesson_date,
                    start_time=start_time,
                    duration_minutes=duration_minutes,
                    status=status,
                    lesson_type="one_time",
                    notes=notes,
                )
            else:
                repeat_until = form.cleaned_data["repeat_until"]
                repeat_every_weeks = int(form.cleaned_data["repeat_every_weeks"])
                series_id = uuid.uuid4()

                current_date = lesson_date
                while current_date <= repeat_until:
                    Lesson.objects.create(
                        course=course,
                        title=title,
                        lesson_date=current_date,
                        start_time=start_time,
                        duration_minutes=duration_minutes,
                        status=status,
                        lesson_type="recurring",
                        series_id=series_id,
                        notes=notes,
                    )
                    current_date += timedelta(days=7 * repeat_every_weeks)

            return redirect(
                "lesson_schedule_day",
                year=selected_date.year,
                month=selected_date.month,
                day=selected_date.day,
            )
    else:
        form = LessonCreateForm(
            teacher=request.user,
            initial_date=selected_date,
        )

    return render(
        request,
        "lessons/create_lesson.html",
        {
            "form": form,
            "selected_date": selected_date,
            "course_participants_json": json.dumps(course_participants_data, ensure_ascii=False),
        },
    )


@login_required
def edit_lesson(request, lesson_id):
    lesson = get_object_or_404(
        Lesson.objects.select_related("course"),
        id=lesson_id,
    )

    if request.user.role != "teacher":
        return HttpResponseForbidden("Только преподаватель может редактировать занятия")

    if lesson.course.teacher != request.user:
        return HttpResponseForbidden("Вы не можете редактировать это занятие")

    if request.method == "POST":
        action = request.POST.get("action", "save")

        if action == "cancel":
            lesson.status = "cancelled"
            lesson.save()
            return redirect(
                "lesson_schedule_day",
                year=lesson.lesson_date.year,
                month=lesson.lesson_date.month,
                day=lesson.lesson_date.day,
            )

        if action == "restore":
            lesson.status = "planned"
            lesson.save()
            return redirect(
                "lesson_schedule_day",
                year=lesson.lesson_date.year,
                month=lesson.lesson_date.month,
                day=lesson.lesson_date.day,
            )

        old_date = lesson.lesson_date
        old_time = lesson.start_time

        form = LessonEditForm(request.POST, instance=lesson)
        if form.is_valid():
            lesson = form.save(commit=False)

            if lesson.lesson_date != old_date or lesson.start_time != old_time:
                if not lesson.original_date:
                    lesson.original_date = old_date
                if not lesson.original_start_time:
                    lesson.original_start_time = old_time

            lesson.save()
            return redirect(
                "lesson_schedule_day",
                year=lesson.lesson_date.year,
                month=lesson.lesson_date.month,
                day=lesson.lesson_date.day,
            )
    else:
        form = LessonEditForm(instance=lesson)

    return render(
        request,
        "lessons/edit_lesson.html",
        {
            "lesson": lesson,
            "form": form,
        },
    )