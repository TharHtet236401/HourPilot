from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from workspaces.models import Workplace

from .forms import ShiftForm


def _user_shifts(user):
    return user.shifts.select_related("workplace").order_by("-date", "-start_time")


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
        shifts = _user_shifts(request.user)
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


@login_required
def shift_create(request):
    try:
        workplaces = Workplace.objects.filter(
            user=request.user,
            is_active=True,
        )

        if not workplaces.exists() and request.method == "GET":
            return render(
                request,
                "shifts/partials/modal_no_workplace.html",
            )

        if request.method == "POST":
            form = ShiftForm(request.POST, user=request.user)
            if form.is_valid():
                shift = form.save(commit=False)
                shift.user = request.user
                shift.hourly_rate_at_time = shift.workplace.hourly_rate
                shift.save()
                return render(
                    request,
                    "shifts/partials/create_success.html",
                    {"shifts": _user_shifts(request.user)},
                )
        else:
            form = ShiftForm(user=request.user)

        return render(
            request,
            "shifts/partials/modal_form.html",
            {"form": form},
        )
    except Exception:
        form = ShiftForm(request.POST or None, user=request.user)
        return render(
            request,
            "shifts/partials/modal_form.html",
            {
                "form": form,
                "error": "Could not save this shift.",
            },
        )
