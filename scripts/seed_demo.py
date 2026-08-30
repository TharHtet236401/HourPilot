"""
Seed dummy workplaces and shifts for local testing.

  uv run python scripts/seed_demo.py
  uv run python scripts/seed_demo.py --reset
  uv run python scripts/seed_demo.py --email you@example.com

See scripts/README.md for full usage.
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.django_setup import setup

setup()

from scripts.seed import (  # noqa: E402
    DEMO_EMAIL,
    DEMO_PASSWORD,
    SeedError,
    get_or_create_user,
    seed_demo,
)


def main():
    parser = argparse.ArgumentParser(
        description="Create dummy workplaces and shifts for local testing."
    )
    parser.add_argument(
        "--email",
        help="User to attach the dummy data to. Uses the first user, or creates a demo account.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete that user's workplaces and shifts before seeding.",
    )
    args = parser.parse_args()

    try:
        user, created = get_or_create_user(args.email)
        workplace_count, shift_count = seed_demo(user, reset=args.reset)
    except SeedError as exc:
        print(exc, file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Could not seed dummy data: {exc}", file=sys.stderr)
        return 1

    if created:
        print(f"Created demo user {DEMO_EMAIL}.")

    print(
        f"Seeded {workplace_count} workplaces and {shift_count} shifts for {user.email}."
    )
    if user.email == DEMO_EMAIL:
        print(f"Demo login: {DEMO_EMAIL} / {DEMO_PASSWORD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
