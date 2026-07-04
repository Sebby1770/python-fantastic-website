# Cloud Staging Notes

This project is intentionally small, but it now carries the launch hooks a real web app needs.

## Containerisation

- `Dockerfile` builds the Flask runtime.
- `docker-compose.yml` gives you a local staging profile with a persisted SQLite contact ledger.
- `/health` and `/ready` can be wired to a load balancer, reverse proxy, or Kubernetes probe.

## Load Balancer And Proxy

Set `TRUST_PROXY_HEADERS=true` only when the app is behind a trusted reverse proxy. It enables `ProxyFix` for `X-Forwarded-*` headers so generated URLs, protocol detection, and client IP rate limiting work correctly behind a load balancer.

## Embedded Database

Contact submissions are stored in SQLite with WAL enabled and an index on `created_at`. Email and client identifiers are hashed with `CONTACT_HASH_SALT`; the database is useful for local demos and staging, not as a full CRM.

## Observability

- `X-Request-ID` is returned on each response.
- `X-Response-Time-Ms` exposes request latency.
- `/metrics` reports request count, error count, average latency, contact submissions, rate-limited requests, and rolling 60-second QPS.
- Set `METRICS_TOKEN` to require `Authorization: Bearer <token>` for `/metrics`.
- Set `ADMIN_TOKEN` to protect `/admin/contacts`, which returns hash prefixes and message previews rather than raw email addresses.
- `/admin/export.json` returns a no-raw-email export of recent contacts, metrics, and integration state for support handoffs.
- `CONTACT_HONEYPOT_FIELD` defaults to `website`; filled honeypot submissions are counted and ignored without revealing the filter.
- `/openapi.json` and `/api/status` make integration and uptime checks easier for external tools.

## Serverless Path

For Lambda-style deployment, keep the contact ledger external. Good fits:

- SQS for contact-event buffering.
- DynamoDB for submission metadata.
- S3 for generated site assets.
- CloudWatch alarms on `/metrics` counters or API Gateway logs.

## Vercel And Supabase

Vercel support is configured through `vercel.json` and `[tool.vercel]` in `pyproject.toml`. The build step copies Flask static assets into `public/static` so they can be served from Vercel's CDN while `app.py` runs as the Python Function.

Supabase contact sync is optional and server-side only. Apply `supabase/migrations/*_asteria_contact_submissions.sql`, then set `SUPABASE_URL` and `SUPABASE_SECRET_KEY` in Vercel. The app sends only hashed email/client identifiers plus a short message preview. On Vercel, the local SQLite fallback defaults to `/tmp/contacts.sqlite3`, so treat it as ephemeral and use Supabase for durable production records.
