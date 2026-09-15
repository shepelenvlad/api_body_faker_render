import json
from pathlib import Path
from typing import Optional

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"

# Категории (табы во фронтенде) — id совпадает с именем папки в schemas/.
# Порядок в этом списке = порядок табов в UI.
CATEGORIES: list[dict] = [
    {"id": "procedures", "label": "Procedures"},
    {"id": "registry", "label": "Registry"},
    {"id": "jobber", "label": "Jobber"},
    {"id": "bids", "label": "Bids"},
]

_CATEGORY_IDS = {c["id"] for c in CATEGORIES}


def list_categories() -> list[dict]:
    """Список табов для фронтенда."""
    return CATEGORIES


def _category_dir(category_id: str) -> Optional[Path]:
    """Возвращает папку категории, только если это известная категория
    (защита от path traversal через category_id)."""
    if category_id not in _CATEGORY_IDS:
        return None
    path = SCHEMAS_DIR / category_id
    if not path.is_dir():
        return None
    return path


def _load_schema_file(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_schemas(category_id: str) -> list[dict]:
    """Сканирует папку схем выбранной категории при каждом вызове — новые/
    изменённые .json файлы подхватываются без перезапуска бэкенда."""
    category_dir = _category_dir(category_id)
    if category_dir is None:
        return []

    result = []
    for path in sorted(category_dir.glob("*.json")):
        try:
            schema = _load_schema_file(path)
        except json.JSONDecodeError:
            # Пропускаем битые файлы, чтобы не ронять весь список
            continue
        result.append(
            {
                "id": path.stem,
                "title": schema.get("title", path.stem),
                "description": schema.get("description", ""),
            }
        )
    return result


def get_schema(category_id: str, schema_id: str) -> Optional[dict]:
    category_dir = _category_dir(category_id)
    if category_dir is None:
        return None
    # Только имя файла, без "../" и путей — простая защита от path traversal
    safe_id = Path(schema_id).name
    path = category_dir / f"{safe_id}.json"
    if not path.exists() or path.parent != category_dir:
        return None
    return _load_schema_file(path)
