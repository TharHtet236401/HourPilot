from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from workspaces.models import Workplace

from .forms import ShiftForm
from .models import Shift
from .services import (
    calendar_month,
    dashboard_stats,
    empty_calendar_month,
    empty_dashboard_stats,
)


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
        return render(
            request,
            "shifts/home.html",
            {"stats": dashboard_stats(request.user)},
        )
    except Exception:
        messages.error(request, "Could not load the dashboard.")
        return render(
            request,
            "shifts/home.html",
            {"stats": empty_dashboard_stats()},
        )


def _calendar_context(request):
    today = timezone.localdate()
    try:
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))
        date(year, month, 1)
    except (TypeError, ValueError):
        year, month = today.year, today.month

    selected = None
    selected_value = request.GET.get("day")
    if selected_value:
        try:
            selected = date.fromisoformat(selected_value)
        except ValueError:
            selected = None

    return calendar_month(request.user, year, month, selected)


@login_required
def shift_calendar(request):
    try:
        context = _calendar_context(request)
        template = (
            "shifts/partials/calendar.html"
            if request.headers.get("HX-Request")
            else "shifts/calendar.html"
        )
        return render(request, template, context)
    except Exception:
        messages.error(request, "Could not load the calendar.")
        template = (
            "shifts/partials/calendar.html"
            if request.headers.get("HX-Request")
            else "shifts/calendar.html"
        )
        return render(request, template, empty_calendar_month())


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
