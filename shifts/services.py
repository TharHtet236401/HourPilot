from collections import defaultdict
from datetime import timedelta
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
            "name": "",
            "count": 0,
            "minutes": 0,
            "pay": Decimal("0.00"),
        }
    )

    for shift in shifts:
        row = grouped[shift.workplace_id]
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
    }


def dashboard_stats(user):
    shifts = list(
        user.shifts.select_related("workplace").order_by("-date", "-start_time")
    )
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
    }
