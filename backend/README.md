# AgentMind Backend

FastAPI бекенд з WebSocket підтримкою та рефлексивною системою пам'яті для платформи AgentMind.

**Версія**: 0.4.0 (Етап 4 завершено)

## Структура

```
backend/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI додаток з WebSocket
│   ├── memory/              # Модуль пам'яті ✨
│   │   ├── __init__.py
│   │   ├── manager.py       # MemoryManager + vector search (Етап 4)
│   │   ├── stm.py           # ShortTermMemoryBuffer
│   │   ├── schema.py        # Pydantic моделі (Етап 2)
│   │   ├── extraction_models.py  # Extraction моделі (Етап 3)
│   │   ├── consolidation.py      # ConsolidationGraph + embeddings (Етап 3-4)
│   │   ├── embeddings.py         # EmbeddingManager (Етап 3)
│   │   └── retrieval.py          # RetrievalGraph (Етап 4)
│   └── api/                 # API endpoints (Етап 3-4)
│       ├── __init__.py
│       ├── consolidation.py # Consolidation endpoints (Етап 3)
│       └── retrieval.py     # Search endpoints (Етап 4)
├── tests/
│   ├── conftest.py
│   ├── test_memory_manager.py
│   ├── test_stm_buffer.py
│   ├── test_schema.py                    # Unit тести (Етап 2)
│   ├── test_bitemporal_ltm.py            # Integration тести (Етап 2)
│   ├── test_extraction_models.py         # Unit тести (Етап 3)
│   ├── test_consolidation_graph.py       # Unit тести (Етап 3)
│   ├── test_consolidation_integration.py # Integration тести (Етап 3)
│   ├── test_deduplication.py             # Integration тести (Етап 3)
│   ├── test_vector_search.py             # Unit тести (Етап 4)
│   ├── test_retrieval_graph.py           # Unit тести (Етап 4)
│   ├── test_retrieval_api.py             # Integration тести (Етап 4)
│   └── test_retrieval_integration.py     # E2E тести (Етап 4)
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
- `POST /api/search` - Гібридний пошук в пам'яті (Етап 4)
- `GET /api/search/status` - Статус системи пошуку (Етап 4)

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

### Retrieval (Етап 4)

#### RetrievalGraph (`src/memory/retrieval.py`)

LangGraph state machine для гібридного пошуку в LTM.

**Workflow:**
1. `vector_search` - пошук схожих вузлів через embeddings
2. `graph_expansion` - розширення на 1-hop сусідів та statements
3. `response_synthesis` - генерація текстової відповіді через LLM

**Гібридний пошук:**
- Vector similarity search (cosine similarity з FalkorDB vector index)
- Graph traversal для контексту (neighbors + statements)
- LLM synthesis з атрибуцією джерел

**Методи:**
- `search(query, graph_types)` - виконати пошук
- Підтримка фільтрації по graph_type (internal/external)

#### Vector Search (`src/memory/manager.py`)

Розширення MemoryManager для векторного пошуку:

**Методи:**
- `store_node_embedding(node_id, embedding)` - зберегти embedding для вузла
- `vector_search_nodes(query_embedding, top_k, graph_type)` - пошук схожих вузлів
- Використання FalkorDB vector indices з cosine similarity

## 🧪 Тестування

### Запуск всіх тестів

```bash
# Через Docker
docker-compose exec backend python -m pytest tests/ -v

# Локально
poetry run pytest tests/ -v
```

### Тестові категорії

**Unit тести (60+ тестів):**
- `test_schema.py` - валідація Pydantic моделей (31)
- `test_extraction_models.py` - extraction models (10)
- `test_consolidation_graph.py` - структура графа (4)
- `test_retrieval_graph.py` - retrieval graph structure (7)
- `test_retrieval_api.py` - API endpoint validation (8)

**Integration тести (50+ тестів):**
- `test_memory_manager.py` - підключення та базові операції (7)
- `test_stm_buffer.py` - робота з STM (12)
- `test_bitemporal_ltm.py` - бітемпоральні операції (10)
- `test_deduplication.py` - дедуплікація exact + vector (6)
- `test_consolidation_integration.py` - консолідація з embeddings (6)
- `test_vector_search.py` - vector search операції (6)
- `test_retrieval_integration.py` - E2E retrieval workflow (6)

**Всього: 112 тести**
- **101 стабільних** (unit + integration) - ✅ проходять завжди
- **11 E2E тестів** (з LLM calls) - ✅ проходять окремо

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

# Гібридний пошук (Етап 4)
from src.memory import RetrievalGraph

# Створити retrieval graph
retrieval = RetrievalGraph(
    memory_manager=manager,
    top_k=5  # Top 5 results
)

# Пошук по всіх графах
result = retrieval.search("What does Alice like?")
print(f"Response: {result['response']}")
print(f"Sources: {result['metadata']['sources_count']}")

# Пошук тільки в Internal графі
result = retrieval.search(
    "What are my preferences?",
    graph_types=[GraphType.INTERNAL]
)
print(f"Response: {result['response']}")
```

## 📚 Додаткова документація

- **Архітектура пам'яті**: [../docs/Reflexive_Memory_Architecture.md](../docs/Reflexive_Memory_Architecture.md)
- **План розробки**: [../docs/AgentMind_Plan.md](../docs/AgentMind_Plan.md)

