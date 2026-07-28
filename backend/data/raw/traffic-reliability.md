# Traffic Control & Reliability Patterns

## Overview
Production systems must handle traffic spikes, prevent abuse, and gracefully degrade when components fail. These patterns protect your application from cascading failures and ensure reliability under load.

## IP-Based Rate Limiting
Restricts how many requests a single user or IP address can make per time window. Essential for API protection and abuse prevention.

```python
from fastapi import Request, HTTPException
from collections import defaultdict
import time

rate_limits = defaultdict(list)

async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    now = time.time()
    window = 60  # 1 minute
    max_requests = 100

    # Clean old entries
    rate_limits[client_ip] = [t for t in rate_limits[client_ip] if now - t < window]

    if len(rate_limits[client_ip]) >= max_requests:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    rate_limits[client_ip].append(now)
    return await call_next(request)
```

## Token Bucket Algorithm
Allows brief bursts of requests while maintaining a strict long-term rate limit. More flexible than fixed-window rate limiting.

### How It Works
1. A bucket holds tokens (e.g., capacity = 10)
2. Tokens are added at a fixed rate (e.g., 1 per second)
3. Each request consumes one token
4. If the bucket is empty, the request is rejected
5. Burst traffic is allowed when the bucket is full

## Circuit Breaker Pattern
Automatically disables failing third-party APIs temporarily so they don't freeze your entire application.

### States
- **Closed**: Normal operation, requests pass through
- **Open**: Failures exceeded threshold, requests are immediately rejected
- **Half-Open**: After a timeout, allows a few test requests to check recovery

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, reset_timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.state = "closed"
        self.last_failure_time = None

    def call(self, func, *args):
        if self.state == "open":
            if time.time() - self.last_failure_time > self.reset_timeout:
                self.state = "half-open"
            else:
                raise Exception("Circuit is open")

        try:
            result = func(*args)
            self.failure_count = 0
            self.state = "closed"
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            raise e
```

## Graceful Degradation
Switches off non-essential features when the server is overloaded. For example:
- Disable avatar loading under heavy traffic
- Show cached recommendations instead of real-time ones
- Reduce image quality or skip thumbnails
- Queue non-critical notifications instead of sending immediately

## Asynchronous Message Queues
Moves slow tasks to background workers so the API remains fast.

### Common Use Cases
- Image processing and resizing
- Email and notification sending
- PDF generation
- Data exports and reports
- Webhook delivery

### Tools
- **Redis Queue (RQ)**: Simple Python job queue
- **Celery**: Full-featured distributed task queue
- **Bull/BullMQ**: Node.js queue backed by Redis
- **RabbitMQ**: Enterprise-grade message broker

## API Idempotency Keys
Prevents double-charging or double-posting if a user clicks a button twice or a network retry occurs.

```python
@app.post("/api/charge")
async def charge(request: ChargeRequest):
    # Check if this idempotency key was already processed
    existing = await db.get(f"idempotency:{request.idempotency_key}")
    if existing:
        return existing  # Return cached response

    # Process the charge
    result = await process_payment(request)

    # Cache the result with TTL
    await db.setex(f"idempotency:{request.idempotency_key}", 86400, result)
    return result
```

## Token Consumption Quotas
Tracks and limits how many expensive AI API tokens a user can consume per day. Critical for controlling costs in AI-powered applications.

### Implementation
- Track token usage per user per day in Redis or a database
- Set daily/monthly limits per pricing tier
- Return remaining quota in response headers
- Send warnings at 80% and 95% usage thresholds
