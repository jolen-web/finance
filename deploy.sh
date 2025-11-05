#!/bin/bash

# Finance App Deployment Script for Google Cloud Run
# This script deploys the Flask Finance Tracker to Google Cloud Run

set -e

PROJECT_ID="jinolen"
SERVICE_NAME="finance-tracker"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
GCLOUD="/Users/njpinton/google-cloud-sdk/bin/gcloud"

echo "===================================="
echo "Finance Tracker - Google Cloud Deployment"
echo "===================================="
echo "Project: $PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"
echo ""

# Step 1: Build Docker image
echo "📦 Building Docker image..."
docker build --platform=linux/amd64 -t "${IMAGE_NAME}:latest" .

# Step 2: Push to Container Registry
echo "📤 Pushing image to Google Container Registry..."
docker push "${IMAGE_NAME}:latest"

# Step 3: Enable required APIs
echo "🔧 Enabling Google Cloud APIs..."
$GCLOUD services enable run.googleapis.com \
    containerregistry.googleapis.com \
    cloudbuild.googleapis.com \
    compute.googleapis.com \
    --project=$PROJECT_ID 2>&1 || echo "⚠️  Some APIs may already be enabled"

# Step 4: Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
$GCLOUD run deploy $SERVICE_NAME \
    --image "${IMAGE_NAME}:latest" \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --project=$PROJECT_ID \
    --memory=2Gi \
    --cpu=1 \
    --timeout=3600 \
    --set-env-vars="FLASK_ENV=production,DATABASE_URL=sqlite:///instance/finance.db" \
    --port=5000

# Step 5: Get service URL
echo ""
echo "✅ Deployment complete!"
echo ""
SERVICE_URL=$($GCLOUD run services describe $SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --project=$PROJECT_ID \
    --format='value(status.url)')

echo "🌐 Your app is live at: $SERVICE_URL"
echo ""
echo "📝 Important Notes:"
echo "  - Database will be fresh on startup. Run migrations if needed."
echo "  - Environment variables should be set in Cloud Run service settings"
echo "  - Check logs: gcloud run logs read $SERVICE_NAME --region=$REGION"
echo ""
