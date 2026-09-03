import calendar
import math
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django.utils import timezone

from workspaces.colors import workplace_color_hex, workplace_color_key


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
            "color_key": "teal",
            "count": 0,
            "minutes": 0,
            "pay": Decimal("0.00"),
        }
    )

    for shift in shifts:
        row = grouped[shift.workplace_id]
        row["id"] = shift.workplace_id
        row["name"] = shift.workplace.name
        row["color_key"] = workplace_color_key(shift.workplace_id)
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


def _polar(cx, cy, radius, degrees):
    radians = math.radians(degrees)
    return cx + radius * math.cos(radians), cy + radius * math.sin(radians)


def _slice_path(start_deg, sweep, cx=50, cy=50, radius=40):
    end_deg = start_deg + sweep
    start_x, start_y = _polar(cx, cy, radius, start_deg)
    end_x, end_y = _polar(cx, cy, radius, end_deg)
    large_arc = 1 if sweep > 180 else 0
    return (
        f"M {cx:.2f} {cy:.2f} L {start_x:.2f} {start_y:.2f} "
        f"A {radius} {radius} 0 {large_arc} 1 {end_x:.2f} {end_y:.2f} Z"
    )


def workplace_pies(breakdown):
    pay_total = sum((row["pay"] for row in breakdown), Decimal("0.00"))
    minutes_total = sum(row["minutes"] for row in breakdown)
    return {
        "pay": _pie_slices(breakdown, "pay", pay_total, money=True),
        "hours": _pie_slices(breakdown, "minutes", minutes_total, money=False),
    }


def _pie_slices(breakdown, value_key, total, money):
    slices = []
    if total <= 0:
        return slices

    usable = [row for row in breakdown if row[value_key] > 0]
    cursor = -90.0
    remaining_angle = 360.0
    total_value = float(total)

    for index, row in enumerate(usable):
        value = float(row[value_key])
        if index == len(usable) - 1:
            sweep = remaining_angle
        else:
            sweep = value / total_value * 360.0
            remaining_angle -= sweep

        percent = 0
        if total_value > 0:
            percent = int(Decimal(value / total_value * 100).quantize(Decimal(1)))

        full = sweep >= 359.99
        slices.append(
            {
                "name": row["name"],
                "color_key": row["color_key"],
                "hex": workplace_color_hex(row["id"]),
                "percent": percent,
                "full": full,
                "path": None if full else _slice_path(cursor, max(sweep, 0.01)),
                "value_display": f"£{row['pay']}" if money else row["hours_display"],
            }
        )
        cursor += sweep

    return slices


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
    hours = Decimal(all_time["minutes"]) / Decimal(60)
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


STAT_PERIODS = (
    {"key": "week", "label": "This week"},
    {"key": "month", "label": "This month"},
    {"key": "year", "label": "This year"},
    {"key": "all", "label": "All time"},
)


def _average_rate(summary):
    hours = Decimal(summary["minutes"]) / Decimal(60)
    if hours <= 0:
        return Decimal("0.00")
    return (summary["pay"] / hours).quantize(Decimal("0.01"))


def _shift_month(year, month, delta):
    index = year * 12 + (month - 1) + delta
    next_year, next_month = divmod(index, 12)
    return next_year, next_month + 1


def _period_bounds(period, today):
    if period == "week":
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        previous_start = start - timedelta(days=7)
        previous_end = start - timedelta(days=1)
        return start, min(end, today), previous_start, previous_end
    if period == "month":
        start = today.replace(day=1)
        previous_year, previous_month = _shift_month(start.year, start.month, -1)
        previous_last = calendar.monthrange(previous_year, previous_month)[1]
        previous_start = date(previous_year, previous_month, 1)
        previous_end = date(
            previous_year, previous_month, min(today.day, previous_last)
        )
        return start, today, previous_start, previous_end
    if period == "year":
        start = today.replace(month=1, day=1)
        try:
            previous_end = today.replace(year=today.year - 1)
        except ValueError:
            previous_end = date(today.year - 1, today.month, 28)
        previous_start = date(today.year - 1, 1, 1)
        return start, today, previous_start, previous_end
    return None, today, None, None


def _pay_change(current, previous):
    if previous["pay"] <= 0:
        return None
    percent = ((current["pay"] - previous["pay"]) / previous["pay"] * 100).quantize(
        Decimal(1)
    )
    return {"percent": percent, "up": percent >= 0}


