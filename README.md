# GraphRAG Framework - Testing Environment

Тестове середовище для роботи з FalkorDB та розробки GraphRAG системи.

## Швидкий старт

### 1. Запуск контейнерів
```bash
docker-compose up -d --build
```

### 2. Перевірка статусу
```bash
docker-compose ps
```

### 3. Підключення до Python контейнера
```bash
docker exec -it graphrag-dev bash
```

### 4. Запуск тестів
```bash
# Всередині контейнера
python src/test_connection.py
python src/basic_operations.py
python src/speed_test.py
python src/bitemporal_test.py
```

## Структура проекту

- `src/` - Python код
- `data/` - Дані для тестування
- `docker-compose.yml` - Конфігурація Docker
- `requirements.txt` - Python залежності

## Зупинка

```bash
docker-compose down
```

## Зупинка + видалення даних

```bash
docker-compose down -v
```

---

## Результати тестів та приклади

### 1) test_connection.py
Команда:
```bash
python src/test_connection.py
```
Очікуваний вивід:
```text
🔌 Підключення до FalkorDB...
✅ З'єднання успішне: Hello from FalkorDB!

📊 Параметри підключення:
   Host: falkordb
   Port: 6379
   Граф: test_graph

🧹 Тестовий граф видалено
```

### 2) basic_operations.py (CRUD + запити)
Команда:
```bash
python src/basic_operations.py
```
Очікуваний вивід (скорочено):
```text
============================================================
🚀 DEMO: Базові операції з FalkorDB
============================================================

✅ Підключено до графу: demo_graph
🧹 Граф очищено

--- Крок 1: Створення сутностей ---
✅ Створено Person: John Doe
✅ Створено Person: Jane Smith
✅ Створено Company: TechCorp
✅ Створено Company: StartupXYZ

--- Крок 2: Створення зв'язків ---
✅ Створено зв'язок: John Doe -[WORKS_FOR]-> TechCorp
✅ Створено зв'язок: Jane Smith -[WORKS_FOR]-> StartupXYZ
✅ Створено зв'язок: John Doe -[KNOWS]-> Jane Smith

--- Крок 3: Пошук сутностей ---
✅ Знайдено: John Doe
✅ Знайдено: TechCorp

--- Крок 4: Отримання зв'язків ---
📊 Зв'язки для John Doe:
   → KNOWS: Jane Smith
   → WORKS_FOR: TechCorp
📊 Зв'язки для Jane Smith:
   → WORKS_FOR: StartupXYZ

--- Крок 5: Складний запит ---
🔍 Люди в Tech компаніях:
   • John Doe працює в TechCorp

--- Крок 6: Всі вузли ---
📋 Всі вузли в графі:
   • John Doe (Person)
   • Jane Smith (Person)
   • TechCorp (Company)
   • StartupXYZ (Company)

============================================================
✅ Демо завершено успішно!
============================================================
```

### 3) speed_test.py (метрики продуктивності)
Команда:
```bash
python src/speed_test.py
```
Ключові метрики:
- Створення вузла: ≈ 0.42 ms (середнє), min 0.31 ms, max 0.85 ms
- Простий запит: ≈ 0.60 ms (середнє)
- Складний запит: ≈ 0.78 ms (середнє)
- Пакетне створення 100 вузлів: ≈ 5.20 ms (≈ 19 238 вузлів/сек, ~0.03 ms/вузол)

