import { useEffect, useState } from 'react';
import { fetchSchemas, generateBody, SchemaInfo } from './api';
import './App.css';

function App() {
  const [schemas, setSchemas] = useState<SchemaInfo[]>([]);
  const [selectedId, setSelectedId] = useState<string>('');
  const [result, setResult] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchSchemas()
      .then((data) => {
        setSchemas(data);
        if (data.length > 0) setSelectedId(data[0].id);
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  const handleGenerate = async () => {
    if (!selectedId) return;
    setError('');
    try {
      const body = await generateBody(selectedId);
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

      <div className="controls">
        <select value={selectedId} onChange={(e) => setSelectedId(e.target.value)}>
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
          <pre>{result}</pre>
          <button onClick={handleCopy}>{copied ? 'Скопировано!' : 'Скопировать'}</button>
        </div>
      )}
    </div>
  );
}

export default App;
