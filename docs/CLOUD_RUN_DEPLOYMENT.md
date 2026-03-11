# Google Cloud Run Deployment Guide: I'mGood (API Only)

This guide explains how to deploy the **I'mGood Backend API** to Google Cloud Run. This is intended to be used in a hybrid setup where the Frontend is hosted on Firebase Hosting.

## 1. Prerequisites

*   A Google Cloud Project (GCP) with billing enabled.
*   The [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and initialized (`gcloud init`).
*   Firestore enabled in **Native Mode** in your GCP project.
*   Firebase project linked to this GCP project.

## 2. Setup Artifact Registry

Create a repository to store your Docker images:

```bash
gcloud artifacts repositories create imgood-repo \
    --repository-format=docker \
    --location=us-central1 \
    --description="Docker repository for I'mGood API"
```

## 3. Build and Push the API Image

Build the optimized API-only image using **Google Cloud Build**. Note that we now use `--file Dockerfile.api`.

```bash
gcloud builds submit --tag us-central1-docker.pkg.dev/YOUR_PROJECT_ID/imgood-repo/api:latest \
  --file Dockerfile.api .
```

## 4. Deploy to Cloud Run

### Step A: Create Service Account (One-time)
This allows the API to talk to Firestore without needing a JSON key file.

```bash
# Create the service account
gcloud iam service-accounts create imgood-runner

# Grant Firestore access
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:imgood-runner@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/datastore.user"
```

### Step B: Deploy
Run the deployment command. Provide your runtime secrets (like Resend) here:

```bash
gcloud run deploy imgood-api \
  --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/imgood-repo/api:latest \
  --service-account imgood-runner@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="SECRET_KEY=YOUR_JWT_SECRET" \
  --set-env-vars="PHONE_SALT=YOUR_PHONE_SALT" \
  --set-env-vars="RESEND_API_KEY=YOUR_RESEND_KEY" \
  --set-env-vars="RESEND_SENDER=I'mGood <onboarding@resend.dev>" \
  --set-env-vars="ENFORCE_APP_CHECK=true" \
  --port 8080
```

## 5. Verification

Once deployed, the command will output a Service URL (e.g., `https://imgood-api-xyz.a.run.app`). 

1.  Check the health endpoint: `https://imgood-api-xyz.a.run.app/api/health`
2.  Use this URL in your **Firebase Hosting** setup or update `frontend/src/constants.ts`.

## 6. Next Steps
Now that your API is live, follow the **`HYBRID_DEPLOYMENT.md`** guide to deploy your frontend to Firebase Hosting and connect it to this API.
