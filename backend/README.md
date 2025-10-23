# AgentMind Backend

FastAPI бекенд з WebSocket підтримкою та рефлексивною системою пам'яті для платформи AgentMind.

**Версія**: 0.2.0 (Етап 2 завершено)

## Структура

```
backend/
├── src/
│   ├── __init__.py
│   ├── main.py          # FastAPI додаток з WebSocket
│   └── memory/          # Модуль пам'яті ✨
│       ├── __init__.py
│       ├── manager.py   # MemoryManager + бітемпоральні операції
│       ├── stm.py       # ShortTermMemoryBuffer
│       └── schema.py    # Pydantic моделі (Етап 2)
├── tests/
│   ├── conftest.py
│   ├── test_memory_manager.py
│   ├── test_stm_buffer.py
│   ├── test_schema.py           # Unit тести моделей (Етап 2)
│   └── test_bitemporal_ltm.py   # Integration тести (Етап 2)
├── Dockerfile
├── pyproject.toml       # Poetry залежності
├── pytest.ini
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

## 🧠 Модуль пам'яті (Етап 1-2)

### MemoryManager (`src/memory/manager.py`)

Головний клас для роботи з FalkorDB.

**Базові операції:**
- `get_graph(name)` - отримання графу
- `clear_graph(name)` - очищення графу
- `is_connected()` - перевірка з'єднання

**Бітемпоральні операції (Етап 2):**
- `create_conceptual_node(node)` - створення вузла з бітемпоральністю
- `create_conceptual_edge(edge)` - створення ребра з бітемпоральністю
- `create_statement(stmt)` - створення твердження (Statement)
- `expire_node(node_id, tx_time_to)` - застарівання вузла
- `expire_edge(edge_id, tx_time_to)` - застарівання ребра
- `query_nodes_at_time(label, valid_time, tx_time, graph_type)` - бітемпоральний запит
- `get_statements_for_concept(conceptual_id)` - отримання всіх тверджень про сутність

### ShortTermMemoryBuffer (`src/memory/stm.py`)

FIFO буфер для короткострокової пам'яті на базі Redis.

**Операції:**
- `add(observation)` - додати спостереження
- `get_all()` - отримати всі спостереження
- `get_recent(n)` - отримати N останніх
- `clear()` - очистити буфер

### Pydantic моделі (`src/memory/schema.py`)

**Базові моделі:**
- `GraphType` - enum: `internal` / `external`
- `SourceType` - типи джерел: `user`, `agent_inference`, `system_config`, etc.
- `Source` - атрибуція джерела (name, type, reliability_score)
- `BiTemporalMixin` - міксін з бітемпоральними полями

**Концептуальні сутності:**
- `ConceptualNode` - вузол графа знань
- `ConceptualEdge` - ребро графа знань
- `Statement` - твердження про сутність з атрибуцією джерела

**Валідація:**
- `valid_from < valid_until`
- `tx_time_from <= tx_time_to`
- `confidence ∈ [0.0, 1.0]`
- `reliability_score ∈ [0.0, 1.0]`

## 🧪 Тестування

### Запуск всіх тестів

```bash
# Через Docker
docker-compose exec backend python -m pytest tests/ -v

# Локально
poetry run pytest tests/ -v
```

### Тестові категорії

**Unit тести (31 тест):**
- `test_schema.py` - валідація Pydantic моделей

**Integration тести (29 тестів):**
- `test_memory_manager.py` - підключення та базові операції
- `test_stm_buffer.py` - робота з STM
- `test_bitemporal_ltm.py` - бітемпоральні операції

**Всього: 60 тестів, всі проходять ✅**

### Приклад використання

```python
from datetime import datetime
from src.memory import MemoryManager, ConceptualNode, GraphType, Source, Statement, SourceType

# Підключення
manager = MemoryManager(host="localhost", port=6379)

# Створення вузла
node = ConceptualNode(
    label="Person",
    name="Alice",
    graph_type=GraphType.INTERNAL,
    valid_from=datetime(2025, 1, 1),
    valid_until=datetime(2025, 12, 31)
)

node_id = manager.create_conceptual_node(node)

# Створення твердження про вузол
source = Source(name="User_001", type=SourceType.USER)
stmt = Statement(
    asserts_about_conceptual_id=node_id,
    source=source,
    attributes={"likes": "Python"},
    confidence=0.9
)

stmt_id = manager.create_statement(stmt)

# Бітемпоральний запит
nodes = manager.query_nodes_at_time(
    label="Person",
    valid_time=datetime(2025, 6, 1),
    tx_time=datetime.now(),
    graph_type=GraphType.INTERNAL
)
```

## 📚 Додаткова документація

- **Архітектура пам'яті**: [../docs/Reflexive_Memory_Architecture.md](../docs/Reflexive_Memory_Architecture.md)
- **План розробки**: [../docs/AgentMind_Plan.md](../docs/AgentMind_Plan.md)

