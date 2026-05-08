from django.urls import path
from . import views

urlpatterns = [
    path("", views.grade_list, name="grade_list"),
    path("create/", views.create_grade, name="create_grade"),
    path("<int:grade_id>/", views.grade_detail, name="grade_detail"),
]