Повний вивід:
```text
✅ Підключено до тестового графу

============================================================
⚡ ТЕСТИ ШВИДКОСТІ FalkorDB
============================================================

🔄 Створення 100 вузлів...
✅ Середній час створення: 0.42 ms
   Min: 0.31 ms | Max: 0.85 ms

🔄 Пакетне створення 100 вузлів...
✅ Час пакетного створення: 5.20 ms
   Швидкість: 19238 вузлів/сек

🔄 Створення 50 зв'язків...
✅ Середній час створення зв'язку: 0.67 ms

🔄 Виконання 100 простих запитів...
✅ Середній час запиту: 0.60 ms

🔄 Виконання 50 складних запитів...
✅ Середній час складного запиту: 0.78 ms

🔄 Обхід графу (глибина 3)...
✅ Час обходу: 0.87 ms
   Глибина 3: 1 шляхів
   Глибина 2: 1 шляхів
   Глибина 1: 1 шляхів

============================================================
📊 ПІДСУМОК
============================================================
Створення вузла:      0.42 ms (середнє)
Пакетне створення:    0.03 ms (на вузол)
Створення зв'язку:    0.67 ms (середнє)
Простий запит:        0.60 ms (середнє)
Складний запит:       0.78 ms (середнє)
Обхід графу:          0.87 ms
============================================================
```

### 4) bitemporal_test.py (bitemporal edges: valid_from/valid_until, created_at/expired_at)
Команда:
```bash
python src/bitemporal_test.py
```
Повний вивід:
```text
✅ Підключено до графу: bitemporal_test

======================================================================
⏰ BITEMPORAL TEST - Зв'язки з часовими мітками
======================================================================

--- Крок 1: Створення сутностей ---

✅ Створено Person: John Smith (Software Engineer)
✅ Створено Company: Apple Inc (Technology)
✅ Створено Company: Microsoft (Technology)

--- Крок 2: John працював в Apple (2020-2023) ---

✅ Створено зв'язок: John Smith -[WORKS_FOR]-> Apple Inc
   valid_from: 2020-01-15T00:00:00
   valid_until: 2023-12-31T00:00:00

--- Крок 3: Перевірка на 2022 рік ---

🔍 Чи працював John Smith в Apple Inc на 2022-06-01T00:00:00?
   ✅ ТАК: з 2020-01-15T00:00:00 до 2023-12-31T00:00:00

--- Крок 4: Перевірка на 2024 рік ---

🔍 Чи працював John Smith в Apple Inc на 2024-10-20T00:00:00?
   ❌ НІ

--- Крок 5: John переходить в Microsoft (2024) ---

✅ Створено зв'язок: John Smith -[WORKS_FOR]-> Microsoft
   valid_from: 2024-01-01T00:00:00
   valid_until: null

--- Крок 6: Повна історія роботи ---

📋 Історія роботи John Smith:
   Microsoft: 2024-01-01T00:00:00 → теперішній час (✅ Актуально)
   Apple Inc: 2020-01-15T00:00:00 → 2023-12-31T00:00:00 (✅ Актуально)

--- Крок 7: Позначаємо старий зв'язок як expired ---

⏰ Застарів зв'язок: John Smith -[WORKS_FOR]-> Apple Inc
   expired_at: 2025-10-20T11:09:10.213365

--- Крок 8: Історія після expire ---

📋 Історія роботи John Smith:
   Microsoft: 2024-01-01T00:00:00 → теперішній час (✅ Актуально)
   Apple Inc: 2020-01-15T00:00:00 → 2025-10-20T11:09:10.213365 (❌ Застаріло)

--- Крок 9: Де John працював у 2022-2024? ---

📊 Результат:
   • Apple Inc: 2020-01-15T00:00:00 → 2025-10-20T11:09:10.213365 (❌ Застарілий)
   • Microsoft: 2024-01-01T00:00:00 → досі (✅ Активний)

======================================================================
✅ Bitemporal тест завершено!
======================================================================
```

