# 🧠 AgentMind Platform

Комплексна платформа для управління пам'яттю самонавчальних ШІ-агентів.

**Версія**: 0.2.0 (Етап 2 - Бітемпоральна пам'ять)

## 📋 Архітектура

```
AgentMind/
├── backend/          # FastAPI + LangGraph + FalkorDB
├── frontend/         # Next.js + WebSocket
├── docs/            # Документація
└── docker-compose.yml
```

### Компоненти

- **Backend**: FastAPI з WebSocket підтримкою для оркестрації процесів мислення
- **Frontend**: Next.js SPA з реал-тайм візуалізацією графу пам'яті
- **Database**: FalkorDB для графової та векторної пам'яті
- **Orchestration**: LangGraph для керування процесами консолідації та пошуку

## 🚀 Швидкий старт

### Передумови

- Docker & Docker Compose
- OpenAI API ключ

### 1. Налаштування

Створіть `.env` файл в кореневій директорії:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. Запуск всіх сервісів

```bash
docker-compose up -d --build
```

Це запустить:
- **FalkorDB**: `localhost:6379`
- **Backend**: `http://localhost:8000`
- **Frontend**: `http://localhost:3000`

### 3. Перевірка статусу

```bash
docker-compose ps
```

Всі сервіси повинні бути в стані `Up`.

### 4. Відкрийте застосунок

Перейдіть до **http://localhost:3000** у браузері.

Ви побачите:
- ✅ Статус WebSocket з'єднання
- 📊 Реал-тайм повідомлення від бекенду
- 🧪 Кнопку для відправки тестових повідомлень

## 📡 API Ендпоінти

### Backend (http://localhost:8000)

- `GET /` - Інформація про сервіс
- `GET /health` - Health check
- `WebSocket /ws/graph-updates` - WebSocket для оновлень графу в реальному часі
- `POST /api/broadcast` - Тестовий broadcast

### Приклади

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Broadcast повідомлення (тест WebSocket)
```bash
curl -X POST http://localhost:8000/api/broadcast?message=Hello
```

## 🧪 Тестування WebSocket

1. Відкрийте frontend: http://localhost:3000
2. Перевірте що статус "Підключено" (зелений індикатор)
3. Натисніть "Відправити тестове повідомлення"
4. Ви побачите відповідь від бекенду в списку повідомлень

## 🛠️ Розробка

### Backend

```bash
cd backend
poetry install
poetry run uvicorn src.main:app --reload
```

Детальніше: [backend/README.md](backend/README.md)

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Детальніше: [frontend/README.md](frontend/README.md)

## 📂 Структура проєкту

```
AgentMind/
├── backend/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI додаток
│   │   └── memory/           # Модуль пам'яті (Етап 1-2)
│   │       ├── __init__.py
│   │       ├── manager.py    # MemoryManager + бітемпоральні операції
│   │       ├── stm.py        # ShortTermMemoryBuffer
│   │       └── schema.py     # Pydantic моделі (NEW in Етап 2)
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_memory_manager.py
│   │   ├── test_stm_buffer.py
│   │   ├── test_schema.py             # NEW in Етап 2
│   │   └── test_bitemporal_ltm.py     # NEW in Етап 2
│   ├── Dockerfile
│   ├── pyproject.toml        # Poetry залежності
│   ├── pytest.ini
│   └── README.md
│
├── frontend/
│   ├── src/
│   │   └── app/
│   │       ├── page.tsx      # Головна сторінка
│   │       ├── layout.tsx
│   │       └── globals.css
│   ├── Dockerfile
│   ├── package.json
│   └── README.md
│
├── docs/
│   ├── AgentMind_Plan.md                      # Повний план розробки
│   └── Reflexive_Memory_Architecture.md       # NEW - Архітектурний документ
│
├── docker-compose.yml        # Orchestration
├── .gitignore
└── README.md                 # Цей файл
```

## 📖 Документація

- **План розробки**: [docs/AgentMind_Plan.md](docs/AgentMind_Plan.md)
- **Архітектура пам'яті**: [docs/Reflexive_Memory_Architecture.md](docs/Reflexive_Memory_Architecture.md)
- **Backend API**: [backend/README.md](backend/README.md)
- **Frontend**: [frontend/README.md](frontend/README.md)
- **Швидкий старт**: [QUICKSTART.md](QUICKSTART.md)

## 🗺️ Поточний прогрес

### ✅ Етап 0: Фундамент (ЗАВЕРШЕНО)

- [x] Структура директорій
- [x] docker-compose.yml для 3 сервісів
- [x] Backend: FastAPI з WebSocket
- [x] Frontend: Next.js з WebSocket клієнтом
- [x] Перший запуск і тестування

### ✅ Етап 1: Ядро пам'яті (ЗАВЕРШЕНО)

- [x] MemoryManager для підключення до FalkorDB
- [x] ShortTermMemoryBuffer (STM) з Redis-like операціями
- [x] Unit та integration тести
- [x] TDD підхід

### ✅ Етап 2: Довгострокова пам'ять + бітемпоральність (ЗАВЕРШЕНО)

- [x] Pydantic моделі з валідацією (Source, ConceptualNode, ConceptualEdge, Statement)
- [x] BiTemporalMixin з valid_time та transaction_time
- [x] GraphType для поділу на Internal/External графи
- [x] Методи MemoryManager для бітемпоральних операцій
- [x] 31 unit тестів + 10 integration тестів
- [x] Реалізація multi-source truth (Statement-based architecture)
- [x] **60/60 тестів пройшли успішно** ✨

### 🔄 Наступні етапи

- **Етап 3**: Консолідація та дедуплікація (LangGraph)
- **Етап 4**: Гібридний пошук (векторний + графовий)
- **Етап 5**: Інтеграція та візуалізація

## 🔧 Корисні команди

### Docker

```bash
# Запуск всіх сервісів
docker-compose up -d

# Зупинка
docker-compose down

# Зупинка + видалення даних
docker-compose down -v

# Логи конкретного сервісу
docker-compose logs -f backend
docker-compose logs -f frontend

# Перебудувати і запустити
docker-compose up -d --build

# Доступ до контейнера
docker exec -it agentmind-backend bash
```

### Діагностика

```bash
# Перевірка здоров'я backend
curl http://localhost:8000/health

# Перевірка FalkorDB
docker exec -it agentmind-falkordb redis-cli ping
```

## 🧹 Очищення

Видалити всі дані та перезапустити:

```bash
docker-compose down -v
docker-compose up -d --build
```

## 🤝 Методологія розробки

Проєкт розробляється за методологією **TDD (Test-Driven Development)**:

1. Спочатку пишуться тести
2. Потім реалізується функціонал
3. Код рефакториться

Кожен новий функціонал покривається тестами перед реалізацією.

## 📝 Примітки

- `.env` файл не комітиться в git (див. `.gitignore`)
- Для production використовуйте `.env.production`
- FalkorDB дані зберігаються в Docker volume `falkordb_data`

## 📄 Ліцензія

MIT

---

**Версія**: 0.2.0  
**Дата**: 23.10.2025  
**Статус**: Етап 2 завершено ✅ (60/60 тестів пройшли)
