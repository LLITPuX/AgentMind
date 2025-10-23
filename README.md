# 🧠 AgentMind Platform

Комплексна платформа для управління пам'яттю самонавчальних ШІ-агентів.

**Версія**: 0.4.0 (Етап 4 - Гібридний пошук)

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

**Основні:**
- `GET /` - Інформація про сервіс
- `GET /health` - Health check
- `WebSocket /ws/graph-updates` - WebSocket для оновлень графу в реальному часі
- `POST /api/broadcast` - Тестовий broadcast

**Консолідація (Етап 3):**
- `POST /api/consolidate` - Запустити консолідацію STM → LTM
- `GET /api/consolidation/status` - Статус STM буфера

**Гібридний пошук (Етап 4):**
- `POST /api/search` - Пошук в пам'яті (векторний + графовий)
- `GET /api/search/status` - Статус системи пошуку

### Приклади

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Broadcast повідомлення (тест WebSocket)
```bash
curl -X POST http://localhost:8000/api/broadcast?message=Hello
```

#### Консолідація пам'яті (Етап 3)
```bash
# Перевірити статус STM
curl http://localhost:8000/api/consolidation/status

# Запустити консолідацію
curl -X POST http://localhost:8000/api/consolidate
```

#### Пошук в пам'яті (Етап 4)
```bash
# Пошук по всіх графах
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "What does Alice like?"}'

# Пошук тільки в Internal графі
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "What are my preferences?", "graph_types": ["internal"]}'

# Статус системи пошуку
curl http://localhost:8000/api/search/status
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
│   │   ├── main.py              # FastAPI додаток
│   │   ├── memory/              # Модуль пам'яті (Етап 1-4)
│   │   │   ├── __init__.py
│   │   │   ├── manager.py       # MemoryManager + vector search (Етап 4)
│   │   │   ├── stm.py           # ShortTermMemoryBuffer
│   │   │   ├── schema.py        # Pydantic моделі (Етап 2)
│   │   │   ├── extraction_models.py  # Extraction моделі (Етап 3)
│   │   │   ├── consolidation.py      # ConsolidationGraph + embeddings (Етап 3-4)
│   │   │   ├── embeddings.py         # EmbeddingManager (Етап 3)
│   │   │   └── retrieval.py          # RetrievalGraph (Етап 4)
│   │   └── api/                 # API endpoints (Етап 3-4)
│   │       ├── __init__.py
│   │       ├── consolidation.py # Consolidation endpoints (Етап 3)
│   │       └── retrieval.py     # Search endpoints (Етап 4)
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_memory_manager.py
│   │   ├── test_stm_buffer.py
│   │   ├── test_schema.py                    # Етап 2
│   │   ├── test_bitemporal_ltm.py            # Етап 2
│   │   ├── test_extraction_models.py         # Етап 3
│   │   ├── test_consolidation_graph.py       # Етап 3
│   │   ├── test_consolidation_integration.py # Етап 3
│   │   ├── test_deduplication.py             # Етап 3
│   │   ├── test_vector_search.py             # NEW in Етап 4
│   │   ├── test_retrieval_graph.py           # NEW in Етап 4
│   │   ├── test_retrieval_api.py             # NEW in Етап 4
│   │   └── test_retrieval_integration.py     # NEW in Етап 4
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

### ✅ Етап 3: Консолідація та дедуплікація (ЗАВЕРШЕНО)

- [x] LangGraph ConsolidationGraph для STM → LTM
- [x] Extraction models (ExtractedEntity, ExtractedRelation)
- [x] LLM-based entity extraction з structured output
- [x] 2-рівнева дедуплікація (exact match + vector similarity)
- [x] EmbeddingManager для семантичної схожості
- [x] FastAPI ендпоінти (/api/consolidate, /api/consolidation/status)
- [x] 24 нових тести (unit + integration)
- [x] **84/84 тести пройшли успішно** ✨

### ✅ Етап 4: Гібридний пошук (ЗАВЕРШЕНО)

- [x] Vector search методи в MemoryManager (store_node_embedding, vector_search_nodes)
- [x] FalkorDB векторні індекси для ConceptualNode.embedding
- [x] Модифікація ConsolidationGraph для збереження embeddings
- [x] RetrievalGraph з LangGraph state machine
- [x] Вузли: vector_search, graph_expansion, response_synthesis
- [x] Гібридний пошук (векторний + графовий) по обох графах
- [x] FastAPI ендпоінт POST /api/search з фільтрацією по graph_type
- [x] 20+ нових тестів (unit + integration + E2E)
- [x] **Всі тести пройшли успішно** ✨

### 🔄 Наступні етапи

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

**Версія**: 0.4.0  
**Дата**: 23.10.2025  
**Статус**: Етап 4 завершено ✅ (112 тестів: 101 unit+integration + 11 E2E)
