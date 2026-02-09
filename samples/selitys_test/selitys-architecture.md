# Architecture

Repository: `test_backend`

---

## Subsystems

### API Layer

**Directory:** `app/api/`

HTTP API handlers and endpoints

**Key files:**
- `app/api/router.py`
- `app/api/routes/auth_route.py`
- `app/api/routes/invoices_route.py`
- `app/api/routes/products_route.py`
- `app/api/routes/users_route.py`

### Routing

**Directory:** `app/api/routes/`

HTTP route definitions

**Key files:**
- `app/api/routes/auth_route.py`
- `app/api/routes/invoices_route.py`
- `app/api/routes/products_route.py`
- `app/api/routes/users_route.py`

### Core

**Directory:** `app/core/`

Core application configuration and utilities

**Key files:**
- `app/core/config.py`
- `app/core/dependencies.py`
- `app/core/security.py`

### Database

**Directory:** `app/db/`

Database connection and queries

**Key files:**
- `app/db/base.py`
- `app/db/session.py`

### Data Models

**Directory:** `app/models/`

Database models and entities

**Key files:**
- `app/models/audit_log_table.py`
- `app/models/invoice_item_table.py`
- `app/models/invoice_table.py`
- `app/models/product_table.py`
- `app/models/product_unit_table.py`

### Schemas

**Directory:** `app/schemas/`

Data validation and serialization schemas

**Key files:**
- `app/schemas/invoice_item_schema.py`
- `app/schemas/invoice_schema.py`
- `app/schemas/product_schema.py`
- `app/schemas/product_unit_schema.py`
- `app/schemas/stock_adjustment_schema.py`

### Services

**Directory:** `app/services/`

Business logic and service layer

**Key files:**
- `app/services/audit_service.py`
- `app/services/invoice_service.py`
- `app/services/product_service.py`
- `app/services/product_unit_service.py`
- `app/services/user_service.py`

## Patterns Detected

- Layered architecture (routes -> services -> models)
- Dependency injection
- Request/response schema validation
- Database migrations

## Coupling and Dependencies

Based on the detected subsystems, the likely dependency flow is:

```
API/Routes -> Services -> Models -> Database
```

## Risk Areas

### High Severity

**Possible hardcoded secret** - `tests/test_invoices_flow.py`

Appears to contain hardcoded credentials or secrets

### Medium Severity

**Limited test coverage** - `tests/`

Only 5 test files for 52 code files

### Low Severity

**Large file** - `README.md`

File has 563 lines, may be difficult to maintain

**Large file** - `uv.lock`

File has 1627 lines, may be difficult to maintain

