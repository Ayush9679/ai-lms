# AI-LMS — Enterprise AI Learning Management System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql)](https://postgresql.org)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00)](https://sqlalchemy.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://docker.com)
[![Gemini](https://img.shields.io/badge/Gemini-1.5Flash-4285F4?logo=google)](https://aistudio.google.com)

A production-grade, enterprise AI Learning Management System backend built with **FastAPI**, **PostgreSQL**, **SQLAlchemy 2.0**, and **Google Gemini AI**.

---

## ✨ Features

### 🔐 Authentication & Security
- JWT access + refresh tokens
- bcrypt password hashing
- Email verification flow
- Forgot/reset password
- Role-Based Access Control (RBAC): Student, Teacher, Admin
- Rate limiting (100 req/min global, 10 req/min for AI)
- CORS configuration

### 📚 Course Management
- Full CRUD with slug generation
- Thumbnail & file uploads (images, videos, PDFs)
- Course levels (Beginner, Intermediate, Advanced)
- Draft/Published/Archived status workflow
- Full-text search with filtering and sorting

### 📖 Lesson System
- Ordered lessons with video + PDF support
- Transcript storage for AI processing
- Per-student progress tracking (watch time, completion %)
- Automatic course completion calculation

### ❓ Quiz Engine
- MCQ, True/False, Subjective question types
- Manual creation + AI generation (Gemini)
- Negative marking support
- Configurable attempt limits
- Auto-grading with instant score breakdown
- Score history per student

### 📝 Assignment System
- Teacher creates assignments with due dates
- Students submit text and/or file uploads
- Teacher grades with marks + feedback
- Complete submission history

### 🤖 AI Features (Google Gemini 1.5 Flash)
- **AI Tutor**: Context-aware chat with conversation history
- **Notes Generator**: Structured notes from lessons/PDFs/text
- **Summarization**: Short/medium/long summaries with key points
- **Quiz Generator**: AI-generated quizzes from any content
- **Flashcard Generator**: Study flashcards from lessons/text
- **Study Planner**: Personalized weekly study plans
- **Learning Recommendations**: Next lessons, weak topics, practice plan

### 📊 Dashboards
- **Student**: Enrolled courses, progress, quiz scores, recent activity
- **Teacher**: Course stats, enrolled students, analytics
- **Admin**: Platform-wide stats (users, courses, enrollments)

### 🏗️ Architecture
- Clean Architecture (API → Services → Repositories → Models)
- Async SQLAlchemy 2.0 with asyncpg
- Alembic migrations
- Structured JSON logging with request correlation
- Docker Compose for one-command startup

---

## 🚀 Quick Start

### Prerequisites
- [Docker Desktop](https://docker.com/products/docker-desktop) (required)
- A [Gemini API key](https://aistudio.google.com/app/apikey) (optional, for AI features)

### 1. Clone & Configure

```bash
git clone <your-repo>
cd ai-lms
cp .env.example .env
```

Edit `.env` and set:
```env
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
GEMINI_API_KEY=AIza...  # Your Gemini API key
```

### 2. Start (One Command)

```bash
docker compose up --build
```

This will:
1. Build the FastAPI image
2. Start PostgreSQL with health checks
3. Start the API server (waits for DB to be ready)
4. Create upload directories

### 3. Run Migrations

```bash
docker compose exec api alembic upgrade head
```

### 4. Open API Docs

| URL | Description |
|-----|-------------|
| http://localhost:8000/docs | **Swagger UI** (interactive) |
| http://localhost:8000/redoc | **ReDoc** (readable) |
| http://localhost:8000/ | Health check |

---

## 🔑 API Authentication

1. **Register**: `POST /api/v1/auth/register`
2. **Login**: `POST /api/v1/auth/login` → get `access_token`
3. In Swagger, click **Authorize 🔒** → enter `<your_token>`
4. All protected endpoints now work

---

## 📡 API Endpoints

### 🔐 Authentication (`/api/v1/auth`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register new user |
| POST | `/login` | Login, get tokens |
| POST | `/refresh` | Refresh access token |
| GET | `/me` | Get current user |
| POST | `/verify-email` | Verify email |
| POST | `/forgot-password` | Request password reset |
| POST | `/reset-password` | Complete password reset |
| POST | `/change-password` | Change own password |

### 👤 Users (`/api/v1/users`)
| Method | Endpoint | Access |
|--------|----------|--------|
| GET | `/me` | All users |
| PATCH | `/me` | All users |
| POST | `/me/avatar` | All users |
| GET | `/` | Admin only |
| GET | `/{id}` | Admin only |
| PATCH | `/{id}` | Admin only |
| DELETE | `/{id}` | Admin only |

### 📚 Courses (`/api/v1/courses`)
| Method | Endpoint | Access |
|--------|----------|--------|
| POST | `/` | Teacher/Admin |
| GET | `/` | Public |
| GET | `/my` | Teacher/Admin |
| GET | `/{id}` | Public |
| PATCH | `/{id}` | Teacher (own) / Admin |
| DELETE | `/{id}` | Teacher (own) / Admin |
| POST | `/{id}/thumbnail` | Teacher (own) / Admin |
| POST | `/{id}/files` | Teacher (own) / Admin |
| GET | `/{id}/files` | Any |

### 📖 Lessons (`/api/v1`)
| Method | Endpoint | Access |
|--------|----------|--------|
| POST | `/courses/{id}/lessons` | Teacher/Admin |
| GET | `/courses/{id}/lessons` | Any (published only for students) |
| GET | `/lessons/{id}` | Any |
| PATCH | `/lessons/{id}` | Teacher (own) / Admin |
| DELETE | `/lessons/{id}` | Teacher (own) / Admin |
| POST | `/lessons/{id}/video` | Teacher/Admin |
| POST | `/lessons/{id}/pdf` | Teacher/Admin |
| POST | `/lessons/{id}/progress` | Student |
| GET | `/lessons/{id}/progress` | Student |

### 🎓 Enrollments (`/api/v1/enrollments`)
| Method | Endpoint | Access |
|--------|----------|--------|
| POST | `/` | Student |
| GET | `/my` | Student |
| DELETE | `/{course_id}` | Student |
| GET | `/courses/{id}/students` | Teacher/Admin |
| GET | `/{course_id}/status` | Any |

### ❓ Quizzes (`/api/v1`)
| Method | Endpoint | Access |
|--------|----------|--------|
| POST | `/courses/{id}/quizzes` | Teacher/Admin |
| POST | `/courses/{id}/quizzes/ai-generate` | Teacher/Admin |
| GET | `/courses/{id}/quizzes` | Any |
| GET | `/quizzes/{id}` | Any |
| PATCH | `/quizzes/{id}` | Teacher (own) / Admin |
| DELETE | `/quizzes/{id}` | Teacher (own) / Admin |
| POST | `/quizzes/{id}/attempts` | Student |
| GET | `/quizzes/{id}/my-attempts` | Student |
| GET | `/students/quiz-history` | Student |

### 📝 Assignments (`/api/v1`)
| Method | Endpoint | Access |
|--------|----------|--------|
| POST | `/courses/{id}/assignments` | Teacher/Admin |
| GET | `/courses/{id}/assignments` | Any |
| GET | `/assignments/{id}` | Any |
| PATCH | `/assignments/{id}` | Teacher (own) / Admin |
| DELETE | `/assignments/{id}` | Teacher (own) / Admin |
| POST | `/assignments/{id}/submit` | Student |
| POST | `/assignments/{id}/submit-file` | Student |
| GET | `/assignments/{id}/submissions` | Teacher (own) / Admin |
| PATCH | `/submissions/{id}/grade` | Teacher (own) / Admin |
| GET | `/my-submissions` | Student |

### 🤖 AI Features (`/api/v1/ai`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat` | AI tutor chat |
| GET | `/chat/sessions` | List sessions |
| GET | `/chat/sessions/{id}` | Session history |
| DELETE | `/chat/sessions/{id}` | Delete session |
| POST | `/notes/generate` | Generate notes |
| GET | `/notes` | List my notes |
| POST | `/summarize` | Summarize content |
| POST | `/flashcards/generate` | Generate flashcards |
| GET | `/flashcards` | List my flashcards |
| POST | `/study-plan/generate` | Generate study plan |
| GET | `/study-plans` | List my plans |
| GET | `/recommendations` | Get recommendations |

### 📊 Dashboard (`/api/v1/dashboard`)
| Method | Endpoint | Access |
|--------|----------|--------|
| GET | `/student` | Any |
| GET | `/teacher` | Any |
| GET | `/admin` | Admin only |

### 🔍 Search (`/api/v1/search`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/courses` | Full-text course search |

---

## 🏛️ Architecture

```
app/
├── api/v1/          # Routers (routing only, no business logic)
│   ├── auth.py
│   ├── users.py
│   ├── courses.py
│   ├── lessons.py
│   ├── enrollments.py
│   ├── quizzes.py
│   ├── assignments.py
│   ├── ai.py
│   ├── dashboard.py
│   └── search.py
├── core/            # Configuration, security, logging, exceptions
├── models/          # SQLAlchemy 2.0 ORM models (UUID PKs, soft delete)
├── schemas/         # Pydantic v2 request/response models
├── repositories/    # Database access layer (no SQL in routers/services)
├── services/        # Business logic layer
├── ai/              # Gemini AI client and feature service
├── middleware/      # Rate limiting, request logging
└── dependencies/    # FastAPI dependencies (auth guards, DB session)
alembic/             # Database migrations
tests/               # pytest test suite
```

---

## 🌐 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `SECRET_KEY` | ✅ | JWT signing key (32+ chars) |
| `GEMINI_API_KEY` | ⚡ | Google Gemini API key (for AI features) |
| `ALGORITHM` | | JWT algorithm (default: HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | | Token expiry (default: 60) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | | Refresh expiry (default: 7) |
| `CORS_ORIGINS` | | Allowed origins (JSON array) |
| `UPLOAD_DIR` | | File upload path (default: /app/uploads) |
| `MAX_UPLOAD_SIZE_MB` | | Max file size in MB (default: 50) |
| `GEMINI_MODEL` | | Gemini model (default: gemini-1.5-flash) |
| `RATE_LIMIT_PER_MINUTE` | | Global rate limit (default: 100) |
| `AI_RATE_LIMIT_PER_MINUTE` | | AI rate limit (default: 10) |
| `SMTP_HOST` | | SMTP server (optional, for email) |
| `DEBUG` | | Enable debug logging (default: false) |

---

## 🧪 Running Tests

```bash
# Install test dependencies
pip install aiosqlite pytest-asyncio

# Run tests
docker compose exec api pytest tests/ -v

# With coverage
docker compose exec api pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## 🗄️ Database Migrations

```bash
# Run all migrations
docker compose exec api alembic upgrade head

# Create a new migration
docker compose exec api alembic revision --autogenerate -m "description"

# Downgrade one step
docker compose exec api alembic downgrade -1

# Show migration history
docker compose exec api alembic history
```

---

## 🐳 Docker Commands

```bash
# Start all services
docker compose up --build

# Start in background
docker compose up -d --build

# View logs
docker compose logs -f api
docker compose logs -f postgres

# Stop
docker compose down

# Stop and remove volumes (DELETES ALL DATA)
docker compose down -v

# Rebuild just the API
docker compose up --build api
```

---

## 🔒 RBAC Summary

| Permission | Student | Teacher | Admin |
|-----------|---------|---------|-------|
| Register / Login | ✅ | ✅ | ✅ |
| View courses | ✅ | ✅ | ✅ |
| Enroll in courses | ✅ | | |
| Watch lessons / take quizzes | ✅ | | |
| Submit assignments | ✅ | | |
| Use AI tutor / notes / flashcards | ✅ | ✅ | ✅ |
| Create / edit courses | | ✅ | ✅ |
| Upload videos / PDFs / lessons | | ✅ | ✅ |
| Create quizzes (manual + AI) | | ✅ | ✅ |
| Create assignments / grade | | ✅ | ✅ |
| View enrolled students | | ✅ | ✅ |
| Manage all users | | | ✅ |
| Delete anything | | | ✅ |
| Admin dashboard | | | ✅ |

---

## 📝 License

MIT License — See [LICENSE](LICENSE) for details.
