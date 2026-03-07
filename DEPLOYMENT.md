# Deployment Guide: I'mGood Check-In

This guide explains how to deploy the I'mGood application using Docker.

## 1. Prerequisites

- A Firebase Project (for Authentication and Push Notifications).
- A Google Cloud Project with Firestore enabled.
- A Resend API Key (for email notifications).
- Docker and Docker Compose installed on your server.

## 2. Environment Variables

Create a `.env` file based on `.env.example`. You will need:

### Backend Variables
- `SECRET_KEY`: A long, random string for JWT signing.
- `PHONE_SALT`: A unique string for hashing phone numbers.
- `FIREBASE_SERVICE_ACCOUNT_JSON`: The full JSON content of your Google Cloud Service Account key.
- `RESEND_API_KEY`: Your Resend API key.
- `RESEND_SENDER`: The email address emails will be sent from (e.g., `I'mGood <onboarding@resend.dev>`).

### Frontend (Build-time) Variables
These are required during `docker build` to bundle the Firebase configuration into the frontend:
- `VITE_FIREBASE_API_KEY`
- `VITE_FIREBASE_AUTH_DOMAIN`
- `VITE_FIREBASE_PROJECT_ID`
- `VITE_FIREBASE_STORAGE_BUCKET`
- `VITE_FIREBASE_MESSAGING_SENDER_ID`
- `VITE_FIREBASE_APP_ID`
- `VITE_FIREBASE_VAPID_KEY`

## 3. Build and Run with Docker

### Using Docker Build Directly
You must pass the frontend variables as build arguments:

```bash
docker build 
  --build-arg VITE_FIREBASE_API_KEY=your_key 
  --build-arg VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com 
  --build-arg VITE_FIREBASE_PROJECT_ID=your_project_id 
  --build-arg VITE_FIREBASE_STORAGE_BUCKET=your_project.appspot.com 
  --build-arg VITE_FIREBASE_MESSAGING_SENDER_ID=123456789 
  --build-arg VITE_FIREBASE_APP_ID=1:123456789:web:abcdef \
  --build-arg VITE_FIREBASE_VAPID_KEY=your_vapid_key \
  --build-arg VITE_RECAPTCHA_V3_SITE_KEY=your_recaptcha_key \
  -t imgood-app .
  ```

  Then run it:
  ```bash
  docker run -p 8080:8080 --env-file .env imgood-app
  ```

  ### Using Docker Compose (Recommended)
  Create a `docker-compose.yml`:

  ```yaml
  services:
  app:
    build:
      context: .
      args:
        - VITE_FIREBASE_API_KEY=${VITE_FIREBASE_API_KEY}
        - VITE_FIREBASE_AUTH_DOMAIN=${VITE_FIREBASE_AUTH_DOMAIN}
        - VITE_FIREBASE_PROJECT_ID=${VITE_FIREBASE_PROJECT_ID}
        - VITE_FIREBASE_STORAGE_BUCKET=${VITE_FIREBASE_STORAGE_BUCKET}
        - VITE_FIREBASE_MESSAGING_SENDER_ID=${VITE_FIREBASE_MESSAGING_SENDER_ID}
        - VITE_FIREBASE_APP_ID=${VITE_FIREBASE_APP_ID}
        - VITE_FIREBASE_VAPID_KEY=${VITE_FIREBASE_VAPID_KEY}
        - VITE_RECAPTCHA_V3_SITE_KEY=${VITE_RECAPTCHA_V3_SITE_KEY}
    ports:
      - "${API_PORT:-8080}:8080"

    env_file:
      - .env
    restart: always
```

Run with:
```bash
docker compose up -d --build
```

## 4. Production Checklist

1. [ ] Ensure `SECRET_KEY` and `PHONE_SALT` are strong and backed up.
2. [ ] Verify Firestore security rules allow the service account to read/write.
3. [ ] Configure your domain and SSL (e.g., via Nginx or Cloudflare).
4. [ ] Set up a database backup strategy for Firestore.
