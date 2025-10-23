# AgentMind Backend

FastAPI бекенд з WebSocket підтримкою та рефлексивною системою пам'яті для платформи AgentMind.

**Версія**: 0.3.0 (Етап 3 завершено)

## Структура

```
backend/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI додаток з WebSocket
│   ├── memory/              # Модуль пам'яті ✨
│   │   ├── __init__.py
│   │   ├── manager.py       # MemoryManager + бітемпоральні операції
│   │   ├── stm.py           # ShortTermMemoryBuffer
│   │   ├── schema.py        # Pydantic моделі (Етап 2)
│   │   ├── extraction_models.py  # Extraction моделі (Етап 3)
│   │   ├── consolidation.py      # ConsolidationGraph (Етап 3)
│   │   └── embeddings.py         # EmbeddingManager (Етап 3)
│   └── api/                 # API endpoints (Етап 3)
│       ├── __init__.py
│       └── consolidation.py # Consolidation endpoints
├── tests/
│   ├── conftest.py
│   ├── test_memory_manager.py
│   ├── test_stm_buffer.py
│   ├── test_schema.py                    # Unit тести (Етап 2)
│   ├── test_bitemporal_ltm.py            # Integration тести (Етап 2)
│   ├── test_extraction_models.py         # Unit тести (Етап 3)
│   ├── test_consolidation_graph.py       # Unit тести (Етап 3)
│   ├── test_consolidation_integration.py # Integration тести (Етап 3)
│   └── test_deduplication.py             # Integration тести (Етап 3)
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
- `POST /api/consolidate` - Запустити консолідацію STM → LTM (Етап 3)
- `GET /api/consolidation/status` - Статус STM буфера (Етап 3)

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

### Consolidation (Етап 3)

#### ConsolidationGraph (`src/memory/consolidation.py`)

LangGraph state machine для консолідації STM → LTM.

**Workflow:**
1. `fetch_observations` - витягує observations зі STM
2. `extract_entities` - LLM виділення сутностей та зв'язків
3. `deduplicate_entities` - пошук дублікатів (exact match + vector similarity)
4. `save_to_ltm` - збереження ConceptualNodes/Edges/Statements
5. `cleanup_stm` - очищення оброблених спостережень

**Дедуплікація (2-рівнева):**
- Exact match: `label + name + graph_type`
- Vector similarity: cosine similarity > 0.85 (через embeddings)

#### EmbeddingManager (`src/memory/embeddings.py`)

Utility для роботи з векторними embeddings.

**Методи:**
- `generate_embedding(text)` - створити embedding
- `cosine_similarity(vec1, vec2)` - обчислити схожість
- `find_most_similar(query, candidates, threshold)` - знайти найсхожіший

#### Extraction Models (`src/memory/extraction_models.py`)

Pydantic моделі для structured output від LLM:
- `ExtractedEntity` - сутність виділена з тексту
- `ExtractedRelation` - зв'язок між сутностями
- `ExtractionResult` - повний результат екстракції

## 🧪 Тестування

### Запуск всіх тестів

```bash
# Через Docker
docker-compose exec backend python -m pytest tests/ -v

# Локально
poetry run pytest tests/ -v
```

### Тестові категорії

**Unit тести (45 тестів):**
- `test_schema.py` - валідація Pydantic моделей (31)
- `test_extraction_models.py` - extraction models (10)
- `test_consolidation_graph.py` - структура графа (4)

**Integration тести (39 тестів):**
- `test_memory_manager.py` - підключення та базові операції (7)
- `test_stm_buffer.py` - робота з STM (12)
- `test_bitemporal_ltm.py` - бітемпоральні операції (10)
- `test_deduplication.py` - дедуплікація exact + vector (6)
- `test_consolidation_integration.py` - консолідація workflow (4)

**Всього: 84 тести, всі проходять ✅**

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

# Консолідація STM → LTM
from src.memory import ConsolidationGraph, ShortTermMemoryBuffer, Observation

# Додати спостереження в STM
stm = ShortTermMemoryBuffer()
stm.add(Observation(
    content="Alice likes Python programming",
    timestamp=datetime.now(),
    metadata={"source": "chat"}
))

# Створити консолідацію
consolidation = ConsolidationGraph(
    stm_buffer=stm,
    memory_manager=manager
)

# Запустити (потребує OPENAI_API_KEY)
result = consolidation.run()
print(f"Processed: {result['observations_processed']}")
print(f"Entities: {result['entities_extracted']}")
print(f"Nodes created: {result['nodes_created']}")
```

## 📚 Додаткова документація

- **Архітектура пам'яті**: [../docs/Reflexive_Memory_Architecture.md](../docs/Reflexive_Memory_Architecture.md)
- **План розробки**: [../docs/AgentMind_Plan.md](../docs/AgentMind_Plan.md)

