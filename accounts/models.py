from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Profile(models.Model):
    CURRENCY_GBP = "GBP"
    CURRENCY_EUR = "EUR"
    CURRENCY_USD = "USD"
    CURRENCY_CHOICES = (
        (CURRENCY_GBP, "£ Pound"),
        (CURRENCY_EUR, "€ Euro"),
        (CURRENCY_USD, "$ US dollar"),
    )

    DATE_UK = "uk"
    DATE_US = "us"
    DATE_ISO = "iso"
    DATE_FORMAT_CHOICES = (
        (DATE_UK, "9 Sep 2026"),
        (DATE_US, "Sep 9, 2026"),
        (DATE_ISO, "2026-09-09"),
    )

    WEEK_MON = "mon"
    WEEK_SUN = "sun"
    WEEK_START_CHOICES = (
        (WEEK_MON, "Monday"),
        (WEEK_SUN, "Sunday"),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    display_name = models.CharField(
        max_length=80,
        blank=True,
        help_text="Shown on CSV exports. Leave blank to use your email.",
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default=CURRENCY_GBP,
    )
    date_format = models.CharField(
        max_length=8,
        choices=DATE_FORMAT_CHOICES,
        default=DATE_UK,
    )
    week_start = models.CharField(
        max_length=3,
        choices=WEEK_START_CHOICES,
        default=WEEK_MON,
    )
    weekly_hour_goal = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.5")), MaxValueValidator(Decimal(168))],
        help_text="Optional weekly hours target. Leave blank for none.",
    )

    def __str__(self):
        return self.display_name or self.user.email
