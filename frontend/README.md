# AgentMind Frontend

Next.js фронтенд з WebSocket підключенням для платформи AgentMind.

## Структура

```
frontend/
├── src/
│   └── app/
│       ├── layout.tsx       # Базовий layout
│       ├── page.tsx         # Головна сторінка з WebSocket
│       ├── page.module.css  # Стилі
│       └── globals.css      # Глобальні стилі
├── public/
├── Dockerfile
├── package.json
├── next.config.js
└── tsconfig.json
```

## Розробка

### Локальний запуск (без Docker)

```bash
cd frontend
npm install
npm run dev
```

### Запуск з Docker

```bash
docker-compose up frontend
```

## Функції

- ✅ WebSocket підключення до бекенду
- ✅ Індикатор статусу з'єднання
- ✅ Відображення повідомлень в реальному часі
- ✅ Адаптивний дизайн
- ✅ TypeScript

## Налаштування

Змінні середовища (`.env.local`):
```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

