# Free-tier deployment guide

This guide deploys the Next.js frontend to Vercel, the FastAPI API as a Docker web service on Render, and PostgreSQL on Supabase. It is suitable for a demo and recruiter walkthrough. Free services can sleep, pause, restart, and have limited storage; this setup is not a high-availability production topology.

## 1. Create the PostgreSQL database

1. Create a Supabase project and set a strong database password.
2. In the project dashboard, open **Connect** and choose the **Session pooler** connection string. The session pooler is reachable over IPv4 and supports the session behavior used by this SQLAlchemy application.
3. Copy the pooler host, username, database name, and password into a secure local secret store. URL-encode reserved characters in the password.
4. Keep database backups outside the free project. The current free plan can pause projects after a week of low activity and does not include automatic backups. Review the [free project pausing policy](https://supabase.com/docs/guides/platform/free-project-pausing), [database connection guide](https://supabase.com/docs/guides/database/connecting-to-postgres), and [free plan limits](https://supabase.com/pricing) before deploying.

The Render API environment needs a SQLAlchemy async URL in this form, using the exact values from Supabase:

```text
postgresql+asyncpg://<pooler-username>:<URL-encoded-password>@<pooler-host>:5432/postgres
```

Set `DATABASE_SSL=true`. The application then asks `asyncpg` to use TLS. Use the session pooler on port `5432`; avoid transaction mode for this persistent API because transaction pooling has different session and prepared-statement behavior.

## 2. Deploy the API on Render

1. Push `chore/production-ready` to GitHub and connect the repository to Render.
2. Create a **Web Service**, select the repository branch, and choose **Docker** as the runtime. Render will build the root `Dockerfile`.
3. Set the start command to:

   ```sh
   alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --workers 1
   ```

   This applies database migrations before serving requests. For the current single-process deployment, the process count stays at one because request limits are held in process memory.

4. Configure these environment variables in Render:

   | Variable | Value |
   | --- | --- |
   | `ENVIRONMENT` | `production` |
   | `DEBUG` | `false` |
   | `DATABASE_URL` | Supabase session-pooler SQLAlchemy URL above |
   | `DATABASE_SSL` | `true` |
   | `DATABASE_POOL_SIZE` | `3` |
   | `DATABASE_MAX_OVERFLOW` | `2` |
   | `SECRET_KEY` | A fresh random key from `python -c "import secrets; print(secrets.token_hex(32))"` |
   | `CORS_ORIGINS` | JSON array containing the deployed frontend origin, for example `["https://your-app.vercel.app"]` |
   | `UPLOAD_DIR` | `/tmp/ai-lms-uploads` |
   | `GEMINI_API_KEY` | Optional; add a Gemini API key to enable AI operations |
   | `GEMINI_MODEL` | `gemini-2.5-flash` or another model enabled for your account |

   Keep credentials in the Render environment settings. Do not add secrets to Git or to the frontend's `NEXT_PUBLIC_*` variables.

5. Deploy, then check `https://<render-service>.onrender.com/health` and `/docs`.

Render's free web services spin down after 15 minutes without incoming traffic; waking a service can take about a minute. Its free filesystem is ephemeral, so files uploaded to `/tmp/ai-lms-uploads` are lost on restart, redeploy, or spin-down. Persistent file storage is not implemented in this repository. See [Render's free service limits](https://render.com/docs/free) and [FAQ](https://render.com/docs/faq).

## 3. Seed the demo accounts and sample course

After the API has run migrations, use a trusted local terminal to run the seed script against the same database. Set `DATABASE_URL`, `DATABASE_SSL=true`, and `SECRET_KEY` in a temporary local environment or a protected local `.env`, then run:

```bash
python -m pip install -r requirements.txt
python -m scripts.seed_demo
```

The script creates a demo teacher and student, a published Python course, one lesson, and an enrollment. It does not update an existing demo account. Do not use these demo credentials with real data.

## 4. Deploy the frontend on Vercel

1. Import the same GitHub repository into Vercel.
2. Set the **Root Directory** to `frontend`; keep the detected Next.js framework and default build settings.
3. Set `NEXT_PUBLIC_API_URL` to `https://<render-service>.onrender.com` (no `/api/v1` suffix).
4. Deploy and copy the resulting production origin.
5. Add that exact origin to Render's `CORS_ORIGINS` JSON array and redeploy the API.

Vercel builds from the connected Git branch and supports Next.js deployments; see [Git deployments](https://vercel.com/docs/git) and [environment variables](https://vercel.com/docs/environment-variables). Set the Vercel production branch deliberately; this repository's hardening branch should be reviewed and merged before making it the production branch.

## 5. Confirm the deployment

- Visit the frontend and sign in with the demo student account documented in `README.md`.
- Check `/health`, log in, open the student dashboard, and open the seeded course.
- If AI is enabled, try the tutor or recommendations page. If it is not enabled, AI operations return service unavailable.
- Confirm Render's configured CORS origin exactly matches the browser URL, including `https://` and without a trailing slash.
- Replace the README live-demo placeholder after the public frontend URL is stable.

## Known free-tier limits

- Render's API has a cold start after idle time; the first request can be slow.
- Supabase Free projects can pause after a week of low database activity and do not include automatic backups.
- Uploaded files are stored on the API's ephemeral filesystem. The app does not currently support an object-storage provider.
- Rate limits use the process-local in-memory backend. They are not shared across multiple API instances and reset when the process restarts.
- Email verification and password-reset tokens are stored, but outbound email delivery is not implemented.
- Demo credentials are public by design and must stay isolated from real user data.
