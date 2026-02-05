# Codebase Overview

Repository: `test_backend`

---

## System Purpose

This appears to be API service with database persistence with authentication.

### What This System Does

This system manages auditlog, auditlogs, invoiceitem, invoiceitems, invoice data. It exposes a REST API with 19 endpoints (1 DELETE, 8 GET, 1 PATCH, 9 POST). Authentication uses OAuth. Data is persisted using SQLAlchemy ORM with a relational database. Database schema changes are managed through Alembic migrations.

### Domain Entities

The system manages these core data types:

- **AuditLog**
- **AuditLogs (table: audit_logs)**
- **InvoiceItem**
- **InvoiceItems (table: invoice_items)**
- **Invoice**
- **Invoices (table: invoices)**
- **Product**
- **Products (table: products)**
- **ProductUnit**
- **ProductUnits (table: product_units)**

### API Surface

The API exposes 19 endpoint(s):

| Method | Path | Source |
|--------|------|--------|
| `POST` | `/register` | Endpoint in auth_route.py |
| `POST` | `/token` | Endpoint in auth_route.py |
| `POST` | `/login` | Endpoint in auth_route.py |
| `GET` | `/me` | Endpoint in auth_route.py |
| `GET` | `/ping` | Endpoint in auth_route.py |
| `POST` | `/` | Endpoint in invoices_route.py |
| `POST` | `/{invoice_id}/items` | Endpoint in invoices_route.py |
| `GET` | `/all` | Endpoint in invoices_route.py |
| `POST` | `/{invoice_id}/finalize` | Endpoint in invoices_route.py |
| `POST` | `/{invoice_id}/cancel` | Endpoint in invoices_route.py |
| `GET` | `/{invoice_id}` | Endpoint in invoices_route.py |
| `POST` | `/` | Endpoint in products_route.py |
| `GET` | `/` | Endpoint in products_route.py |
| `GET` | `/{product_id}` | Endpoint in products_route.py |
| `GET` | `/{product_id}/units` | Endpoint in products_route.py |

*... and 4 more endpoints*

## Technology Stack

**Languages:**
- Python: 4,034 lines
- Markdown: 563 lines
- INI: 147 lines
- Shell: 98 lines
- TOML: 22 lines

**Frameworks and Libraries:**
- FastAPI (Web Framework)
- SQLAlchemy (ORM)
- Alembic (Database Migrations)
- Pydantic (Data Validation)
- pytest (Testing)

## Project Structure

**Directories:**
- `alembic/` - Alembic database migrations
- `app/` - Main application code
- `scripts/` - Utility scripts
- `tests/` - Test files

**Key Files:**
- `README.md` - Project documentation
- `alembic.ini` - Alembic configuration
- `main.py` - Application entry point
- `pyproject.toml` - Project configuration and dependencies
- `test_api_comprehensive.py` - .py file (481 lines)
- `uv.lock` - uv lock file

## Entry Points

- `app/main.py` - Main application entry point
- `main.py` - Main application entry point

## Configuration

**Configuration Files:**
- `app/core/config.py`
- `pyproject.toml`

**Environment Variables:**
- `VIGILIS_SECRET_KEY`
- `VIGILIS_JWT_ALGORITHM`
- `VIGILIS_ACCESS_TOKEN_EXPIRE_MINUTES`
- `VIGILIS_CORS_ORIGINS`
- `VIGILIS_ADMIN_PASSWORD`
- `VIGILIS_CASHIER_PASSWORD`
- `VIGILIS_SALES_PASSWORD`

## Quick Stats

- **Total Files:** 65
- **Total Lines:** 6,883
- **Languages:** 5
- **Primary Language:** Python

