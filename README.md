# AgentMind

AgentMind is an async-first AI agent platform consisting of a FastAPI backend and a Vite/React frontend.

> Frontend UX is being modelled after [`LLITPuX/Dynamic-Memory-AI-Agent`](https://github.com/LLITPuX/Dynamic-Memory-AI-Agent). The repository is cloned locally under `Dynamic-Memory-AI-Agent-ref/` for reference only; no code is copied verbatim.

## Quick start

1. Copy environment variables:
   ```powershell
   Copy-Item .env.example .env
   ```
   Update secrets before running services.

2. Launch the stack with Docker Compose:
   ```powershell
   docker compose up --build
   ```

Services:

- Backend available at `http://localhost:8000`
- Frontend available at `http://localhost:5173`
- PostgreSQL exposed on `localhost:5432`
- Redis exposed on `localhost:6379`

## Backend (FastAPI)

- Located in `backend`
- Async SQLAlchemy with PostgreSQL
- Redis ready for caching/state persistence
- Tests live in `backend/tests`
- Run locally:
  ```powershell
  cd backend
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -e .[dev]
  uvicorn app.main:app --reload
  ```

## Frontend (React + Vite + TypeScript)

- Located in `frontend`
- Strict TypeScript configuration with Vite tooling
- API base URL configured through `VITE_API_BASE_URL`
- Chat UI, analysis dashboard, speech-to-text input, and prompt/schema settings mirror the UX of the reference project
- Run locally:
  ```powershell
  cd frontend
  corepack enable
  pnpm install
  pnpm dev
  ```

## Tooling

- Docker Compose for orchestrating services
- Ruff & mypy configured for backend linting
- ESLint configured via `standard-with-typescript` preset

## Security notice

Do not commit secrets. Always update `.env` locally and keep `.env.example` in sync with non-sensitive defaults.

