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

export async function fetchCategories(): Promise<CategoryInfo[]> {
  const res = await fetch(`${BASE_URL}/categories`);
  if (!res.ok) throw new Error('Не удалось загрузить список категорий');
  return res.json();
}

export async function fetchSchemas(categoryId: string): Promise<SchemaInfo[]> {
  const res = await fetch(`${BASE_URL}/schemas/${categoryId}`);
  if (!res.ok) throw new Error('Не удалось загрузить список схем');
  return res.json();
}

export async function generateBody(categoryId: string, schemaId: string): Promise<unknown> {
  const res = await fetch(`${BASE_URL}/generate/${categoryId}/${schemaId}`);
  if (!res.ok) throw new Error('Не удалось сгенерировать тело запроса');
  return res.json();
}
