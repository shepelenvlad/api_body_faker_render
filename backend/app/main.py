from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.generator import generate_from_schema
from app.registry import get_schema, list_schemas

app = FastAPI(title="REST API JSON Body Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # для dev; в проде укажите конкретный домен фронта
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/schemas")
def get_schemas():
    """Список схем для дропдауна на фронте."""
    return list_schemas()


@app.get("/api/generate/{schema_id}")
def generate(schema_id: str):
    """Генерирует JSON-тело по выбранной схеме."""
    schema = get_schema(schema_id)
    if schema is None:
        raise HTTPException(status_code=404, detail=f"Схема '{schema_id}' не найдена")
    return generate_from_schema(schema)


@app.get("/api/health")
def health():
    return {"status": "ok"}
