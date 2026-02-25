# Architecture Document

**Dead-Man Switch: Clean Architecture for Extensible Local-First Systems**

---

## 1. Executive Summary

This document explains the architectural decisions behind Dead-Man Switch, focusing on **modularity, testability, and future extensibility**. The design enables evolution from a local prototype to cloud APIs, multi-user systems, and mobile backends without major refactoring.

**Key Principle:** Business logic lives in the domain layer, never in HTTP handlers.

---

## 2. Design Philosophy

### 2.1 Core Principles

| Principle | Why | How |
|-----------|-----|-----|
| **Separation of Concerns** | Each layer has one responsibility | API ≠ Services ≠ DB |
| **Dependency Inversion** | High-level policy doesn't depend on low-level details | Repositories abstract DB, Services call repositories |
| **Testability** | Business logic can be tested without HTTP/DB | Pure domain functions, mockable services |
| **Extensibility** | New features don't break existing code | Interfaces designed for adapters (notifications, auth) |
| **Simplicity** | Start minimal, grow cleanly | No premature optimization or async complexity |

### 2.2 Decisions Made

#### Decision: Local-First with Cloud-Ready Design
**Why:** Start with zero cloud dependency, but enable future migration.
- **Trade-off:** SQLite (local) vs Postgres (cloud). We chose SQLite.
- **Mitigation:** DatabaseURL in config — changing to Postgres requires one line change in `app/db/database.py`.
- **Future-proof:** Repositories abstract all DB queries, so ORM swap is contained.

#### Decision: Synchronous Python (No Async)
**Why:** Complexity kills maintenance. The scheduler is the only background job.
- **Trade-off:** Can't handle thousands of concurrent users yet.
- **Mitigation:** Async is trivial to add layer-by-layer when needed (start with routes, then services).
- **Benefit:** Easier to reason about, test, and debug.

