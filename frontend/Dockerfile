# syntax=docker/dockerfile:1.6

FROM node:20-alpine AS base

WORKDIR /app

COPY package.json pnpm-lock.yaml* ./

RUN corepack enable \
    && pnpm install --frozen-lockfile --ignore-scripts || pnpm install --ignore-scripts

COPY . .

CMD ["pnpm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]


