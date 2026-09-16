import React, { useEffect, useState } from 'react';
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

  return React.createElement(
    'div',
    { className: 'container' },
    React.createElement('h1', null, 'JSON Body Generator'),
    React.createElement(
      'p',
      { className: 'subtitle' },
      'Генератор тела запроса для тестирования REST API',
    ),
    React.createElement(
      'div',
      { className: 'tabs' },
      categories.map((c: CategoryInfo) =>
        React.createElement(
          'button',
          {
            key: c.id,
            className: `tab ${c.id === activeCategory ? 'tab-active' : ''}`,
            onClick: () => setActiveCategory(c.id),
          },
          c.label,
        ),
      ),
    ),
    React.createElement(
      'div',
      { className: 'controls' },
      React.createElement(
        'select',
        {
          value: selectedId,
          onChange: (e: React.ChangeEvent<HTMLSelectElement>) => setSelectedId(e.target.value),
          disabled: schemas.length === 0,
        },
        schemas.length === 0 && React.createElement('option', { value: '' }, 'Нет схем в этой категории'),
        schemas.map((s: SchemaInfo) => React.createElement('option', { key: s.id, value: s.id }, s.title)),
      ),
      React.createElement('button', { onClick: handleGenerate, disabled: !selectedId }, 'Сгенерировать'),
    ),
    selectedSchema?.description &&
      React.createElement('p', { className: 'description' }, selectedSchema.description),
    error && React.createElement('p', { className: 'error' }, error),
    result &&
      React.createElement(
        'div',
        { className: 'result' },
        React.createElement('button', { onClick: handleCopy }, copied ? 'Скопировано!' : 'Скопировать'),
        React.createElement('pre', null, result),
      ),
  );
}

export default App;
