# Aventus Backend - Refactoring Implementation Plan

> **Document Version:** 1.0
> **Created:** December 9, 2024
> **Purpose:** Complete guide for refactoring the Aventus backend from monolithic to modular architecture

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current State Analysis](#2-current-state-analysis)
3. [Target Architecture](#3-target-architecture)
4. [Refactoring Scope](#4-refactoring-scope)
5. [Target Folder Structure](#5-target-folder-structure)
6. [Implementation Phases](#6-implementation-phases)
7. [Detailed Implementation Guide](#7-detailed-implementation-guide)
8. [Code Patterns & Examples](#8-code-patterns--examples)
9. [Migration Checklist](#9-migration-checklist)
10. [Testing Strategy](#10-testing-strategy)
11. [Rollback Plan](#11-rollback-plan)

---

## 1. Executive Summary

### Goal
Transform the current monolithic, procedural codebase into a modular, object-oriented, scalable architecture following SOLID principles and clean architecture patterns.

### Key Problems to Solve
- **3,807-line route files** with mixed concerns
- **2,894-line email.py** with hardcoded HTML templates
- **No middlewares** for logging, error handling, rate limiting
- **Procedural code** instead of OOP
- **No standardized migrations** (ad-hoc scripts)
- **No testing infrastructure**
- **No containerization**
- **Tightly coupled components** that can't be tested or extended independently

### Key Outcomes
- Clean separation of concerns
- Testable, maintainable code
- Extensible architecture (add features without modifying existing code)
- Fault isolation (one component failing doesn't crash others)
- Production-ready infrastructure (Docker, Alembic, logging, monitoring)

---

## 2. Current State Analysis

### Current Folder Structure
```
Aventus Backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/           # 11 SQLAlchemy models
│   │   ├── user.py
│   │   ├── contractor.py      # 305 lines
│   │   ├── client.py
│   │   ├── contract.py
│   │   ├── timesheet.py
│   │   ├── work_order.py
│   │   ├── third_party.py
│   │   ├── quote_sheet.py     # 199 columns
│   │   ├── proposal.py
│   │   └── template.py
│   ├── routes/           # 10 route files (~7,500 lines total)
│   │   ├── auth.py            # 381 lines
│   │   ├── contractors.py     # 3,807 lines (MAIN PROBLEM)
│   │   ├── clients.py         # 239 lines
│   │   ├── contracts.py       # 541 lines
│   │   ├── timesheets.py      # 645 lines
│   │   ├── work_orders.py     # 483 lines
│   │   ├── third_parties.py   # 255 lines
│   │   ├── quote_sheets.py    # 637 lines
│   │   ├── proposals.py       # 291 lines
│   │   └── templates.py       # 155 lines
│   ├── schemas/          # Pydantic models
│   └── utils/            # Mixed utilities
│       ├── auth.py
│       ├── email.py           # 2,894 lines (14 functions with hardcoded HTML)
│       ├── storage.py
│       ├── cohf_pdf_generator.py
│       ├── contract_pdf_generator.py
│       ├── work_order_pdf_generator.py
│       ├── quote_sheet_pdf_generator.py
│       └── timesheet_pdf_generator.py
├── migrations/           # Ad-hoc migration scripts
├── run.py
├── setup.bat
└── requirements.txt
```

### Current Problems

| Problem | Location | Impact |
|---------|----------|--------|
| Massive route files | `contractors.py` (3,807 lines) | Unmaintainable, untestable |
| Hardcoded templates | `email.py` (2,894 lines) | Can't change branding without code changes |
| No middlewares | `main.py` | No logging, error handling, rate limiting |
| Procedural code | Everywhere | No reusability, hard to extend |
| Duplicated code | PDF generators, email functions | Same logic repeated 5-14 times |
| No migrations | `migrations/` folder | Ad-hoc scripts, no version control |
| No tests | N/A | Can't verify changes don't break things |
| No Docker | `run.py`, `setup.bat` | Can't deploy consistently |
| Tight coupling | Routes call DB, email, storage directly | Can't test in isolation |

---

## 3. Target Architecture

### Architecture Principles

1. **Modular Monolith** - Clean boundaries, single deployment
2. **Clean Architecture** - Dependencies point inward (domain has no dependencies)
3. **SOLID Principles** - Single responsibility, open/closed, etc.
4. **Dependency Injection** - Pass dependencies, don't hardcode them
5. **Strategy Pattern** - For varying behaviors (onboarding routes)
6. **Repository Pattern** - Abstract database access
7. **Adapter Pattern** - Abstract external services

### Layer Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        API LAYER                                │
│   FastAPI routers (thin, HTTP only, no business logic)          │
├─────────────────────────────────────────────────────────────────┤
│                      SERVICE LAYER                              │
│   Application use cases, orchestration, transaction management  │
├─────────────────────────────────────────────────────────────────┤
│                      DOMAIN LAYER                               │
│   Pure business logic, entities, rules (NO framework code)      │
├─────────────────────────────────────────────────────────────────┤
│                    REPOSITORY LAYER                             │
│   Database access abstractions, SQLAlchemy implementations      │
├─────────────────────────────────────────────────────────────────┤
│                     ADAPTER LAYER                               │
│   External integrations (Email, Storage, PDF, Queue)            │
└─────────────────────────────────────────────────────────────────┘
```

### Dependency Flow

```
API → Services → Domain ← Repositories
                   ↑
                Adapters

Domain has NO dependencies on other layers.
Services depend on Domain and interfaces (not implementations).
Adapters implement interfaces defined in Domain or Services.
```

---

## 4. Refactoring Scope

### Complete List of Changes

| # | Topic | Current State | Target State | Priority |
|---|-------|---------------|--------------|----------|
| 1 | Folder Structure | Flat `routes/`, `utils/` | Layered architecture | HIGH |
| 2 | Middlewares | Only CORS | 6 middlewares (correlation, logging, errors, rate limit, security, timing) | HIGH |
| 3 | Templates | Hardcoded in Python | Jinja2 with base + components | HIGH |
| 4 | OOP Refactor | Procedural functions | Classes with inheritance, polymorphism | HIGH |
| 5 | Repository Pattern | Direct DB calls in routes | Repository classes | HIGH |
| 6 | Service Layer | Logic in routes | Service classes | HIGH |
| 7 | Domain Layer | Mixed with routes | Pure business logic classes | HIGH |
| 8 | Adapters | Direct calls to Resend, Supabase | Interface + Implementation | HIGH |
| 9 | Error Handling | Scattered try/catch | Custom exception hierarchy | MEDIUM |
| 10 | Logging | `print()` statements | Structured JSON logging | MEDIUM |
| 11 | Alembic | Ad-hoc scripts | Proper migrations | MEDIUM |
| 12 | Docker | None | Dockerfile + docker-compose | MEDIUM |
| 13 | Testing | None | Unit + Integration tests | MEDIUM |
| 14 | Configuration | Single `.env` | Environment-specific configs | MEDIUM |
| 15 | Background Jobs | Synchronous | SQS + Workers | LOW |
| 16 | Caching | None | Redis | LOW |
| 17 | API Versioning | Basic `/api/v1/` | Deprecation strategy | LOW |

---

## 5. Target Folder Structure

```
aventus-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI app initialization + middleware setup
│   ├── database.py               # SQLAlchemy engine + session
│   │
│   ├── api/                      # HTTP Layer (THIN - no business logic)
│   │   ├── __init__.py
│   │   ├── dependencies.py       # Shared FastAPI dependencies
│   │   ├── responses.py          # Standard response formatters
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py         # Main router that includes all sub-routers
│   │       ├── auth.py           # ~50 lines (delegates to AuthService)
│   │       ├── contractors.py    # ~100 lines (delegates to ContractorService)
│   │       ├── clients.py
│   │       ├── contracts.py
│   │       ├── timesheets.py
│   │       ├── work_orders.py
│   │       ├── third_parties.py
│   │       ├── quote_sheets.py
│   │       ├── proposals.py
│   │       └── templates.py
│   │
│   ├── domain/                   # Business Logic (NO framework dependencies)
│   │   ├── __init__.py
│   │   │
│   │   ├── contractor/
│   │   │   ├── __init__.py
│   │   │   ├── entity.py         # Contractor entity (business object)
│   │   │   ├── value_objects.py  # ContractorStatus, OnboardingRoute, etc.
│   │   │   ├── rules.py          # Business rules validation
│   │   │   ├── state_machine.py  # Status transitions
│   │   │   └── exceptions.py     # ContractorNotFoundError, etc.
│   │   │
│   │   ├── onboarding/
│   │   │   ├── __init__.py
│   │   │   ├── workflow.py       # Workflow orchestration
│   │   │   ├── registry.py       # Strategy registry
│   │   │   └── strategies/
│   │   │       ├── __init__.py
│   │   │       ├── base.py       # OnboardingStrategy ABC
│   │   │       ├── uae.py        # UAEOnboardingStrategy
│   │   │       ├── saudi.py      # SaudiOnboardingStrategy
│   │   │       ├── offshore.py   # OffshoreOnboardingStrategy
│   │   │       ├── wps.py        # WPSOnboardingStrategy
│   │   │       └── freelancer.py # FreelancerOnboardingStrategy
│   │   │
│   │   ├── client/
│   │   │   ├── __init__.py
│   │   │   ├── entity.py
│   │   │   └── exceptions.py
│   │   │
│   │   ├── contract/
│   │   │   ├── __init__.py
│   │   │   ├── entity.py
│   │   │   ├── state_machine.py
│   │   │   └── exceptions.py
│   │   │
│   │   ├── work_order/
│   │   │   ├── __init__.py
│   │   │   ├── entity.py
│   │   │   ├── state_machine.py
│   │   │   └── exceptions.py
│   │   │
│   │   ├── timesheet/
│   │   │   ├── __init__.py
│   │   │   ├── entity.py
│   │   │   └── exceptions.py
│   │   │
│   │   ├── quote_sheet/
│   │   │   ├── __init__.py
│   │   │   ├── entity.py
│   │   │   └── exceptions.py
│   │   │
│   │   ├── token/
│   │   │   ├── __init__.py
│   │   │   └── token.py          # Token value object with validation
│   │   │
│   │   └── shared/
│   │       ├── __init__.py
│   │       ├── entity.py         # Base entity class
│   │       └── value_objects.py  # Shared value objects
│   │
│   ├── services/                 # Application Use Cases
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── contractor_service.py
│   │   ├── onboarding_service.py
│   │   ├── client_service.py
│   │   ├── contract_service.py
│   │   ├── work_order_service.py
│   │   ├── timesheet_service.py
│   │   ├── quote_sheet_service.py
│   │   ├── notification_service.py
│   │   └── document_service.py
│   │
│   ├── repositories/             # Data Access Layer
│   │   ├── __init__.py
│   │   ├── interfaces/           # Repository interfaces (ABCs)
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── contractor_repo.py
│   │   │   ├── client_repo.py
│   │   │   └── ...
│   │   └── implementations/      # SQLAlchemy implementations
│   │       ├── __init__.py
│   │       ├── base.py           # BaseRepository implementation
│   │       ├── contractor_repo.py
│   │       ├── client_repo.py
│   │       └── ...
│   │
│   ├── adapters/                 # External Service Integrations
│   │   ├── __init__.py
│   │   │
│   │   ├── email/
│   │   │   ├── __init__.py
│   │   │   ├── interface.py      # EmailSender ABC
│   │   │   ├── resend_adapter.py # Resend implementation
│   │   │   └── template_engine.py
│   │   │
│   │   ├── storage/
│   │   │   ├── __init__.py
│   │   │   ├── interface.py      # StorageAdapter ABC
│   │   │   └── supabase_adapter.py
│   │   │
│   │   ├── pdf/
│   │   │   ├── __init__.py
│   │   │   ├── interface.py      # PDFGenerator ABC
│   │   │   ├── base.py           # BasePDFGenerator with shared logic
│   │   │   ├── registry.py       # PDFGeneratorRegistry
│   │   │   ├── cohf_generator.py
│   │   │   ├── contract_generator.py
│   │   │   ├── work_order_generator.py
│   │   │   ├── quote_sheet_generator.py
│   │   │   └── timesheet_generator.py
│   │   │
│   │   └── queue/
│   │       ├── __init__.py
│   │       ├── interface.py      # QueueAdapter ABC
│   │       ├── sqs_adapter.py    # AWS SQS implementation
│   │       └── memory_adapter.py # In-memory for testing/dev
│   │
│   ├── models/                   # SQLAlchemy ORM Models
│   │   ├── __init__.py
│   │   ├── base.py               # Base model with common fields
│   │   ├── user.py
│   │   ├── contractor.py
│   │   ├── client.py
│   │   ├── contract.py
│   │   ├── timesheet.py
│   │   ├── work_order.py
│   │   ├── third_party.py
│   │   ├── quote_sheet.py
│   │   ├── proposal.py
│   │   └── template.py
│   │
│   ├── schemas/                  # Pydantic Request/Response Models
│   │   ├── __init__.py
│   │   ├── base.py               # Shared schema utilities
│   │   ├── auth.py
│   │   ├── contractor.py
│   │   ├── client.py
│   │   ├── contract.py
│   │   ├── timesheet.py
│   │   ├── work_order.py
│   │   ├── third_party.py
│   │   ├── quote_sheet.py
│   │   ├── proposal.py
│   │   └── template.py
│   │
│   ├── middlewares/              # Request/Response Processing
│   │   ├── __init__.py
│   │   ├── correlation.py        # X-Correlation-ID handling
│   │   ├── logging.py            # Request/response logging
│   │   ├── error_handler.py      # Global exception handling
│   │   ├── rate_limit.py         # Rate limiting
│   │   ├── security.py           # Security headers
│   │   └── timing.py             # Response time tracking
│   │
│   ├── exceptions/               # Custom Exceptions
│   │   ├── __init__.py
│   │   ├── base.py               # BaseAppException
│   │   ├── auth.py               # AuthenticationError, AuthorizationError
│   │   ├── contractor.py         # ContractorNotFoundError, etc.
│   │   ├── validation.py         # ValidationError variants
│   │   └── external.py           # EmailError, StorageError, etc.
│   │
│   ├── workers/                  # Background Job Processors
│   │   ├── __init__.py
│   │   ├── base.py               # BaseWorker
│   │   ├── email_worker.py       # Async email sending
│   │   └── pdf_worker.py         # Async PDF generation
│   │
│   ├── telemetry/                # Observability
│   │   ├── __init__.py
│   │   ├── logger.py             # Structured JSON logger
│   │   ├── tracing.py            # OpenTelemetry setup
│   │   └── metrics.py            # Custom metrics
│   │
│   ├── config/                   # Configuration Management
│   │   ├── __init__.py
│   │   ├── settings.py           # Pydantic Settings class
│   │   ├── feature_flags.py      # Feature flag definitions
│   │   └── environments/
│   │       ├── __init__.py
│   │       ├── base.py           # Shared settings
│   │       ├── development.py
│   │       ├── staging.py
│   │       └── production.py
│   │
│   └── templates/                # Jinja2 Templates
│       ├── email/
│       │   ├── base.html         # Master email layout
│       │   ├── components/
│       │   │   ├── header.html
│       │   │   ├── footer.html
│       │   │   ├── button.html
│       │   │   ├── credentials_box.html
│       │   │   ├── expiry_notice.html
│       │   │   └── signature_block.html
│       │   ├── contract_signing.html
│       │   ├── activation.html
│       │   ├── password_reset.html
│       │   ├── document_upload.html
│       │   ├── documents_uploaded.html
│       │   ├── review_notification.html
│       │   ├── quote_sheet_request.html
│       │   ├── proposal.html
│       │   ├── work_order.html
│       │   ├── work_order_client.html
│       │   ├── timesheet_manager.html
│       │   ├── timesheet_uploaded.html
│       │   └── cohf.html
│       └── pdf/
│           ├── base.html
│           ├── cohf.html
│           ├── contract.html
│           ├── work_order.html
│           ├── quote_sheet.html
│           └── timesheet.html
│
├── alembic/                      # Database Migrations
│   ├── versions/
│   │   └── .gitkeep
│   ├── env.py
│   ├── script.py.mako
│   └── alembic.ini
│
├── tests/                        # Test Suite
│   ├── __init__.py
│   ├── conftest.py               # Pytest fixtures
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── domain/
│   │   │   ├── test_contractor.py
│   │   │   ├── test_onboarding_strategies.py
│   │   │   └── test_state_machines.py
│   │   └── services/
│   │       ├── test_contractor_service.py
│   │       └── test_notification_service.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── api/
│   │   │   ├── test_contractors_api.py
│   │   │   └── test_auth_api.py
│   │   └── repositories/
│   │       └── test_contractor_repo.py
│   └── fixtures/
│       ├── contractors.py
│       └── users.py
│
├── docker/
│   ├── Dockerfile                # Main application
│   ├── Dockerfile.worker         # Background worker
│   └── docker-compose.yml        # Local development
│
├── docs/
│   ├── api/
│   │   └── openapi.yaml
│   ├── architecture/
│   │   ├── overview.md
│   │   ├── layers.md
│   │   └── patterns.md
│   └── adrs/                     # Architecture Decision Records
│       ├── 001-modular-monolith.md
│       ├── 002-repository-pattern.md
│       └── 003-strategy-pattern.md
│
├── scripts/
│   ├── seed_db.py
│   ├── migrate.py
│   └── setup_local.sh
│
├── .env.example
├── .env.development
├── .env.staging
├── .env.production
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

---

## 6. Implementation Phases

### Phase 0: Foundation (Week 1)
**Goal:** Set up infrastructure without breaking existing code

- [ ] Create new folder structure (alongside existing)
- [ ] Set up Docker + docker-compose
- [ ] Set up Alembic migrations
- [ ] Set up structured logging (telemetry/)
- [ ] Create base classes and interfaces
- [ ] Set up pytest + fixtures

### Phase 1: Middlewares (Week 1)
**Goal:** Add cross-cutting concerns

- [ ] Implement CorrelationIdMiddleware
- [ ] Implement LoggingMiddleware
- [ ] Implement ErrorHandlingMiddleware
- [ ] Implement RateLimitMiddleware
- [ ] Implement SecurityHeadersMiddleware
- [ ] Implement TimingMiddleware
- [ ] Wire up in main.py

### Phase 2: Templates (Week 2)
**Goal:** Extract hardcoded HTML to Jinja2 templates

- [ ] Create base email template
- [ ] Create email components (header, footer, button, etc.)
- [ ] Create all 14 email templates
- [ ] Create EmailTemplateEngine
- [ ] Create PDF base template
- [ ] Create PDF templates
- [ ] Test all templates render correctly

### Phase 3: Domain Layer (Week 2-3)
**Goal:** Extract pure business logic

- [ ] Create domain entities
- [ ] Create value objects (ContractorStatus, OnboardingRoute, etc.)
- [ ] Create state machines for status transitions
- [ ] Create onboarding strategies (UAE, Saudi, Offshore, WPS, Freelancer)
- [ ] Create strategy registry
- [ ] Create domain exceptions
- [ ] Create Token value object
- [ ] Unit test all domain logic

### Phase 4: Repository Layer (Week 3)
**Goal:** Abstract database access

- [ ] Create repository interfaces
- [ ] Create BaseRepository implementation
- [ ] Create ContractorRepository
- [ ] Create ClientRepository
- [ ] Create all other repositories
- [ ] Integration test repositories

### Phase 5: Adapter Layer (Week 3-4)
**Goal:** Abstract external services

- [ ] Create EmailSender interface + ResendAdapter
- [ ] Create StorageAdapter interface + SupabaseAdapter
- [ ] Create PDFGenerator interface + implementations
- [ ] Create BasePDFGenerator with shared logic
- [ ] Create QueueAdapter interface (for future)
- [ ] Test adapters with mocks

### Phase 6: Service Layer (Week 4)
**Goal:** Create application use cases

- [ ] Create ContractorService
- [ ] Create OnboardingService
- [ ] Create ClientService
- [ ] Create ContractService
- [ ] Create WorkOrderService
- [ ] Create TimesheetService
- [ ] Create QuoteSheetService
- [ ] Create NotificationService
- [ ] Create DocumentService
- [ ] Create AuthService
- [ ] Test services with mocked repositories/adapters

### Phase 7: API Layer Refactor (Week 5)
**Goal:** Make routes thin, delegate to services

- [ ] Refactor auth routes (~50 lines)
- [ ] Refactor contractors routes (~100 lines)
- [ ] Refactor clients routes
- [ ] Refactor all other routes
- [ ] Create shared dependencies
- [ ] Create response formatters
- [ ] Integration test all endpoints

### Phase 8: Testing & Documentation (Week 5-6)
**Goal:** Ensure quality and knowledge transfer

- [ ] Achieve 80%+ test coverage on domain
- [ ] Achieve 60%+ test coverage on services
- [ ] API integration tests for all endpoints
- [ ] Update OpenAPI documentation
- [ ] Write architecture documentation
- [ ] Create ADRs for major decisions

### Phase 9: Cleanup & Optimization (Week 6)
**Goal:** Remove old code, optimize

- [ ] Remove old `utils/email.py`
- [ ] Remove old route files
- [ ] Remove ad-hoc migration scripts
- [ ] Performance testing
- [ ] Security audit
- [ ] Final code review

---

## 7. Detailed Implementation Guide

### 7.1 Middlewares Implementation

#### CorrelationIdMiddleware
```python
# app/middlewares/correlation.py
import uuid
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Context variable accessible throughout request lifecycle
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle X-Correlation-ID header.
    - Extracts from incoming request or generates new UUID
    - Makes it available via context variable
    - Adds to response headers
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Get from header or generate new
        correlation_id = request.headers.get(
            "X-Correlation-ID",
            str(uuid.uuid4())
        )

        # Store in context (accessible anywhere in request lifecycle)
        correlation_id_var.set(correlation_id)

        # Process request
        response = await call_next(request)

        # Add to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        return response


def get_correlation_id() -> str:
    """Helper function to get current correlation ID"""
    return correlation_id_var.get()
```

#### LoggingMiddleware
```python
# app/middlewares/logging.py
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.telemetry.logger import get_logger
from app.middlewares.correlation import get_correlation_id

logger = get_logger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured request/response logging.
    - Logs request start with method, path, client IP
    - Logs request completion with status code and duration
    - Includes correlation ID in all logs
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()

        # Log request start
        logger.info(
            "Request started",
            extra={
                "correlation_id": get_correlation_id(),
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else "unknown",
            }
        )

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log request completion
        log_method = logger.info if response.status_code < 400 else logger.warning
        log_method(
            "Request completed",
            extra={
                "correlation_id": get_correlation_id(),
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            }
        )

        return response
```

#### ErrorHandlingMiddleware
```python
# app/middlewares/error_handler.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.telemetry.logger import get_logger
from app.middlewares.correlation import get_correlation_id
from app.exceptions.base import BaseAppException
from app.exceptions.auth import AuthenticationError, AuthorizationError
from app.exceptions.validation import ValidationError
from pydantic import ValidationError as PydanticValidationError

logger = get_logger(__name__)

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Global exception handler middleware.
    - Catches all exceptions
    - Returns consistent error response format
    - Logs errors with full context
    - Never exposes stack traces to clients
    """

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)

        except AuthenticationError as e:
            return self._create_error_response(401, "authentication_error", str(e))

        except AuthorizationError as e:
            return self._create_error_response(403, "authorization_error", str(e))

        except ValidationError as e:
            return self._create_error_response(422, "validation_error", str(e), e.details)

        except PydanticValidationError as e:
            return self._create_error_response(422, "validation_error", "Invalid request data", e.errors())

        except BaseAppException as e:
            return self._create_error_response(e.status_code, e.error_code, str(e))

        except Exception as e:
            # Log full exception for debugging
            logger.exception(
                "Unhandled exception",
                extra={
                    "correlation_id": get_correlation_id(),
                    "path": request.url.path,
                    "method": request.method,
                }
            )

            # Return safe message to client
            return self._create_error_response(
                500,
                "internal_error",
                "An unexpected error occurred. Please try again later."
            )

    def _create_error_response(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: dict = None
    ) -> JSONResponse:
        content = {
            "success": False,
            "error": {
                "code": error_code,
                "message": message,
                "correlation_id": get_correlation_id(),
            }
        }
        if details:
            content["error"]["details"] = details

        return JSONResponse(status_code=status_code, content=content)
```

#### RateLimitMiddleware
```python
# app/middlewares/rate_limit.py
import time
from collections import defaultdict
from typing import Dict, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.middlewares.correlation import get_correlation_id

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiter.
    For production, use Redis-based rate limiting.
    """

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Clean old requests (older than 1 minute)
        self.requests[client_ip] = [
            t for t in self.requests[client_ip]
            if now - t < 60
        ]

        # Check limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "code": "rate_limit_exceeded",
                        "message": "Too many requests. Please slow down.",
                        "correlation_id": get_correlation_id(),
                        "retry_after": 60,
                    }
                },
                headers={"Retry-After": "60"}
            )

        # Record request
        self.requests[client_ip].append(now)

        return await call_next(request)
```

#### SecurityHeadersMiddleware
```python
# app/middlewares/security.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security headers to all responses.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Only add HSTS in production
        # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response
```

#### TimingMiddleware
```python
# app/middlewares/timing.py
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class TimingMiddleware(BaseHTTPMiddleware):
    """
    Adds X-Response-Time header to all responses.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        return response
```

#### Wire Up in main.py
```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middlewares.correlation import CorrelationIdMiddleware
from app.middlewares.logging import LoggingMiddleware
from app.middlewares.error_handler import ErrorHandlingMiddleware
from app.middlewares.rate_limit import RateLimitMiddleware
from app.middlewares.security import SecurityHeadersMiddleware
from app.middlewares.timing import TimingMiddleware
from app.api.v1.router import router as api_v1_router
from app.config.settings import settings

def create_app() -> FastAPI:
    app = FastAPI(
        title="Aventus HR API",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Add middlewares (order matters - first added = outermost)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(TimingMiddleware)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=100)
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(api_v1_router, prefix="/api/v1")

    return app

app = create_app()
```

---

### 7.2 Templates Implementation

#### Base Email Template
```html
<!-- app/templates/email/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ subject }}</title>
    <style>
        /* Reset */
        * { margin: 0; padding: 0; box-sizing: border-box; }

        /* Base styles */
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #1a1a1a;
            background-color: #f5f5f5;
            padding: 20px 0;
        }

        /* Email wrapper */
        .email-wrapper {
            max-width: 560px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        /* Header */
        .header {
            background-color: #ffffff;
            padding: 24px 24px 16px 24px;
            text-align: center;
            border-bottom: 2px solid #f0f0f0;
        }
        .logo { max-width: 120px; height: auto; margin-bottom: 12px; }
        .header-title { color: #FF6B00; font-size: 18px; font-weight: 600; margin: 0; }

        /* Content */
        .content { padding: 24px; }
        .greeting { font-size: 18px; font-weight: 600; color: #1a1a1a; margin-bottom: 16px; }
        .intro-text { font-size: 14px; color: #4a4a4a; margin-bottom: 16px; line-height: 1.6; }

        /* CTA Button */
        .cta-container { text-align: center; margin: 20px 0; }
        .cta-button {
            display: inline-block;
            background-color: #FF6B00;
            color: #ffffff;
            text-decoration: none;
            padding: 12px 32px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 14px;
        }

        /* Notice box */
        .notice {
            background-color: #fffbf0;
            border-left: 3px solid #ffa726;
            padding: 12px 16px;
            margin: 20px 0;
            border-radius: 4px;
        }
        .notice strong { color: #f57c00; display: block; margin-bottom: 4px; font-size: 13px; }
        .notice p { margin: 0; color: #5d4037; font-size: 13px; }

        /* Credentials box */
        .credentials {
            background-color: #f9f9f9;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 16px;
            margin: 16px 0;
        }
        .credentials-title { font-size: 13px; font-weight: 600; color: #333333; margin-bottom: 12px; }
        .cred-row { margin-bottom: 10px; }
        .cred-label { font-size: 12px; color: #666666; display: block; margin-bottom: 4px; }
        .cred-value {
            font-size: 14px;
            color: #1a1a1a;
            font-weight: 500;
            font-family: 'Courier New', monospace;
            background-color: #ffffff;
            padding: 6px 10px;
            border-radius: 3px;
            border: 1px solid #d0d0d0;
            display: inline-block;
        }

        /* Divider */
        .divider { height: 1px; background-color: #e0e0e0; margin: 20px 0; }

        /* Signature */
        .signature { margin-top: 20px; font-size: 14px; color: #4a4a4a; }
        .signature-name { font-weight: 600; color: #FF6B00; }

        /* Footer */
        .footer {
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            border-top: 1px solid #e0e0e0;
        }
        .footer-text { font-size: 12px; color: #6b6b6b; margin: 6px 0; }
    </style>
</head>
<body>
    <div class="email-wrapper">
        <div class="header">
            <img src="{{ logo_url }}" alt="{{ company_name }}" class="logo">
            <h1 class="header-title">{{ company_name }}</h1>
        </div>

        <div class="content">
            {% block content %}{% endblock %}
        </div>

        <div class="footer">
            <p class="footer-text">This is an automated message. Please do not reply to this email.</p>
            <p class="footer-text">If you did not expect this email, please contact us immediately.</p>
            <p class="footer-text" style="margin-top: 15px; color: #999;">&copy; 2025 {{ company_name }}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
```

#### Contract Signing Email Template
```html
<!-- app/templates/email/contract_signing.html -->
{% extends "email/base.html" %}

{% block content %}
<h2 class="greeting">Hello, {{ contractor_name }}!</h2>

<p class="intro-text">
    Welcome to {{ company_name }}! We're thrilled to have you join our team.
</p>

<div style="background-color: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 6px; padding: 20px; margin: 20px 0; text-align: center;">
    <div style="font-size: 36px; margin-bottom: 10px;">📄</div>
    <div style="font-size: 16px; font-weight: 600; color: #1a1a1a; margin-bottom: 8px;">Your Employment Contract is Ready</div>
    <p style="color: #6b6b6b; font-size: 14px; margin-top: 10px;">
        Please review and sign your employment contract to complete your onboarding.
    </p>
</div>

<div class="cta-container">
    <a href="{{ contract_link }}" class="cta-button">Review & Sign Contract</a>
</div>

<div class="notice">
    <strong>Time-Sensitive Document</strong>
    <p>This contract link will expire on <strong>{{ expiry_date }}</strong>. Please review and sign it at your earliest convenience.</p>
</div>

<div class="divider"></div>

<p class="intro-text">
    If you have any questions or concerns about the contract, please don't hesitate to reach out to our HR team. We're here to help make this process as smooth as possible.
</p>

<div class="signature">
    Best regards,<br>
    <span class="signature-name">The {{ company_name }} Team</span>
</div>
{% endblock %}
```

#### Activation Email Template
```html
<!-- app/templates/email/activation.html -->
{% extends "email/base.html" %}

{% block content %}
<h2 class="greeting">Welcome, {{ contractor_name }}!</h2>

<p class="intro-text">
    Your account has been created. Below are your login credentials to access your dashboard.
</p>

<div class="credentials">
    <div class="credentials-title">Login Credentials</div>
    <div class="cred-row">
        <span class="cred-label">Email</span><br>
        <span class="cred-value">{{ contractor_email }}</span>
    </div>
    <div class="cred-row">
        <span class="cred-label">Temporary Password</span><br>
        <span class="cred-value">{{ temporary_password }}</span>
    </div>
</div>

<div class="notice">
    <strong>Important Security Notice</strong>
    <p>For your security, you will be required to change your password upon first login. Please keep your credentials secure and do not share them with anyone.</p>
</div>

<div class="cta-container">
    <a href="{{ login_link }}" class="cta-button">Login to Dashboard</a>
</div>

<div class="signature">
    Best regards,<br>
    <span class="signature-name">The {{ company_name }} Team</span>
</div>
{% endblock %}
```

#### Email Template Engine
```python
# app/adapters/email/template_engine.py
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from typing import Any, Dict
from app.config.settings import settings

class EmailTemplateEngine:
    """
    Jinja2-based email template rendering engine.
    - Loads templates from templates/email/
    - Provides common context (company_name, logo_url)
    - Renders templates with provided context
    """

    def __init__(self):
        template_dir = Path(__file__).parent.parent.parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def render(self, template_name: str, **context: Any) -> str:
        """
        Render an email template with context.

        Args:
            template_name: Template name without extension (e.g., "contract_signing")
            **context: Variables to pass to the template

        Returns:
            Rendered HTML string
        """
        template = self.env.get_template(f"email/{template_name}.html")

        # Merge with default context
        full_context = {
            "company_name": settings.company_name,
            "logo_url": settings.logo_url,
            **context
        }

        return template.render(**full_context)

    def render_with_subject(self, template_name: str, subject: str, **context: Any) -> tuple[str, str]:
        """
        Render template and return both subject and HTML.

        Returns:
            Tuple of (subject, html_content)
        """
        html = self.render(template_name, subject=subject, **context)
        return subject, html


# Singleton instance
email_template_engine = EmailTemplateEngine()
```

---

### 7.3 Domain Layer Implementation

#### Base Entity
```python
# app/domain/shared/entity.py
from abc import ABC
from datetime import datetime
from typing import Optional

class Entity(ABC):
    """Base class for all domain entities."""

    def __init__(
        self,
        id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at

    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)
```

#### Contractor Value Objects
```python
# app/domain/contractor/value_objects.py
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class ContractorStatus(str, Enum):
    """All possible contractor statuses."""
    DRAFT = "draft"
    PENDING_DOCUMENTS = "pending_documents"
    DOCUMENTS_UPLOADED = "documents_uploaded"
    PENDING_COHF = "pending_cohf"
    AWAITING_COHF_SIGNATURE = "awaiting_cohf_signature"
    COHF_COMPLETED = "cohf_completed"
    PENDING_THIRD_PARTY_QUOTE = "pending_third_party_quote"
    PENDING_CDS_CS = "pending_cds_cs"
    CDS_CS_COMPLETED = "cds_cs_completed"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING_CLIENT_WO_SIGNATURE = "pending_client_wo_signature"
    WORK_ORDER_COMPLETED = "work_order_completed"
    PENDING_3RD_PARTY_CONTRACT = "pending_3rd_party_contract"
    PENDING_CONTRACT_UPLOAD = "pending_contract_upload"
    CONTRACT_APPROVED = "contract_approved"
    PENDING_SIGNATURE = "pending_signature"
    SIGNED = "signed"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    TERMINATED = "terminated"


class OnboardingRoute(str, Enum):
    """Available onboarding routes."""
    WPS = "wps"
    FREELANCER = "freelancer"
    UAE = "uae"  # 3rd Party UAE
    SAUDI = "saudi"  # 3rd Party Saudi
    OFFSHORE = "offshore"


@dataclass(frozen=True)
class PersonalInfo:
    """Value object for contractor personal information."""
    first_name: str
    surname: str
    middle_name: Optional[str] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None
    date_of_birth: Optional[str] = None
    marital_status: Optional[str] = None

    @property
    def full_name(self) -> str:
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.surname)
        return " ".join(parts)


@dataclass(frozen=True)
class ContactInfo:
    """Value object for contact information."""
    email: str
    phone: str
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
```

#### Contractor State Machine
```python
# app/domain/contractor/state_machine.py
from typing import Dict, Set
from app.domain.contractor.value_objects import ContractorStatus
from app.domain.contractor.exceptions import InvalidStatusTransitionError

class ContractorStateMachine:
    """
    Manages valid status transitions for contractors.
    Ensures business rules around status changes are enforced.
    """

    # Define valid transitions: from_status -> {valid_to_statuses}
    TRANSITIONS: Dict[ContractorStatus, Set[ContractorStatus]] = {
        ContractorStatus.DRAFT: {
            ContractorStatus.PENDING_DOCUMENTS,
        },
        ContractorStatus.PENDING_DOCUMENTS: {
            ContractorStatus.DOCUMENTS_UPLOADED,
            ContractorStatus.CANCELLED,
        },
        ContractorStatus.DOCUMENTS_UPLOADED: {
            ContractorStatus.PENDING_COHF,       # UAE route
            ContractorStatus.PENDING_THIRD_PARTY_QUOTE,  # Saudi route
            ContractorStatus.PENDING_CDS_CS,     # Other routes
            ContractorStatus.CANCELLED,
        },
        ContractorStatus.PENDING_COHF: {
            ContractorStatus.AWAITING_COHF_SIGNATURE,
            ContractorStatus.CANCELLED,
        },
        ContractorStatus.AWAITING_COHF_SIGNATURE: {
            ContractorStatus.COHF_COMPLETED,
            ContractorStatus.CANCELLED,
        },
        ContractorStatus.COHF_COMPLETED: {
            ContractorStatus.PENDING_CDS_CS,
            ContractorStatus.CANCELLED,
        },
        ContractorStatus.PENDING_THIRD_PARTY_QUOTE: {
            ContractorStatus.PENDING_CDS_CS,
            ContractorStatus.CANCELLED,
        },
        ContractorStatus.PENDING_CDS_CS: {
            ContractorStatus.CDS_CS_COMPLETED,
            ContractorStatus.CANCELLED,
        },
        ContractorStatus.CDS_CS_COMPLETED: {
            ContractorStatus.PENDING_REVIEW,
            ContractorStatus.CANCELLED,
        },
        ContractorStatus.PENDING_REVIEW: {
            ContractorStatus.APPROVED,
            ContractorStatus.REJECTED,
            ContractorStatus.PENDING_CDS_CS,  # Recall for edits
        },
        ContractorStatus.APPROVED: {
            ContractorStatus.PENDING_CLIENT_WO_SIGNATURE,
            ContractorStatus.CANCELLED,
        },
        ContractorStatus.REJECTED: {
            ContractorStatus.DRAFT,  # Start over
            ContractorStatus.CANCELLED,
        },
        ContractorStatus.PENDING_CLIENT_WO_SIGNATURE: {
            ContractorStatus.WORK_ORDER_COMPLETED,
            ContractorStatus.CANCELLED,
        },
        ContractorStatus.WORK_ORDER_COMPLETED: {
            ContractorStatus.PENDING_3RD_PARTY_CONTRACT,  # UAE
            ContractorStatus.PENDING_SIGNATURE,           # Others
            ContractorStatus.CANCELLED,
        },
        ContractorStatus.PENDING_3RD_PARTY_CONTRACT: {
            ContractorStatus.CONTRACT_APPROVED,
            ContractorStatus.CANCELLED,
        },
        ContractorStatus.CONTRACT_APPROVED: {
            ContractorStatus.PENDING_SIGNATURE,
            ContractorStatus.CANCELLED,
        },
        ContractorStatus.PENDING_SIGNATURE: {
            ContractorStatus.SIGNED,
            ContractorStatus.CANCELLED,
        },
        ContractorStatus.SIGNED: {
            ContractorStatus.ACTIVE,
        },
        ContractorStatus.ACTIVE: {
            ContractorStatus.SUSPENDED,
            ContractorStatus.TERMINATED,
        },
        ContractorStatus.SUSPENDED: {
            ContractorStatus.ACTIVE,
            ContractorStatus.TERMINATED,
        },
    }

    @classmethod
    def can_transition(cls, from_status: ContractorStatus, to_status: ContractorStatus) -> bool:
        """Check if a transition is valid."""
        allowed = cls.TRANSITIONS.get(from_status, set())
        return to_status in allowed

    @classmethod
    def transition(cls, from_status: ContractorStatus, to_status: ContractorStatus) -> ContractorStatus:
        """
        Perform a status transition.

        Raises:
            InvalidStatusTransitionError: If transition is not allowed
        """
        if not cls.can_transition(from_status, to_status):
            raise InvalidStatusTransitionError(
                f"Cannot transition from {from_status.value} to {to_status.value}"
            )
        return to_status

    @classmethod
    def get_allowed_transitions(cls, from_status: ContractorStatus) -> Set[ContractorStatus]:
        """Get all allowed transitions from a status."""
        return cls.TRANSITIONS.get(from_status, set())
```

#### Onboarding Strategy Base
```python
# app/domain/onboarding/strategies/base.py
from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass
from app.domain.contractor.value_objects import ContractorStatus

@dataclass
class OnboardingResult:
    """Result of an onboarding step execution."""
    next_status: ContractorStatus
    message: str
    requires_external_action: bool = False
    external_action_type: str = None  # "email", "signature", etc.

class OnboardingStrategy(ABC):
    """
    Abstract base class for onboarding strategies.
    Each route (UAE, Saudi, Offshore, etc.) implements this interface.
    """

    @property
    @abstractmethod
    def route_name(self) -> str:
        """Return the route identifier."""
        pass

    @abstractmethod
    def get_required_documents(self) -> List[str]:
        """Return list of required document types for this route."""
        pass

    @abstractmethod
    def get_workflow_steps(self) -> List[str]:
        """Return ordered list of workflow step identifiers."""
        pass

    @abstractmethod
    def get_next_status(self, current_status: ContractorStatus) -> ContractorStatus:
        """Determine the next status based on current status."""
        pass

    @abstractmethod
    async def execute_step(self, contractor_id: int, step: str, data: dict) -> OnboardingResult:
        """
        Execute a specific onboarding step.

        Args:
            contractor_id: The contractor being onboarded
            step: The step identifier
            data: Step-specific data

        Returns:
            OnboardingResult with next status and any required actions
        """
        pass
```

#### UAE Onboarding Strategy
```python
# app/domain/onboarding/strategies/uae.py
from typing import List
from app.domain.onboarding.strategies.base import OnboardingStrategy, OnboardingResult
from app.domain.contractor.value_objects import ContractorStatus, OnboardingRoute

class UAEOnboardingStrategy(OnboardingStrategy):
    """
    UAE (3rd Party) onboarding strategy.

    Workflow: Documents → Route → COHF → CDS → Review → Work Order → 3rd Party Contract → Activate

    Key difference: COHF before CDS, 3rd party uploads their contract.
    """

    @property
    def route_name(self) -> str:
        return OnboardingRoute.UAE.value

    def get_required_documents(self) -> List[str]:
        return [
            "passport",
            "photo",
            "emirates_id",
            "visa",
            "degree",
        ]

    def get_workflow_steps(self) -> List[str]:
        return [
            "documents",
            "route_selection",
            "cohf",
            "cds_costing",
            "admin_review",
            "work_order",
            "third_party_contract",
            "activation",
        ]

    def get_next_status(self, current_status: ContractorStatus) -> ContractorStatus:
        transitions = {
            ContractorStatus.DOCUMENTS_UPLOADED: ContractorStatus.PENDING_COHF,
            ContractorStatus.PENDING_COHF: ContractorStatus.AWAITING_COHF_SIGNATURE,
            ContractorStatus.AWAITING_COHF_SIGNATURE: ContractorStatus.COHF_COMPLETED,
            ContractorStatus.COHF_COMPLETED: ContractorStatus.PENDING_CDS_CS,
            ContractorStatus.PENDING_CDS_CS: ContractorStatus.CDS_CS_COMPLETED,
            ContractorStatus.CDS_CS_COMPLETED: ContractorStatus.PENDING_REVIEW,
            ContractorStatus.APPROVED: ContractorStatus.PENDING_CLIENT_WO_SIGNATURE,
            ContractorStatus.WORK_ORDER_COMPLETED: ContractorStatus.PENDING_3RD_PARTY_CONTRACT,
            ContractorStatus.CONTRACT_APPROVED: ContractorStatus.PENDING_SIGNATURE,
            ContractorStatus.SIGNED: ContractorStatus.ACTIVE,
        }
        return transitions.get(current_status)

    async def execute_step(self, contractor_id: int, step: str, data: dict) -> OnboardingResult:
        """Execute UAE-specific step logic."""

        if step == "cohf":
            return OnboardingResult(
                next_status=ContractorStatus.AWAITING_COHF_SIGNATURE,
                message="COHF form submitted. Awaiting 3rd party signature.",
                requires_external_action=True,
                external_action_type="cohf_signature",
            )

        if step == "third_party_contract":
            return OnboardingResult(
                next_status=ContractorStatus.CONTRACT_APPROVED,
                message="3rd party contract uploaded and approved.",
                requires_external_action=False,
            )

        # Default behavior for other steps
        return OnboardingResult(
            next_status=self.get_next_status(ContractorStatus(data.get("current_status"))),
            message=f"Step {step} completed.",
        )
```

#### Saudi Onboarding Strategy
```python
# app/domain/onboarding/strategies/saudi.py
from typing import List
from app.domain.onboarding.strategies.base import OnboardingStrategy, OnboardingResult
from app.domain.contractor.value_objects import ContractorStatus, OnboardingRoute

class SaudiOnboardingStrategy(OnboardingStrategy):
    """
    Saudi (3rd Party) onboarding strategy.

    Workflow: Documents → Route → Quote Sheet → CDS → Review → Work Order → Contract → Activate

    Key difference: Quote sheet from 3rd party before CDS.
    """

    @property
    def route_name(self) -> str:
        return OnboardingRoute.SAUDI.value

    def get_required_documents(self) -> List[str]:
        return [
            "passport",
            "photo",
            "degree",
            "iqama",
        ]

    def get_workflow_steps(self) -> List[str]:
        return [
            "documents",
            "route_selection",
            "quote_sheet",
            "cds_costing",
            "admin_review",
            "work_order",
            "contract",
            "activation",
        ]

    def get_next_status(self, current_status: ContractorStatus) -> ContractorStatus:
        transitions = {
            ContractorStatus.DOCUMENTS_UPLOADED: ContractorStatus.PENDING_THIRD_PARTY_QUOTE,
            ContractorStatus.PENDING_THIRD_PARTY_QUOTE: ContractorStatus.PENDING_CDS_CS,
            ContractorStatus.PENDING_CDS_CS: ContractorStatus.CDS_CS_COMPLETED,
            ContractorStatus.CDS_CS_COMPLETED: ContractorStatus.PENDING_REVIEW,
            ContractorStatus.APPROVED: ContractorStatus.PENDING_CLIENT_WO_SIGNATURE,
            ContractorStatus.WORK_ORDER_COMPLETED: ContractorStatus.PENDING_SIGNATURE,
            ContractorStatus.SIGNED: ContractorStatus.ACTIVE,
        }
        return transitions.get(current_status)

    async def execute_step(self, contractor_id: int, step: str, data: dict) -> OnboardingResult:
        """Execute Saudi-specific step logic."""

        if step == "quote_sheet":
            return OnboardingResult(
                next_status=ContractorStatus.PENDING_THIRD_PARTY_QUOTE,
                message="Quote sheet request sent to 3rd party.",
                requires_external_action=True,
                external_action_type="quote_sheet_submission",
            )

        # Default behavior
        return OnboardingResult(
            next_status=self.get_next_status(ContractorStatus(data.get("current_status"))),
            message=f"Step {step} completed.",
        )
```

#### Strategy Registry
```python
# app/domain/onboarding/registry.py
from typing import Dict, Type, List
from app.domain.onboarding.strategies.base import OnboardingStrategy
from app.domain.contractor.value_objects import OnboardingRoute

class OnboardingRegistry:
    """
    Registry for onboarding strategies.
    Allows dynamic registration and lookup of strategies by route.
    """

    _strategies: Dict[str, Type[OnboardingStrategy]] = {}

    @classmethod
    def register(cls, route: OnboardingRoute):
        """
        Decorator to register a strategy class.

        Usage:
            @OnboardingRegistry.register(OnboardingRoute.UAE)
            class UAEOnboardingStrategy(OnboardingStrategy):
                ...
        """
        def decorator(strategy_class: Type[OnboardingStrategy]):
            cls._strategies[route.value] = strategy_class
            return strategy_class
        return decorator

    @classmethod
    def get(cls, route: str) -> OnboardingStrategy:
        """
        Get a strategy instance for a route.

        Args:
            route: Route identifier (e.g., "uae", "saudi")

        Returns:
            OnboardingStrategy instance

        Raises:
            KeyError: If route is not registered
        """
        if route not in cls._strategies:
            raise KeyError(f"No strategy registered for route: {route}")
        return cls._strategies[route]()

    @classmethod
    def available_routes(cls) -> List[str]:
        """Get list of all registered routes."""
        return list(cls._strategies.keys())

    @classmethod
    def is_registered(cls, route: str) -> bool:
        """Check if a route is registered."""
        return route in cls._strategies


# Register all strategies
from app.domain.onboarding.strategies.uae import UAEOnboardingStrategy
from app.domain.onboarding.strategies.saudi import SaudiOnboardingStrategy
from app.domain.onboarding.strategies.offshore import OffshoreOnboardingStrategy
from app.domain.onboarding.strategies.wps import WPSOnboardingStrategy
from app.domain.onboarding.strategies.freelancer import FreelancerOnboardingStrategy

OnboardingRegistry.register(OnboardingRoute.UAE)(UAEOnboardingStrategy)
OnboardingRegistry.register(OnboardingRoute.SAUDI)(SaudiOnboardingStrategy)
OnboardingRegistry.register(OnboardingRoute.OFFSHORE)(OffshoreOnboardingStrategy)
OnboardingRegistry.register(OnboardingRoute.WPS)(WPSOnboardingStrategy)
OnboardingRegistry.register(OnboardingRoute.FREELANCER)(FreelancerOnboardingStrategy)
```

---

### 7.4 Repository Layer Implementation

#### Repository Interface
```python
# app/repositories/interfaces/base.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional

T = TypeVar("T")

class IRepository(ABC, Generic[T]):
    """Abstract repository interface."""

    @abstractmethod
    async def get(self, id: int) -> Optional[T]:
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        pass

    @abstractmethod
    async def create(self, entity: T) -> T:
        pass

    @abstractmethod
    async def update(self, id: int, entity: T) -> Optional[T]:
        pass

    @abstractmethod
    async def delete(self, id: int) -> bool:
        pass
```

#### Base Repository Implementation
```python
# app/repositories/implementations/base.py
from typing import TypeVar, Generic, Type, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from app.repositories.interfaces.base import IRepository

ModelType = TypeVar("ModelType")

class BaseRepository(Generic[ModelType]):
    """
    Base repository implementation with common CRUD operations.
    All entity-specific repositories inherit from this.
    """

    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    async def get(self, id: int) -> Optional[ModelType]:
        """Get entity by ID."""
        return self.db.query(self.model).filter(self.model.id == id).first()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get all entities with pagination."""
        return self.db.query(self.model).offset(skip).limit(limit).all()

    async def create(self, data: dict) -> ModelType:
        """Create new entity."""
        entity = self.model(**data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    async def update(self, id: int, data: dict) -> Optional[ModelType]:
        """Update entity by ID."""
        entity = await self.get(id)
        if entity:
            for field, value in data.items():
                if hasattr(entity, field):
                    setattr(entity, field, value)
            self.db.commit()
            self.db.refresh(entity)
        return entity

    async def delete(self, id: int) -> bool:
        """Delete entity by ID."""
        entity = await self.get(id)
        if entity:
            self.db.delete(entity)
            self.db.commit()
            return True
        return False

    async def filter_by(self, **kwargs) -> List[ModelType]:
        """Filter entities by field values."""
        return self.db.query(self.model).filter_by(**kwargs).all()

    async def count(self, **kwargs) -> int:
        """Count entities matching filter."""
        query = self.db.query(self.model)
        if kwargs:
            query = query.filter_by(**kwargs)
        return query.count()
```

#### Contractor Repository
```python
# app/repositories/implementations/contractor_repo.py
from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.implementations.base import BaseRepository
from app.models.contractor import Contractor
from app.domain.contractor.value_objects import ContractorStatus, OnboardingRoute

class ContractorRepository(BaseRepository[Contractor]):
    """
    Contractor-specific repository with domain-specific queries.
    """

    def __init__(self, db: Session):
        super().__init__(Contractor, db)

    async def get_by_email(self, email: str) -> Optional[Contractor]:
        """Find contractor by email."""
        return self.db.query(Contractor).filter(Contractor.email == email).first()

    async def get_by_token(self, token: str) -> Optional[Contractor]:
        """Find contractor by document upload token."""
        return self.db.query(Contractor).filter(
            Contractor.document_upload_token == token
        ).first()

    async def get_by_contract_token(self, token: str) -> Optional[Contractor]:
        """Find contractor by contract signing token."""
        return self.db.query(Contractor).filter(
            Contractor.contract_token == token
        ).first()

    async def get_by_status(self, status: ContractorStatus) -> List[Contractor]:
        """Get all contractors with a specific status."""
        return self.db.query(Contractor).filter(
            Contractor.status == status.value
        ).all()

    async def get_by_route(self, route: OnboardingRoute) -> List[Contractor]:
        """Get all contractors on a specific onboarding route."""
        return self.db.query(Contractor).filter(
            Contractor.onboarding_route == route.value
        ).all()

    async def get_active(self) -> List[Contractor]:
        """Get all active contractors."""
        return self.db.query(Contractor).filter(
            Contractor.status == ContractorStatus.ACTIVE.value
        ).all()

    async def get_pending_review(self) -> List[Contractor]:
        """Get contractors pending admin review."""
        return self.db.query(Contractor).filter(
            Contractor.status == ContractorStatus.PENDING_REVIEW.value
        ).all()

    async def search(
        self,
        query: str = None,
        status: str = None,
        route: str = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[Contractor], int]:
        """
        Search contractors with filters.

        Returns:
            Tuple of (contractors, total_count)
        """
        q = self.db.query(Contractor)

        if query:
            search_filter = f"%{query}%"
            q = q.filter(
                (Contractor.first_name.ilike(search_filter)) |
                (Contractor.surname.ilike(search_filter)) |
                (Contractor.email.ilike(search_filter))
            )

        if status:
            q = q.filter(Contractor.status == status)

        if route:
            q = q.filter(Contractor.onboarding_route == route)

        total = q.count()
        contractors = q.offset(skip).limit(limit).all()

        return contractors, total
```

---

### 7.5 Service Layer Implementation

#### Contractor Service
```python
# app/services/contractor_service.py
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from app.repositories.implementations.contractor_repo import ContractorRepository
from app.domain.contractor.value_objects import ContractorStatus, OnboardingRoute
from app.domain.contractor.state_machine import ContractorStateMachine
from app.domain.contractor.exceptions import (
    ContractorNotFoundError,
    InvalidStatusTransitionError,
)
from app.domain.token.token import Token
from app.schemas.contractor import ContractorCreate, ContractorUpdate
from app.telemetry.logger import get_logger

logger = get_logger(__name__)

class ContractorService:
    """
    Application service for contractor management.
    Orchestrates domain logic, repositories, and adapters.
    """

    def __init__(self, repo: ContractorRepository):
        self.repo = repo

    async def create_initial(self, data: ContractorCreate) -> dict:
        """
        Create initial contractor record.
        Generates document upload token and sends email.
        """
        # Generate upload token
        token = Token.generate(hours=168)  # 7 days

        contractor_data = {
            **data.dict(),
            "status": ContractorStatus.PENDING_DOCUMENTS.value,
            "document_upload_token": token.value,
            "document_upload_token_expiry": token.expiry,
        }

        contractor = await self.repo.create(contractor_data)

        logger.info(
            "Contractor created",
            extra={
                "contractor_id": contractor.id,
                "email": contractor.email,
                "status": contractor.status,
            }
        )

        return {
            "contractor": contractor,
            "upload_token": token.value,
            "upload_expiry": token.expiry,
        }

    async def get(self, id: int) -> Optional[dict]:
        """Get contractor by ID."""
        contractor = await self.repo.get(id)
        if not contractor:
            raise ContractorNotFoundError(f"Contractor {id} not found")
        return contractor

    async def get_by_token(self, token: str) -> Optional[dict]:
        """Get contractor by document upload token."""
        contractor = await self.repo.get_by_token(token)
        if not contractor:
            raise ContractorNotFoundError("Invalid or expired token")

        # Validate token expiry
        token_obj = Token(token, contractor.document_upload_token_expiry)
        token_obj.validate()

        return contractor

    async def update_status(self, id: int, new_status: ContractorStatus) -> dict:
        """
        Update contractor status with validation.
        Uses state machine to ensure valid transitions.
        """
        contractor = await self.get(id)
        current_status = ContractorStatus(contractor.status)

        # Validate transition
        ContractorStateMachine.transition(current_status, new_status)

        # Update
        updated = await self.repo.update(id, {"status": new_status.value})

        logger.info(
            "Contractor status updated",
            extra={
                "contractor_id": id,
                "from_status": current_status.value,
                "to_status": new_status.value,
            }
        )

        return updated

    async def search(
        self,
        query: str = None,
        status: str = None,
        route: str = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[dict], int]:
        """Search contractors with pagination."""
        skip = (page - 1) * page_size
        contractors, total = await self.repo.search(
            query=query,
            status=status,
            route=route,
            skip=skip,
            limit=page_size,
        )
        return contractors, total

    async def select_route(self, id: int, route: OnboardingRoute) -> dict:
        """Select onboarding route for contractor."""
        contractor = await self.get(id)

        # Validate current status allows route selection
        if contractor.status != ContractorStatus.DOCUMENTS_UPLOADED.value:
            raise InvalidStatusTransitionError(
                "Route can only be selected after documents are uploaded"
            )

        updated = await self.repo.update(id, {
            "onboarding_route": route.value,
        })

        logger.info(
            "Onboarding route selected",
            extra={
                "contractor_id": id,
                "route": route.value,
            }
        )

        return updated
```

#### Notification Service
```python
# app/services/notification_service.py
from typing import Optional
from datetime import datetime
from app.adapters.email.interface import IEmailSender
from app.adapters.email.template_engine import EmailTemplateEngine
from app.config.settings import settings
from app.telemetry.logger import get_logger

logger = get_logger(__name__)

class NotificationService:
    """
    Application service for sending notifications.
    Abstracts email sending behind a clean interface.
    """

    def __init__(
        self,
        email_sender: IEmailSender,
        template_engine: EmailTemplateEngine,
    ):
        self.email = email_sender
        self.templates = template_engine

    async def send_contract_email(
        self,
        contractor_email: str,
        contractor_name: str,
        contract_token: str,
        expiry_date: datetime,
    ) -> bool:
        """Send contract signing invitation."""
        contract_link = f"{settings.contract_signing_url}?token={contract_token}"

        html = self.templates.render(
            "contract_signing",
            contractor_name=contractor_name,
            contract_link=contract_link,
            expiry_date=expiry_date.strftime("%B %d, %Y at %I:%M %p"),
        )

        success = await self.email.send(
            to=contractor_email,
            subject="Your Employment Contract - Action Required",
            html=html,
        )

        logger.info(
            "Contract email sent",
            extra={
                "to": contractor_email,
                "success": success,
            }
        )

        return success

    async def send_activation_email(
        self,
        contractor_email: str,
        contractor_name: str,
        temporary_password: str,
    ) -> bool:
        """Send account activation email with credentials."""
        html = self.templates.render(
            "activation",
            contractor_name=contractor_name,
            contractor_email=contractor_email,
            temporary_password=temporary_password,
            login_link=settings.frontend_url,
        )

        success = await self.email.send(
            to=contractor_email,
            subject=f"Welcome to {settings.company_name}",
            html=html,
        )

        logger.info(
            "Activation email sent",
            extra={
                "to": contractor_email,
                "success": success,
            }
        )

        return success

    async def send_document_upload_email(
        self,
        contractor_email: str,
        contractor_name: str,
        upload_token: str,
        expiry_date: datetime,
    ) -> bool:
        """Send document upload request."""
        upload_link = f"{settings.frontend_url}/documents/upload/{upload_token}"

        html = self.templates.render(
            "document_upload",
            contractor_name=contractor_name,
            upload_link=upload_link,
            expiry_date=expiry_date.strftime("%B %d, %Y at %I:%M %p"),
        )

        return await self.email.send(
            to=contractor_email,
            subject="Document Upload Request - Action Required",
            html=html,
        )

    # ... Additional notification methods for all 14 email types
```

---

### 7.6 API Layer Implementation

#### Thin Contractor Routes
```python
# app/api/v1/contractors.py
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from app.api.dependencies import get_contractor_service, get_current_user
from app.api.responses import paginated_response, success_response
from app.services.contractor_service import ContractorService
from app.schemas.contractor import (
    ContractorCreate,
    ContractorResponse,
    ContractorListResponse,
    RouteSelection,
)
from app.domain.contractor.exceptions import (
    ContractorNotFoundError,
    InvalidStatusTransitionError,
)

router = APIRouter(prefix="/contractors", tags=["Contractors"])

@router.post("/initial", response_model=dict)
async def create_initial_contractor(
    data: ContractorCreate,
    service: ContractorService = Depends(get_contractor_service),
    current_user = Depends(get_current_user),
):
    """
    Create initial contractor record.
    Generates document upload token and prepares for onboarding.
    """
    result = await service.create_initial(data)
    return success_response(result)


@router.get("/", response_model=ContractorListResponse)
async def list_contractors(
    query: Optional[str] = Query(None, description="Search by name or email"),
    status: Optional[str] = Query(None, description="Filter by status"),
    route: Optional[str] = Query(None, description="Filter by onboarding route"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: ContractorService = Depends(get_contractor_service),
    current_user = Depends(get_current_user),
):
    """List contractors with filters and pagination."""
    contractors, total = await service.search(
        query=query,
        status=status,
        route=route,
        page=page,
        page_size=page_size,
    )
    return paginated_response(contractors, total, page, page_size)


@router.get("/{id}", response_model=ContractorResponse)
async def get_contractor(
    id: int,
    service: ContractorService = Depends(get_contractor_service),
    current_user = Depends(get_current_user),
):
    """Get contractor by ID."""
    contractor = await service.get(id)
    return success_response(contractor)


@router.get("/token/{token}", response_model=ContractorResponse)
async def get_contractor_by_token(
    token: str,
    service: ContractorService = Depends(get_contractor_service),
):
    """Get contractor by document upload token (public endpoint)."""
    contractor = await service.get_by_token(token)
    return success_response(contractor)


@router.post("/{id}/select-route", response_model=ContractorResponse)
async def select_onboarding_route(
    id: int,
    data: RouteSelection,
    service: ContractorService = Depends(get_contractor_service),
    current_user = Depends(get_current_user),
):
    """Select onboarding route for contractor."""
    contractor = await service.select_route(id, data.route)
    return success_response(contractor)


# ... Additional thin endpoints that delegate to services
```

#### API Dependencies
```python
# app/api/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.contractor_service import ContractorService
from app.services.notification_service import NotificationService
from app.repositories.implementations.contractor_repo import ContractorRepository
from app.adapters.email.resend_adapter import ResendEmailSender
from app.adapters.email.template_engine import email_template_engine
from app.utils.auth import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """Get current authenticated user from JWT token."""
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    # ... fetch user from DB
    return payload


def get_contractor_service(db: Session = Depends(get_db)) -> ContractorService:
    """Factory for ContractorService with dependencies."""
    repo = ContractorRepository(db)
    return ContractorService(repo)


def get_notification_service() -> NotificationService:
    """Factory for NotificationService with dependencies."""
    email_sender = ResendEmailSender()
    return NotificationService(email_sender, email_template_engine)
```

#### Response Formatters
```python
# app/api/responses.py
from typing import TypeVar, Generic, List, Optional, Any
from pydantic import BaseModel

T = TypeVar("T")

class SuccessResponse(BaseModel):
    success: bool = True
    data: Any

class PaginatedResponse(BaseModel):
    success: bool = True
    data: List[Any]
    pagination: dict

def success_response(data: Any) -> dict:
    """Format successful response."""
    return {
        "success": True,
        "data": data,
    }

def paginated_response(
    items: List[Any],
    total: int,
    page: int,
    page_size: int,
) -> dict:
    """Format paginated response."""
    total_pages = (total + page_size - 1) // page_size
    return {
        "success": True,
        "data": items,
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        }
    }

def error_response(code: str, message: str, details: dict = None) -> dict:
    """Format error response."""
    response = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        }
    }
    if details:
        response["error"]["details"] = details
    return response
```

---

## 8. Code Patterns & Examples

### Pattern 1: Strategy Pattern (Onboarding Routes)
```python
# Adding a new route (Qatar) - NO modification to existing code
# Just create a new file:

# app/domain/onboarding/strategies/qatar.py
from app.domain.onboarding.strategies.base import OnboardingStrategy
from app.domain.onboarding.registry import OnboardingRegistry
from app.domain.contractor.value_objects import OnboardingRoute

@OnboardingRegistry.register(OnboardingRoute.QATAR)  # Auto-registered!
class QatarOnboardingStrategy(OnboardingStrategy):
    # ... implement Qatar-specific logic
```

### Pattern 2: Repository Pattern (Data Access)
```python
# Service doesn't know about SQLAlchemy
class ContractorService:
    def __init__(self, repo: IContractorRepository):  # Interface
        self.repo = repo

    async def get(self, id: int):
        return await self.repo.get(id)  # Could be SQL, MongoDB, API, etc.
```

### Pattern 3: Adapter Pattern (External Services)
```python
# Easy to swap implementations
class NotificationService:
    def __init__(self, email_sender: IEmailSender):  # Interface
        self.email = email_sender

# Production
service = NotificationService(ResendEmailSender())

# Testing
service = NotificationService(MockEmailSender())

# Future migration
service = NotificationService(SESEmailSender())
```

### Pattern 4: Template Method (PDF Generation)
```python
class BasePDFGenerator:
    def generate(self, data: dict) -> BytesIO:
        elements = []
        elements.extend(self.create_header(data))    # Shared
        elements.extend(self.build_content(data))    # Abstract - subclass implements
        elements.extend(self.create_footer(data))    # Shared
        return self._build_pdf(elements)

    @abstractmethod
    def build_content(self, data: dict) -> list:
        pass  # Each PDF type implements this
```

### Pattern 5: Value Objects (Immutable Domain Objects)
```python
@dataclass(frozen=True)  # Immutable
class Token:
    value: str
    expiry: datetime

    @property
    def is_valid(self) -> bool:
        return self.expiry > datetime.utcnow()

    def validate(self) -> None:
        if not self.is_valid:
            raise TokenExpiredError()
```

---

## 9. Migration Checklist

### Pre-Migration
- [ ] Create Git branch for refactor
- [ ] Set up new folder structure (parallel to existing)
- [ ] Set up Docker + docker-compose
- [ ] Set up Alembic
- [ ] Set up pytest
- [ ] Create base classes and interfaces

### Phase 1: Infrastructure
- [ ] Implement all 6 middlewares
- [ ] Set up structured logging
- [ ] Create custom exception hierarchy
- [ ] Wire middlewares in main.py
- [ ] Test error handling

### Phase 2: Templates
- [ ] Create base email template
- [ ] Create all email component templates
- [ ] Create all 14 email templates
- [ ] Create EmailTemplateEngine
- [ ] Create base PDF template
- [ ] Create all PDF templates
- [ ] Test all templates render

### Phase 3: Domain
- [ ] Create domain entities
- [ ] Create value objects
- [ ] Create state machines
- [ ] Create all 5 onboarding strategies
- [ ] Create strategy registry
- [ ] Create Token value object
- [ ] Unit test domain layer

### Phase 4: Repositories
- [ ] Create repository interfaces
- [ ] Create BaseRepository
- [ ] Create all entity repositories
- [ ] Integration test repositories

### Phase 5: Adapters
- [ ] Create email adapter interface + implementation
- [ ] Create storage adapter interface + implementation
- [ ] Create PDF generator base + implementations
- [ ] Create PDF registry
- [ ] Test adapters

### Phase 6: Services
- [ ] Create ContractorService
- [ ] Create OnboardingService
- [ ] Create NotificationService
- [ ] Create all other services
- [ ] Test services with mocks

### Phase 7: API
- [ ] Refactor auth routes
- [ ] Refactor contractor routes
- [ ] Refactor all other routes
- [ ] Create API dependencies
- [ ] Create response formatters
- [ ] Integration test all endpoints

### Phase 8: Cleanup
- [ ] Remove old utils/email.py
- [ ] Remove old route files
- [ ] Remove ad-hoc migrations
- [ ] Update documentation
- [ ] Final testing
- [ ] Code review

---

## 10. Testing Strategy

### Unit Tests (Domain Layer)
```python
# tests/unit/domain/test_contractor_state_machine.py
import pytest
from app.domain.contractor.state_machine import ContractorStateMachine
from app.domain.contractor.value_objects import ContractorStatus
from app.domain.contractor.exceptions import InvalidStatusTransitionError

class TestContractorStateMachine:
    def test_valid_transition(self):
        result = ContractorStateMachine.transition(
            ContractorStatus.DRAFT,
            ContractorStatus.PENDING_DOCUMENTS
        )
        assert result == ContractorStatus.PENDING_DOCUMENTS

    def test_invalid_transition_raises(self):
        with pytest.raises(InvalidStatusTransitionError):
            ContractorStateMachine.transition(
                ContractorStatus.DRAFT,
                ContractorStatus.ACTIVE  # Can't go directly to ACTIVE
            )

    def test_get_allowed_transitions(self):
        allowed = ContractorStateMachine.get_allowed_transitions(
            ContractorStatus.PENDING_REVIEW
        )
        assert ContractorStatus.APPROVED in allowed
        assert ContractorStatus.REJECTED in allowed
```

### Integration Tests (API Layer)
```python
# tests/integration/api/test_contractors_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestContractorsAPI:
    def test_create_initial_contractor(self, auth_headers):
        response = client.post(
            "/api/v1/contractors/initial",
            json={
                "first_name": "John",
                "surname": "Doe",
                "email": "john@example.com",
                "phone": "+1234567890",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "upload_token" in data["data"]

    def test_get_contractor_by_invalid_token(self):
        response = client.get("/api/v1/contractors/token/invalid-token")
        assert response.status_code == 404
```

### Test Fixtures
```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db):
    def override_get_db():
        yield db
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers():
    # Create test user and return auth headers
    return {"Authorization": "Bearer test-token"}
```

---

## 11. Rollback Plan

### If Refactor Fails

1. **Git Revert**: All changes are on a separate branch
   ```bash
   git checkout main
   git branch -D refactor-branch
   ```

2. **Parallel Deployment**: Old and new can run side-by-side during transition

3. **Feature Flags**: New code paths can be toggled off
   ```python
   if settings.USE_NEW_CONTRACTOR_SERVICE:
       service = NewContractorService()
   else:
       service = OldContractorService()
   ```

4. **Database Compatibility**: Alembic supports downgrade migrations
   ```bash
   alembic downgrade -1
   ```

### Monitoring During Rollout

- Watch error rates in logs
- Monitor response times
- Check for 5xx errors
- Verify email delivery
- Test critical workflows manually

---

## Appendix A: File Count Comparison

### Before
| Directory | Files | Total Lines |
|-----------|-------|-------------|
| routes/ | 10 | ~7,500 |
| models/ | 11 | ~1,200 |
| utils/ | 9 | ~4,500 |
| schemas/ | 8 | ~800 |
| **Total** | **38** | **~14,000** |

### After
| Directory | Files | Avg Lines/File |
|-----------|-------|----------------|
| api/v1/ | 12 | ~50-100 |
| domain/ | 25 | ~50-150 |
| services/ | 10 | ~100-200 |
| repositories/ | 15 | ~50-100 |
| adapters/ | 15 | ~50-150 |
| middlewares/ | 6 | ~30-50 |
| templates/ | 20 | N/A (HTML) |
| tests/ | 30+ | ~50-100 |
| **Total** | **130+** | **~50-150** |

More files, but each file has a **single responsibility** and is **easy to understand**.

---

## Appendix B: Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Architecture | Modular Monolith | Simpler ops than microservices, same benefits |
| State Management | State Machine | Enforces valid transitions, prevents bugs |
| Onboarding Routes | Strategy Pattern | Open/closed principle, easy to add new routes |
| Data Access | Repository Pattern | Testable, swappable implementations |
| External Services | Adapter Pattern | Loose coupling, easy to mock/swap |
| Templates | Jinja2 | Industry standard, inheritance support |
| Migrations | Alembic | SQLAlchemy native, version controlled |
| Testing | pytest | De facto Python standard |
| Logging | Structured JSON | CloudWatch/ELK compatible |
| Containerization | Docker | Industry standard, reproducible |

---

## Appendix C: Dependencies to Add

```txt
# requirements.txt additions
alembic==1.13.1
jinja2==3.1.2
pytest==8.0.0
pytest-asyncio==0.23.0
pytest-cov==4.1.0
httpx==0.26.0  # For async test client
structlog==24.1.0  # Structured logging
```

---

**Document End**

*This document should be used as the reference for all refactoring work. Update this document as decisions are made or approaches change.*
