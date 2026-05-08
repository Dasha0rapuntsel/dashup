import json

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from courses.models import Course, Enrollment
from .forms import QuizCreateForm, QuestionForm, ChoiceFormSet
from .models import Quiz, Question, Choice, QuizAttempt, AttemptAnswer


@login_required
def quiz_list(request):
    if request.user.role == "teacher":
        quizzes = (
            Quiz.objects
            .filter(course__teacher=request.user)
            .select_related("course")
            .prefetch_related("questions")
            .order_by("-created_at")
        )
        return render(request, "quizzes/teacher_quiz_list.html", {"quizzes": quizzes})

    enrolled_ids = Enrollment.objects.filter(
        student=request.user, is_active=True, course__is_active=True
    ).values_list("course_id", flat=True)

    quizzes = (
        Quiz.objects
        .filter(course_id__in=enrolled_ids, is_active=True)
        .filter(Q(assigned_students__isnull=True) | Q(assigned_students=request.user))
        .distinct()
        .select_related("course")
        .prefetch_related("questions")
        .order_by("-created_at")
    )

    finished_ids = set(
        QuizAttempt.objects
        .filter(student=request.user, is_finished=True)
        .values_list("quiz_id", flat=True)
    )

    quiz_data = []
    for q in quizzes:
        attempt = (
            QuizAttempt.objects
            .filter(quiz=q, student=request.user, is_finished=True)
            .order_by("-finished_at")
            .first()
        )
        quiz_data.append({
            "quiz": q,
            "is_finished": q.id in finished_ids,
            "attempt": attempt,
        })

    return render(request, "quizzes/student_quiz_list.html", {"quiz_data": quiz_data})


@login_required
def create_quiz(request):
    if request.user.role != "teacher":
        return HttpResponseForbidden("Только преподаватель может создавать тесты")

    if request.method == "POST":
        form = QuizCreateForm(request.POST, teacher=request.user)
        if form.is_valid():
            quiz = form.save(commit=False)
            if quiz.course.teacher != request.user:
                return HttpResponseForbidden("Нельзя создавать тесты для чужого направления")
            quiz.save()
            form.save_m2m()
            return redirect("add_question", quiz_id=quiz.id)
    else:
        form = QuizCreateForm(teacher=request.user)

    return render(request, "quizzes/create_quiz.html", {"form": form})


