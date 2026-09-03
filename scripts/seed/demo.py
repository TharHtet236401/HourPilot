"""Create the demo user (if needed) and write dummy workplaces / shifts."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from shifts.models import Shift
from workspaces.models import Workplace

from .data import SHIFT_PATTERNS, WORKPLACES

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "demo1234"


class SeedError(Exception):
    pass


def get_or_create_user(email=None):
    User = get_user_model()
    created = False

    if email:
        try:
            return User.objects.get(email__iexact=email), created
        except User.DoesNotExist as exc:
            raise SeedError(f"No user with email {email}.") from exc

    existing = User.objects.order_by("id").first()
    if existing:
        return existing, created

    username_field = getattr(User, "USERNAME_FIELD", "username")
    defaults = {
        "email": DEMO_EMAIL,
        "password": DEMO_PASSWORD,
    }
    if username_field != "email" and "username" in [
        field.name for field in User._meta.fields
    ]:
        defaults["username"] = "demo"

    created = True
    return User.objects.create_user(**defaults), created


@transaction.atomic
def seed_demo(user, reset=False):
    if reset:
        user.shifts.all().delete()
        user.workplaces.all().delete()
    elif user.workplaces.exists() or user.shifts.exists():
        raise SeedError(
            f"{user.email} already has data. Re-run with --reset to replace it."
        )

    workplaces = {}
    for item in WORKPLACES:
        workplace = Workplace.objects.create(user=user, **item)
        workplaces[workplace.name] = workplace

    today = timezone.localdate()
    start = today - timedelta(days=70)
    created_shifts = 0

    for (
        offset,
        workplace_name,
        start_time,
        end_time,
        break_minutes,
        notes,
    ) in SHIFT_PATTERNS:
        shift_date = start + timedelta(days=offset)
        if shift_date > today:
            continue
        workplace = workplaces[workplace_name]
        Shift.objects.create(
            user=user,
            workplace=workplace,
            date=shift_date,
            start_time=start_time,
            end_time=end_time,
            break_minutes=break_minutes,
            hourly_rate_at_time=workplace.hourly_rate,
            notes=notes,
        )
        created_shifts += 1

    return len(workplaces), created_shifts
