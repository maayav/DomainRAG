# Web Security

## Overview
Web security encompasses practices and technologies used to protect websites, applications, and APIs from cyber threats. Understanding common vulnerabilities is essential for building secure web applications. The OWASP Top 10 is the standard awareness document for web application security.

## Common Vulnerabilities

### Cross-Site Scripting (XSS)
XSS occurs when an attacker injects malicious scripts into content that is served to other users. There are three main types: stored XSS (persistent), reflected XSS (non-persistent), and DOM-based XSS. Mitigation includes proper output encoding, Content Security Policy headers, and input validation.

```html
<!-- Vulnerable -->
<div>{{ user_input }}</div>

<!-- Safe with escaping -->
<div>{{ user_input|escape }}</div>
```

### Cross-Site Request Forgery (CSRF)
CSRF tricks an authenticated user into performing unwanted actions on a web application. The attacker crafts a malicious request that the victim's browser sends automatically if they are authenticated. Mitigation includes anti-CSRF tokens, SameSite cookies, and checking the Origin header.

### SQL Injection
SQL injection occurs when untrusted data is concatenated into SQL queries. Attackers can read, modify, or delete database contents. Parameterized queries (prepared statements) are the definitive defense.

```python
# Vulnerable
query = f"SELECT * FROM users WHERE id = {user_id}"

# Safe
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))
```

## Security Headers

- **Content-Security-Policy** — Controls which resources can be loaded and executed
- **Strict-Transport-Security** — Forces HTTPS connections
- **X-Content-Type-Options** — Prevents MIME type sniffing
- **X-Frame-Options** — Prevents clickjacking by controlling iframe embedding
- **Referrer-Policy** — Controls what information is sent in the Referrer header

## Examples

### Implementing CSP
```
Content-Security-Policy: default-src 'self'; script-src 'self' https://trusted-cdn.com; style-src 'self' 'unsafe-inline'; img-src 'self' data:; object-src 'none'
```

### CORS Configuration
CORS (Cross-Origin Resource Sharing) controls which origins can access your API. A permissive CORS policy is a security risk.

```python
# Restrictive CORS
Access-Control-Allow-Origin: https://myapp.com
Access-Control-Allow-Methods: GET, POST
Access-Control-Allow-Headers: Content-Type, Authorization
```

### Best Practices
- Always use HTTPS with valid TLS certificates
- Hash and salt passwords using bcrypt, Argon2, or PBKDF2
- Use parameterized queries for all database operations
- Implement proper authentication with session management
- Apply the principle of least privilege to all user roles
- Keep all dependencies updated to patch known vulnerabilities
- Validate and sanitize all user input on the server side (never trust client-side validation alone)
- Log security-relevant events and monitor for suspicious activity