from django.urls import path
from . import views

urlpatterns = [
    path("", views.payment_list, name="payment_list"),
    path("create/", views.create_payment, name="create_payment"),
    path("<int:payment_id>/", views.payment_detail, name="payment_detail"),
    path("<int:payment_id>/mark-paid/", views.mark_payment_paid, name="mark_payment_paid"),
]