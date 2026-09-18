# JSON Body Generator

Генератор тіла запиту для тестування REST API. Обираєш схему в дропдауні на
фронтенді — бекенд генерує JSON, заповнений правдоподібними даними (через
Faker) згідно з JSON Schema, яку ти сам описуєш у файлі.

## Запуск

```bash
docker-compose up --build
```

- Фронтенд: http://localhost:8080
- Бекенд (Swagger): http://localhost:8000/docs

## Деплой на Render

У корені репозиторію є `render.yaml` (Blueprint) — заводить одразу два
сервіси: бекенд (Docker web service) і фронтенд (static site).

1. Заведи репозиторій на GitHub/GitLab і підключи його в Render:
   **New → Blueprint**, вибери репозиторій — Render сам знайде `render.yaml`
   і запропонує створити обидва сервіси.
2. Перевір домени після першого деплою. За замовчуванням Render видає
   `https://<name>.onrender.com`, тож у `render.yaml` заздалегідь прописані:
   - `json-body-generator-api.onrender.com` (бекенд)
   - `json-body-generator-ui.onrender.com` (фронтенд, звідси береться
     `CORS_ORIGINS` бекенда)

   Якщо Render видав інше ім'я (наприклад, обране зайняте) — онови у
   дашборді Render:
   - `CORS_ORIGINS` бекенда — на реальний URL фронтенда;
   - `VITE_API_BASE_URL` фронтенда — на реальний URL бекенда, і зроби
     **Manual Deploy** фронтенда заново (ця змінна вшивається у білд, а не
     читається в рантаймі).
3. Готово: фронтенд — статичні файли на CDN Render, звертається напряму до
   публічного URL бекенда (без проксі), бекенд віддає CORS-заголовки саме
   для цього origin'у.

**Важливо:** на Render немає volume для `backend/schemas/` — папка
запікається в Docker-образ на етапі білда (`COPY schemas ./schemas` у
`backend/Dockerfile`). Це означає, що додавання нової схеми = закомітити
`.json`-файл у git і задеплоїти бекенд заново (на відміну від локального
запуску через `docker-compose`, де файл підхоплюється без ребілду).

## Категорії (таби) та як додати нову схему

Схеми згруповані по категоріях — кожній відповідає окрема папка в
`backend/schemas/` і окремий таб у UI:

- `backend/schemas/procedures/` — таб **Procedures**
- `backend/schemas/registry/` — таб **Registry**
- `backend/schemas/jobber/` — таб **Jobber**
- `backend/schemas/bids/` — таб **Bids**

Список та порядок табів заданий у `backend/app/registry.py` (`CATEGORIES`).

1. Поклади файл `<будь-яка_назва>.json` у потрібну підпапку, напр.
   `backend/schemas/bids/`.
2. Перемкни відповідний таб на фронтенді — нова схема одразу з'явиться в
   дропдауні цього таба, перезбирати бекенд не потрібно (папка примонтована
   як volume).

Ім'я файлу (без `.json`) — це `id` схеми всередині своєї категорії. Поля
`title` та `description` всередині JSON — те, що побачить користувач у
дропдауні.

## Базові ключові слова JSON Schema

- `type`: `object`, `array`, `string`, `integer`, `number`, `boolean`, `null`
- `properties`, `required` — для `object`
- `items`, `minItems`, `maxItems` — для `array`
- `format` (`email`, `date`, `date-time`, `uuid`, `uri`, `hostname`, `ipv4`, `ipv6`, `phone`)
- `enum` — випадковий вибір одного зі значень
- `const` — фіксоване значення
- `example` / `default` — якщо задано, використовується як є (Faker поле не чіпає)
- `minimum` / `maximum` — для чисел
- `minLength` / `maxLength` — для рядків

Якщо для рядкового поля не задано `format`, генератор намагається вгадати
зміст поля за його іменем (`email`, `first_name`, `phone`, `address`, `price`
тощо) і підібрати відповідний Faker-метод. Поля, що виглядають як
кількості/коди (`quantity`, `number`, `code`, `type`, `species`, `object` —
але не `...Name`), заповнюються цифрами, а не текстом.

## Розширені можливості (додані під час роботи з валідатором)

Реальні API часто мають умови, яких немає в "чистому" JSON Schema
(cross-field-залежності, обов'язкова унікальність, значення відносно
поточного часу). Для цього в генератор додано кілька кастомних ключів
схеми — вони не ламають стандартний JSON Schema, а лише розширюють його.

### `relativeHours` — дата відносно "зараз"