### 5) openai_extraction_test.py (OpenAI + FalkorDB інтеграція)
Команда:
```bash
python src/openai_extraction_test.py
```
Повний вивід:
```text
✅ OpenAI підключено
✅ FalkorDB граф: openai_test

======================================================================
🤖 OpenAI + FalkorDB Integration Test
======================================================================

📄 Текст для аналізу:
----------------------------------------------------------------------

        John Smith joined Apple Inc. as a Senior Software Engineer in January 2020. 
        He works on the iOS development team in Cupertino, California.
        In 2023, he was promoted to Tech Lead and now manages a team of 5 engineers.
        Apple Inc. is a technology company founded by Steve Jobs.
        
----------------------------------------------------------------------

--- Крок 1: Витягування сутностей через OpenAI ---

🤖 Відправляю запит до OpenAI...
✅ Витягнуто 5 сутностей
✅ Витягнуто 4 зв'язків

📋 Витягнуті дані:
{
  "entities": [
    {
      "name": "John Smith",
      "type": "Person",
      "properties": {},
      "confidence": 0.95
    },
    {
      "name": "Apple Inc.",
      "type": "Organization",
      "properties": {
        "founded_by": "Steve Jobs"
      },
      "confidence": 0.95
    },
    {
      "name": "Cupertino, California",
      "type": "Location",
      "properties": {},
      "confidence": 0.95
    },
    {
      "name": "iOS development team",
      "type": "Event",
      "properties": {},
      "confidence": 0.9
    },
    {
      "name": "Tech Lead",
      "type": "Event",
      "properties": {},
      "confidence": 0.9
    }
  ],
  "relationships": [
    {
      "source": "John Smith",
      "target": "Apple Inc.",
      "type": "WORKS_FOR",
      "properties": {
        "role": "Senior Software Engineer"
      },
      "temporal": {
        "valid_from": "2020-01-01T00:00:00",
        "valid_until": null
      },
      "confidence": 0.9
    },
    {
      "source": "John Smith",
      "target": "Apple Inc.",
      "type": "WORKS_FOR",
      "properties": {
        "role": "Tech Lead"
      },
      "temporal": {
        "valid_from": "2023-01-01T00:00:00",
        "valid_until": null
      },
      "confidence": 0.9
    },
    {
      "source": "John Smith",
      "target": "iOS development team",
      "type": "WORKS_FOR",
      "properties": {},
      "temporal": {
        "valid_from": "2020-01-01T00:00:00",
        "valid_until": null
      },
      "confidence": 0.9
    },
    {
      "source": "Apple Inc.",
      "target": "Cupertino, California",
      "type": "LOCATED_IN",
      "properties": {},
      "confidence": 0.95
    }
  ]
}

--- Крок 2: Збереження в FalkorDB ---

💾 Збереження в FalkorDB...
  ✅ Person: John Smith
  ✅ Organization: Apple Inc.
  ✅ Location: Cupertino, California
  ✅ Event: iOS development team
  ✅ Event: Tech Lead
  ✅ John Smith -[WORKS_FOR]-> Apple Inc.
  ✅ John Smith -[WORKS_FOR]-> Apple Inc.
  ✅ John Smith -[WORKS_FOR]-> iOS development team
  ✅ Apple Inc. -[LOCATED_IN]-> Cupertino, California
✅ Збережено в граф

--- Крок 3: Запит до графу ---

❓ Запит: Хто де працює?

📊 Результат:
   • John Smith працює в Apple Inc. з 2023-01-01T00:00:00
   • John Smith працює в Apple Inc. з 2020-01-01T00:00:00

--- Крок 4: Всі сутності в графі ---

📊 Всі сутності:
   • John Smith (Person) - confidence: 0.95
   • Apple Inc. (Organization) - confidence: 0.95
   • Cupertino, California (Location) - confidence: 0.95
   • iOS development team (Event) - confidence: 0.9
   • Tech Lead (Event) - confidence: 0.9

======================================================================
✅ Тест завершено!
======================================================================
```

---

## Примітки
- `.env` зберігається локально і не комітиться (див. `.gitignore`).
- `docker-compose.yml` піднімає `falkordb` та дев-контейнер `graphrag-dev`, мапить `./src` і `./data` в `/app`.
- Для інтеграції з OpenAI встановлено `openai==1.12.0` (API ключ очікується в `OPENAI_API_KEY`).
