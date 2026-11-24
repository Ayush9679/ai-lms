# AI-LMS

AI-LMS is a learning management system with a FastAPI backend and a Next.js web client. It supports student, teacher, and admin accounts; course delivery; quizzes and assignments; dashboards; and optional Gemini-powered study tools.

## Features

- JWT access and refresh tokens, bcrypt password hashing, and role checks for teacher and admin operations.
- Course creation and publishing, lessons, course files, student enrollment, and lesson progress.
- Quiz creation (manual or AI-generated), attempts, answer records, and score history.
- Assignments, student submissions, and teacher grading.
- Student, teacher, and admin dashboard APIs, plus paginated course search.
- Optional Gemini API integration for tutor chat, notes, summaries, flashcards, study plans, quiz generation, and recommendations.
- Validated uploads for course resources, lesson media, avatars, and assignment submissions.

The API has email verification and password reset endpoints and stores their tokens, but SMTP delivery is not implemented. The AI recommendation prompt currently receives the student ID and optional course and published lesson titles; it does not calculate recommendations from quiz scores or lesson progress. Course prices are stored in INR, but billing, paid subscriptions, and standalone learning paths are not implemented.

## Tech stack

| Area | Technology |
| --- | --- |
| Backend API | Python, FastAPI, Pydantic |
| Database | PostgreSQL, async SQLAlchemy, Alembic |
| AI provider | Google Gemini API (optional) |
| Frontend | Next.js App Router, React, TypeScript, Tailwind CSS |
| Tests and lint | pytest, pytest-asyncio, Ruff, ESLint, TypeScript |
| Local services | Docker Compose |

## Architecture

```mermaid
flowchart LR
  Browser[Next.js browser client] -->|HTTP /api/v1| API[FastAPI]
  API --> Auth[JWT and role dependencies]
  API --> Services[Application services]
  Services --> Repos[SQLAlchemy repositories]
  Repos --> DB[(PostgreSQL)]
  Services --> Files[Private Cloudflare R2]
  Services -->|Optional AI requests| Gemini[Gemini API]
  Migrations[Alembic migrations] --> DB
```

<!-- Screenshot placeholder: add a student dashboard image at docs/screenshots/student-dashboard.png. -->
<!-- Screenshot placeholder: add a course lesson image at docs/screenshots/course-lesson.png. -->

## Requirements

- Docker Desktop for the local PostgreSQL service.
- Python 3.12 or newer for local backend tools.
- Node.js 20.9 or newer and npm for the frontend.
- A Gemini API key only if you want to use AI endpoints.

## Local setup

1. Copy `.env.example` to `.env`. Generate `SECRET_KEY` with `python -c "import secrets; print(secrets.token_hex(32))"`, and replace the database password placeholder with a URL-safe value. Set `GEMINI_API_KEY` only if you need AI features.
2. Start PostgreSQL and the API:

   ```bash
   docker compose up --build -d
   docker compose exec api alembic upgrade head
   docker compose exec api python -m scripts.seed_demo
   ```

3. Start the frontend in another terminal:

   ```bash
   cd frontend
   npm ci
   cp .env.local.example .env.local
   npm run dev
   ```

4. Open `http://localhost:3000`. The backend is at `http://localhost:8000`; interactive API docs are at `/docs`.

The Compose service passes the database URL to the API using the `postgres` service name. To run the API directly on the host, set `DATABASE_URL` to a host-reachable PostgreSQL URL first. Do not commit `.env` or `.env.local`.

### Private R2 media

Set `STORAGE_ENDPOINT_URL`, `STORAGE_REGION=auto`, `STORAGE_ACCESS_KEY_ID`, `STORAGE_SECRET_ACCESS_KEY`, and `STORAGE_BUCKET=ai-lms-media` in the backend environment. `STORAGE_ENDPOINT_URL` is preferred; `STORAGE_ACCOUNT_ID` is an optional fallback for constructing the R2 endpoint. Keep the bucket private and keep these credentials off the frontend. Browser uploads use short-lived presigned PUT URLs. Lesson media and course files are served with expiring presigned GET URLs after the backend checks the caller's enrollment or course ownership.

Paid courses use verified Razorpay Test Mode checkout when enabled. Free enrollment uses the existing enrollment endpoint. Paid lesson media and course files require an active or completed enrollment backed by a captured payment. Course owners and admins retain their content preview access.

