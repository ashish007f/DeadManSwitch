# Dead-Man Switch 📍

**Local-first check-in system for peace of mind.**

A minimal, extensible Python application that tracks periodic check-ins and evaluates safety status. Designed as a local prototype that can evolve into cloud APIs, mobile backends, and multi-user systems without major refactoring.

## Overview

Dead-Man Switch monitors your well-being through periodic check-ins. If you miss a check-in, the system escalates status from **SAFE** → **DUE_SOON** → **MISSED**, allowing trusted contacts to be notified (future feature).

**Core Capabilities:**

- ✓ Record check-ins with a single click
- ✓ Automatic status evaluation (SAFE / DUE_SOON / MISSED)
- ✓ Configurable check-in intervals
- ✓ Store instructions for trusted contacts
- ✓ Background scheduler monitors status continuously
- ✓ Clean API for future integrations
- ✓ Zero cloud dependency (runs locally)

## Quick Start

### Prerequisites

- Python 3.11+
- `uv` package manager

### Installation

```bash
# Clone repository
git clone <repo>
cd DeadManSwitch

# Install dependencies
uv sync

# Start the application
uv run uvicorn app.main:app --reload
```

### Usage

Open your browser:

```
http://localhost:8000
```

**Dashboard Features:**

- 📍 Check In Now button
- 📊 Current status display (SAFE/DUE_SOON/MISSED)
- ⏱ Hours until next check-in
- ⚙️ Settings panel (adjust interval, store instructions)
- 🔄 Auto-refresh (5-second polling)

### API Endpoints


| Method | Endpoint            | Purpose                          |
| ------ | ------------------- | -------------------------------- |
| `POST` | `/api/checkin`      | Record a check-in                |
| `GET`  | `/api/status`       | Get current status               |
| `GET`  | `/api/settings`     | Get check-in interval            |
| `POST` | `/api/settings`     | Update check-in interval         |
| `GET`  | `/api/instructions` | Get trusted contact instructions |
| `POST` | `/api/instructions` | Save instructions                |


### Example API Calls

```bash
# Check in
curl -X POST http://localhost:8000/api/checkin

# Get status
curl http://localhost:8000/api/status

# Update interval to 24 hours
curl -X POST http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{"checkin_interval_hours": 24}'

# Save instructions
curl -X POST http://localhost:8000/api/instructions \
  -H "Content-Type: application/json" \
  -d '{"content": "If I miss 48 hours, call my emergency contact"}'
```

## Database

**Location:** `./checkin.db` (SQLite)

**Tables:**

- `checkins` — Records each check-in timestamp
- `settings` — Application configuration (interval hours)
- `instructions` — Instructions for trusted contacts

**Query with SQLite CLI:**

```bash
sqlite3 checkin.db
sqlite> SELECT * FROM checkins;
sqlite> SELECT * FROM settings;
```

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design decisions, layering strategy, and extensibility patterns.

**Quick Overview:**

```
FastAPI Routes
     ↓
Service Layer (business logic)
     ↓
Repository Layer (data access)
     ↓
Domain Logic (pure functions)
     ↓
SQLAlchemy ORM + SQLite
```

## Development

### Project Structure

```
app/
├── main.py                 # FastAPI entrypoint
├── config.py              # Environment configuration
├── api/
│   └── routes.py          # HTTP endpoints
├── services/
│   └── auth_service.py # Business logic orchestration
│   └── checkin_service.py # Business logic orchestration
├── repositories/
│   └── auth_repo.py       # Data access layer
│   └── checkin_repo.py    # Data access layer
├── domain/
│   ├── models.py          # Pydantic DTOs
│   └── status.py          # Pure domain logic
├── db/
│   ├── database.py        # SQLAlchemy setup
│   └── schema.py          # ORM models
├── scheduler/
│   └── jobs.py            # Background monitoring
└── templates/
    └── index.html         # Dashboard UI
```

### Running Tests

```bash
uv run python test_routes.py
```

## Future Roadmap

**Phase 1 (Done):**

- ✓ Local check-in tracking
- ✓ Status calculation
- ✓ Minimal UI dashboard
- ✓ Clean API
- ✓ basic user authentication

**Phase 2 (Future):**

- Mobile app (React Native)
- Notification adapters (SMS, WhatsApp)
- Emergency contact management

**Phase 3 (Planned):**

- User authentication
- Encryption layer
- Cloud deployment (AWS Lambda, Vercel)

## Configuration

### Environment Variables

```bash
# .env file (optional)
DATABASE_URL=sqlite:///./checkin.db
CHECK_INTERVAL_MINUTES=1
```

**Defaults:**

- Check interval: 1 minute (for monitoring)
- Database: SQLite at `./checkin.db`

## Dependencies


| Package       | Purpose              |
| ------------- | -------------------- |
| `fastapi`     | Web framework        |
| `uvicorn`     | ASGI server          |
| `sqlalchemy`  | ORM                  |
| `pydantic`    | Data validation      |
| `apscheduler` | Background scheduler |
| `jinja2`      | Template rendering   |


See `pyproject.toml` for versions.

## License

MIT

## Contributing

Contributions welcome! Please follow the architectural patterns in [ARCHITECTURE.md](ARCHITECTURE.md).

---

**Built with clean architecture principles for local-first, cloud-ready applications.**