# 🚀 Швидкий старт AgentMind

## Крок 1: Створіть .env файл

```bash
# В кореневій директорії створіть файл .env
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

⚠️ **Замініть** `your_api_key_here` на ваш реальний OpenAI API ключ!

## Крок 2: Запустіть систему

```bash
docker-compose up -d --build
```

Це займе 2-5 хвилин при першому запуску (завантаження образів, встановлення залежностей).

## Крок 3: Перевірте статус

```bash
docker-compose ps
```

Очікуваний вивід:
```
NAME                    STATUS              PORTS
agentmind-backend       Up                  0.0.0.0:8000->8000/tcp
agentmind-falkordb      Up (healthy)        0.0.0.0:6379->6379/tcp
agentmind-frontend      Up                  0.0.0.0:3000->3000/tcp
```

## Крок 4: Відкрийте застосунок

🌐 **Frontend**: http://localhost:3000  
📡 **Backend API**: http://localhost:8000  
💾 **FalkorDB**: localhost:6379

## Крок 5: Тестування

### Frontend (браузер)

1. Відкрийте http://localhost:3000
2. Перевірте індикатор статусу - має бути "Підключено" (зелений)
3. Натисніть "Відправити тестове повідомлення"
4. Перегляньте отримані повідомлення

### Backend (термінал)

```bash
# Health check
curl http://localhost:8000/health

# Broadcast тест
curl -X POST "http://localhost:8000/api/broadcast?message=Test"
```

## 🛑 Зупинка

```bash
# Зупинити без видалення даних
docker-compose down

# Зупинити + видалити дані
docker-compose down -v
```

## 📋 Логи

```bash
# Всі сервіси
docker-compose logs -f

# Тільки backend
docker-compose logs -f backend

# Тільки frontend
docker-compose logs -f frontend
```

## ❗ Типові проблеми

### Порт вже зайнятий

```bash
# Перевірте що порти вільні
netstat -ano | findstr :3000
netstat -ano | findstr :8000
netstat -ano | findstr :6379

# Зупиніть процес або змініть порти в docker-compose.yml
```

### Backend не стартує

```bash
# Перевірте логи
docker-compose logs backend

# Перебудуйте
docker-compose up -d --build backend
```

### Frontend не підключається до WebSocket

1. Перевірте що backend запущений: http://localhost:8000/health
2. Перевірте логи frontend: `docker-compose logs frontend`
3. Перевірте консоль браузера (F12)

## 🧪 Запуск тестів

Перевірте, що система пам'яті працює коректно:

```bash
# Запустити всі тести (84 тести)
docker-compose exec backend python -m pytest tests/ -v

# Тільки unit тести (45 тестів)
docker-compose exec backend python -m pytest tests/test_schema.py tests/test_extraction_models.py tests/test_consolidation_graph.py -v

# Тільки integration тести (39 тестів)
docker-compose exec backend python -m pytest tests/test_bitemporal_ltm.py tests/test_deduplication.py tests/test_consolidation_integration.py -v
```

Очікуваний результат: **84 passed** ✅

## ✅ Все працює!

Якщо ви бачите:
- ✅ Frontend з зеленим індикатором статусу
- ✅ Backend відповідає на `/health`
- ✅ Повідомлення передаються через WebSocket
- ✅ Всі тести проходять (84/84)
- ✅ API консолідації доступний

**Вітаємо! Етапи 0-3 завершено!** 🎉

### Що вже реалізовано:

- ✅ **Етап 0**: Фундамент (Docker, FastAPI, Next.js, WebSocket)
- ✅ **Етап 1**: Ядро пам'яті (MemoryManager, STM)
- ✅ **Етап 2**: Бітемпоральна пам'ять (Statement-based architecture)
- ✅ **Етап 3**: Консолідація (LangGraph, дедуплікація, embeddings)

Переходьте до **Етапу 4** (Гібридний пошук) згідно [docs/AgentMind_Plan.md](docs/AgentMind_Plan.md)

