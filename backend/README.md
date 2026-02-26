# Dead Man Switch - Backend 📍

**Clean, Production-Grade Safety API.**

The backend for the Dead Man Switch system, built with **FastAPI**, **SQLAlchemy**, and **Firebase Admin**. It provides secure identity management, status monitoring, and notification dispatch.

## 🚀 Features
- **Stateless API:** Designed for high scalability and decoupling.
- **Production Auth:** Integrates with **Firebase Auth** for secure, carrier-grade SMS verification.
- **Privacy First:** Uses **SHA-256 Hashing** for phone number identification and **E.164 normalization**.
- **Automated Monitoring:** Background scheduler evaluates safety status in real-time.
- **Clean Architecture:** Strictly layered into Domain, Service, Repository, and API tiers.

---

## 🛠️ Setup & Installation

### 1. Prerequisites
- **Python 3.11+**
- **uv** package manager

### 2. Install Dependencies
```bash
cd backend
uv sync
```

### 3. Firebase Admin Setup
This project requires a Firebase Service Account to verify users:
1.  Go to **Firebase Console > Project Settings > Service Accounts**.
2.  Click **"Generate new private key"**.
3.  Save the file as `backend/firebase-key.json`.
    - *Alternatively, set the `FIREBASE_SERVICE_ACCOUNT` environment variable with the JSON string content.*

### 4. Run the API
```bash
uv run uvicorn app.main:app --reload
```
The API will be live at `http://localhost:8000`.

---

## 🧪 Testing
We maintain a comprehensive test suite covering status logic and full API integration.
```bash
cd backend
uv run pytest
```

---

## 🗺️ API Endpoints

### Authentication
| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/auth/verify-firebase` | Exchange Firebase Token for session |
| `POST` | `/api/auth/logout` | Clear session |
| `GET` | `/api/me` | Get current user info |

### Core Logic
| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/checkin` | Record a safety check-in |
| `GET` | `/api/status` | Get current safety status |
| `GET/POST` | `/api/settings` | Manage interval & contacts |
| `GET/POST` | `/api/instructions` | Manage emergency instructions |

---

## 📂 Project Structure
```
backend/
├── app/
│   ├── api/          # FastAPI Routes
│   ├── services/     # Business logic orchestration
│   ├── repositories/ # Data access layer (SQLAlchemy)
│   ├── domain/       # Pure logic & Security (Hashing/Normalization)
│   ├── db/           # Database schema & setup
│   └── scheduler/    # Background status monitoring
└── tests/            # Integration & Logic tests
```

---

## 🔒 Security & Standards
- **Normalization:** All phone numbers are converted to E.164 format via `phonenumbers`.
- **Identity:** Internal user identification is done via SHA-256 hashes of phone numbers.
- **Layers:** Business rules are isolated from API and DB changes.
