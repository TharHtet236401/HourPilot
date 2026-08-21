from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def home(request):
    try:
        return render(request, "shifts/home.html")
    except Exception:
        messages.error(request, "Could not load the home page.")
        return render(request, "shifts/home.html")


@login_required
def shift_list(request):
    try:
        shifts = (
            request.user.shifts.select_related("workplace")
            .order_by("-date", "-start_time")
        )

        return render(
            request,
            "shifts/list.html",
            {"shifts": shifts},
        )
    except Exception:
        messages.error(request, "Could not load your shifts.")
        return render(
            request,
            "shifts/list.html",
            {"shifts": []},
        )
