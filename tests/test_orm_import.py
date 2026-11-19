import os
import sqlite3
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
MANAGE_PY = BASE_DIR / "manage.py"
IMPORT_SCRIPT = BASE_DIR / "db" / "import_sqlite_to_orm.py"
INSPECT_SCRIPT = BASE_DIR / "db" / "inspect_source_db.py"
SCHEMA_PATH = BASE_DIR / "sql" / "schema.sql"


def create_source_database(
    database_path: Path,
    product_brand_id: int = 1,
) -> None:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with sqlite3.connect(database_path) as connection:
        connection.executescript(schema)
        connection.execute(
            "INSERT INTO brands (id, name) VALUES (?, ?)",
            (1, "Librederm"),
        )
        connection.execute(
            "INSERT INTO categories (id, name) VALUES (?, ?)",
            (1, "Лицо"),
        )
        connection.execute(
            """
            INSERT INTO products (
                id,
                name,
                brand_id,
                category_id,
                quantity,
                expiry_date
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                7,
                "Крем",
                product_brand_id,
                1,
                2,
                "2027-05-10",
            ),
        )


def make_test_environment(
    settings_directory: Path,
    target_db: Path,
) -> dict[str, str]:
    settings_file = settings_directory / "test_settings.py"
    settings_file.write_text(
        "from cosmetic_inventory.settings import *\n"
        f"DATABASES['default']['NAME'] = {str(target_db)!r}\n",
        encoding="utf-8",
    )

    environment = os.environ.copy()
    python_path = environment.get("PYTHONPATH")
    paths = [str(settings_directory), str(BASE_DIR)]
    if python_path:
        paths.append(python_path)
    environment["PYTHONPATH"] = os.pathsep.join(paths)
    environment["DJANGO_SETTINGS_MODULE"] = "test_settings"
    return environment


def run_command(
    *command: str | Path,
    environment: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *(str(part) for part in command)],
        cwd=BASE_DIR,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def migrate_target(environment: dict[str, str]) -> None:
    result = run_command(
        MANAGE_PY,
        "migrate",
        "--noinput",
        "--verbosity",
        "0",
        environment=environment,
    )
    assert result.returncode == 0, result.stderr


def test_source_inspection_is_read_only(tmp_path: Path) -> None:
    source_db = tmp_path / "source.sqlite"
    create_source_database(source_db)
    before = source_db.read_bytes()

    result = run_command(INSPECT_SCRIPT, source_db)

    assert result.returncode == 0, result.stderr
    assert "Таблица: brands" in result.stdout
    assert "Таблица: categories" in result.stdout
    assert "Таблица: products" in result.stdout
    assert "Количество записей: 1" in result.stdout
    assert source_db.read_bytes() == before


def test_import_preserves_ids_relations_and_is_repeatable(
    tmp_path: Path,
) -> None:
    source_db = tmp_path / "source.sqlite"
    target_db = tmp_path / "target.sqlite"
    create_source_database(source_db)
    environment = make_test_environment(tmp_path, target_db)
    migrate_target(environment)

    first_result = run_command(
        IMPORT_SCRIPT,
        source_db,
        environment=environment,
    )
    second_result = run_command(
        IMPORT_SCRIPT,
        source_db,
        environment=environment,
    )

    assert first_result.returncode == 0, first_result.stderr
    assert second_result.returncode == 0, second_result.stderr
    assert "Брендов: 1" in second_result.stdout
    assert "Категорий: 1" in second_result.stdout
    assert "Средств: 1" in second_result.stdout

    with sqlite3.connect(target_db) as connection:
        brand = connection.execute(
            "SELECT id, name FROM products_brand"
        ).fetchone()
        category = connection.execute(
            "SELECT id, name FROM products_category"
        ).fetchone()
        product = connection.execute(
            """
            SELECT
                id,
                name,
                brand_id,
                category_id,
                quantity,
                expiry_date,
                slug,
                low_stock
            FROM products_product
            """
        ).fetchone()

        assert brand == (1, "Librederm")
        assert category == (1, "Лицо")
        assert product == (
            7,
            "Крем",
            1,
            1,
            2,
            "2027-05-10",
            "krem-7",
            0,
        )
        assert connection.execute(
            "SELECT COUNT(*) FROM products_product"
        ).fetchone()[0] == 1


def test_import_rejects_broken_source_relations(
    tmp_path: Path,
) -> None:
    source_db = tmp_path / "source.sqlite"
    target_db = tmp_path / "target.sqlite"
    create_source_database(source_db, product_brand_id=999)
    environment = make_test_environment(tmp_path, target_db)
    migrate_target(environment)

    result = run_command(
        IMPORT_SCRIPT,
        source_db,
        environment=environment,
    )

    assert result.returncode != 0
    assert "несуществующие бренды: [999]" in result.stderr
    with sqlite3.connect(target_db) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM products_brand"
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM products_category"
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM products_product"
        ).fetchone()[0] == 0
