# CI/CD Pipelines

## Overview
Continuous Integration and Continuous Deployment (CI/CD) is a practice that automates the building, testing, and deployment of software changes. CI ensures that code changes are automatically tested when merged, while CD automates the delivery to staging or production environments.

## CI/CD Concepts

### Continuous Integration
CI is the practice of merging all developer working copies into a shared mainline several times a day. Each merge triggers an automated build and test suite to catch integration errors early. A good CI pipeline includes linting, type checking, unit tests, integration tests, and security scans.

### Continuous Deployment
CD extends CI by automatically deploying every change that passes the pipeline to production. Continuous Delivery (a related concept) stops short of production deployment, keeping the code always in a deployable state but requiring manual approval for production releases.

## Pipeline Stages

A typical CI/CD pipeline consists of these stages:

1. **Source** — Triggered by a push or pull request to the repository
2. **Build** — Compile code, install dependencies, build artifacts
3. **Test** — Run linting, unit tests, integration tests, and code quality checks
4. **Security** — Scan for vulnerabilities in dependencies and code
5. **Deploy (Staging)** — Deploy to a staging environment for further validation
6. **Deploy (Production)** — Deploy to production, often with a gradual rollout

## Example

### GitHub Actions Workflow
```yaml
name: CI/CD Pipeline
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: pytest --cov=app tests/
      - run: ruff check app/

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh
```

### Deployment Strategies
- **Rolling Update** — Replace instances gradually, maintaining availability
- **Blue-Green** — Run two identical environments; switch traffic from old to new
- **Canary** — Route a small percentage of traffic to the new version, then gradually increase
- **Feature Flags** — Deploy code hidden behind flags, enable when ready

### Best Practices
- Keep the pipeline fast — developers should get feedback within 10 minutes
- Run tests in parallel where possible to reduce total pipeline time
- Make the pipeline idempotent — re-running should produce the same result
- Fail fast — fail the pipeline at the first sign of trouble
- Store build artifacts so they can be inspected and redeployed if needed