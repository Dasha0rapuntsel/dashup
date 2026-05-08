from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import TelegramProfile


@login_required
def telegram_link(request):
    profile, created = TelegramProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        if not profile.is_linked:
            code = profile.generate_link_code()

    return render(request, "notifications/telegram_link.html", {
        "profile": profile,
    })
