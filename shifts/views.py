from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from workspaces.models import Workplace

from .forms import ShiftForm
from .models import Shift


def _user_shifts(user):
    return user.shifts.select_related("workplace").order_by("-date", "-start_time")


def _shift_form_success(request, message):
    return render(
        request,
        "shifts/partials/list_refresh.html",
        {
            "shifts": _user_shifts(request.user),
            "message": message,
        },
    )


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
                return _shift_form_success(request, "Shift added.")
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


@login_required
def shift_update(request, pk):
    shift = get_object_or_404(
        Shift.objects.select_related("workplace"),
        pk=pk,
        user=request.user,
    )

    try:
        if request.method == "POST":
            form = ShiftForm(request.POST, user=request.user, instance=shift)
            if form.is_valid():
                shift = form.save(commit=False)
                shift.hourly_rate_at_time = shift.workplace.hourly_rate
                shift.save()
                return _shift_form_success(request, "Shift updated.")
        else:
            form = ShiftForm(user=request.user, instance=shift)

        return render(
            request,
            "shifts/partials/modal_form.html",
            {"form": form, "shift": shift},
        )
    except Exception:
        form = ShiftForm(
            request.POST or None,
            user=request.user,
            instance=shift,
        )
        return render(
            request,
            "shifts/partials/modal_form.html",
            {
                "form": form,
                "shift": shift,
                "error": "Could not update this shift.",
            },
        )


@login_required
def shift_delete(request, pk):
    shift = get_object_or_404(
        Shift.objects.select_related("workplace"),
        pk=pk,
        user=request.user,
    )

    try:
        if request.method == "POST":
            shift.delete()
            return _shift_form_success(request, "Shift deleted.")

        return render(
            request,
            "shifts/partials/modal_delete.html",
            {"shift": shift},
        )
    except Exception:
        return render(
            request,
            "shifts/partials/modal_delete.html",
            {
                "shift": shift,
                "error": "Could not delete this shift.",
            },
        )
