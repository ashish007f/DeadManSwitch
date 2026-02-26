# I'mGood ✅

**A production-ready safety system built with Clean Architecture.**

This project is a modern implementation of "I'mGood" – a safety mechanism that triggers automatically if the user fails to check in within a pre-defined interval.

## 📂 Project Structure

This is a decoupled mono-repo consisting of two main modules:

### 1. [Backend](./backend)
- **Tech Stack:** Python (FastAPI), SQLAlchemy, SQLite, Firebase Admin.
- **Purpose:** Core business logic, status monitoring, secure identity management, and persistent storage.
- **Key Feature:** Automated status evaluation (SAFE → DUE_SOON → MISSED).

### 2. [Frontend](./frontend)
- **Tech Stack:** React (TypeScript), Vite, Lucide-React, Firebase SDK.
- **Purpose:** Mobile-first dashboard for user interaction, check-ins, and configuration.
- **Key Feature:** Production-grade Phone Authentication via Firebase.

---

## 🚦 Getting Started

To run the entire system locally, follow the setup instructions in each module:

1.  **Backend Setup:** See [backend/README.md](./backend/README.md)
2.  **Frontend Setup:** See [frontend/README.md](./frontend/README.md)

---

## 🗺️ Roadmap & Design

- **Architecture:** See [ARCHITECTURE.md](./ARCHITECTURE.md) for the Clean Architecture design patterns.
- **Plan:** See [PLAN.md](./PLAN.md) for the phased production-grade rollout plan.

## 🔒 Security
- **Carrier-Grade Auth:** Uses Firebase Phone Auth for reliable SMS verification.
- **Privacy Centric:** User phone numbers are normalized and hashed (SHA-256) for internal identification.
- **Strict Layering:** Domain logic is decoupled from infrastructure to ensure long-term maintainability.