#### Decision: Background Scheduler (APScheduler)
**Why:** Local monitoring of status changes needed without polling from frontend constantly.
- **Trade-off:** Single-machine scheduler only (can't scale to multiple servers yet).
- **Mitigation:** Future: Replace with Celery + Redis, or AWS Lambda, without touching business logic.
- **Design:** Scheduler is configured at app startup/shutdown, isolated in `app/scheduler/`.

---

## 3. Layered Architecture

### 3.1 The Stack

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Routes                       │
│                  (HTTP Request/Response)                │
│            Responsibility: Input validation,            │
│              response formatting, HTTP-specific         │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                   Service Layer                         │
│             (Business Logic Orchestration)              │
│        Responsibility: Workflows, rule enforcement,     │
│         transaction coordination, error handling        │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                  Repository Layer                       │
│              (Data Access Abstraction)                  │
│         Responsibility: All DB queries encapsulated,    │
│         never leaked to higher layers                   │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                   Domain Layer                          │
│              (Pure Business Logic)                      │
│         Responsibility: Status calculation rules,       │
│         state machines, validation logic.               │
│         ZERO dependencies on FastAPI, DB, or HTTP       │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│         SQLAlchemy ORM + SQLite Database                │
│                 (Persistence)                          │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Layer Responsibilities

#### **Layer 1: API Routes** (`app/api/routes.py`)

**Responsibility:** HTTP concerns only.

```python
@router.post("/checkin", response_model=CheckInResponse)
async def checkin(service: CheckInService = ServiceDep) -> CheckInResponse:
    return service.record_checkin()
```

**Why this matters:**
- Routes receive HTTP requests, delegate to services
- Never perform database queries directly
- Never implement business logic
- Routes are **thin adapters** between HTTP and domain

**Future benefit:**
- Swap FastAPI for Flask, Django, or gRPC without touching services
- Routes stay simple → easy to understand and modify

---

#### **Layer 2: Service Layer** (`app/services/checkin_service.py`)

**Responsibility:** Business logic orchestration.

```python
def record_checkin(self) -> CheckInResponse:
    checkin = self.checkin_repo.record_checkin()
    status = self.compute_current_status()
    return CheckInResponse(
        timestamp=checkin.timestamp,
        status=status,
        hours_until_due=hours_until_due(checkin.timestamp, ...),
    )
```

**What it does:**
- Calls repositories to fetch/save data
- Calls domain logic to compute results
- Handles transactions and error handling
- Never executes SQL directly

**Why this matters:**
- Services are reusable: call from API routes, CLI, background jobs, webhooks
- Easy to test: mock repositories, inject test data
- Business logic is explicit here (orchestration lives here)

**Future benefit:**
- Add authentication: `service.record_checkin(user_id)`
- Add multi-tenancy: `service.record_checkin(tenant_id)`
- Add notifications: `service.notify_on_status_change(event)`

---

#### **Layer 3: Repository Layer** (`app/repositories/checkin_repo.py`)

**Responsibility:** Data access abstraction.

```python
class CheckInRepository:
    def record_checkin(self) -> CheckIn:
        checkin = CheckIn(timestamp=datetime.utcnow())
        self.db.add(checkin)
        self.db.commit()
        self.db.refresh(checkin)
        return checkin
```

**What it does:**
- Encapsulates all database queries
- Never exposes SQL or SQLAlchemy session
- Returns domain objects (ORM models), not raw rows

**Why this matters:**
- Database queries are in ONE place
- Changing DB queries doesn't affect services or routes
- Easy to test: mock repository with in-memory data

**Future benefit:**
- Swap SQLite → Postgres: only repos change
- Add caching: repos handle it internally
- Add database monitoring: all queries logged in repos

---

#### **Layer 4: Domain Layer** (`app/domain/`)

**Responsibility:** Pure business logic.

```python
def compute_status(last_checkin: datetime | None, interval_hours: int) -> CheckInStatus:
    if last_checkin is None:
        return CheckInStatus.MISSED
    
    elapsed_hours = (now - last_checkin).total_seconds() / 3600
    threshold_safe = 0.8 * interval_hours
    threshold_due_soon = interval_hours
    
    if elapsed_hours < threshold_safe:
        return CheckInStatus.SAFE
    elif elapsed_hours < threshold_due_soon:
        return CheckInStatus.DUE_SOON
    else:
        return CheckInStatus.MISSED
```

**What it does:**
- Implements status calculation rules
- NO database queries
- NO HTTP concerns
- NO framework dependencies

**Why this matters:**
- Testable without database or HTTP
- Reusable from CLI, scripts, webhooks
- Rules are business logic, not tied to implementation

**Future benefit:**
- Use same logic in mobile app (recompile as WebAssembly)
- Use in cloud function (AWS Lambda)
- Reference implementation for other platforms

---

### 3.3 Data Flow Example

**User clicks "Check In":**

```
1. Browser: POST /api/checkin

2. Route (routes.py):
   checkin() → service.record_checkin()

3. Service (checkin_service.py):
   record_checkin()
   ├─ repo.record_checkin()          ← Add to DB
   ├─ compute_current_status()       ← Call domain logic
   └─ Return CheckInResponse

4. Domain (status.py):
   compute_status(last_checkin, interval)
   └─ Return CheckInStatus.SAFE

5. Repository (checkin_repo.py):
   record_checkin()
   └─ Execute INSERT, return model

6. Database:
   INSERT INTO checkins (timestamp) VALUES (now())

7. Response sent back to browser
```

**Each layer is independent:**
- Routes don't know about database
- Services don't know about HTTP
- Domain doesn't know about anything except math

---

## 4. Extensibility Patterns

### 4.1 Adding Notifications (Future)

**Current state:** Scheduler logs status changes.
**Goal:** Send email/SMS when status changes to MISSED.

**Design:**

```python
# app/notifications/notifiers.py
class Notifier(ABC):
    @abstractmethod
    def send(self, event: StatusChangeEvent):
        pass

class EmailNotifier(Notifier):
    def send(self, event: StatusChangeEvent):
        # Email logic
        pass

class WhatsAppNotifier(Notifier):
    def send(self, event: StatusChangeEvent):
        # WhatsApp logic
        pass

# app/scheduler/jobs.py
def _check_status(self):
    service = CheckInService(db)
    current_status = service.compute_current_status()
    
    if current_status != self._last_status:
        # NEW: Notify
        event = StatusChangeEvent(
            old_status=self._last_status,
            new_status=current_status,
        )
        for notifier in self.notifiers:
            notifier.send(event)
        
        self._last_status = current_status
```

**Why this works:**
- No changes to routes, services, or domain logic
- Notifier is plugged in at scheduler initialization
- Easy to add multiple notifiers (email + SMS)
- Easy to test: mock notifier

---

### 4.2 Adding Authentication

**Current state:** No user concept.
**Goal:** Support multiple users, each with own check-in history.

**Changes needed:**

```python
# app/domain/models.py - Add user_id
class CheckInResponse(BaseModel):
    user_id: int
    timestamp: datetime
    status: CheckInStatus

# app/repositories/checkin_repo.py
def get_last_checkin(self, user_id: int) -> CheckIn | None:
    return self.db.query(CheckIn).filter(
        CheckIn.user_id == user_id
    ).order_by(CheckIn.timestamp.desc()).first()

# app/services/checkin_service.py
def record_checkin(self, user_id: int) -> CheckInResponse:
    checkin = self.checkin_repo.record_checkin(user_id)
    ...

# app/api/routes.py
@router.post("/checkin")
async def checkin(
    current_user: User = Depends(get_current_user),
    service: CheckInService = ServiceDep,
) -> CheckInResponse:
    return service.record_checkin(current_user.id)
```

**Why this works:**
- User context flows through all layers naturally
- Database schema adds `user_id` column
- Services and domain logic stay mostly unchanged
- No restructuring needed

---

### 4.3 Cloud Deployment

**Current state:** Local SQLite, APScheduler.
**Goal:** Deploy to AWS Lambda with RDS and SQS.

**Changes:**

```python
# app/db/database.py
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:pass@rds-endpoint.aws.amazonaws.com/checkin"
)

# app/scheduler/jobs.py → app/workers/lambda_handler.py
# Lambda invokes domain logic directly, no scheduler

# Services and domain logic: ZERO changes needed
```

**Why this works:**
- Repos abstract database, so Postgres swap is transparent
- Domain logic is pure functions, works anywhere
- Services don't care where they're called from

---

## 5. Testing Strategy

### 5.1 Unit Tests (Domain Logic)

**No database, no HTTP needed.**

```python
def test_compute_status():
    last = datetime(2026, 2, 1, 0, 0, 0)
    now = datetime(2026, 2, 3, 0, 0, 0)  # 48 hours later
    
    status = compute_status(last, interval_hours=48)
    assert status == CheckInStatus.MISSED
```

**Why this works:**
- Pure functions = deterministic, fast
- No setup/teardown
- Can run offline

---

### 5.2 Integration Tests (Service + Repository)

**Uses in-memory database or test database.**

```python
def test_record_checkin_updates_status():
    db = get_test_db()
    service = CheckInService(db)
    
    # Record first check-in
    response = service.record_checkin()
    assert response.status == CheckInStatus.SAFE
    
    # Advance time, check status changes
    mock_now(48 hours later)
    status = service.compute_current_status()
    assert status == CheckInStatus.MISSED
```

**Why this works:**
- Tests business workflows
- Uses real repositories (in-memory DB)
- Doesn't start HTTP server

---

### 5.3 End-to-End Tests (Full Stack)

**Starts app, makes HTTP requests.**

```python
def test_checkin_api():
    response = client.post("/api/checkin")
    assert response.status_code == 200
    assert response.json()["status"] == "SAFE"
```

**Why this works:**
- Tests full request/response cycle
- Validates route → service → repository → domain
- Catches integration issues

---

## 6. Deployment Roadmap

### Phase 1: Local Development (Now)
- ✓ SQLite + APScheduler
- ✓ Single-machine
- ✓ Minimal UI
- Use case: Personal protection

### Phase 2: Mobile (Future)
- [ ] Mobile app (React Native)
- [ ] Push notifications
- Use case: Smartphone integration

### Phase 3: Cloud API (Next)
- [ ] Postgres database
- [ ] FastAPI on Heroku/Railway
- [ ] Background jobs on Celery
- Use case: Multiple users, web app

### Phase 4: Enterprise (Long-term)
- [ ] Multi-tenant SaaS
- [ ] Fine-grained permissions
- [ ] Audit logging
- [ ] Encryption at rest
- Use case: Organizations

**Why this works:**
- Each phase requires minimal changes to business logic
- Layers insulate us from infrastructure changes
- Can retire/replace components independently

---

## 7. Configuration Management

### 7.1 Environment-Based Config

```python
# app/config.py
class Settings(BaseSettings):
    database_url: str = "sqlite:///./checkin.db"
    check_interval_minutes: int = 1
    
    class Config:
        env_file = ".env"

settings = Settings()
```

**Why this works:**
- Works locally (SQLite, .env)
- Works in cloud (environment variables, Postgres URL)
- No code changes needed

### 7.2 .env Example

```bash
# Local development
DATABASE_URL=sqlite:///./checkin.db
CHECK_INTERVAL_MINUTES=1

# Production (on Heroku)
DATABASE_URL=postgresql://...
CHECK_INTERVAL_MINUTES=5
```

---

## 8. Error Handling & Transactions

### 8.1 Service-Level Error Handling

```python
# app/services/checkin_service.py
def record_checkin(self) -> CheckInResponse:
    try:
        checkin = self.checkin_repo.record_checkin()
        status = self.compute_current_status()
        return CheckInResponse(
            timestamp=checkin.timestamp,
            status=status,
            hours_until_due=...,
        )
    except Exception as e:
        logger.error(f"Failed to record check-in: {e}")
        raise
```

**Why this works:**
- Errors logged with context
- Exceptions propagate to routes for HTTP error responses
- Database transactions rolled back automatically

---

## 9. Performance Considerations

### 9.1 Current Optimizations

- **Database indexes:** Check-in queries by timestamp (implicit via order_by)
- **Caching:** Settings cached per request (re-queried only when updated)
- **Batch operations:** (Future) bulk-fetch check-ins for analytics

### 9.2 Future Scaling

If needed:
- Add Redis caching layer (transparent to services)
- Move scheduler to Celery (transparent to domain logic)
- Add database connection pooling (one line in `database.py`)
- Add query optimization hints (in repositories)

**Why this works:**
- Changes isolated to infrastructure layers
- Services and domain logic unaffected

---

## 10. Security Considerations

### 10.1 Current State

- ✓ Input validation (Pydantic models)
- ✓ SQL injection prevention (SQLAlchemy ORM)
- ⚠ No authentication (local-only)

### 10.2 Future Security

Phase 2+ will add:
- [ ] User authentication (JWT tokens)
- [ ] Role-based access control (RBAC)
- [ ] Audit logging (who changed what, when)
- [ ] Encryption at rest (database-level)
- [ ] Rate limiting (on API endpoints)

**Design:** All security checks happen in routes or middleware, business logic stays pure.

---

## 11. Monitoring & Observability

### 11.1 Current

- Scheduler logs status changes to console
- API access logs from Uvicorn

### 11.2 Future

- [ ] Structured logging (JSON)
- [ ] Metrics (Prometheus)
- [ ] Tracing (OpenTelemetry)
- [ ] Alerting (PagerDuty)

**Why this works:**
- Observability added at infrastructure layer
- Services emit events that logging layer captures

---

## 12. Key Takeaways for Maintainers

| Rule | Why |
|------|-----|
| **Never put SQL in routes** | Breaks testability, ties HTTP to data |
| **Services orchestrate, don't compute** | Makes them reusable from any context |
| **Domain logic is pure functions** | Testable, shareable, independent |
| **Repositories abstract all DB access** | Swapping databases becomes a config change |
| **Routes are thin adapters** | Keep HTTP concerns out of business logic |
| **Config via environment** | Same code works locally and in cloud |

---

## 13. Code Review Checklist

When reviewing new code:

- [ ] Business logic in domain layer? (not routes, not services)
- [ ] Services only orchestrate? (no SQL, no HTTP)
- [ ] Routes delegate to services? (no business logic)
- [ ] Repositories abstract DB? (no SQLAlchemy in services)
- [ ] No hardcoded values? (use config)
- [ ] Can it be tested without HTTP/DB? (if it's business logic)
- [ ] Error handling appropriate? (logs with context)

---

## 14. Future Architecture Evolution

```
Phase 1 (Now)                Phase 2              Phase 3
────────────────────────────────────────────────────────
FastAPI Routes              FastAPI              FastAPI
    ↓                           ↓                    ↓
CheckInService          CheckInService      CheckInService (unchanged)
    ↓                           ↓                    ↓
CheckInRepository   CheckInRepository    Multi-tenant Repository
    ↓                           ↓                    ↓
SQLite                        SQLite        Postgres + Cache Layer
    ↓                           ↓                    ↓
APScheduler                APScheduler        AWS Lambda + SQS
```

**The domain layer (`status.py`) never changes.**

---

## Conclusion

This architecture prioritizes **clarity over cleverness**, enabling the system to evolve from a local prototype to a cloud-native, multi-user application without fundamental refactoring.

Each layer has one job, depends only on layers below it, and can be tested independently. This makes the codebase maintainable, testable, and extensible.

**Remember:** The best architecture is one that makes the next change easy.

---

*Last updated: February 14, 2026*
*Maintained by: Architecture team*
