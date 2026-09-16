import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.generator import generate_from_schema
from app.registry import get_schema, list_categories, list_schemas

app = FastAPI(title="REST API JSON Body Generator")

# CORS_ORIGINS: список дозволених origin'ів через кому (напр. URL фронтенда
# на Render). Якщо не задано — дозволяються всі (зручно для локальної розробки).
_cors_origins_env = os.environ.get("CORS_ORIGINS", "*").strip()
allow_origins = (
    ["*"] if _cors_origins_env == "*" else [o.strip() for o in _cors_origins_env.split(",") if o.strip()]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/categories")
def get_categories():
    """Список категорий (табов) для фронта."""
    return list_categories()


@app.get("/api/schemas/{category_id}")
def get_schemas(category_id: str):
    """Список схем выбранной категории для дропдауна на фронте."""
    return list_schemas(category_id)


@app.get("/api/generate/{category_id}/{schema_id}")
def generate(category_id: str, schema_id: str):
    """Генерирует JSON-тело по выбранной схеме из выбранной категории."""
    schema = get_schema(category_id, schema_id)
    if schema is None:
        raise HTTPException(
            status_code=404,
            detail=f"Схема '{schema_id}' в категории '{category_id}' не найдена",
        )
    return generate_from_schema(schema)


@app.get("/api/health")
def health():
    return {"status": "ok"}
