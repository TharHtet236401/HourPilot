"""Load Django so standalone scripts can use models.

Call setup() before importing app code.
"""

import os
import sys
from pathlib import Path


def setup():
    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    import django

    django.setup()
