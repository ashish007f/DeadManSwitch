# Google Cloud Run Deployment Guide: I'mGood

This guide explains how to deploy the I'mGood application to Google Cloud Run using the `gcloud` CLI.

## 1. Prerequisites

*   A Google Cloud Project (GCP) with billing enabled.
*   The [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and initialized (`gcloud init`).
*   Firestore enabled in **Native Mode** in your GCP project.
*   Firebase project linked to this GCP project (for Authentication).

## 2. Setup Artifact Registry

Create a repository to store your Docker images:

```bash
gcloud artifacts repositories create imgood-repo 
    --repository-format=docker 
    --location=us-central1 
    --description="Docker repository for I'mGood app"
```

## 3. Build and Push the Image

Build the image using **Google Cloud Build**. This is faster and handles the push to the registry automatically. 

**Note:** You MUST replace the placeholders with your actual values from your `.env` file.

```bash
gcloud builds submit --tag us-central1-docker.pkg.dev/YOUR_PROJECT_ID/imgood-repo/app:latest 
  --build-arg VITE_FIREBASE_API_KEY=YOUR_KEY 
  --build-arg VITE_FIREBASE_AUTH_DOMAIN=YOUR_PROJECT.firebaseapp.com 
  --build-arg VITE_FIREBASE_PROJECT_ID=YOUR_PROJECT_ID 
  --build-arg VITE_FIREBASE_STORAGE_BUCKET=YOUR_PROJECT.appspot.com 
  --build-arg VITE_FIREBASE_MESSAGING_SENDER_ID=YOUR_SENDER_ID 
  --build-arg VITE_FIREBASE_APP_ID=YOUR_APP_ID 
  --build-arg VITE_FIREBASE_VAPID_KEY=YOUR_VAPID_KEY
```

## 4. Deploy to Cloud Run

Assign a service account that has the `Cloud Datastore User` role so the app can access Firestore without a JSON key file.

### Step A: Create Service Account (One-time)
```bash
# Create the service account
gcloud iam service-accounts create imgood-runner

# Grant Firestore access
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID 
    --member="serviceAccount:imgood-runner@YOUR_PROJECT_ID.iam.gserviceaccount.com" 
    --role="roles/datastore.user"
```

### Step B: Deploy
Run the deployment command. Provide your runtime secrets (like Resend) here:

```bash
gcloud run deploy imgood-service 
  --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/imgood-repo/app:latest 
  --service-account imgood-runner@YOUR_PROJECT_ID.iam.gserviceaccount.com 
  --region us-central1 
  --allow-unauthenticated 
  --set-env-vars="SECRET_KEY=YOUR_JWT_SECRET" 
  --set-env-vars="PHONE_SALT=YOUR_PHONE_SALT" 
  --set-env-vars="RESEND_API_KEY=YOUR_RESEND_KEY" 
  --set-env-vars="RESEND_SENDER=I'mGood <onboarding@resend.dev>" 
  --port 8080
```

## 5. Security Checklist for Production

1.  **Secret Manager:** For high-security environments, replace `--set-env-vars` with `--set-secrets`.
2.  **Firebase Rules:** Ensure your Firebase Auth and Firestore rules are configured to only allow your service account and authorized users.
3.  **Domain:** Map your custom domain in the Cloud Run console under "Manage Custom Domains".

## 6. Verification

Once deployed, the command will output a Service URL (e.g., `https://imgood-service-xyz.a.run.app`). 
1.  Visit the URL to verify the frontend loads.
2.  Check `/api/health` to verify the backend is live.
3.  Check the "Logs" tab in the Google Cloud Console for any Firestore connection errors.
