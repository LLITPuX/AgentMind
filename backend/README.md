# AgentMind Backend

FastAPI бекенд з WebSocket підтримкою для платформи AgentMind.

## Структура

```
backend/
├── src/
│   ├── __init__.py
│   └── main.py          # FastAPI додаток з WebSocket
├── Dockerfile
├── pyproject.toml       # Poetry залежності
└── README.md
```

## Розробка

### Локальний запуск (без Docker)

```bash
cd backend
poetry install
poetry run uvicorn src.main:app --reload
```

### Запуск з Docker

```bash
docker-compose up backend
```

## API Ендпоінти

- `GET /` - Інформація про сервіс
- `GET /health` - Health check
- `WebSocket /ws/graph-updates` - WebSocket для оновлень графу

## WebSocket Protocol

### Клієнт → Сервер
```json
{
  "type": "message",
  "content": "..."
}
```

### Сервер → Клієнт
```json
{
  "type": "connection|graph_update|ping",
  "timestamp": "2024-10-20T12:00:00"
}
```

