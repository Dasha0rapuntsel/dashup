from django.urls import path
from . import views

urlpatterns = [
    path("", views.homework_list, name="homework_list"),
    path("create/", views.create_homework, name="create_homework"),
    path("<int:homework_id>/", views.homework_detail, name="homework_detail"),
    path("<int:homework_id>/submit/", views.submit_homework, name="submit_homework"),
    path("status/<int:status_id>/review/", views.review_submission, name="review_submission"),
]