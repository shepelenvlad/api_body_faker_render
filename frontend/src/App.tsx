import { useEffect, useState } from 'react';
import { CategoryInfo, fetchCategories, fetchSchemas, generateBody, SchemaInfo } from './api';
import './App.css';

function App() {
  const [categories, setCategories] = useState<CategoryInfo[]>([]);
  const [activeCategory, setActiveCategory] = useState<string>('');

  const [schemas, setSchemas] = useState<SchemaInfo[]>([]);
  const [selectedId, setSelectedId] = useState<string>('');
  const [result, setResult] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [copied, setCopied] = useState(false);

  // Загружаем список табов один раз при старте
  useEffect(() => {
    fetchCategories()
      .then((data) => {
        setCategories(data);
        if (data.length > 0) setActiveCategory(data[0].id);
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  // При смене активного таба — подтягиваем дропдаун со схемами именно этой категории
  useEffect(() => {
    if (!activeCategory) return;
    setError('');
    setResult('');
    setSelectedId('');
    fetchSchemas(activeCategory)
      .then((data) => {
        setSchemas(data);
        setSelectedId(data.length > 0 ? data[0].id : '');
      })
      .catch((e: Error) => setError(e.message));
  }, [activeCategory]);

  const handleGenerate = async () => {
    if (!selectedId || !activeCategory) return;
    setError('');
    try {
      const body = await generateBody(activeCategory, selectedId);
      setResult(JSON.stringify(body, null, 2));
      setCopied(false);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(result);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const selectedSchema = schemas.find((s) => s.id === selectedId);

  return (
    <div className="container">
      <h1>JSON Body Generator</h1>
      <p className="subtitle">Генератор тела запроса для тестирования REST API</p>

      <div className="tabs">
        {categories.map((c) => (
          <button
            key={c.id}
            className={`tab ${c.id === activeCategory ? 'tab-active' : ''}`}
            onClick={() => setActiveCategory(c.id)}
          >
            {c.label}
          </button>
        ))}
      </div>

      <div className="controls">
        <select
          value={selectedId}
          onChange={(e) => setSelectedId(e.target.value)}
          disabled={schemas.length === 0}
        >
          {schemas.length === 0 && <option value="">Нет схем в этой категории</option>}
          {schemas.map((s) => (
            <option key={s.id} value={s.id}>
              {s.title}
            </option>
          ))}
        </select>
        <button onClick={handleGenerate} disabled={!selectedId}>
          Сгенерировать
        </button>
      </div>

      {selectedSchema?.description && (
        <p className="description">{selectedSchema.description}</p>
      )}

      {error && <p className="error">{error}</p>}

      {result && (
        <div className="result">
          <button onClick={handleCopy}>{copied ? 'Скопировано!' : 'Скопировать'}</button>
          <pre>{result}</pre>
        </div>
      )}
    </div>
  );
}

export default App;
