from django.contrib import admin
from django.urls import path, include
from users import views as user_views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("admin/", admin.site.urls),

    path("", user_views.home, name="home"),
    path("portal/", user_views.portal, name="portal"),

    path("login/", user_views.user_login, name="login"),
    path("register/", user_views.register, name="register"),
    path("logout/", user_views.user_logout, name="logout"),

    path("student/", user_views.student_dashboard, name="student_dashboard"),
    path("teacher/", user_views.teacher_dashboard, name="teacher_dashboard"),

    path("courses/", include("courses.urls")),
    path("lessons/", include("lessons.urls")),
    path("homework/", include("homework.urls")),
    path("payments/", include("payments.urls")),
    path("grades/", include("grades.urls")),
    path("quizzes/", include("quizzes.urls")),
    path("notifications/", include("notifications.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
