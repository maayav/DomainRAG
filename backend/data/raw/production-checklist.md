# Production Engineering Guide

## Security

- **Rate limiting**: Enable IP-based or token-based rate limiting on all API endpoints to prevent abuse and brute-force attacks.
- **Row-Level Security (RLS)**: Enable RLS on databases so users can only access their own data. Essential defense-in-depth.
- **Secrets management**: Never expose API keys in client code, git, or logs. Use environment variables or a secret manager. Rotate keys regularly. Use separate keys for dev and prod.
- **CAPTCHA**: Add to login, registration, password reset, and public submission forms.
- **HTTPS**: Enforce everywhere with HSTS headers. Use TLS 1.3 minimum. Redirect all HTTP to HTTPS.
- **Input sanitization**: Use parameterized queries (never string-interpolated SQL). Escape HTML output to prevent XSS. Validate file uploads. Use allowlists over denylists.
- **Dependency auditing**: Run npm audit, pip-audit, or cargo audit in CI. Pin versions with lock files. Use Dependabot or Renovate for automated updates.
- **Data minimization**: Only collect what's needed. Add data retention and deletion policies. Provide user data export and deletion for GDPR compliance.
- **Encryption**: Encrypt data in transit (TLS) and at rest (database, file storage, backups). Use full-disk encryption on servers. Encrypt sensitive fields at the column level.
- **PaaS over IaaS**: Prefer managed services where possible. PaaS providers handle OS patching and infrastructure hardening.
- **Network security**: Default-deny both inbound and outbound traffic. Explicitly allowlist only what's needed.
- **Supply chain security**: Generate SBOMs. Use code signing. Lock exact dependency versions.

## Reliability

- **Token bucket rate limiting**: Allows brief bursts while enforcing long-term limits. More flexible than fixed-window rate limiting.
- **Circuit breaker pattern**: Automatically disable failing third-party APIs (closed/open/half-open states) to prevent cascading failures.
- **Graceful degradation**: Disable non-essential features under load (avatars, real-time recommendations, thumbnails).
- **Async queues**: Move slow tasks (emails, PDFs, image processing, exports, webhooks) to background workers with Celery, BullMQ, RQ, or RabbitMQ.
- **Idempotency keys**: Prevent duplicate processing on mutating endpoints (e.g., payments) when retries or double-clicks occur.
- **Token consumption quotas**: Track and cap per-user token usage for paid AI APIs. Send warnings at 80% and 95% thresholds.

## Architecture

- **Stateless design**: No server-side session state in memory. Use JWTs or external stores (Redis) for sessions so instances can scale horizontally.
- **Reverse proxy**: Put Nginx or Caddy in front for SSL termination, static files, routing, and compression.
- **Connection pooling**: Size database pool ~2-3x CPU cores. Set max_overflow for bursts and pool_recycle to prevent stale connections.
- **Database indexing**: Index columns used in WHERE, JOIN, and ORDER BY. Don't over-index. Use EXPLAIN ANALYZE to verify.
- **Read replicas**: Offload SELECT traffic from the primary database for read-heavy workloads. Design for eventual consistency.</think>

<｜DSML｜tool_calls>
<｜DSML｜invoke name="edit">
<｜DSML｜parameter name="filePath" string="true">/home/gman/dev/projects/DomainRAG/backend/app/main.py