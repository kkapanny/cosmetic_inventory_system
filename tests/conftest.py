import os
import tempfile
from pathlib import Path

import django
from django.conf import settings
from django.core.management import call_command
from django.test.utils import setup_test_environment


_TEST_DIRECTORY = tempfile.TemporaryDirectory(
    prefix="cosmetic_inventory_tests_",
)
_TEST_DATABASE = Path(_TEST_DIRECTORY.name) / "db.sqlite3"

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "cosmetic_inventory.settings",
)
settings.DATABASES["default"]["NAME"] = _TEST_DATABASE
django.setup()
setup_test_environment()


def prepare_test_database() -> None:
    from db.import_sqlite_to_orm import import_inventory

    call_command("migrate", verbosity=0, interactive=False)
    import_inventory()


prepare_test_database()
