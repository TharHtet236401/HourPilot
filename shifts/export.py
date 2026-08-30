import csv
import io
import re

from .services import format_minutes, summarize_shifts


def filtered_shifts(user, workplace=None, date_from=None, date_to=None):
    shifts = user.shifts.select_related("workplace").order_by("date", "start_time")
    if workplace:
        shifts = shifts.filter(workplace=workplace)
    if date_from:
        shifts = shifts.filter(date__gte=date_from)
    if date_to:
        shifts = shifts.filter(date__lte=date_to)
    return list(shifts)


def export_filename(workplace=None, date_from=None, date_to=None):
    parts = ["shifts"]
    if workplace:
        slug = re.sub(r"[^a-z0-9]+", "-", workplace.name.lower()).strip("-")
        parts.append(slug[:40] or "workplace")
    if date_from:
        parts.append(date_from.isoformat())
    if date_to:
        parts.append(date_to.isoformat())
    return f"{'-'.join(parts)}.csv"


def shifts_csv(shifts):
    buffer = io.StringIO()
    buffer.write("\ufeff")
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "Date",
            "Workplace",
            "Start",
            "End",
            "Break (minutes)",
            "Duration",
            "Hourly rate",
            "Pay",
            "Notes",
        ]
    )

    for shift in shifts:
        writer.writerow(
            [
                shift.date.isoformat(),
                shift.workplace.name,
                shift.start_time.strftime("%H:%M"),
                shift.end_time.strftime("%H:%M"),
                shift.break_minutes,
                shift.duration_display(),
                f"{shift.hourly_rate_at_time:.2f}",
                f"{shift.estimated_earnings():.2f}",
                shift.notes.replace("\r\n", " ").replace("\n", " "),
            ]
        )

    summary = summarize_shifts(shifts)
    writer.writerow([])
    writer.writerow(
        [
            "Total",
            "",
            "",
            "",
            "",
            format_minutes(summary["minutes"]),
            "",
            f"{summary['pay']:.2f}",
            f"{summary['count']} shift{'s' if summary['count'] != 1 else ''}",
        ]
    )
    return buffer.getvalue()
