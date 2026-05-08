from django.db.models.signals import post_save
from django.dispatch import receiver

from courses.models import Enrollment
from .models import Homework, HomeworkStatus


@receiver(post_save, sender=Homework)
def create_homework_statuses(sender, instance, created, **kwargs):
    if not created:
        return

    enrollments = Enrollment.objects.filter(
        course=instance.course,
        is_active=True,
        student__role="student",
    ).select_related("student")

    for enrollment in enrollments:
        HomeworkStatus.objects.get_or_create(
            homework=instance,
            student=enrollment.student,
        )


@receiver(post_save, sender=Enrollment)
def create_statuses_for_new_enrollment(sender, instance, created, **kwargs):
    if not created or not instance.is_active:
        return

    homeworks = Homework.objects.filter(course=instance.course, is_active=True)

    for homework in homeworks:
        HomeworkStatus.objects.get_or_create(
            homework=homework,
            student=instance.student,
        )