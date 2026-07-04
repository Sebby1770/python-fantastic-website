# Changelog

## 2.2.0 - 2026-07-04

- Added `/api/status`, `/api/changelog`, and `/openapi.json` for API discovery and integration.
- Added optional Bearer-token protection for `/metrics` and `/admin/contacts`.
- Added privacy-preserving admin contact summaries with hash prefixes instead of raw email or client identifiers.
- Added contact retention pruning and stronger cross-origin/HSTS response headers.
- Expanded tests for API discovery, ops tokens, contact summaries, and security headers.

## 2.1.0 - 2026-06-30

- Added request IDs, response timing headers, JSON metrics, and rolling 60-second QPS reporting.
- Added an embedded SQLite contact ledger with WAL mode, indexed timestamps, and hashed email/client identifiers.
- Added trusted proxy/load-balancer support through `ProxyFix`.
- Added Docker Compose, Kubernetes deployment/service manifests, and cloud/serverless staging notes.
- Expanded tests around metrics and privacy-preserving contact persistence.

## 2.0.0 - 2026-06-30

- Added production-style security headers, cache controls, payload caps, and contact rate limiting.
- Added `/ready`, `/robots.txt`, and `/sitemap.xml` alongside the existing health route.
- Added a visible launch-ops section and changelog section to the site.
- Added Docker containerization and GitHub Actions CI.
- Expanded tests around readiness, headers, sitemap, robots, and throttling.

## 1.0.0 - 2026-05-06

- Initial Flask studio website.
- Added responsive sections, local generated assets, contact endpoint, and route tests.
