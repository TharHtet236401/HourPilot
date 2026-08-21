from django.db import models

# Create your models here.
from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.db import models

from workspaces.models import Workplace


class Shift(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shifts",
    )

    workplace = models.ForeignKey(
        Workplace,
        on_delete=models.PROTECT,
        related_name="shifts",
    )

    date = models.DateField()

    start_time = models.TimeField()

    end_time = models.TimeField()

    break_minutes = models.PositiveIntegerField(default=0)

    hourly_rate_at_time = models.DecimalField(
        max_digits=6,
        decimal_places=2,
    )

    notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.date} - {self.workplace.name}"

    def duration_minutes(self):
        start = datetime.combine(
            self.date,
            self.start_time,
        )

        end = datetime.combine(
            self.date,
            self.end_time,
        )

        # Handle shifts crossing midnight
        if end <= start:
            end += timedelta(days=1)

        total_minutes = int(
            (end - start).total_seconds() / 60
        )

        return total_minutes - self.break_minutes

    def duration_hours(self):
        return Decimal(self.duration_minutes()) / Decimal("60")

    def duration_display(self):
        minutes = max(self.duration_minutes(), 0)
        hours, remaining = divmod(minutes, 60)

        if hours and remaining:
            return f"{hours}h {remaining}m"
        if hours:
            return f"{hours}h"
        return f"{remaining}m"

    def estimated_earnings(self):
        return (
            self.duration_hours()
            * self.hourly_rate_at_time
        ).quantize(Decimal("0.01"))