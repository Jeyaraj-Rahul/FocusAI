# DocuGen AI

Production-level starter architecture for a full-stack AI-powered document automation platform.

This repository contains the project structure plus the first implemented module: JWT authentication.

## Tech Stack

- Frontend: React, Vite, Tailwind CSS
- Backend: Python, FastAPI
- Database: SQLite for local development, PostgreSQL-ready for Docker/production
- AI integration: OpenAI API-ready service layer
- Documents: `python-docx`, `docxtpl`, `reportlab`, `mammoth`, `pypandoc`
- Auth architecture: JWT-ready security module
- Deployment: Docker and Docker Compose

## Folder Structure

```text
docugen-ai/
  backend/
    app/
      api/
        routes/
      controllers/
      core/
      db/
      middleware/
      models/
      schemas/
      services/
      utils/
      main.py
    storage/
      generated/
      uploads/
    .env.example
    Dockerfile
    requirements.txt
  frontend/
    public/
    src/
      api/
      assets/
      components/
        common/
        layout/
        upload/
      context/
      hooks/
      lib/
      pages/
      services/
      styles/
      utils/
      main.jsx
    .env.example
    Dockerfile
    package.json
  docs/
    API.md
  docker-compose.yml
  README.md
```

## Local Setup

### Backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

### Docker

```bash
docker compose up --build
```

Docker Compose overrides `DATABASE_URL` to use the bundled PostgreSQL service. Local development defaults to SQLite so the API can run without starting Docker.

## Environment Files

- `backend/.env.example`: backend API, JWT, database, OpenAI, CORS, and storage settings
- `frontend/.env.example`: frontend API base URL

## Development Notes

- JWT authentication is implemented in `backend/app/api/routes/auth.py`, `backend/app/core/security.py`, and `frontend/src/context/AuthContext.jsx`.
- OpenAI writing assistance is implemented in `backend/app/services/openai_service.py` and exposed through `backend/app/api/routes/ai.py`.
- Add FastAPI routes in `backend/app/api/routes`.
- Keep business orchestration in `backend/app/controllers`.
- Keep reusable backend logic in `backend/app/services`.
- Add SQLAlchemy models in `backend/app/models`.
- Add Pydantic request/response contracts in `backend/app/schemas`.
- Add React route pages in `frontend/src/pages`.
- Add reusable UI in `frontend/src/components`.
- Add frontend API wrappers in `frontend/src/services`.
- Add reusable hooks in `frontend/src/hooks`.