def _nice_axis_max(max_pay):
    max_pay = Decimal(max_pay or 0)
    if max_pay <= 0:
        return Decimal("10.00")

    value = float(max_pay)
    magnitude = 10 ** math.floor(math.log10(value))
    fraction = value / magnitude
    if fraction <= 1:
        nice = 1
    elif fraction <= 2:
        nice = 2
    elif fraction <= 2.5:
        nice = 2.5
    elif fraction <= 5:
        nice = 5
    else:
        nice = 10
    return Decimal(str(nice * magnitude)).quantize(Decimal("0.01"))


def _format_axis_pay(amount):
    amount = Decimal(amount).quantize(Decimal("0.01"))
    if amount == amount.to_integral_value():
        return f"£{int(amount)}"
    return f"£{amount}"


def _timeline_axis(axis_max):
    ticks = []
    for step in (4, 3, 2, 1, 0):
        amount = (axis_max * Decimal(step) / Decimal(4)).quantize(Decimal("0.01"))
        ticks.append(
            {
                "label": _format_axis_pay(amount),
                "percent": step * 25,
            }
        )
    return ticks


def _bar_percent(pay, axis_max):
    if axis_max <= 0 or pay <= 0:
        return 0
    return int((pay / axis_max * 100).quantize(Decimal(1)))


def _day_highlights(shifts):
    if not shifts:
        return {"busiest_day": None, "best_pay_day": None}

    by_day = defaultdict(list)
    for shift in shifts:
        by_day[shift.date].append(shift)

    summaries = []
    for day, day_shifts in by_day.items():
        summary = summarize_shifts(day_shifts)
        summary["date"] = day
        summaries.append(summary)

    busiest = max(summaries, key=lambda item: (item["minutes"], item["pay"]))
    best_pay = max(summaries, key=lambda item: (item["pay"], item["minutes"]))
    return {"busiest_day": busiest, "best_pay_day": best_pay}


def _timeline_points(shifts, period, today):
    by_day = defaultdict(list)
    for shift in shifts:
        by_day[shift.date].append(shift)

    points = []
    if period == "week":
        week_start = today - timedelta(days=today.weekday())
        for offset in range(7):
            day = week_start + timedelta(days=offset)
            summary = summarize_shifts(by_day.get(day, []))
            points.append(
                {
                    "label": day.strftime("%a"),
                    "title": day.strftime("%A %d %b"),
                    "is_current": day == today,
                    **summary,
                }
            )
    elif period == "month":
        last_day = calendar.monthrange(today.year, today.month)[1]
        for day_number in range(1, last_day + 1):
            day = date(today.year, today.month, day_number)
            summary = summarize_shifts(by_day.get(day, []))
            points.append(
                {
                    "label": str(day_number),
                    "title": day.strftime("%A %d %b"),
                    "is_current": day == today,
                    **summary,
                }
            )
    elif period == "year":
        by_month = defaultdict(list)
        for shift in shifts:
            by_month[shift.date.month].append(shift)
        for month in range(1, 13):
            month_start = date(today.year, month, 1)
            summary = summarize_shifts(by_month.get(month, []))
            points.append(
                {
                    "label": month_start.strftime("%b"),
                    "title": month_start.strftime("%B %Y"),
                    "is_current": month == today.month,
                    **summary,
                }
            )
    else:
        by_month = defaultdict(list)
        for shift in shifts:
            by_month[(shift.date.year, shift.date.month)].append(shift)
        for delta in range(-11, 1):
            year, month = _shift_month(today.year, today.month, delta)
            month_start = date(year, month, 1)
            summary = summarize_shifts(by_month.get((year, month), []))
            points.append(
                {
                    "label": month_start.strftime("%b"),
                    "title": month_start.strftime("%B %Y"),
                    "is_current": year == today.year and month == today.month,
                    **summary,
                }
            )

    max_pay = max((point["pay"] for point in points), default=Decimal("0.00"))
    axis_max = _nice_axis_max(max_pay)
    for point in points:
        point["percent"] = _bar_percent(point["pay"], axis_max)
    return points, _timeline_axis(axis_max)


def empty_statistics_stats():
    empty = _empty_summary()
    return {
        "has_shifts": False,
        "period": "month",
        "period_label": "This month",
        "period_range_label": "",
        "periods": STAT_PERIODS,
        "summary": empty,
        "previous": empty,
        "change": None,
        "average_rate": Decimal("0.00"),
        "average_shift": format_minutes(0),
        "by_workplace": [],
        "pie": {"pay": [], "hours": []},
        "timeline": [],
        "timeline_axis": [],
        "highlights": {"busiest_day": None, "best_pay_day": None},
        "workplaces": [],
        "selected_workplace": None,
    }


