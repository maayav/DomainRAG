# Async Python

## Overview
Asynchronous programming in Python allows concurrent execution of I/O-bound tasks without the overhead of threads. The `asyncio` library, introduced in Python 3.4 and matured through subsequent versions, provides the foundation for writing concurrent code using the `async`/`await` syntax.

## Core Concepts
An `async def` function defines a coroutine. Coroutines are suspended at `await` expressions, allowing the event loop to run other tasks while waiting for I/O operations to complete. This is ideal for web requests, database queries, file operations, and network communication.

### The Event Loop
The event loop is the core of asyncio. It manages the execution of multiple coroutines, scheduling them when they're ready to run and suspending them when they await. Starting in Python 3.10, `asyncio.run()` is the preferred way to launch an async program.

## Examples

### Basic Coroutine
```python
import asyncio

async def fetch_data(url):
    print(f"Fetching {url}")
    await asyncio.sleep(1)
    return f"Data from {url}"

async def main():
    result = await fetch_data("https://example.com")
    print(result)

asyncio.run(main())
```

### Concurrent Execution with gather
```python
async def main():
    urls = ["https://site1.com", "https://site2.com", "https://site3.com"]
    results = await asyncio.gather(*[fetch_data(url) for url in urls])
    print(results)

asyncio.run(main())
```

### Task Groups (Python 3.11+)
```python
async def main():
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(fetch_data("https://site1.com"))
        task2 = tg.create_task(fetch_data("https://site2.com"))
    print(task1.result(), task2.result())
```

### Async Context Managers
```python
class AsyncResource:
    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *args):
        await self.disconnect()

async def use_resource():
    async with AsyncResource() as res:
        await res.do_work()
```

### Common Async Libraries
- `aiohttp` — Async HTTP client/server
- `aiosqlite` — Async SQLite access
- `asyncpg` — Async PostgreSQL driver
- `httpx` — HTTP client with async support
- `aiofiles` — Async file operations

### Best Practices
- Use `asyncio.run()` as the entry point
- Avoid mixing blocking code with async code without using `loop.run_in_executor()`
- Use `asyncio.Semaphore` to limit concurrency when rate-limited
- Prefer `TaskGroup` over manual `gather` for structured concurrency in Python 3.11+