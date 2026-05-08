from django.urls import path
from . import views

urlpatterns = [
    path("schedule/", views.lesson_schedule, name="lesson_schedule"),
    path("schedule/<int:year>/<int:month>/", views.lesson_schedule_month, name="lesson_schedule_month"),
    path("schedule/day/<int:year>/<int:month>/<int:day>/", views.lesson_schedule_day, name="lesson_schedule_day"),
    path("schedule/day/<int:year>/<int:month>/<int:day>/add/", views.create_lesson_on_date, name="create_lesson_on_date"),
    path("lesson/<int:lesson_id>/edit/", views.edit_lesson, name="edit_lesson"),
]