@login_required
def import_quiz_json(request):
    """Импорт теста из JSON-файла."""
    if request.user.role != "teacher":
        return HttpResponseForbidden("Только преподаватель может импортировать тесты")

    teacher_courses = Course.objects.filter(teacher=request.user, is_active=True).order_by("title")
    error = None
    success = None

    if request.method == "POST":
        course_id = request.POST.get("course")
        json_file = request.FILES.get("json_file")
        json_text = request.POST.get("json_text", "").strip()

        if not course_id:
            error = "Выберите направление."
        else:
            course = get_object_or_404(Course, id=course_id, teacher=request.user)

            raw = None
            if json_file:
                try:
                    raw = json.loads(json_file.read().decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    error = "Не удалось прочитать JSON-файл. Проверьте формат."
            elif json_text:
                try:
                    raw = json.loads(json_text)
                except json.JSONDecodeError:
                    error = "Некорректный JSON. Проверьте синтаксис."
            else:
                error = "Загрузите файл или вставьте JSON в текстовое поле."

            if raw and not error:
                try:
                    quiz_title = raw.get("title", "Импортированный тест")
                    quiz_desc = raw.get("description", "")
                    time_limit = raw.get("time_limit_minutes")
                    questions_data = raw.get("questions", [])

                    if not questions_data:
                        error = "В JSON нет вопросов (ключ 'questions')."
                    else:
                        quiz = Quiz.objects.create(
                            course=course,
                            title=quiz_title,
                            description=quiz_desc,
                            time_limit_minutes=time_limit,
                            is_active=True,
                        )

                        for i, qdata in enumerate(questions_data):
                            q_type = qdata.get("type", "single")
                            if q_type not in ("single", "multiple", "text"):
                                q_type = "single"

                            question = Question.objects.create(
                                quiz=quiz,
                                text=qdata.get("text", f"Вопрос {i+1}"),
                                question_type=q_type,
                                points=qdata.get("points", 1),
                                order=i + 1,
                            )

                            for ch_data in qdata.get("choices", []):
                                Choice.objects.create(
                                    question=question,
                                    text=ch_data.get("text", ""),
                                    is_correct=ch_data.get("correct", False),
                                )

                        success = f'Тест "{quiz.title}" создан — {len(questions_data)} вопросов.'

                except Exception as e:
                    error = f"Ошибка при создании теста: {str(e)}"

    return render(request, "quizzes/import_quiz.html", {
        "courses": teacher_courses,
        "error": error,
        "success": success,
    })


@login_required
def add_question(request, quiz_id):
    if request.user.role != "teacher":
        return HttpResponseForbidden("Только преподаватель может добавлять вопросы")

    quiz = get_object_or_404(Quiz, id=quiz_id, course__teacher=request.user)
    questions = quiz.questions.prefetch_related("choices").all()

    if request.method == "POST":
        q_form = QuestionForm(request.POST)
        if q_form.is_valid():
            question = q_form.save(commit=False)
            question.quiz = quiz
            question.order = questions.count() + 1
            question.save()

            if question.question_type in ("single", "multiple"):
                formset = ChoiceFormSet(request.POST, instance=question)
                if formset.is_valid():
                    formset.save()

            return redirect("add_question", quiz_id=quiz.id)
    else:
        q_form = QuestionForm()

    formset = ChoiceFormSet()

    return render(request, "quizzes/add_question.html", {
        "quiz": quiz,
        "questions": questions,
        "q_form": q_form,
        "formset": formset,
    })


@login_required
def quiz_detail(request, quiz_id):
    quiz = get_object_or_404(
        Quiz.objects.select_related("course", "course__teacher")
        .prefetch_related("questions__choices"),
        id=quiz_id,
    )

    if request.user.role == "teacher":
        if quiz.course.teacher != request.user:
            return HttpResponseForbidden("Вы не можете просматривать этот тест")

        attempts = (
            QuizAttempt.objects
            .filter(quiz=quiz, is_finished=True)
            .select_related("student")
            .order_by("-finished_at")
        )

        return render(request, "quizzes/teacher_quiz_detail.html", {
            "quiz": quiz,
            "attempts": attempts,
        })

    enrolled = Enrollment.objects.filter(
        student=request.user, course=quiz.course, is_active=True
    ).exists()
    if not enrolled:
        return HttpResponseForbidden("У вас нет доступа к этому тесту")

    attempt = (
        QuizAttempt.objects
        .filter(quiz=quiz, student=request.user, is_finished=True)
        .order_by("-finished_at")
        .first()
    )

    return render(request, "quizzes/student_quiz_detail.html", {
        "quiz": quiz,
        "attempt": attempt,
    })


@login_required
def take_quiz(request, quiz_id):
    if request.user.role != "student":
        return HttpResponseForbidden("Только ученик может проходить тесты")

    quiz = get_object_or_404(
        Quiz.objects.prefetch_related("questions__choices"),
        id=quiz_id,
        is_active=True,
    )

    enrolled = Enrollment.objects.filter(
        student=request.user, course=quiz.course, is_active=True
    ).exists()
    if not enrolled:
        return HttpResponseForbidden("Вы не записаны на это направление")

    questions = quiz.questions.all()

    if request.method == "POST":
        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            student=request.user,
            max_score=quiz.max_score,
        )

        total_score = 0

        for question in questions:
            answer_obj = AttemptAnswer.objects.create(
                attempt=attempt,
                question=question,
            )

            if question.question_type == "text":
                text_answer = request.POST.get(f"question_{question.id}_text", "").strip()
                answer_obj.text_answer = text_answer
                answer_obj.save()

            elif question.question_type == "single":
                selected_id = request.POST.get(f"question_{question.id}")
                if selected_id:
                    try:
                        choice = Choice.objects.get(id=int(selected_id), question=question)
                        answer_obj.selected_choices.add(choice)
                        if choice.is_correct:
                            answer_obj.is_correct = True
                            answer_obj.points_earned = question.points
                            total_score += question.points
                    except (Choice.DoesNotExist, ValueError):
                        pass
                answer_obj.save()

            elif question.question_type == "multiple":
                selected_ids = request.POST.getlist(f"question_{question.id}")
                correct_ids = set(
                    question.choices.filter(is_correct=True).values_list("id", flat=True)
                )
                chosen_ids = set()
                for sid in selected_ids:
                    try:
                        choice = Choice.objects.get(id=int(sid), question=question)
                        answer_obj.selected_choices.add(choice)
                        chosen_ids.add(choice.id)
                    except (Choice.DoesNotExist, ValueError):
                        pass

                if chosen_ids == correct_ids:
                    answer_obj.is_correct = True
                    answer_obj.points_earned = question.points
                    total_score += question.points

                answer_obj.save()

        attempt.score = total_score
        attempt.is_finished = True
        attempt.finished_at = timezone.now()
        attempt.save()

        return redirect("quiz_result", attempt_id=attempt.id)

    return render(request, "quizzes/take_quiz.html", {
        "quiz": quiz,
        "questions": questions,
    })


@login_required
def quiz_result(request, attempt_id):
    attempt = get_object_or_404(
        QuizAttempt.objects.select_related("quiz", "quiz__course", "student")
        .prefetch_related("answers__question", "answers__selected_choices"),
        id=attempt_id,
    )

    if request.user.role == "teacher":
        if attempt.quiz.course.teacher != request.user:
            return HttpResponseForbidden("Вы не можете просматривать этот результат")
    else:
        if attempt.student != request.user:
            return HttpResponseForbidden("Вы не можете просматривать этот результат")

    answers = attempt.answers.select_related("question").prefetch_related(
        "selected_choices", "question__choices"
    ).order_by("question__order")

    return render(request, "quizzes/quiz_result.html", {
        "attempt": attempt,
        "answers": answers,
    })
