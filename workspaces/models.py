from django.conf import settings
from django.db import models

from .colors import workplace_color_key


class Workplace(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workplaces",
    )

    name = models.CharField(max_length=100)

    hourly_rate = models.DecimalField(
        max_digits=6,
        decimal_places=2,
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def color_key(self):
        return workplace_color_key(self.pk)

    def __str__(self):
        return self.name
