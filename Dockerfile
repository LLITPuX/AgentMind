FROM python:3.11-slim

# Встановлюємо системні залежності
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копіюємо requirements
COPY requirements.txt .

# Встановлюємо Python пакети
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо код
COPY . .

# Створюємо директорії
RUN mkdir -p /app/src /app/data

CMD ["bash"]
