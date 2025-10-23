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

## ✅ Все працює!

Якщо ви бачите:
- ✅ Frontend з зеленим індикатором статусу
- ✅ Backend відповідає на `/health`
- ✅ Повідомлення передаються через WebSocket

**Вітаємо! Етап 0 завершено!** 🎉

Переходьте до **Етапу 1** згідно [docs/AgentMind_Plan.md](docs/AgentMind_Plan.md)

