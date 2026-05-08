from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PaymentCreateForm, PaymentMarkPaidForm
from .models import Payment


@login_required
def payment_list(request):
    if request.user.role == "teacher":
        payments = (
            Payment.objects
            .filter(course__teacher=request.user)
            .select_related("student", "course")
            .order_by("-due_date")
        )
        return render(
            request,
            "payments/teacher_payment_list.html",
            {"payments": payments},
        )

    payments = (
        Payment.objects
        .filter(student=request.user)
        .select_related("course")
        .order_by("-due_date")
    )
    return render(
        request,
        "payments/student_payment_list.html",
        {"payments": payments},
    )


@login_required
def create_payment(request):
    if request.user.role != "teacher":
        return HttpResponseForbidden("Только преподаватель может создавать оплаты")

    if request.method == "POST":
        form = PaymentCreateForm(request.POST, teacher=request.user)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.status = "pending"
            payment.save()
            return redirect("payment_detail", payment_id=payment.id)
    else:
        form = PaymentCreateForm(teacher=request.user)

    return render(
        request,
        "payments/create_payment.html",
        {"form": form},
    )


@login_required
def payment_detail(request, payment_id):
    payment = get_object_or_404(
        Payment.objects.select_related("student", "course", "course__teacher"),
        id=payment_id,
    )

    if request.user.role == "teacher":
        if payment.course.teacher != request.user:
            return HttpResponseForbidden("Вы не можете просматривать эту оплату")

        form = PaymentMarkPaidForm(
            initial={
                "method": payment.method,
                "paid_at": payment.paid_at,
                "note": payment.note,
            }
        )

        return render(
            request,
            "payments/teacher_payment_detail.html",
            {
                "payment": payment,
                "form": form,
            },
        )

    if payment.student != request.user:
        return HttpResponseForbidden("Вы не можете просматривать эту оплату")

    return render(
        request,
        "payments/student_payment_detail.html",
        {"payment": payment},
    )


@login_required
def mark_payment_paid(request, payment_id):
    if request.user.role != "teacher":
        return HttpResponseForbidden("Только преподаватель может отмечать оплату")

    payment = get_object_or_404(
        Payment.objects.select_related("course"),
        id=payment_id,
    )

    if payment.course.teacher != request.user:
        return HttpResponseForbidden("Вы не можете редактировать эту оплату")

    if request.method == "POST":
        form = PaymentMarkPaidForm(request.POST, instance=payment)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.status = "paid"
            payment.save()
            return redirect("payment_detail", payment_id=payment.id)

    return redirect("payment_detail", payment_id=payment.id)