from django.urls import path
from . import views

urlpatterns = [
    path("telegram/link/", views.telegram_link, name="telegram_link"),
]
