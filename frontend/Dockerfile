FROM node:20-alpine

WORKDIR /app

# Копіюємо package.json та встановлюємо залежності
COPY package.json package-lock.json* ./
RUN npm install

# Копіюємо код
COPY . .

# Expose port
EXPOSE 3000

# Запускаємо в dev режимі
CMD ["npm", "run", "dev"]

