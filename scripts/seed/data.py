"""Dummy workplaces and shifts used by scripts/seed_demo.py.

Each SHIFT_PATTERNS row is:
    (days_after_start, workplace_name, start_time, end_time, break_minutes, notes)

Dates are counted from 70 days before today. workplace_name must match WORKPLACES.
"""

from datetime import time
from decimal import Decimal

WORKPLACES = [
    {"name": "Tesco Extra", "hourly_rate": Decimal("12.50"), "is_active": True},
    {"name": "Cafe Nero", "hourly_rate": Decimal("11.80"), "is_active": True},
    {"name": "Warehouse", "hourly_rate": Decimal("13.20"), "is_active": True},
    {"name": "Private tutoring", "hourly_rate": Decimal("18.00"), "is_active": True},
    {"name": "The Crown pub", "hourly_rate": Decimal("11.44"), "is_active": True},
    {"name": "City Library", "hourly_rate": Decimal("12.00"), "is_active": True},
    {"name": "Sainsbury's", "hourly_rate": Decimal("12.21"), "is_active": True},
    {"name": "Campus shop", "hourly_rate": Decimal("11.60"), "is_active": True},
    {"name": "Evening cleaning", "hourly_rate": Decimal("12.80"), "is_active": False},
]

SHIFT_PATTERNS = [
    (0, "Tesco Extra", time(8, 0), time(16, 0), 30, "Covered produce."),
    (1, "Cafe Nero", time(7, 30), time(13, 30), 15, ""),
    (2, "Warehouse", time(6, 0), time(14, 0), 30, "Early inbound."),
    (3, "Private tutoring", time(17, 0), time(19, 0), 0, "GCSE maths."),
    (4, "The Crown pub", time(17, 30), time(23, 0), 20, "Friday evening."),
    (5, "City Library", time(10, 0), time(16, 0), 30, ""),
    (6, "Sainsbury's", time(12, 0), time(20, 0), 30, "Late checkout."),
    (8, "Campus shop", time(9, 0), time(15, 0), 15, ""),
    (9, "Tesco Extra", time(9, 0), time(17, 0), 45, ""),
    (10, "Cafe Nero", time(8, 0), time(14, 0), 20, "Busy lunch."),
    (11, "Warehouse", time(14, 0), time(22, 0), 30, ""),
    (12, "Private tutoring", time(16, 30), time(18, 30), 0, ""),
    (14, "The Crown pub", time(18, 0), time(23, 30), 15, ""),
    (15, "City Library", time(9, 30), time(17, 0), 30, "Stock check."),
    (16, "Sainsbury's", time(7, 0), time(13, 0), 20, ""),
    (17, "Campus shop", time(11, 0), time(17, 0), 15, ""),
    (18, "Tesco Extra", time(8, 30), time(16, 30), 30, ""),
    (19, "Cafe Nero", time(7, 0), time(12, 0), 0, "Open up."),
    (21, "Warehouse", time(6, 30), time(14, 30), 30, ""),
    (22, "Private tutoring", time(17, 0), time(20, 0), 0, "Two students."),
    (23, "The Crown pub", time(16, 0), time(22, 0), 20, ""),
    (24, "City Library", time(12, 0), time(18, 0), 15, ""),
    (25, "Sainsbury's", time(13, 0), time(21, 0), 30, ""),
    (26, "Campus shop", time(10, 0), time(16, 0), 15, ""),
    (28, "Tesco Extra", time(10, 0), time(18, 0), 30, ""),
    (29, "Cafe Nero", time(9, 0), time(15, 0), 20, ""),
    (31, "Warehouse", time(7, 0), time(15, 0), 30, ""),
    (32, "Private tutoring", time(18, 0), time(20, 0), 0, ""),
    (33, "The Crown pub", time(17, 0), time(23, 0), 20, "Saturday night."),
    (35, "City Library", time(9, 0), time(13, 0), 0, "Morning only."),
    (36, "Sainsbury's", time(8, 0), time(16, 0), 30, ""),
    (38, "Campus shop", time(12, 30), time(18, 30), 15, ""),
    (39, "Tesco Extra", time(7, 30), time(15, 30), 30, ""),
    (42, "Evening cleaning", time(20, 0), time(23, 0), 0, "Old contract."),
    (43, "Cafe Nero", time(8, 0), time(16, 0), 30, ""),
    (45, "Warehouse", time(6, 0), time(12, 0), 15, "Half day."),
]
