import json
from pathlib import Path
from typing import Optional

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"


def _load_schema_file(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_schemas() -> list[dict]:
    """Сканирует папку схем при каждом вызове — новые/изменённые .json файлы
    подхватываются без перезапуска бэкенда."""
    result = []
    for path in sorted(SCHEMAS_DIR.glob("*.json")):
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


def get_schema(schema_id: str) -> Optional[dict]:
    # Только имя файла, без "../" и путей — простая защита от path traversal
    safe_id = Path(schema_id).name
    path = SCHEMAS_DIR / f"{safe_id}.json"
    if not path.exists() or path.parent != SCHEMAS_DIR:
        return None
    return _load_schema_file(path)
