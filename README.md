# SaaS Agendamento — Backend (Python / FastAPI)

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Preencha `.env` com a connection string do Supabase (Project Settings → Database → Connection string → URI) e um `JWT_SECRET` próprio.

## Banco

Rode `db/schema.sql` e `db/seed.sql` no SQL Editor do Supabase antes de subir a API.

## Endpoints

| Método | Rota | Auth |
|---|---|---|
| POST | `/api/auth/login` | — |
| POST | `/api/auth/registrar-owner` | — |
| GET | `/api/services?tenant=slug` | — |
| POST | `/api/services` | owner |
| POST | `/api/appointments` | — |
| GET | `/api/appointments` | owner |

Documentação interativa em `/docs` após subir o servidor.
