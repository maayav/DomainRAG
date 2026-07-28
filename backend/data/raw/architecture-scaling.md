# Core Architecture & Scaling

## Overview
Building a production-ready web application requires careful attention to architecture patterns that enable horizontal and vertical scaling, fault tolerance, and high availability. This document covers the foundational infrastructure patterns every backend engineer should understand.

## Stateless Architecture
Stateless architecture ensures server instances can scale up or down without losing user session data. Each request contains all the information needed to process it — no server stores session state locally. This is the foundation of horizontal scaling.

### Key Principles
- Store sessions in external stores (Redis, database)
- Use JWTs or token-based auth instead of server-side sessions
- Design APIs to be idempotent where possible
- Avoid in-memory caches that can't be shared across instances

## Vertical vs Horizontal Scaling
- **Vertical Scaling**: Adding more CPU, RAM, or disk to a single server. Simple but has physical limits.
- **Horizontal Scaling**: Adding more server instances behind a load balancer. More complex but virtually unlimited.

## Reverse Proxy
A reverse proxy like Nginx or Caddy sits in front of your application servers to handle:
- SSL/TLS termination
- Static file serving
- Request routing and URL rewriting
- Compression (gzip/brotli)
- Connection pooling

```nginx
upstream backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
}

server {
    listen 443 ssl;
    server_name example.com;

    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Load Balancing
Load balancers distribute incoming traffic across multiple backend servers.

### Algorithms
- **Round-Robin**: Distributes requests sequentially across servers. Simple and effective for homogeneous servers.
- **Least Connections**: Routes to the server with the fewest active connections. Better for long-running requests.
- **IP Hash**: Routes based on client IP for session affinity without sticky sessions.
- **Weighted Round-Robin**: Assigns more traffic to more powerful servers.

### Sticky Sessions
Binds a user's session to a specific server instance. Use only if stateless storage isn't fully ready. Implemented via cookies or IP hash. Disadvantage: uneven load distribution and failover complexity.

## Database Connection Pooling
Reuses a fixed pool of database connections instead of creating new ones per request. Prevents the database from crashing under high traffic.

```python
# SQLAlchemy connection pooling
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql://user:pass@localhost/db",
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
)
```

### Best Practices
- Set pool size to 2-3x the number of CPU cores
- Use `max_overflow` for burst traffic
- Set `pool_recycle` to prevent stale connections
- Monitor active vs idle connections

## Redis Session Store
Moves user login sessions out of local server memory into a fast, shared cache. Enables stateless architecture and horizontal scaling.

```python
import redis

session_store = redis.Redis(host="localhost", port=6379, db=0)
session_store.setex(f"session:{session_id}", 3600, user_data)
```

## Read Replicas
Directs heavy read traffic (searches, listings, dashboards) to replica databases, keeping the primary database fast for writes.

### Implementation Pattern
- Primary handles: INSERT, UPDATE, DELETE
- Replicas handle: SELECT queries
- Use connection routing in your ORM or middleware
- Replication lag is typically < 1 second but design for eventual consistency

## Database Indexing
Speeds up queries on frequently searched columns. Essential for columns used in WHERE, JOIN, and ORDER BY clauses.

```sql
-- Single column index
CREATE INDEX idx_users_email ON users(email);

-- Composite index (order matters)
CREATE INDEX idx_orders_user_date ON orders(user_id, created_at DESC);

-- Partial index for active records
CREATE INDEX idx_active_users ON users(email) WHERE is_active = true;
```

### Rules of Thumb
- Index columns used in WHERE clauses and JOINs
- Don't over-index — each index slows down writes
- Use EXPLAIN ANALYZE to verify index usage
- Consider covering indexes for read-heavy queries
