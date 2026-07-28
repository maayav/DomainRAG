# Production Security Best Practices

## Overview
Security must be built into every layer of your application from day one. This guide covers the most impactful security measures for modern web applications, from input validation to supply chain security.

## Rate Limiting
Enable rate limiting on all API endpoints to prevent brute-force attacks, credential stuffing, and denial-of-service. Use IP-based, user-based, or token-based rate limiting depending on the endpoint sensitivity.

## Row-Level Security (RLS)
Enable RLS on your database to ensure users can only access their own data. This is a critical defense-in-depth measure.

```sql
-- PostgreSQL RLS example
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_documents ON documents
    USING (user_id = current_setting('app.current_user_id')::uuid);
```

## API Key Management
Never expose API keys in client-side code, git repositories, or logs.
- Store secrets in environment variables or secret managers (AWS Secrets Manager, HashiCorp Vault)
- Rotate keys regularly
- Use separate keys for development and production
- Implement key scoping (read-only vs read-write)

## CAPTCHA Protection
Add CAPTCHA (reCAPTCHA, hCaptcha, Turnstile) to:
- Login and registration forms
- Password reset flows
- Contact forms and public submission endpoints
- Any endpoint vulnerable to bot abuse

## HTTPS Everywhere
- Enforce HTTPS on all endpoints with HSTS headers
- Use TLS 1.3 minimum
- Redirect all HTTP traffic to HTTPS
- Set Strict-Transport-Security header with long max-age

## Input Sanitization
Sanitize every input — never trust client data.
- Use parameterized queries to prevent SQL injection
- Escape HTML output to prevent XSS
- Validate and sanitize file uploads (type, size, content)
- Use allowlists over denylists for input validation

```python
# Parameterized query (SAFE)
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))

# String interpolation (VULNERABLE - never do this)
cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")
```

## Dependency Management
Update dependencies regularly and audit for known vulnerabilities.
- Run `npm audit`, `pip-audit`, or `cargo audit` in CI/CD
- Pin dependency versions for reproducible builds
- Use Dependabot or Renovate for automated updates
- Generate SBOMs (Software Bill of Materials) for enterprise compliance

## Data Privacy
Only collect data you actually need. Over-collection creates liability.
- Implement data minimization principles
- Add data retention policies with automatic deletion
- Provide user data export and deletion (GDPR compliance)
- Anonymize or pseudonymize data where possible

## Encryption
Use encryption everywhere — in modern cloud environments it adds negligible overhead.

### Types
- **In Transit**: TLS/SSL for all network communication
- **At Rest**: Encrypt databases, file storage, and backups
- **Disk Encryption**: Full-disk encryption on all servers
- **Field-Level**: Encrypt sensitive columns (SSN, credit cards) in the database

## Cloud Security (PaaS vs IaaS)
Use managed services (PaaS) over self-hosted (IaaS) when possible.
- PaaS: Provider handles OS patching, security updates, and infrastructure hardening
- IaaS/VMs: You must patch the OS, database, and all installed software yourself
- The shared responsibility model means the cloud provider handles infrastructure security, but you handle application security

## Network Security
Default deny inbound AND outbound traffic. Even HTTP/HTTPS outbound can be exploited.

```yaml
# Example firewall rules
inbound:
  - port: 443, source: 0.0.0.0/0     # HTTPS only
  - port: 22, source: 10.0.0.0/8     # SSH from VPN only
outbound:
  - port: 443, destination: api.stripe.com  # Only allowed external APIs
  - port: 5432, destination: db.internal    # Database
  - deny: all                               # Block everything else
```

## Supply Chain Security
- Generate and maintain SBOMs for all dependencies
- Enable code signing to verify repository integrity
- Use lock files (package-lock.json, poetry.lock) to pin exact versions
- Consider memory-safe languages (Rust, Go) for security-critical components
- JavaScript/Node.js is heavily targeted by supply chain attackers due to its popularity

## Open Source Security Tools
- **DependencyTrack**: Software composition analysis platform
- **Grype**: Vulnerability scanner for container images and filesystems
- **Syft**: SBOM generation tool
- **Trivy**: Comprehensive vulnerability scanner
- **Semgrep**: Static analysis for security patterns
- **OWASP ZAP**: Web application security testing
