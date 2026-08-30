from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from config.pagination import (
    SHIFT_PAGE_SIZE,
    list_page_url,
    page_number_from_request,
    paginate,
)
from workspaces.models import Workplace

from .export import export_filename, filtered_shifts, shifts_csv
from .forms import ShiftExportForm, ShiftForm
from .models import Shift
from .services import (
    calendar_month,
    dashboard_stats,
    empty_calendar_month,
    empty_dashboard_stats,
    empty_statistics_stats,
    statistics_stats,
    summarize_shifts,
)


def _user_shifts(user):
    return user.shifts.select_related("workplace").order_by("-date", "-start_time")


def _shift_list_context(request, page=None):
    page_obj = paginate(
        _user_shifts(request.user),
        page if page is not None else page_number_from_request(request),
        SHIFT_PAGE_SIZE,
    )
    return {
        "shifts": page_obj.object_list,
        "page_obj": page_obj,
        "page_url_name": "shift_list",
        "list_target": "#shift-list",
    }


def _shift_form_success(request, message, page=None):
    context = _shift_list_context(request, page=page)
    context["message"] = message
    response = render(request, "shifts/partials/list_refresh.html", context)
    response["HX-Push-Url"] = list_page_url("shift_list", context["page_obj"].number)
    return response


def _dashboard_workplace(request):
    workplace_id = request.GET.get("workplace")
    if not workplace_id:
        return None

    try:
        return Workplace.objects.get(pk=workplace_id, user=request.user)
    except (Workplace.DoesNotExist, ValueError, TypeError):
        return None


@login_required
def home(request):
    try:
        workplace = _dashboard_workplace(request)
        context = {"stats": dashboard_stats(request.user, workplace=workplace)}
        template = (
            "shifts/partials/dashboard.html"
            if request.headers.get("HX-Request")
            else "shifts/home.html"
        )
        return render(request, template, context)
    except Exception:
        messages.error(request, "Could not load the dashboard.")
        template = (
            "shifts/partials/dashboard.html"
            if request.headers.get("HX-Request")
            else "shifts/home.html"
        )
        return render(
            request,
            template,
            {"stats": empty_dashboard_stats()},
        )


def _stats_period(request):
    period = request.GET.get("period", "month")
    if period not in {"week", "month", "year", "all"}:
        return "month"
    return period


@login_required
def shift_statistics(request):
    try:
        workplace = _dashboard_workplace(request)
        context = {
            "stats": statistics_stats(
                request.user,
                period=_stats_period(request),
                workplace=workplace,
            )
        }
        template = (
            "shifts/partials/statistics.html"
            if request.headers.get("HX-Request")
            else "shifts/statistics.html"
        )
        return render(request, template, context)
    except Exception:
        messages.error(request, "Could not load your statistics.")
        template = (
            "shifts/partials/statistics.html"
            if request.headers.get("HX-Request")
            else "shifts/statistics.html"
        )
        return render(request, template, {"stats": empty_statistics_stats()})


def _calendar_context(request):
    today = timezone.localdate()
    try:
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))
        date(year, month, 1)
    except (TypeError, ValueError):
        year, month = today.year, today.month

    return calendar_month(request.user, year, month)


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
def calendar_day(request):
    try:
        selected = date.fromisoformat(request.GET.get("day", ""))
        shifts = list(
            request.user.shifts.filter(date=selected)
            .select_related("workplace")
            .order_by("start_time")
        )
        return render(
            request,
            "shifts/partials/modal_day.html",
            {
                "selected": selected,
                "selected_shifts": shifts,
                "day_summary": summarize_shifts(shifts),
            },
        )
    except Exception:
        return render(
            request,
            "shifts/partials/modal_day.html",
            {
                "selected": None,
                "selected_shifts": [],
                "day_summary": summarize_shifts([]),
                "error": "Could not load this day.",
            },
        )


@login_required
def shift_list(request):
    try:
        context = _shift_list_context(request)
        template = (
            "shifts/partials/list.html"
            if request.headers.get("HX-Request")
            else "shifts/list.html"
        )
        return render(request, template, context)
    except Exception:
        messages.error(request, "Could not load your shifts.")
        template = (
            "shifts/partials/list.html"
            if request.headers.get("HX-Request")
            else "shifts/list.html"
        )
        return render(
            request,
            template,
            {
                "shifts": [],
                "page_obj": None,
                "page_url_name": "shift_list",
                "list_target": "#shift-list",
            },
        )


def _export_form_context(request, form=None):
    today = timezone.localdate()
    first_shift = (
        request.user.shifts.order_by("date").values_list("date", flat=True).first()
    )
    last_shift = (
        request.user.shifts.order_by("-date").values_list("date", flat=True).first()
    )
    all_from = first_shift or today
    all_to = last_shift or today
    if form is None:
        form = ShiftExportForm(
            user=request.user,
            initial={
                "date_from": today.replace(day=1),
                "date_to": today,
            },
        )
    return {
        "form": form,
        "today": today.isoformat(),
        "week_start": (today - timedelta(days=today.weekday())).isoformat(),
        "month_start": today.replace(day=1).isoformat(),
        "year_start": today.replace(month=1, day=1).isoformat(),
        "all_from": all_from.isoformat(),
        "all_to": all_to.isoformat(),
    }


@login_required
def shift_export_form(request):
    try:
        return render(
            request,
            "shifts/partials/modal_export.html",
            _export_form_context(request),
        )
    except Exception:
        return render(
            request,
            "shifts/partials/modal_export.html",
            {
                **_export_form_context(request),
                "error": "Could not open the export form.",
            },
        )


@login_required
def shift_export_csv(request):
    try:
        form = ShiftExportForm(request.GET or None, user=request.user)
        if not form.is_valid():
            messages.error(request, "Could not export those shifts. Check the dates.")
            return redirect("shift_list")

        workplace = form.cleaned_data.get("workplace")
        date_from = form.cleaned_data.get("date_from")
        date_to = form.cleaned_data.get("date_to")
        shifts = filtered_shifts(
            request.user,
            workplace=workplace,
            date_from=date_from,
            date_to=date_to,
        )
        response = HttpResponse(
            shifts_csv(shifts),
            content_type="text/csv; charset=utf-8",
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{export_filename(workplace, date_from, date_to)}"'
        )
        return response
    except Exception:
        messages.error(request, "Could not export your shifts.")
        return redirect("shift_list")


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
                return _shift_form_success(request, "Shift added.", page=1)
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
