from django.urls import path
from . import views

urlpatterns = [
    path("", views.quiz_list, name="quiz_list"),
    path("create/", views.create_quiz, name="create_quiz"),
    path("import/", views.import_quiz_json, name="import_quiz_json"),
    path("<int:quiz_id>/", views.quiz_detail, name="quiz_detail"),
    path("<int:quiz_id>/add-question/", views.add_question, name="add_question"),
    path("<int:quiz_id>/take/", views.take_quiz, name="take_quiz"),
    path("result/<int:attempt_id>/", views.quiz_result, name="quiz_result"),
]
