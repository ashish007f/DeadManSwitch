# I'mGood - Mobile Frontend

This is the mobile-first frontend for the I'mGood project, built with **React**, **TypeScript**, and **Vite**.

## 🚀 Features
- **Modern Mobile UI:** Responsive, clean interface using `lucide-react`.
- **Firebase Auth:** Production-grade phone authentication with invisible reCAPTCHA.
- **Dynamic Status:** Visual feedback (Green/Amber/Red) based on your check-in status.
- **Decoupled:** Communicates with the FastAPI backend via a secure proxy.

---

## 🛠️ Setup & Installation

### 1. Prerequisites
- **Node.js** (v18 or higher recommended)
- **npm** or **yarn**

### 2. Install Dependencies
```bash
cd frontend
npm install
```

### 3. Firebase Configuration
The app uses Firebase Phone Authentication. You need to provide your own Firebase config:

1.  Create a project in the [Firebase Console](https://console.firebase.google.com/).
2.  Enable **Phone Authentication** in the "Build > Authentication" section.
3.  Register a **Web App** in Project Settings.
4.  Create a `.env.local` file in the `frontend/` directory:
    ```env
    VITE_FIREBASE_API_KEY=your_api_key
    VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
    VITE_FIREBASE_PROJECT_ID=your_project_id
    VITE_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
    VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
    VITE_FIREBASE_APP_ID=your_app_id
    ```
    *(Alternatively, edit `src/firebase.ts` directly, though `.env` is preferred for security).*

---

## 💻 Development

### Run the App
```bash
npm run dev
```
The app will be available at `http://localhost:5173`.

### Connecting to Backend
The app expects the backend to be running on `http://localhost:8000`. Vite is configured to proxy all `/api` requests to this address.

### Mobile Device Testing
To test on a physical mobile device:
1.  Ensure your phone and computer are on the same Wi-Fi.
2.  Run with the host flag:
    ```bash
    npm run dev -- --host
    ```
3.  Open the **Network URL** shown in your terminal on your phone's browser.

---

## 📦 Production

### Build for Production
```bash
npm run build
```
The production-ready assets will be generated in the `dist/` directory.

### UI/UX Standards
- **Mobile First:** Optimized for small screens and touch interactions.
- **Visual Feedback:** Entire status card changes color based on safety status.
- **Accessibility:** Uses semantic HTML and clear labels.
