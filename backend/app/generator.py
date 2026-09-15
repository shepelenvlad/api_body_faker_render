"""
Генерация JSON-тела на основе JSON Schema.

Приоритет значений для поля:
1. const               -> берём как есть
2. enum                -> случайный выбор из списка
3. example / default   -> берём как есть (автор схемы явно задал значение)
4. иначе               -> генерируем через Faker (по format, затем по имени поля,
                           затем по типу как fallback)

Ограничение v1: $ref / $defs не резолвятся. Если понадобится — легко добавить
resolve_ref() и прокидывать корневую схему вглубь рекурсии.
"""

import random
import re
from datetime import datetime, timedelta
from typing import Any

from faker import Faker

fake = Faker()

# Эвристики по ИМЕНИ поля — работают, если явный "format" в схеме не задан.
# Порядок важен: более специфичные паттерны должны идти раньше общих.
_FIELD_NAME_GENERATORS: list[tuple[re.Pattern, Any]] = [
    (re.compile(r"e[-_]?mail", re.I), lambda: fake.email()),
    (re.compile(r"first[-_]?name", re.I), lambda: fake.first_name()),
    (re.compile(r"last[-_]?name", re.I), lambda: fake.last_name()),
    (re.compile(r"full[-_]?name|^name$", re.I), lambda: fake.name()),
    (re.compile(r"phone", re.I), lambda: fake.numerify("+380#########")),
    (re.compile(r"address", re.I), lambda: fake.address().replace("\n", ", ")),
    (re.compile(r"city", re.I), lambda: fake.city()),
    (re.compile(r"country", re.I), lambda: fake.country()),
    (re.compile(r"company", re.I), lambda: fake.company()),
    (re.compile(r"^id$|_id$", re.I), lambda: str(fake.uuid4())),
    (re.compile(r"url|link", re.I), lambda: fake.url()),
    (re.compile(r"username|login", re.I), lambda: fake.user_name()),
    (re.compile(r"password", re.I), lambda: fake.password()),
    (re.compile(r"zip|postal", re.I), lambda: fake.postcode()),
    (re.compile(r"description|comment|note", re.I), lambda: fake.sentence()),
    (re.compile(r"title", re.I), lambda: fake.sentence(nb_words=4).rstrip(".")),
    (re.compile(r"price|amount|cost", re.I), lambda: round(random.uniform(1, 1000), 2)),
    (re.compile(r"latitude", re.I), lambda: str(fake.latitude())),
    (re.compile(r"longitude", re.I), lambda: str(fake.longitude())),
    (re.compile(r"elevation", re.I), lambda: str(round(random.uniform(0, 500), 6))),
    (re.compile(r"^token$", re.I), lambda: ".".join(fake.lexify("?" * 20) for _ in range(3))),
    (re.compile(r"cadastral", re.I), lambda: fake.numerify("##########:##:###:####")),
]

_FORMAT_GENERATORS = {
    "email": lambda: fake.email(),
    "date": lambda: fake.date(),
    "date-time": lambda: fake.iso8601(),
    "uuid": lambda: str(fake.uuid4()),
    "uri": lambda: fake.url(),
    "url": lambda: fake.url(),
    "hostname": lambda: fake.hostname(),
    "ipv4": lambda: fake.ipv4(),
    "ipv6": lambda: fake.ipv6(),
    "phone": lambda: fake.numerify("+380#########"),
}

# Поля вроде "routeQuantity", "wagonTypes", "loadObjectCode" в реальных схемах
# почти всегда короткие числовые коды/количества, а не свободный текст.
# "...Name" полях (loadObjectName и т.п.) явно хотим текст, поэтому их исключаем.
_NUMERIC_LOOKING_FIELD = re.compile(r"quantity|number|code|species|type|object", re.I)
_NAME_SUFFIX = re.compile(r"name$", re.I)


def _looks_numeric(field_name: str) -> bool:
    if _NAME_SUFFIX.search(field_name):
        return False
    return bool(_NUMERIC_LOOKING_FIELD.search(field_name))


def _random_digits(min_len: int, max_len: int) -> str:
    length = random.randint(min_len, max(min_len, max_len))
    if length <= 0:
        return ""
    return "".join(random.choices("0123456789", k=length))


