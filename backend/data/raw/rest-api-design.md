# REST API Design

## Overview
REST (Representational State Transfer) is an architectural style for designing networked APIs. A well-designed REST API is intuitive, consistent, and follows a set of conventions that make it easy for clients to consume.

## Core Principles
Resources are the key abstraction in REST. Each resource is identified by a URL, and clients interact with resources using standard HTTP methods. Resources should be nouns, not verbs. A well-structured URL hierarchy reflects the relationship between resources.

### HTTP Methods and Their Meanings
- `GET` — Retrieve a resource or collection
- `POST` — Create a new resource
- `PUT` — Replace an existing resource entirely
- `PATCH` — Partially update a resource
- `DELETE` — Remove a resource

## Examples

### URL Structure
```
GET    /api/users           # List all users
GET    /api/users/42        # Get user with ID 42
POST   /api/users           # Create a new user
PUT    /api/users/42        # Replace user 42
PATCH  /api/users/42        # Update user 42's email
DELETE /api/users/42        # Delete user 42
GET    /api/users/42/orders # List orders for user 42
```

### Pagination
```
GET /api/users?page=2&per_page=20
```

Response includes pagination metadata:
```json
{
  "data": [...],
  "pagination": {
    "page": 2,
    "per_page": 20,
    "total": 156,
    "total_pages": 8
  }
}
```

### Status Codes
- `200 OK` — Successful GET, PUT, PATCH
- `201 Created` — Successful POST
- `204 No Content` — Successful DELETE
- `400 Bad Request` — Invalid input
- `401 Unauthorized` — Missing or invalid authentication
- `403 Forbidden` — Authenticated but not authorized
- `404 Not Found` — Resource doesn't exist
- `422 Unprocessable Entity` — Validation errors
- `500 Internal Server Error` — Server-side failure

### Best Practices
- Version your API via URL prefix (`/api/v1/`) or headers
- Use consistent error response format with an error code and message
- Support filtering via query parameters (`?status=active`)
- Use HATEOAS links for discoverability when appropriate
- Rate-limit to protect against abuse, returning `429 Too Many Requests`