Замість випадкової дати з Faker — дата = поточний момент (UTC) + N годин.

```json
"startDate": {
  "type": "string",
  "relativeHours": { "min": 24, "max": 72 }
}
```

Можна задати точне число годин замість діапазону: `"relativeHours": 48`.
Формат виводу — `2026-09-16T10:12:33.456Z` (з мілісекундами та `Z`).

### `if` / `then` / `else` — умовна генерація полів

Підтримується спрощена версія стандартного JSON Schema `if/then/else`:
умова перевіряє вже згенеровані значення полів **того самого об'єкта**
(через `const`/`enum`), і залежно від результату до об'єкта підмішуються
додаткові властивості з `then` або `else`.

```json
"discount": {
  "type": "object",
  "properties": { "discount": { "type": "boolean" } },
  "if": { "properties": { "discount": { "const": true } } },
  "then": {
    "properties": {
      "previousAuctionValue": { "type": "object", "...": "..." },
      "discountPercent": { "type": "number", "minimum": 1, "maximum": 50 }
    }
  }
}
```

Якщо `discount == true` — з'являться `previousAuctionValue` і
`discountPercent`, якщо `false` — цих полів не буде взагалі.

**Обмеження:** умова бачить тільки поля свого рівня вкладеності. Якщо
залежність — між полями різних гілок (наприклад, `tenderAttempts` на
корені і `discount` на корені, але сама умова стосується того, чи можна
взагалі чіпати `discount`) — таке вже не покривається `if/then`, і для
цього є окремі авто-фікси нижче.

### `uniqueBy` — унікальні значення в масиві

Гарантує, що вказане поле в кожному елементі масиву буде іншим (значення
беруться з `enum` цього поля в `items`, перемішуються та роздаються по
елементах без повторів).

```json
"bankAccounts": {
  "type": "array",
  "minItems": 4,
  "maxItems": 4,
  "uniqueBy": "accountType",
  "items": {
    "properties": {
      "accountType": { "enum": ["registrationFee", "guarantee", "other", "payment"] }
    }
  }
}
```

Результат: усі 4 елементи матимуть різний `accountType`, порядок — випадковий.

### `requireValues` — гарантована присутність значень

На відміну від `uniqueBy` (усі різні), гарантує, що конкретні значення
**хоча б раз** зустрінуться в масиві — решта елементів лишаються
випадковими і можуть повторюватись.

```json
"documents": {
  "type": "array",
  "minItems": 2,
  "maxItems": 3,
  "requireValues": { "field": "documentType", "values": ["technicalSpecifications"] },
  "items": { "...": "..." }
}
```

Результат: серед документів завжди буде хоча б один з
`documentType == "technicalSpecifications"`.

### `tokenFromDocuments` — token з єдиного довідника `documents.json`

До цього кожна схема тримала свій `token` як `const`/faker-заглушку окремо
для кожного типу документа — один і той самий `documentType` в різних
схемах міг мати різні (і не завжди валідні) токени. Тепер є єдиний
довідник `backend/schemas/documents.json`:

```json
{
  "notice": "eyJ0eXAiOiJKV1Qi...",
  "illustration": "eyJ0eXAiOiJKV1Qi...",
  "technicalSpecifications": "eyJ0eXAiOiJKV1Qi...",
  "x_itemPlan": "REPLACE_WITH_REAL_TOKEN_FOR_THIS_DOCUMENT_TYPE"
}
```

У схемі, в об'єкті-елементі `documents.items` (поруч з `properties`),
додається ключ:

```json
"documents": {
  "type": "array",
  "items": {
    "type": "object",
    "tokenFromDocuments": "documentType",
    "properties": {
      "token": { "type": "string" },
      "documentType": { "type": "string", "enum": ["notice", "illustration"] }
    }
  }
}
```