def _random_short_string(min_len: int, max_len: int) -> str:
    """Безопасная генерация строки любой длины, включая < 5 символов,
    где fake.text() бросает ValueError."""
    length = random.randint(min_len, max(min_len, max_len))
    if length <= 0:
        return ""
    if length < 5:
        return fake.lexify("?" * length)
    return fake.text(max_nb_chars=max_len)[:max_len]


def _generate_properties(properties: dict, base: dict | None = None) -> dict:
    result = dict(base) if base else {}
    for name, sub_schema in properties.items():
        result[name] = generate_from_schema(sub_schema, field_name=name)
    return result


def _condition_matches(data: dict, condition_schema: dict) -> bool:
    """Проверяет блок "if": сравнивает уже сгенерированные значения
    с const/enum, заданными в условии (поддерживает только простые случаи)."""
    for name, sub_schema in condition_schema.get("properties", {}).items():
        value = data.get(name)
        if "const" in sub_schema and value != sub_schema["const"]:
            return False
        if "enum" in sub_schema and value not in sub_schema["enum"]:
            return False
    return True


def _relative_datetime(spec) -> str:
    """Генерирует ISO-дату как (сейчас UTC + N часов).
    spec может быть числом (фиксированный сдвиг) или {"min": X, "max": Y}
    (случайный сдвиг в диапазоне часов, X может быть дробным)."""
    if isinstance(spec, (int, float)):
        hours = spec
    else:
        min_h = spec.get("min", 0)
        max_h = spec.get("max", min_h)
        hours = random.uniform(min_h, max_h)
    dt = datetime.utcnow() + timedelta(hours=hours)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _fix_discount_tender_attempts(obj: dict) -> None:
    """При tenderAttempts == 1 поле discount вообще нельзя передавать —
    валидатор ругается на сам факт его наличия, не только на discount: true."""
    tender_attempts = obj.get("tenderAttempts")
    if tender_attempts == 1:
        obj.pop("discount", None)


def _fix_discount_amount(obj: dict) -> None:
    """Гарантирует discount.previousAuctionValue.amount > value.amount
    (сравнение имеет смысл только там, где оба ключа — "value" и "discount" —
    присутствуют на одном уровне, то есть фактически только в корне схемы)."""
    value = obj.get("value")
    discount = obj.get("discount")
    if not isinstance(value, dict) or not isinstance(discount, dict):
        return
    prev = discount.get("previousAuctionValue")
    base_amount = value.get("amount")
    if not isinstance(prev, dict) or "amount" not in prev:
        return
    if not isinstance(base_amount, (int, float)):
        return
    prev["amount"] = round(base_amount + random.uniform(50, 5000), 2)


def _fix_date_range(obj: dict) -> None:
    """Если в объекте есть и dateFrom, и dateTill — пересчитывает dateTill
    так, чтобы он гарантированно был позже dateFrom."""
    date_from_raw = obj.get("dateFrom")
    if "dateTill" not in obj or not isinstance(date_from_raw, str):
        return
    try:
        date_from = datetime.fromisoformat(date_from_raw.replace("Z", "+00:00"))
    except ValueError:
        return
    date_till = date_from + timedelta(days=random.randint(30, 180))
    obj["dateTill"] = date_till.isoformat()


def _reapply_conditional(item: dict, schema: dict) -> None:
    """После того как uniqueBy вручную поменял поле, от которого зависит
    if/then/else этого же объекта, — пересчитывает зависимые свойства
    заново (иначе, например, scheme поменяется, а id останется от старой
    scheme, взятый ещё до подмены)."""
    if_schema = schema.get("if")
    if not if_schema:
        return
    if _condition_matches(item, if_schema):
        then_schema = schema.get("then", {})
        for name, sub_schema in then_schema.get("properties", {}).items():
            item[name] = generate_from_schema(sub_schema, field_name=name)
    elif "else" in schema:
        else_schema = schema["else"]
        for name, sub_schema in else_schema.get("properties", {}).items():
            item[name] = generate_from_schema(sub_schema, field_name=name)


