from datetime import date
from urllib.parse import parse_qs, urlparse

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.prefs import prefs_for, week_start_date
from config.pagination import (
    SHIFT_PAGE_SIZE,
    list_page_url,
    page_number_from_request,
    paginate,
)
from workspaces.models import Workplace

from .export import export_filename, filtered_shifts, shifts_csv
from .forms import ShiftExportForm, ShiftFilterForm, ShiftForm
from .models import Shift
from .services import (
    apply_shift_filters,
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


def _last_user_shift(user):
    return _user_shifts(user).first()


def _current_url(request):
    return request.headers.get("HX-Current-URL") or request.build_absolute_uri()


def _request_query(request):
    if request.GET:
        return request.GET
    current = request.headers.get("HX-Current-URL")
    if current:
        return QueryDict(urlparse(current).query)
    return request.GET


def _filter_presets(request):
    today = timezone.localdate()
    return {
        "today": today.isoformat(),
        "week_start": week_start_date(
            today, prefs_for(request.user).week_start
        ).isoformat(),
        "month_start": today.replace(day=1).isoformat(),
        "year_start": today.replace(month=1, day=1).isoformat(),
    }


def _request_on_calendar(request):
    path = urlparse(_current_url(request)).path
    return "/calendar/" in path or path.rstrip("/").endswith("calendar")


def _request_on_shifts(request):
    path = urlparse(_current_url(request)).path
    return "/shifts/" in path and "/export" not in path


def _shift_defaults(request):
    initial = {"date": timezone.localdate()}
    selected_day = request.GET.get("day")
    if selected_day:
        try:
            initial["date"] = date.fromisoformat(selected_day)
        except ValueError:
            pass

    source = None
    copy_id = request.GET.get("copy")
    if copy_id:
        source = (
            request.user.shifts.select_related("workplace").filter(pk=copy_id).first()
        )
    elif request.GET.get("repeat"):
        source = _last_user_shift(request.user)

    if source:
        initial["start_time"] = source.start_time
        initial["end_time"] = source.end_time
        initial["break_minutes"] = source.break_minutes
        if source.workplace.is_active:
            initial["workplace"] = source.workplace

    return initial, source


def _create_form_context(request, form, copied_from=None, extra=None):
    context = {
        "form": form,
        "last_shift": _last_user_shift(request.user),
        "copied_from": copied_from,
        "selected_day": request.GET.get("day", ""),
    }
    if extra:
        context.update(extra)
    return context


def _shift_list_context(request, page=None):
    query = _request_query(request)
    form = ShiftFilterForm(query or None, user=request.user)
    queryset = apply_shift_filters(_user_shifts(request.user), form)
    page_obj = paginate(
        queryset,
        page if page is not None else page_number_from_request(request),
        SHIFT_PAGE_SIZE,
    )
    return {
        "shifts": page_obj.object_list,
        "page_obj": page_obj,
        "page_url_name": "shift_list",
        "list_target": "#shift-list",
        "page_query": query,
        "last_shift": _last_user_shift(request.user),
        "filter_form": form,
        "filters_active": form.has_filters(),
        **_filter_presets(request),
    }


def _empty_shift_list_context(request):
    form = ShiftFilterForm(user=request.user)
    return {
        "shifts": [],
        "page_obj": None,
        "page_url_name": "shift_list",
        "list_target": "#shift-list",
        "last_shift": None,
        "filter_form": form,
        "filters_active": False,
        **_filter_presets(request),
    }


def _shift_form_success(request, message, page=None):
    context = _shift_list_context(request, page=page)
    context["message"] = message
    response = render(request, "shifts/partials/list_refresh.html", context)
    response["HX-Push-Url"] = list_page_url(
        "shift_list",
        context["page_obj"].number,
        _request_query(request),
    )
    return response


def _calendar_form_success(request, message):
    context = _calendar_context(request)
    context["message"] = message
    return render(request, "shifts/partials/calendar_refresh.html", context)


def _toast_form_success(request, message):
    return render(
        request,
        "shifts/partials/toast_refresh.html",
        {"message": message},
    )


def _after_shift_save(request, message, page=None):
    if _request_on_calendar(request):
        return _calendar_form_success(request, message)
    if _request_on_shifts(request):
        return _shift_form_success(request, message, page=page)
    return _toast_form_success(request, message)


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
    year = request.GET.get("year")
    month = request.GET.get("month")
    if year is None or month is None:
        query = parse_qs(urlparse(_current_url(request)).query)
        year = year or (query.get("year") or [None])[0]
        month = month or (query.get("month") or [None])[0]
    try:
        year = int(year or today.year)
        month = int(month or today.month)
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
        return render(
            request,
            template,
            empty_calendar_month(week_start=prefs_for(request.user).week_start),
        )


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
                "last_shift": _last_user_shift(request.user),
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
            _empty_shift_list_context(request),
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
        "week_start": week_start_date(
            today, prefs_for(request.user).week_start
        ).isoformat(),
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
            shifts_csv(shifts, user=request.user),
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
def shift_detail(request, pk):
    try:
        shift = get_object_or_404(
            Shift.objects.select_related("workplace"),
            pk=pk,
            user=request.user,
        )
        return render(
            request,
            "shifts/partials/modal_detail.html",
            {"shift": shift},
        )
    except Exception:
        return render(
            request,
            "shifts/partials/modal_detail.html",
            {
                "shift": None,
                "error": "Could not load this shift.",
            },
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
                return _after_shift_save(request, "Shift added.", page=1)
            return render(
                request,
                "shifts/partials/modal_form.html",
                _create_form_context(request, form),
            )

        initial, copied_from = _shift_defaults(request)
        form = ShiftForm(user=request.user, initial=initial)
        return render(
            request,
            "shifts/partials/modal_form.html",
            _create_form_context(request, form, copied_from=copied_from),
        )
    except Exception:
        form = ShiftForm(request.POST or None, user=request.user)
        return render(
            request,
            "shifts/partials/modal_form.html",
            _create_form_context(
                request,
                form,
                extra={"error": "Could not save this shift."},
            ),
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
                return _after_shift_save(request, "Shift updated.")
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
            return _after_shift_save(request, "Shift deleted.")

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
