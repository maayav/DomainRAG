# Docker Compose

## Overview

Docker Compose is a tool for defining and running multi-container Docker applications. Using a YAML file (`compose.yaml` or `docker-compose.yml`), you declare the services, networks, and volumes that make up your application, then start everything with a single command. Compose is ideal for development, testing, and CI environments where reproducible multi-service setups are required.

## Details

### Services

Each service in Compose corresponds to a container image and its runtime configuration. Services define the container's image, ports, environment variables, dependencies, health checks, and resource limits. The `depends_on` directive controls startup order, though it only waits for a container to start, not for it to become healthy — use `healthcheck` with `depends_on` for true readiness gating.

### Volumes

Volumes persist data generated and used by containers, surviving container restarts and recreations. Compose supports named volumes (managed by Docker) and bind mounts (direct host directory mappings). Named volumes are preferred for production because Docker manages their lifecycle, while bind mounts are common in development for live code reloading.

### Networks

By default, Compose creates a single bridge network for your application, placing all services on the same network where they can reach each other by service name. Custom networks allow you to isolate groups of services, control network driver behavior, and integrate with external networks. Services can be attached to multiple networks for advanced topologies (e.g., a web service on a public-facing network and a database on an internal-only network).

### Environment Variables

Environment variables can be set directly in the Compose file, loaded from an `.env` file, or sourced from a shell environment. The `environment` key accepts key-value pairs, while `env_file` points to a file with `KEY=value` lines. For secrets and sensitive data, use Docker secrets or an external vault rather than plaintext environment variables.

## Examples

```yaml
# docker-compose.yml
version: "3.9"

services:
  web:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgres://user:pass@db:5432/app
      - LOG_LEVEL=debug
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - .:/app
      - /app/node_modules
    networks:
      - frontend
      - backend

  db:
    image: postgres:16-alpine
    restart: unless-stopped
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: app
      POSTGRES_USER: user
      POSTGRES_PASSWORD: "${DB_PASSWORD}"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d app"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend

volumes:
  pgdata:

networks:
  frontend:
  backend:
    internal: true
```

Start the application with `docker compose up -d`, view logs with `docker compose logs -f`, scale services with `docker compose up -d --scale web=3`, and tear everything down with `docker compose down -v` (the `-v` flag removes named volumes).