Після генерації об'єкта генератор бере значення `documentType` цього ж
об'єкта, шукає його як ключ у `documents.json` і, якщо знайшов — підставляє
відповідний `token`. Якщо запису для такого `documentType` в файлі нема —
`token` лишається тим, що вже згенерувала сама схема (тобто це override,
а не обов'язкова заміна — додавати новий тип документа в `documents.json`
не обов'язково одразу).

Це працює й тоді, коли `documentType` **примусово підмінюється** пізніше —
через `uniqueBy` або `requireValues` (обидва тепер перераховують `token`
одразу після підміни, а не лишають його від початково згенерованого типу).

`documents.json` лежить прямо в `backend/schemas/` (не всередині
`procedures/`/`registry`/`jobber`/`bids`), бо типи документів (`notice`,
`illustration` тощо) повторюються між категоріями. Редагується так само
без перезапуску бекенда — файл читається заново при кожному запиті.

**Важливо:** для частини типів документів (усе, що з нашого чату не
зустрічалось у реальних прикладах — `x_itemPlan`, `x_passport`,
`evaluationCriteria` тощо) у файлі стоїть плейсхолдер
`REPLACE_WITH_REAL_TOKEN_FOR_THIS_DOCUMENT_TYPE` — це свідомо, щоб не
підсовувати структурно правдоподібний, але невалідний токен замість
чесного "тут треба реальне значення". Підставте туди справжні токени, щойно
вони з'являться (наприклад, з відповіді реального API завантаження файлу).

### Автоматичні cross-field фікси

Деякі залежності зустрічаються настільки часто, що для них зроблено окремі
"вбудовані" правила (спрацьовують самі, без додаткових ключів у схемі):

- **`dateFrom` / `dateTill` в одному об'єкті** — `dateTill` перераховується
  так, щоб гарантовано бути пізніше за `dateFrom` (+30…180 днів).
- **`discount.previousAuctionValue.amount` vs кореневий `value.amount`** —
  сума попереднього аукціону завжди більша за поточну вартість лоту.
- **`discount` vs `tenderAttempts`** — якщо `tenderAttempts == 1`, ключ
  `discount` прибирається з результату повністю (валідатор забороняє його
  передавати навіть як `{"discount": false}`).

Якщо в новій схемі з'явиться ще одна подібна залежність — простіше додати
ще один такий фікс у `generator.py`, ніж намагатись виразити її через
стандартний JSON Schema.

### Додаткові Faker-евристики за іменем поля

Крім базового списку (email, ім'я, адреса, телефон тощо) додано:

- `latitude` / `longitude` — реалістичні географічні координати
- `elevation` — випадкова висота (0–500, з дробовою частиною)
- `token` (точна назва поля) — рядок, структурно схожий на JWT
  (`xxx.yyy.zzz`), **не є валідним підписаним токеном** — якщо валідатор
  перевіряє підпис/декодування, такий токен варто замінити на `const` з
  реальним значенням прямо в схемі
- `phone` / `format: phone` — фіксований формат `+380` + 9 цифр
  (`fake.numerify("+380#########")`) замість формату за замовчуванням від
  Faker, який не гарантував конкретний вигляд номера

## Наявні приклади схем

- `create_user.json` — базовий приклад (створення користувача)
- `payment_request.json` — базовий приклад (платіж, вкладені об'єкти й масив)
- `railwayCargo_dutch_fast.json` — реальний кейс: продаж послуг з
  використання вагонів (голландський аукціон), з умовною знижкою,
  прив'язкою `previousAuctionId` до `tenderAttempts`
- `basicSell_english_fast.json` — реальний кейс: продаж нерухомості
  (англійський аукціон), з банківськими рахунками (`uniqueBy`),
  документами (`requireValues`) і геолокацією

## Обмеження v1

- `$ref` / `$defs` не резолвляться — схеми мають бути "плоскими" (без
  посилань на перевикористовувані визначення).
- `if/then/else` — спрощена реалізація, працює лише в межах одного рівня
  вкладеності об'єкта (див. вище).
- Валідація згенерованого JSON проти самої схеми (через `jsonschema`) не
  підключена — генератор і так слідує схемі, але кастомний `pattern` не
  перевіряється.

## Структура проєкту

```
backend/
  app/
    main.py         # FastAPI, ендпоінти (категорії/схеми/генерація)
    generator.py    # JSON Schema -> заповнений JSON (Faker + кастомна логіка)
    registry.py     # категорії + сканування підпапок schemas/<category>/ + documents.json
  schemas/
    documents.json  # довідник documentType -> token (спільний для всіх категорій)
    procedures/     # .json схеми таба Procedures
    registry/       # .json схеми таба Registry
    jobber/         # .json схеми таба Jobber
    bids/           # .json схеми таба Bids
frontend/
  src/
    App.tsx       # таби категорій + дропдаун + кнопка "Сгенерувати" + копіювання
    api.ts        # виклики до бекенду (categories/schemas/generate)
```

## API

- `GET /api/categories` — список табів `[{ id, label }]`.
- `GET /api/schemas/{category_id}` — список схем таба для дропдауна.
- `GET /api/generate/{category_id}/{schema_id}` — згенерований JSON.