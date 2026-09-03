# Scripts

Local helper scripts for [HourPilot](../README.md). Run them from the project root with `uv`.

## Seed dummy data

Creates sample workplaces and shifts so Home, Workspaces, Shifts, and Calendar have something to show.

```bash
uv run python scripts/seed_demo.py
```

- Uses your first existing account, or creates `demo@example.com` / `demo1234` if nobody exists yet.
- Stops if that account already has workplaces or shifts, so it does not duplicate data.

Replace existing dummy data:

```bash
uv run python scripts/seed_demo.py --reset
```

Seed a specific account (the user must already exist):

```bash
uv run python scripts/seed_demo.py --email you@example.com
uv run python scripts/seed_demo.py --email you@example.com --reset
```

## Change the dummy data

Edit `scripts/seed/data.py`.

- `WORKPLACES`: name, hourly rate, and whether the workplace is active.
- `SHIFT_PATTERNS`: `(days_after_start, workplace_name, start, end, break_minutes, notes)`.
  - Dates start 70 days before today.
  - `workplace_name` must match a name in `WORKPLACES`.
  - End time must be after start time.

The write logic lives in `scripts/seed/demo.py`. You usually do not need to change it unless you add new fields.

## Add another script

1. Put shared Django bootstrapping in `scripts/django_setup.py` (already used by `seed_demo.py`).
2. Put data in `scripts/<name>/data.py` and logic in `scripts/<name>/...`.
3. Add a runner at `scripts/<name>.py` that:
   - adds the project root to `sys.path`
   - calls `setup()`
   - then imports Django models / seed helpers
4. Run it the same way:

```bash
uv run python scripts/your_script.py
```
