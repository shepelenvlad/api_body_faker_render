export interface CategoryInfo {
  id: string;
  label: string;
}

export interface SchemaInfo {
  id: string;
  title: string;
  description: string;
}

// На Render фронтенд деплоится как статический сайт и обращается к бекенду
// по его публичному URL (VITE_API_BASE_URL, задаётся на этапе билда).
// Локально (vite dev / docker-compose) переменная не задана — используется
// относительный путь /api, который проксируется vite/nginx.
const API_ORIGIN = import.meta.env.VITE_API_BASE_URL ?? '';
const BASE_URL = `${API_ORIGIN}/api`;

async function parseJsonOrThrow<T>(res: Response, fallbackMessage: string): Promise<T> {
  if (!res.ok) throw new Error(fallbackMessage);
  const contentType = res.headers.get('content-type') ?? '';
  if (!contentType.includes('application/json')) {
    // Типовая причина: VITE_API_BASE_URL не применился при билде фронтенда,
    // и запрос ушёл на относительный /api — SPA-рерайт молча вернул
    // index.html вместо JSON от бекенда.
    throw new Error(
      `Бекенд вернул не JSON (похоже, запрос ушёл не туда: ${res.url}). ` +
        `Проверь VITE_API_BASE_URL на фронтенде и что бекенд задеплоен.`
    );
  }
  return res.json();
}

export async function fetchCategories(): Promise<CategoryInfo[]> {
  const res = await fetch(`${BASE_URL}/categories`);
  return parseJsonOrThrow(res, 'Не удалось загрузить список категорий');
}

export async function fetchSchemas(categoryId: string): Promise<SchemaInfo[]> {
  const res = await fetch(`${BASE_URL}/schemas/${categoryId}`);
  return parseJsonOrThrow(res, 'Не удалось загрузить список схем');
}

export async function generateBody(categoryId: string, schemaId: string): Promise<unknown> {
  const res = await fetch(`${BASE_URL}/generate/${categoryId}/${schemaId}`);
  return parseJsonOrThrow(res, 'Не удалось сгенерировать тело запроса');
}
