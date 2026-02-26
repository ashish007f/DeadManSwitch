# Architecture Document: Dead Man Switch

**Clean Architecture for Extensible, Production-Grade Safety Systems**

---

## 1. Executive Summary
Dead Man Switch is a modular safety system designed to transition from a local prototype to a hardened, cloud-ready application. It employs **Clean Architecture** to decouple core business logic from infrastructure, enabling independent scaling and deployment of its components.

---

## 2. Decoupled Mono-Repo Structure
The project is organized as a mono-repo with two completely decoupled modules:

- **`/backend`**: FastAPI safety engine, persistent storage, and background monitoring.
- **`/frontend`**: React/TypeScript mobile-first dashboard.

This separation ensures that either layer can be replaced or scaled independently (e.g., swapping the React frontend for a native iOS/Android app).

---

## 3. Core Architectural Layers (Backend)

### 3.1 API Layer (FastAPI)
- **File:** `backend/app/api/routes.py`
- **Responsibility:** HTTP request/response handling, input validation (Pydantic), and cookie/token management.
- **Principle:** Thin adapters. No business logic lives here.

### 3.2 Service Layer
- **File:** `backend/app/services/`
- **Responsibility:** Orchestrating business workflows (e.g., "Verify Firebase token, then create user").
- **Principle:** Coordinators. They call repositories and domain logic.

### 3.3 Repository Layer
- **File:** `backend/app/repositories/`
- **Responsibility:** All database interactions (SQLAlchemy).
- **Principle:** Data abstraction. The rest of the app doesn't know it's using SQLite.

### 3.4 Domain Layer
- **File:** `backend/app/domain/`
- **Responsibility:** Pure business logic (status calculations) and security primitives (normalization, hashing).
- **Principle:** Zero dependencies. This code is framework-agnostic.

---

## 4. Production Authentication Strategy

We have moved from a local OTP prototype to a hardened **Identity Provider (IdP)** model.

### 4.1 Authentication Flow
1.  **Frontend:** Requests carrier-grade SMS OTP via **Firebase Auth SDK**.
2.  **Firebase:** Handles SMS delivery, rate limiting, and bot protection (reCAPTCHA).
3.  **Frontend:** Exchanges the successful OTP for a **Firebase ID Token**.
4.  **Backend:** Validates the ID Token using `firebase-admin`, normalizes the phone number, and establishes a secure session.

### 4.2 Security & Privacy Standards
- **Normalization:** All phone numbers are converted to **E.164 format** (+1234567890).
- **Identity Privacy:** Internal user identification is driven by **SHA-256 hashes** of the normalized phone numbers. Raw numbers are only stored for notification dispatch.
- **Statelessness:** Designed to move from cookies to **JWT (JSON Web Tokens)** in Phase 2 for better native mobile support.

---

## 5. Background Monitoring
The system uses **APScheduler** to continuously monitor user safety.
- **Job:** `backend/app/scheduler/jobs.py`
- **Trigger:** Evaluates every user's status every minute.
- **States:** `SAFE` → `DUE_SOON` → `MISSED` → `GRACE_PERIOD` → `NOTIFIED`.

---

## 6. Testing Strategy
- **Unit Tests:** Pure status logic in `backend/tests/test_domain_status.py`.
- **Integration Tests:** Full API cycle testing in `backend/tests/test_integration_api.py` using a fresh in-memory SQLite database for every test.

---

## 7. Roadmap Highlights (Execution in PLAN.md)
- **Phase 1 (Completed):** Infrastructure Hardening (Firebase Auth, Hashing, E.164).
- **Phase 2 (Next):** JWT Session Management (Access/Refresh Tokens).
- **Phase 3:** Push Notifications & Adapters (Twilio, WhatsApp).
- **Phase 4:** Biometrics & Passkeys (TouchID/FaceID).

---
*Last updated: February 26, 2026*
