# Hybrid Deployment: Firebase Hosting + Cloud Run

This guide explains how to deploy the **Frontend to Firebase Hosting** and the **Backend to Google Cloud Run**. This is the recommended production setup.

## 1. Backend: Deploy to Cloud Run (API Only)

Follow the **`CLOUD_RUN_DEPLOYMENT.md`** guide to deploy your backend. 
Once deployed, you will get a URL like: `https://imgood-api-xyz-uc.a.run.app`

## 2. Frontend: Update API Base URL

In **`frontend/src/constants.ts`**, ensure the `API_BASE` points to your Cloud Run URL (or relative if using the proxy in Step 3):

```typescript
// For the Proxy approach (Recommended):
export const API_BASE = '/api'; 

// For the Direct approach (Alternative):
// export const API_BASE = 'https://imgood-api-xyz-uc.a.run.app/api';
```

## 3. Frontend: Setup Firebase Hosting

### Step A: Initialize Firebase
If you haven't already:
```bash
npm install -g firebase-tools
firebase login
firebase init hosting
```
*   **Public directory:** `frontend/dist`
*   **Single-page app:** `Yes`
*   **GitHub Actions:** `No` (unless desired)

### Step B: Configure Proxy (firebase.json)
This allows your frontend at `myapp.web.app/api` to securely talk to your Cloud Run backend.

Edit **`firebase.json`** in your root:
```json
{
  "hosting": {
    "public": "frontend/dist",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ],
    "rewrites": [
      {
        "source": "/api/**",
        "run": {
          "serviceId": "imgood-api",
          "region": "us-central1"
        }
      },
      {
        "source": "**",
        "destination": "/index.html"
      }
    ]
  }
}
```

### Step C: Build and Deploy
```bash
# 1. Build frontend with production variables
cd frontend
npm run build

# 2. Deploy to Firebase
cd ..
firebase deploy --only hosting
```

## 4. Why this setup is better:
1.  **Performance:** Firebase Hosting serves your images, JS, and CSS from a global CDN (closer to users).
2.  **Security:** Your API is hidden behind the Firebase domain, and SSL is handled automatically.
3.  **Cost:** Firebase Hosting has a generous free tier, and Cloud Run only charges when your API is actually processing requests.
4.  **CORS:** By using the `/api` rewrite (proxy), you avoid all "Cross-Origin" errors because the browser thinks the frontend and backend are on the same domain.
