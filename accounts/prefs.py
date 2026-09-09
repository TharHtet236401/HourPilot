import calendar
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from django.utils import formats
from django.utils.timezone import localtime

from .models import Profile

CURRENCY_SYMBOLS = {
    Profile.CURRENCY_GBP: "£",
    Profile.CURRENCY_EUR: "€",
    Profile.CURRENCY_USD: "$",
}

DATE_STYLES = {
    Profile.DATE_UK: {
        "short": "j M",
        "medium": "j M Y",
        "long": "l j F Y",
        "datetime": "j M Y, H:i",
    },
    Profile.DATE_US: {
        "short": "M j",
        "medium": "M j, Y",
        "long": "l, F j, Y",
        "datetime": "M j, Y, H:i",
    },
    Profile.DATE_ISO: {
        "short": "Y-m-d",
        "medium": "Y-m-d",
        "long": "Y-m-d",
        "datetime": "Y-m-d H:i",
    },
}

WEEKDAY_LABELS = {
    Profile.WEEK_MON: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    Profile.WEEK_SUN: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
}


@dataclass(frozen=True)
class Prefs:
    display_name: str = ""
    currency: str = Profile.CURRENCY_GBP
    currency_symbol: str = "£"
    date_format: str = Profile.DATE_UK
    date_short: str = DATE_STYLES[Profile.DATE_UK]["short"]
    date_medium: str = DATE_STYLES[Profile.DATE_UK]["medium"]
    date_long: str = DATE_STYLES[Profile.DATE_UK]["long"]
    date_datetime: str = DATE_STYLES[Profile.DATE_UK]["datetime"]
    week_start: str = Profile.WEEK_MON
    weekly_hour_goal: Decimal | None = None
    weekday_labels: tuple[str, ...] = tuple(WEEKDAY_LABELS[Profile.WEEK_MON])

    def format_date(self, value, style="medium"):
        if value is None:
            return ""
        if isinstance(value, datetime):
            value = localtime(value)
            pattern = {
                "short": self.date_short,
                "medium": self.date_medium,
                "long": self.date_long,
                "datetime": self.date_datetime,
            }.get(style, self.date_datetime)
        else:
            pattern = {
                "short": self.date_short,
                "medium": self.date_medium,
                "long": self.date_long,
                "datetime": self.date_medium,
            }.get(style, self.date_medium)
        return formats.date_format(value, pattern)


def get_profile(user):
    if not user or not getattr(user, "is_authenticated", False):
        return None
    cached = getattr(user, "_hourpilot_profile", None)
    if cached is not None:
        return cached
    profile, _ = Profile.objects.get_or_create(user=user)
    user._hourpilot_profile = profile
    return profile


def prefs_for(user=None):
    profile = get_profile(user)
    if profile is None:
        return Prefs()
    styles = DATE_STYLES.get(profile.date_format, DATE_STYLES[Profile.DATE_UK])
    return Prefs(
        display_name=profile.display_name,
        currency=profile.currency,
        currency_symbol=CURRENCY_SYMBOLS.get(profile.currency, "£"),
        date_format=profile.date_format,
        date_short=styles["short"],
        date_medium=styles["medium"],
        date_long=styles["long"],
        date_datetime=styles["datetime"],
        week_start=profile.week_start,
        weekly_hour_goal=profile.weekly_hour_goal,
        weekday_labels=tuple(
            WEEKDAY_LABELS.get(profile.week_start, WEEKDAY_LABELS[Profile.WEEK_MON])
        ),
    )


def week_start_date(today, week_start=Profile.WEEK_MON):
    if week_start == Profile.WEEK_SUN:
        offset = (today.weekday() + 1) % 7
    else:
        offset = today.weekday()
    return today - timedelta(days=offset)


def calendar_firstweekday(week_start=Profile.WEEK_MON):
    if week_start == Profile.WEEK_SUN:
        return calendar.SUNDAY
    return calendar.MONDAY


def user_prefs(request):
    return {"prefs": prefs_for(getattr(request, "user", None))}