`MAX_VIDEO_SIZE_MB=2048` permits a 2 GiB video through one presigned PUT (R2 single PUT supports up to 5 GiB). This flow is not multipart or resumable: a network failure requires retrying the full file. Thumbnail uploads use `MAX_IMAGE_SIZE_MB=10`; JPEG, PNG, WEBP and GIF are signature-validated. The exact private-bucket CORS policy and upload behavior are documented in [docs/r2-uploads.md](docs/r2-uploads.md).

Revision `0002_lesson_media_upload_state` adds verified video state, lesson thumbnails, and one-time upload grant tracking. Revision `0003_course_currency` adds an INR currency code to existing course prices and a verified video-size field. On staging, first back up the database, then run `alembic upgrade head` (or `python -m alembic upgrade head` in the local virtual environment) and verify the API before scheduling the production release. No production migration was run as part of this change.

For deployment, keep the bucket private. Presigned links expire after 15 minutes by default (`STORAGE_PRESIGNED_URL_TTL`). The legacy server-proxied multipart endpoints remain capped by `MAX_UPLOAD_SIZE_MB`. The R2 frontend flow uses direct PUT for media and files.

## Razorpay Test Mode

1. Provision a disposable PostgreSQL database and point the backend's `DATABASE_URL` at it. Use `DEBUG=false`, a local JWT secret and a supported Python virtual environment. Install dependencies with `python -m pip install -r requirements-dev.txt`.
2. Create a Test Mode API key pair in Razorpay and enable automatic payment capture. Set `RAZORPAY_ENABLED=true`, `RAZORPAY_TEST_MODE=true`, the Test Mode key pair, and a separate webhook signing secret in the backend's local `.env`. Keep both secrets on the backend.
3. With the disposable database selected, run `python -m alembic upgrade head`. Revision `0004` follows `0003` and creates `payment_orders`, `payments` and `webhook_events`. Then start the server with `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`.
4. If testing webhook delivery, use a staging HTTPS endpoint or forward a temporary public HTTPS URL to the local server. In the Razorpay Test Mode dashboard, register `https://<test-host>/api/v1/payments/webhook` with the same signing secret and subscribe to `payment.captured`, `payment.failed` and `order.paid`.
5. In [local API docs](http://127.0.0.1:8000/docs), log in as a student who has never joined the paid course. Use a teacher account to create and publish a priced INR course with a thumbnail and at least one verified lesson video. Use the student's bearer token for `POST /api/v1/payments/create-order` and send only `{"course_id":"<course UUID>"}`.
6. Load [Razorpay Standard Checkout](https://razorpay.com/docs/payments/payment-gateway/web-integration/standard/integration-steps/) on a local test page. Pass `razorpay_key_id` as `key`, `razorpay_order_id` as `order_id`, and the returned `amount` (in paise) and `currency`. Use a test payment method from the Razorpay dashboard documentation. Forward the Checkout handler's `razorpay_order_id`, `razorpay_payment_id` and `razorpay_signature` to `POST /api/v1/payments/verify` with the same student token.
7. A captured payment returns `status: captured`. If it is still authorized, retry verification after capture or let the webhook reconcile it. Confirm the active enrollment via `GET /api/v1/enrollments/{course_id}/status` and request a published lesson as that student. Repeating verification or redelivering a webhook should leave one capture and one enrollment.

For a credentials-free run, use `python -m pytest tests/test_payments.py -q`. These tests mock Razorpay, sign test callbacks, and use a disposable in-memory database.

### Recover a payment after an interrupted checkout

Call `POST /api/v1/payments/status` with the student's bearer token and
`{"razorpay_order_id":"order_Example123"}` using the order ID returned by `/payments/create-order`.
Keep that order ID through reloads if the client offers payment recovery. The request requires
only the order ID. A successful response is:

```json
{
  "razorpay_order_id": "order_Example123",
  "course_id": "a5eceaef-ac0e-4996-8770-7a82154cc195",
  "status": "enrolled",
  "safe_to_retry": false,
  "attempt_status": null
}
```

| Status | Meaning |
| --- | --- |
| `created` | Razorpay confirms that the order exists and has no payment attempts. `safe_to_retry` is true only if the original course is still purchasable at the order price and has no active or completed enrollment for the student. |
| `pending` | Capture is unresolved. `attempt_status: "failed"` means Razorpay reported only failed attempts. A late authorization is still possible. |
| `authorized` | Razorpay reports an authorized payment awaiting capture. |
| `captured` | A capture is recorded and the student has no active or completed enrollment. For example, the student may have dropped the course. |
| `enrolled` | A verified capture is recorded and the student has an active or completed enrollment. |
| `unknown` | The gateway timed out, returned inconsistent data, or the status could not otherwise be established. |

When `safe_to_retry` is true, call the existing create-order endpoint for the same course and
check that it returns the same `razorpay_order_id` before reopening Checkout. For unresolved
payments, check status again with backoff. Recovery can make up to three gateway reads with
a 10-second timeout per read. It uses the same transactional capture and enrollment logic
as verification and webhook handling.

Unknown orders, orders owned by another student, and disabled payments return `404`.
Authentication errors return `401` or `403`, invalid bodies return `422`, and requests
over 10 per minute per caller IP return `429` on each backend process. The regular API
rate limit also applies.

The allocation rounds the teacher's share to the nearest paise using half-up rounding and assigns the remainder to the platform. A ₹1,000 capture produces ₹900 in gross teacher earnings and ₹100 in gross platform commission at the default rate. The recorded gateway fee is separate. The teacher amount is a ledger allocation and does not initiate a bank transfer.

The test integration keeps one order per student and course. A failed attempt can retry on that order. Changing the price after opening an order requires operator reconciliation before that student can start a purchase at the new price. Refund processing, chargebacks, order expiry, automated recovery of a gateway order created just before a database failure, and payouts are outside this phase.

Before a live launch, complete end-to-end staging checkout, migration and concurrency testing, and implement refund and dispute reconciliation, alerting, and a process for payment support. Complete Razorpay account activation and review the live capture, webhook and fee configuration. Live keys are rejected by this release and require a separate production release.

## Demo account

Run the seed command after migrations. It creates sample teacher and student accounts, a published Python course, one lesson, and a student enrollment. The seed is idempotent and does not overwrite existing accounts.

| Role | Email | Password |
| --- | --- | --- |
| Student | `demo@ai-lms.local` | `DemoOnly123!` |
| Teacher | `teacher-demo@ai-lms.local` | `DemoOnly123!` |

These credentials are for a disposable demo database only. Do not use them for real users or production data. The demo student login is the recommended recruiter tour.

## Environment variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | Yes | Async SQLAlchemy URL (`postgresql+asyncpg://...`) |
| `SECRET_KEY` | Yes | JWT signing key; use a random value of at least 32 characters |
| `APP_NAME`, `APP_VERSION` | No | API name and version |
| `ENVIRONMENT` | No | Environment label; `production` enables HSTS |
| `DEBUG` | No | SQL echo and development setting; keep `false` in deployment |
| `ALGORITHM` | No | JWT algorithm; supported value is `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Access token lifetime (default 60) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | Refresh token lifetime (default 7) |
| `DATABASE_POOL_SIZE`, `DATABASE_MAX_OVERFLOW` | No | Async PostgreSQL pool sizing |
| `DATABASE_SSL` | No | Enable verified TLS for PostgreSQL connections (default `false`) |
| `DATABASE_SSL_CA_FILE` | Supabase TLS | Path to the Supabase root CA certificate downloaded from Database Settings; certificate and hostname verification remain enabled |
| `CORS_ORIGINS` | No | JSON array of explicit browser origins; wildcard is rejected |
| `UPLOAD_DIR` | No | Local upload directory (default `./uploads`) |
| `STORAGE_ENDPOINT_URL`, `STORAGE_REGION` | For R2 | Canonical R2 S3-compatible endpoint and region (`auto`) |
| `STORAGE_ACCESS_KEY_ID`, `STORAGE_SECRET_ACCESS_KEY`, `STORAGE_BUCKET` | For R2 | Backend-only credentials and canonical private bucket name |
| `STORAGE_ACCOUNT_ID` | Optional | Used only to derive the R2 endpoint if `STORAGE_ENDPOINT_URL` is unset |
| `STORAGE_PRESIGNED_URL_TTL` | No | Presigned download lifetime in seconds (default 900, max 3600) |
| `STORAGE_UPLOAD_GRANT_TTL` | No | Time allowed to complete an authorized upload (default 86400 seconds) |
| `MAX_UPLOAD_SIZE_MB` | No | Maximum upload size (default 50 MB) |
| `MAX_VIDEO_SIZE_MB`, `MAX_IMAGE_SIZE_MB` | No | Direct upload limits (defaults 2048 MB and 10 MB) |
| `TEACHER_REVENUE_SHARE` | No | Default teacher share for existing allocation-helper callers (default `0.90`). Razorpay captures use `PLATFORM_COMMISSION_PERCENT` |
| `RAZORPAY_ENABLED` | For test payments | Explicitly enable the payment API and paid publishing (default `false`) |
| `RAZORPAY_TEST_MODE` | For test payments | Must be `true` when enabled (default `true`) |
| `RAZORPAY_KEY_ID` | When enabled | Test key ID with the `rzp_test_` prefix. Checkout receives this value |
| `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET` | When enabled | Backend-only API and webhook signing secrets |
| `PLATFORM_COMMISSION_PERCENT` | No | Platform share of captured gross in percent (default `10`) |
| `ALLOWED_IMAGE_TYPES`, `ALLOWED_VIDEO_TYPES`, `ALLOWED_DOCUMENT_TYPES` | No | JSON arrays of accepted MIME types |
| `GEMINI_API_KEY` | For AI | Gemini API key; leave empty to disable AI operations |
| `GEMINI_MODEL` | No | Gemini model name |
| `RATE_LIMIT_PER_MINUTE`, `AI_RATE_LIMIT_PER_MINUTE` | No | Per-IP request limits |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` | No | Reserved SMTP configuration; no email sender is implemented |
| `EMAILS_FROM_EMAIL`, `EMAILS_FROM_NAME` | No | Sender labels for a future email integration |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Compose | Local PostgreSQL container credentials |
| `NEXT_PUBLIC_API_URL` | Frontend | Backend origin without `/api/v1` (default `http://localhost:8000`) |

## API overview

All application routes use `/api/v1`.

| Group | Main routes |
| --- | --- |
| Authentication | `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/me`, `/auth/verify-email`, `/auth/forgot-password`, `/auth/reset-password`, `/auth/change-password` |
| Users | `/users/me`, `/users/`, `/users/{user_id}` |
| Courses and lessons | `/courses`, `/courses/{course_id}/lessons`, `/lessons/{lesson_id}`, `/lessons/{lesson_id}/progress` |
| Enrollments | `/enrollments`, `/enrollments/my`, `/enrollments/{course_id}/status` |
| Razorpay Test Mode | `POST /payments/create-order`, `POST /payments/verify`, `POST /payments/status`, `POST /payments/webhook` |
| Quizzes | `/courses/{course_id}/quizzes`, `/quizzes/{quiz_id}/attempts`, `/quizzes/students/quiz-history` |
| Assignments | `/courses/{course_id}/assignments`, `/assignments/{assignment_id}/submit`, `/submissions/{submission_id}/grade` |
| AI | `/ai/chat`, `/ai/notes/generate`, `/ai/summarize`, `/ai/flashcards/generate`, `/ai/study-plan/generate`, `/ai/recommendations` |
| Dashboards and search | `/dashboard/student`, `/dashboard/teacher`, `/dashboard/admin`, `/search/courses` |
| Health | `/health`, `/api/v1/health` |

The route modules and request/response schemas are in `app/api/v1/` and `app/schemas/`. Use `/docs` to inspect the generated OpenAPI document.

## How AI recommendations work

AI calls go to the configured Gemini model through `google-genai`; no local model weights are stored in this repository. The recommendation service includes the authenticated user's ID and, when a course is supplied, the course name and up to ten published lesson titles in its prompt. Gemini returns a JSON recommendation shape. If Gemini is unavailable or the key is missing, AI operations return a service-unavailable response. Configure the API key on the backend only.

## Tests and quality checks

Create a virtual environment, install the development dependencies, and run the automated suite and static checks:

```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements-dev.txt
ruff check app tests alembic
ruff format --check app tests alembic
pytest -q
```

Tests that make live Gemini calls are opt-in with `RUN_LIVE_AI_TESTS=true`; they also require a valid API key and can use provider quota. Recommendation route coverage uses a deterministic stub and does not call Gemini.

Frontend checks:

```bash
cd frontend
npm ci
npm run lint
npm run type-check
npm run build
```

## Live demo

`https://<your-deployed-frontend-url>` (replace after deployment).

## License

No license file is currently included.
