# AI Engineer Job Tracker API

![CI](https://github.com/kashif0074/job-tracker-api/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

A production-style REST API for tracking AI / software-engineering job applications. Users can register, log in with JWT, save job opportunities, update their status, add notes, filter by skills/location/status, and view dashboard statistics — with strict per-user data isolation.

Built as a Month-1 portfolio project to demonstrate real backend engineering: authentication, database migrations, containerization, automated testing, and CI/CD.

---

## ✨ Features

- 🔐 **JWT authentication** — register, login, protected endpoints
- 🔑 **Bcrypt password hashing** — no plain-text passwords ever stored
- 📋 **Full CRUD** for job applications
- 📊 **Status tracking** — `saved` · `applied` · `interview` · `offer` · `rejected`
- 🔍 **Filtering** — by status, location, remote flag, technology
- 🔎 **Search** — by job title or company
- 📄 **Pagination** — `?page=1&limit=10` with a `total` count
- 🛡️ **Per-user isolation** — users can only see/modify their own jobs (404, not 403, to prevent leaking existence)
- 📚 **Auto-generated Swagger docs** at `/docs`
- 🗄️ **Alembic migrations** — versioned schema, not `create_all`
- 🐳 **Dockerized** — one command runs API + Postgres
- 🧪 **22 automated tests** — auth, CRUD, filters, isolation
- ✅ **CI** via GitHub Actions

---

## 🛠️ Tech Stack

| Layer | Choice |
|---|---|
| Language | Python 3.12 |
| Framework | FastAPI 0.115 |
| ORM | SQLAlchemy 2.0 |
| Validation | Pydantic v2 |
| Database | PostgreSQL 16 |
| Auth | JWT (`python-jose`), Bcrypt (`passlib` + `bcrypt`) |
| Migrations | Alembic 1.13 |
| Testing | Pytest, httpx (via FastAPI's `TestClient`) |
| Container | Docker, Docker Compose |
| CI | GitHub Actions |

---

## 🚀 Quick Start

### Option A — Docker Compose (recommended)

Requires: Docker Desktop running.

```bash
git clone https://github.com/kashif0074/job-tracker-api.git
cd job-tracker-api
docker compose up --build
```

Then open:

- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

The `api` container runs `alembic upgrade head` on startup, so the schema is ready before any request.

### Option B — Local development

Requires: Python 3.12+, a running Postgres (or use SQLite).

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

cp .env.example .env                # then edit DATABASE_URL + SECRET_KEY

alembic upgrade head                # create tables
uvicorn app.main:app --reload
```

Swagger at http://localhost:8000/docs.

---

## 📚 API Reference

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| `GET` | `/health` | — | Health check |
| `POST` | `/auth/register` | — | Create an account |
| `POST` | `/auth/login` | — | Login, returns a JWT |
| `GET` | `/auth/me` | ✅ | Current user info |
| `POST` | `/jobs` | ✅ | Create a job |
| `GET` | `/jobs` | ✅ | List / filter / paginate jobs |
| `GET` | `/jobs/{id}` | ✅ | Get one job |
| `PATCH` | `/jobs/{id}` | ✅ | Partial update |
| `DELETE` | `/jobs/{id}` | ✅ | Delete a job |

### Filters & Pagination

```
GET /jobs?status=applied
GET /jobs?location=Remote
GET /jobs?technology=PyTorch
GET /jobs?search=engineer
GET /jobs?page=1&limit=10
GET /jobs?status=saved&location=Remote
```

Response shape:

```json
{
  "total": 42,
  "page": 1,
  "limit": 10,
  "items": [ { "id": 1, "title": "...", ... } ]
}
```

### Example Request

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -d "username=you@example.com&password=password123" | jq -r .access_token)

curl -X POST http://localhost:8000/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Junior AI Engineer",
    "company": "Tech Corp",
    "location": "Remote",
    "status": "saved",
    "technologies": ["Python", "FastAPI", "PyTorch"],
    "application_deadline": "2026-11-30"
  }'
```

---

## 🧪 Running Tests

```bash
pytest -v
```

Expected:

```
==================== 22 passed in ~5s ====================
```

With coverage:

```bash
pytest --cov=app --cov-report=term-missing
```

Test files:

| File | Coverage |
|---|---|
| `tests/test_auth.py` | Register, login, `/me`, invalid tokens, duplicate email |
| `tests/test_jobs.py` | CRUD, filters, pagination, per-user isolation |

Tests use an isolated SQLite database, so they don't touch your dev/prod data.

---

## 🗄️ Database Schema

```
users                          jobs                          notes (planned)
─────                          ────                          ─────
id (PK)                        id (PK)                       id (PK)
email (unique)                 user_id (FK → users.id)       job_id (FK → jobs.id)
hashed_password                title                         content
full_name                      company                       created_at
created_at                     location
                               status
                               technologies
                               job_url
                               application_deadline
                               created_at
                               updated_at
```

Schema is managed by Alembic:

```bash
alembic upgrade head           # apply all migrations
alembic downgrade -1           # roll back one
alembic revision --autogenerate -m "add X"
```

---

## 📂 Project Structure

```
job-tracker-api/
├── app/
│   ├── main.py              # FastAPI app, router wiring
│   ├── config.py            # Settings from env
│   ├── database.py          # Engine, SessionLocal, Base
│   ├── security.py          # Password hashing, JWT
│   ├── dependencies.py      # get_current_user
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── routers/             # HTTP endpoints
│   └── services/            # Business logic
├── alembic/                 # Migrations
├── tests/                   # Pytest suite (22 tests)
├── .github/workflows/       # CI
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
├── .env.example
└── README.md
```

---

## 🐳 Docker

```bash
docker compose up --build         # build + start (foreground)
docker compose up -d --build      # detached
docker compose logs -f api        # follow API logs
docker compose down               # stop, keep data
docker compose down -v            # stop, wipe DB
```

Services:

- `db` — Postgres 16 on host port `5433`
- `api` — FastAPI on host port `8000`

---

## 🔐 Environment Variables

Copy `.env.example` to `.env`:

```env
DATABASE_URL=postgresql+psycopg://appuser:apppassword@localhost:5432/jobtracker
SECRET_KEY=<generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

`.env` is **not** committed — see `.gitignore`.

---

## 📸 Screenshots

### Swagger UI
![Swagger docs](docs/swagger.png)

### Docker Desktop — both services healthy
![Docker Desktop](docs/docker-desktop.png)

### CI green
![CI](docs/ci-green.png)

---

## 🎯 What I Learned

- **JWT auth from scratch** — signing, verifying, protecting routes via dependencies
- **Password security** — bcrypt, salting, never storing plaintext
- **Per-user isolation** — filtering every query by `current_user.id` and returning 404 (not 403) to prevent resource-existence leaks
- **Schema migrations** — why `Base.metadata.create_all` isn't enough; Alembic as the real solution
- **Docker & Compose** — multi-service networking (`db` vs `localhost`), healthchecks, environment-based config
- **Test isolation** — fresh DB per test via fixtures
- **CI/CD** — GitHub Actions running the full suite on every push

---

## 📝 License

MIT — do whatever you want, attribution appreciated.

---

## 👤 Author

**Kashif** — [github.com/kashif0074](https://github.com/kashif0074)
## 🤖 AI Features

- **Skill Extraction** (`POST /jobs/{id}/analyze`): Uses **Groq (Llama 3)** to extract programming languages, frameworks, AI tools, and experience level from job descriptions.
- **Resume Matching** (`GET /jobs/{id}/match`): Uses **sentence-transformers** (local CPU embeddings) and **pgvector** for cosine similarity scoring.
- **100% Free AI Stack**: Local embeddings (CPU-only PyTorch) + Groq free tier. No OpenAI/Gemini API billing required.
## 🧠 Agentic AI Features

### Autonomous Browser Agent
`POST /jobs/agent/scrape-and-save?url=<job-url>` — A **LangGraph** agent that:
1. Plans a scraping strategy
2. Executes **Playwright** browser automation
3. Extracts text from the page
4. Calls the **Groq LLM** to parse skills
5. Saves everything to Postgres + Neo4j

### GraphRAG (Knowledge Graph)
`GET /jobs/graph/related-skills/{skill}` — Traverses a **Neo4j** knowledge graph to find skills that co-occur in job postings.

### Semantic Resume Matching
`GET /jobs/{id}/match` — Uses **sentence-transformers** embeddings stored in **pgvector** for cosine similarity scoring.

## 🏗️ Architecture
