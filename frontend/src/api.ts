export interface SchemaInfo {
  id: string;
  title: string;
  description: string;
}

// Локально (docker-compose) VITE_API_URL не задана — запросы идут через
// nginx-прокси на относительный /api. На Render статический сайт не видит
// приватную сеть, поэтому там VITE_API_URL указывает на публичный URL бэкенда.
const BASE_URL = `${import.meta.env.VITE_API_URL ?? ''}/api`;

export async function fetchSchemas(): Promise<SchemaInfo[]> {
  const res = await fetch(`${BASE_URL}/schemas`);
  if (!res.ok) throw new Error('Не удалось загрузить список схем');
  return res.json();
}

export async function generateBody(schemaId: string): Promise<unknown> {
  const res = await fetch(`${BASE_URL}/generate/${schemaId}`);
  if (!res.ok) throw new Error('Не удалось сгенерировать тело запроса');
  return res.json();
}
