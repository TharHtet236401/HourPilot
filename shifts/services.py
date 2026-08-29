import calendar
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django.utils import timezone


def format_minutes(minutes):
    minutes = max(int(minutes), 0)
    hours, remaining = divmod(minutes, 60)

    if hours and remaining:
        return f"{hours}h {remaining}m"
    if hours:
        return f"{hours}h"
    return f"{remaining}m"


def _empty_summary():
    return {
        "count": 0,
        "minutes": 0,
        "hours_display": format_minutes(0),
        "pay": Decimal("0.00"),
    }


def summarize_shifts(shifts):
    summary = _empty_summary()

    for shift in shifts:
        minutes = max(shift.duration_minutes(), 0)
        summary["count"] += 1
        summary["minutes"] += minutes
        summary["pay"] += shift.estimated_earnings()

    summary["hours_display"] = format_minutes(summary["minutes"])
    summary["pay"] = summary["pay"].quantize(Decimal("0.01"))
    return summary


def workplace_breakdown(shifts):
    grouped = defaultdict(
        lambda: {
            "id": None,
            "name": "",
            "count": 0,
            "minutes": 0,
            "pay": Decimal("0.00"),
        }
    )

    for shift in shifts:
        row = grouped[shift.workplace_id]
        row["id"] = shift.workplace_id
        row["name"] = shift.workplace.name
        row["count"] += 1
        row["minutes"] += max(shift.duration_minutes(), 0)
        row["pay"] += shift.estimated_earnings()

    results = []
    for row in grouped.values():
        row["hours_display"] = format_minutes(row["minutes"])
        row["pay"] = row["pay"].quantize(Decimal("0.01"))
        results.append(row)

    results.sort(key=lambda item: item["pay"], reverse=True)
    return results


def empty_dashboard_stats():
    empty = _empty_summary()
    return {
        "has_shifts": False,
        "all_time": empty,
        "week": empty,
        "month": empty,
        "average_rate": Decimal("0.00"),
        "workplace_count": 0,
        "by_workplace": [],
        "recent_shifts": [],
        "workplaces": [],
        "selected_workplace": None,
    }


def dashboard_stats(user, workplace=None):
    shifts_query = user.shifts.select_related("workplace").order_by(
        "-date", "-start_time"
    )
    if workplace:
        shifts_query = shifts_query.filter(workplace=workplace)

    shifts = list(shifts_query)
    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    week_shifts = [shift for shift in shifts if shift.date >= week_start]
    month_shifts = [shift for shift in shifts if shift.date >= month_start]

    all_time = summarize_shifts(shifts)
    hours = Decimal(all_time["minutes"]) / Decimal("60")
    average_rate = Decimal("0.00")
    if hours > 0:
        average_rate = (all_time["pay"] / hours).quantize(Decimal("0.01"))

    return {
        "has_shifts": bool(shifts),
        "all_time": all_time,
        "week": summarize_shifts(week_shifts),
        "month": summarize_shifts(month_shifts),
        "average_rate": average_rate,
        "workplace_count": user.workplaces.count(),
        "by_workplace": workplace_breakdown(shifts),
        "recent_shifts": shifts[:5],
        "workplaces": list(user.workplaces.order_by("name")),
        "selected_workplace": workplace,
    }


def _month_bounds(year, month):
    first = date(year, month, 1)
    if month == 12:
        last = date(year + 1, 1, 1) - timedelta(days=1)
        next_year, next_month = year + 1, 1
    else:
        last = date(year, month + 1, 1) - timedelta(days=1)
        next_year, next_month = year, month + 1

    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1

    return first, last, prev_year, prev_month, next_year, next_month


def empty_calendar_month(year=None, month=None):
    today = timezone.localdate()
    year = year or today.year
    month = month or today.month
    first, last, prev_year, prev_month, next_year, next_month = _month_bounds(
        year, month
    )
    return {
        "year": year,
        "month": month,
        "title": first.strftime("%B %Y"),
        "weeks": [],
        "selected": None,
        "selected_shifts": [],
        "month_summary": _empty_summary(),
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
        "weekday_labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    }


def calendar_month(user, year, month, selected=None):
    today = timezone.localdate()
    first, last, prev_year, prev_month, next_year, next_month = _month_bounds(
        year, month
    )
    shifts = list(
        user.shifts.filter(date__gte=first, date__lte=last)
        .select_related("workplace")
        .order_by("start_time")
    )
    by_day = defaultdict(list)
    for shift in shifts:
        by_day[shift.date].append(shift)

    if selected and selected.month != month:
        selected = None
    if selected is None and today.year == year and today.month == month:
        selected = today

    weeks = []
    for week in calendar.Calendar(firstweekday=calendar.MONDAY).monthdatescalendar(
        year, month
    ):
        days = []
        for day in week:
            day_shifts = by_day.get(day, [])
            day_summary = summarize_shifts(day_shifts)
            days.append(
                {
                    "date": day,
                    "in_month": day.month == month,
                    "is_today": day == today,
                    "is_selected": selected == day,
                    "shifts": day_shifts,
                    "hours_display": day_summary["hours_display"],
                    "pay": day_summary["pay"],
                    "has_shifts": bool(day_shifts),
                }
            )
        weeks.append(days)

    return {
        "year": year,
        "month": month,
        "title": first.strftime("%B %Y"),
        "weeks": weeks,
        "selected": selected,
        "selected_shifts": by_day.get(selected, []) if selected else [],
        "month_summary": summarize_shifts(shifts),
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
        "weekday_labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    }
