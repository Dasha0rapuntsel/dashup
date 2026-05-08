from django.urls import path
from . import views

urlpatterns = [
    path("", views.course_list, name="course_list"),
    path("my/", views.teacher_course_list, name="teacher_course_list"),
    path("create/", views.create_course, name="create_course"),
    path("<int:course_id>/", views.course_detail, name="course_detail"),
]