def statistics_stats(user, period="month", workplace=None):
    valid_periods = {item["key"] for item in STAT_PERIODS}
    if period not in valid_periods:
        period = "month"

    today = timezone.localdate()
    start, end, previous_start, previous_end = _period_bounds(period, today)
    period_label = next(item["label"] for item in STAT_PERIODS if item["key"] == period)

    shifts_query = user.shifts.select_related("workplace")
    if workplace:
        shifts_query = shifts_query.filter(workplace=workplace)
    shifts = list(shifts_query)

    period_shifts = [
        shift
        for shift in shifts
        if (start is None or shift.date >= start) and shift.date <= end
    ]
    previous_shifts = []
    if previous_start and previous_end:
        previous_shifts = [
            shift for shift in shifts if previous_start <= shift.date <= previous_end
        ]

    summary = summarize_shifts(period_shifts)
    previous = summarize_shifts(previous_shifts)
    breakdown = workplace_breakdown(period_shifts)
    for row in breakdown:
        if summary["pay"] > 0:
            row["share"] = int((row["pay"] / summary["pay"] * 100).quantize(Decimal(1)))
        else:
            row["share"] = 0
        if summary["minutes"] > 0:
            row["hour_share"] = int(
                (Decimal(row["minutes"]) / Decimal(summary["minutes"]) * 100).quantize(
                    Decimal(1)
                )
            )
        else:
            row["hour_share"] = 0

    average_shift = format_minutes(0)
    if summary["count"]:
        average_shift = format_minutes(summary["minutes"] // summary["count"])

    timeline, timeline_axis = _timeline_points(period_shifts, period, today)

    return {
        "has_shifts": bool(period_shifts),
        "period": period,
        "period_label": period_label,
        "period_range_label": _format_range(start, end, shifts, today),
        "periods": STAT_PERIODS,
        "summary": summary,
        "previous": previous,
        "change": _pay_change(summary, previous),
        "average_rate": _average_rate(summary),
        "average_shift": average_shift,
        "by_workplace": breakdown,
        "pie": workplace_pies(breakdown),
        "timeline": timeline,
        "timeline_axis": timeline_axis,
        "highlights": _day_highlights(period_shifts),
        "workplaces": list(user.workplaces.order_by("name")),
        "selected_workplace": workplace,
    }


def _format_range(start, end, shifts, today):
    if start:
        return f"{start.strftime('%d %b %Y')} – {end.strftime('%d %b %Y')}"
    if shifts:
        first = min(shift.date for shift in shifts)
        return f"{first.strftime('%d %b %Y')} – {today.strftime('%d %b %Y')}"
    return ""


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


def unique_workplaces(shifts):
    workplaces = []
    seen = set()
    for shift in shifts:
        if shift.workplace_id in seen:
            continue
        seen.add(shift.workplace_id)
        workplaces.append(shift.workplace)
    return workplaces


def empty_calendar_month(year=None, month=None):
    today = timezone.localdate()
    year = year or today.year
    month = month or today.month
    first, _last, prev_year, prev_month, next_year, next_month = _month_bounds(
        year, month
    )
    return {
        "year": year,
        "month": month,
        "title": first.strftime("%B %Y"),
        "weeks": [],
        "month_summary": _empty_summary(),
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
        "weekday_labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "workplace_legend": [],
    }


def calendar_month(user, year, month):
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

    weeks = []
    for week in calendar.Calendar(firstweekday=calendar.MONDAY).monthdatescalendar(
        year, month
    ):
        days = []
        for day in week:
            day_shifts = by_day.get(day, [])
            day_summary = summarize_shifts(day_shifts)
            day_workplaces = unique_workplaces(day_shifts)
            days.append(
                {
                    "date": day,
                    "in_month": day.month == month,
                    "is_today": day == today,
                    "shifts": day_shifts,
                    "workplaces": day_workplaces,
                    "color_key": (
                        day_workplaces[0].color_key if len(day_workplaces) == 1 else ""
                    ),
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
        "month_summary": summarize_shifts(shifts),
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
        "weekday_labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "workplace_legend": sorted(
            unique_workplaces(shifts), key=lambda workplace: workplace.name.lower()
        ),
    }