def _assign_unique_field(items: list, item_schema: dict, field_name: str) -> None:
    """Поддержка кастомного ключа массива "uniqueBy": <имя поля>.
    Раздаёт значення из enum этого поля по элементам без повторов
    (пока элементов не больше, чем вариантов в enum)."""
    field_schema = item_schema.get("properties", {}).get(field_name, {})
    choices = field_schema.get("enum")
    if not choices:
        return
    pool = list(choices)
    random.shuffle(pool)
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        item[field_name] = pool[i] if i < len(pool) else random.choice(choices)
        _reapply_conditional(item, item_schema)


def _ensure_required_values(items: list, field_name: str, required_values: list) -> None:
    """Поддержка кастомного ключа массива "requireValues": {"field": ..., "values": [...]}.
    Гарантирует, что каждое значение из required_values встретится хотя бы
    в одном элементе массива (в отличие от uniqueBy — не требует различия
    остальных элементов между собой)."""
    if not field_name or not required_values or not items:
        return
    present = {item.get(field_name) for item in items if isinstance(item, dict)}
    missing = [v for v in required_values if v not in present]
    idx = 0
    for value in missing:
        while idx < len(items) and not isinstance(items[idx], dict):
            idx += 1
        if idx >= len(items):
            break
        items[idx][field_name] = value
        idx += 1


def generate_from_schema(schema: dict, field_name: str = "") -> Any:
    if not isinstance(schema, dict):
        return None

    if "const" in schema:
        return schema["const"]
    if schema.get("enum"):
        return random.choice(schema["enum"])
    if "example" in schema:
        return schema["example"]
    if "default" in schema:
        return schema["default"]

    schema_type = schema.get("type", "object")

    if schema_type == "object":
        result = _generate_properties(schema.get("properties", {}))

        if_schema = schema.get("if")
        if if_schema and _condition_matches(result, if_schema):
            then_schema = schema.get("then", {})
            result = _generate_properties(then_schema.get("properties", {}), base=result)
        elif if_schema and "else" in schema:
            else_schema = schema["else"]
            result = _generate_properties(else_schema.get("properties", {}), base=result)

        # "conditionals" — список независимых if/then/else-правил на одном
        # объекте (обычный "if" поддерживает только одно условие за раз,
        # а бывает нужно несколько пар вида hasX -> X одновременно).
        for rule in schema.get("conditionals", []):
            rule_if = rule.get("if", {})
            if _condition_matches(result, rule_if):
                then_schema = rule.get("then", {})
                result = _generate_properties(then_schema.get("properties", {}), base=result)
            elif "else" in rule:
                else_schema = rule["else"]
                result = _generate_properties(else_schema.get("properties", {}), base=result)

        _fix_date_range(result)
        _fix_discount_tender_attempts(result)
        _fix_discount_amount(result)
        return result

    if schema_type == "array":
        item_schema = schema.get("items", {})
        min_items = schema.get("minItems", 1)
        max_items = schema.get("maxItems", max(min_items, 3))
        count = random.randint(min_items, max_items)
        items = [generate_from_schema(item_schema, field_name=field_name) for _ in range(count)]

        unique_by = schema.get("uniqueBy")
        if unique_by:
            _assign_unique_field(items, item_schema, unique_by)

        require_values = schema.get("requireValues")
        if require_values:
            _ensure_required_values(items, require_values.get("field"), require_values.get("values", []))

        return items

    if schema_type == "string":
        if "relativeHours" in schema:
            return _relative_datetime(schema["relativeHours"])

        fmt = schema.get("format")
        if fmt in _FORMAT_GENERATORS:
            return _FORMAT_GENERATORS[fmt]()
        for pattern, generator in _FIELD_NAME_GENERATORS:
            if pattern.search(field_name):
                return generator()
        min_len = schema.get("minLength", 5)
        max_len = schema.get("maxLength", max(min_len, 10))

        if _looks_numeric(field_name):
            return _random_digits(min_len, max_len)

        return _random_short_string(min_len, max_len)

    if schema_type == "integer":
        return random.randint(schema.get("minimum", 0), schema.get("maximum", 1000))

    if schema_type == "number":
        return round(random.uniform(schema.get("minimum", 0), schema.get("maximum", 1000)), 2)

    if schema_type == "boolean":
        return random.choice([True, False])

    if schema_type == "null":
        return None

    return None
