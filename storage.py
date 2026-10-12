# сохранение и загрузка данных проекта в формате JSON

import json
from pathlib import Path


# загрузка списка средств из JSON-файла
def load_products(filename: str | Path) -> list[dict]:
    path = Path(filename)
    try:
        with path.open("r", encoding="utf-8") as file:
            products = json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as error:
        raise ValueError("Файл содержит некорректный JSON.") from error
    except OSError as error:
        raise ValueError(f"Не удалось прочитать файл: {error}") from error

    if not isinstance(products, list):
        raise ValueError("В JSON-файле должен находиться список средств.")
    return products


# сохранение списка средств в JSON-файл
def save_products(filename: str | Path, products: list[dict]) -> None:
    path = Path(filename)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            json.dump(products, file, ensure_ascii=False, indent=4)
    except OSError as error:
        raise ValueError(f"Не удалось сохранить файл: {error}") from error
