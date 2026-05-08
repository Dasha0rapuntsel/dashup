from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "amount", "due_date", "status", "method", "paid_at")
    list_filter = ("status", "method", "course")
    search_fields = ("student__username", "course__title", "period_label")