# Architecture Document: I'mGood

**Clean Architecture for Extensible, Production-Grade Safety Systems**

---

## 1. Executive Summary
I'mGood is designed as a modular, local-first system that evolves into a hardened, cloud-ready application. This document outlines the transition from a local prototype to a production-grade system with a focus on privacy, security, and seamless mobile UX.

---

## 2. Core Architectural Layers
The project follows **Clean Architecture** principles to decouple business logic from infrastructure.

- **API Layer (FastAPI):** Thin adapters for HTTP/REST.
- **Service Layer:** Orchestrates business workflows.
- **Repository Layer:** Abstracted data access (SQLAlchemy).
- **Domain Layer:** Pure business logic (status calculations, rules).
- **Frontend (React/TS):** Decoupled mobile-first UI.

---

## 3. Production Authentication Strategy (Phased Roadmap)

We are moving from a local OTP prototype to a hardened **Identity Provider (IdP)** model.

### Phase 1: Infrastructure Hardening (Current to Next)
- **SMS Provider:** Integrate **Firebase Auth**. Leverage its invisible Recaptcha and high delivery rates.
- **Phone Normalization:** Use `libphonenumber` to enforce **E.164 format** (+1234567890) across all layers.
- **Privacy:** Store phone numbers as **SHA-256 hashes** for identification where possible, keeping raw numbers only in the secure IdP (Firebase).

### Phase 2: Token-Based Session Management
- **JWT Implementation:**
    - **Access Token:** Short-lived (15 min) for API authorization.
    - **Refresh Token:** Long-lived (30 days) stored in `localStorage` (Web) or `SecureStore` (Mobile).
- **Stateless Auth:** Move away from session cookies to `Authorization: Bearer <JWT>` headers to support native mobile wrappers and decoupled deployments.

### Phase 3: Mobile UX & Auto-Verification
- **Auto-OTP:** Implement the **WebOTP API** in the frontend. Allows the mobile browser/app to automatically detect and fill the OTP from incoming SMS.
- **Native Hints:** Enforce `inputMode="numeric"` and `autoComplete="one-time-code"` for frictionless input.

### Phase 4: Security & Rate Limiting
- **Global Rate Limiting:** Implement `slowapi` or Redis-based limiting on the Backend.
    - Limit OTP requests per Phone Number (prevent toll fraud).
    - Limit failed attempts per IP (prevent brute force).
- **Audit Logging:** Track authentication events (login, failed OTP, settings change) without storing PII.

### Phase 5: Passwordless & Biometrics (Passkeys)
- **Passkeys (WebAuthn):** Once a phone is verified, allow the user to register a **Passkey**.
- **Biometrics:** Enable FaceID/TouchID via the browser's `navigator.credentials` API. 
- **Benefit:** Eliminates SMS costs for returning users and provides "Instant-In" UX.

---

## 4. Data Flow: Production Auth
1. **Frontend:** Requests OTP via Firebase Client SDK.
2. **Firebase:** Sends SMS; returns a session ID.
3. **User:** Enters code (or Auto-filled via WebOTP).
4. **Frontend:** Exchanges code for a Firebase ID Token.
5. **Backend:** 
    - Validates Firebase Token via `firebase-admin`.
    - Normalizes Phone Number.
    - Issues custom **Access + Refresh JWTs**.
6. **Frontend:** Stores Refresh Token and enters authenticated state.

---

## 5. Security & Privacy Standards
- **TLS Everywhere:** All communication must be over HTTPS.
- **Secret Management:** API keys (Firebase, Twilio) must never be committed. Use environment variables.
- **PII Protection:** Raw phone numbers are sensitive. The backend only uses them for notification dispatch; all internal indexing uses the user UUID or hashed phone.

---

## 6. Project Reorganization (Completed)
The project is split into two independent modules:
- `/backend`: Python/FastAPI logic, migrations, and tests.
- `/frontend`: React/TypeScript mobile application.

This separation allows for independent scaling, deployment (e.g., Backend on Cloud Run, Frontend on Vercel), and future replacement of either layer.

---
*Last updated: February 26, 2026*
