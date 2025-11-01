# Cloud Run Deployment Guide

This document covers deployment of the Finance Tracker application to Google Cloud Run.

## Current Setup

- **Platform**: Google Cloud Run (Managed)
- **Region**: us-central1
- **Database**: Cloud SQL PostgreSQL (jinolen:us-central1:finance-db)
- **Memory**: 2Gi
- **CPU**: 1
- **Timeout**: 3600s

## Deployment Fixes Applied

### P0 - Critical Fixes (Required for Deployment)

✅ **Port Configuration**
- Dockerfile now exposes port 5000 (changed from 5001)
- Gunicorn binds to 0.0.0.0:5000
- cloudbuild.yaml deploys to port 5000

✅ **Database Configuration**
- config.py now constructs Cloud SQL connection string from environment variables
- Falls back to SQLite for local development
- Connection string format: `postgresql+psycopg2://user:password@/dbname?host=/cloudsql/CLOUD_SQL_CONNECTION`

✅ **Database Migrations**
- Dockerfile CMD now runs `flask db upgrade` before starting Gunicorn
- Ensures schema is current on deployment

✅ **PostgreSQL Support**
- Added libpq5 runtime library to final Docker image
- Enables psycopg2 connection to Cloud SQL

✅ **Secrets Management**
- cloudbuild.yaml now requests three secrets from Secret Manager:
  - `DB_PASSWORD` - Cloud SQL password
  - `SECRET_KEY` - Flask session encryption key
  - `GOOGLE_API_KEY` - Gemini API key for receipt OCR

⚠️ **Exposed API Key Rotation**
- The Google API key in `.env` is exposed in git history
- **Action Required**:
  1. Generate new API key in Google Cloud Console
  2. Revoke the exposed key: `AIzaSyDUKA2cFuBE7QDIK8uH36pSHv47IfmQze0`
  3. Create `gemini-api-key` secret in Secret Manager with the new key
  4. Add `.env` to `.gitignore` to prevent future commits

### P1 - Security Fixes (Required Before Production)

✅ **User Isolation**
- `/receipts/upload/<transaction_id>` now verifies user owns the transaction
- `/receipts/camera/<transaction_id>` now verifies user owns the transaction
- Prevents data leakage between users

✅ **CSRF Protection**
- Added Flask-WTF to requirements.txt
- Initialized CSRFProtect in app factory
- All POST endpoints now protected against cross-site request forgery

### P2 - Production Readiness Fixes

✅ **Health Check Endpoint**
- New `/health` endpoint at `app/routes/main.py:9-28`
- Checks database connectivity
- Returns 200 OK if healthy, 503 Service Unavailable if unhealthy
- Can be used by Cloud Run for health checks

✅ **Structured Logging**
- Added python-json-logger to requirements.txt
- Production environment logs in JSON format
- Compatible with Google Cloud Logging

✅ **Error Handling**
- Custom error handlers for 404, 403, and 500 errors
- Error templates in `app/templates/errors/`
- Proper logging of server errors with stack traces

## Pre-Deployment Setup

### 1. Generate Secrets

```bash
# Generate a secure SECRET_KEY
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')

# Create secrets in Secret Manager
echo -n "$SECRET_KEY" | gcloud secrets create flask-secret-key --data-file=- --project=jinolen

# Add new Gemini API key (after revoking the exposed one)
echo -n "YOUR_NEW_GEMINI_API_KEY" | gcloud secrets create gemini-api-key --data-file=- --project=jinolen

# Verify secrets were created
gcloud secrets list --project=jinolen
```

### 2. Grant Service Account Access

```bash
# Get the default Cloud Run service account
SA="jinolen@appspot.gserviceaccount.com"

# Grant access to secrets
for secret in flask-secret-key gemini-api-key finance-db-password; do
  gcloud secrets add-iam-policy-binding "$secret" \
    --member="serviceAccount:$SA" \
    --role="roles/secretmanager.secretAccessor" \
    --project=jinolen
done
```

### 3. Verify Cloud SQL Setup

```bash
# Check Cloud SQL instance
gcloud sql instances describe finance-db --project=jinolen

# Verify database exists
gcloud sql databases describe finance --instance=finance-db --project=jinolen

# Check postgres user exists
gcloud sql users list --instance=finance-db --project=jinolen
```

## Deployment Process

### Option 1: Cloud Build (Recommended)

```bash
# From the project root directory
gcloud builds submit --config cloudbuild.yaml . --project=jinolen

# Monitor the build
gcloud builds log $(gcloud builds list --project=jinolen --limit=1 --format='value(id)') --project=jinolen --stream
```

### Option 2: Local Deployment Script

```bash
# Update deploy.sh with Cloud SQL configuration
./deploy.sh
```

### Option 3: Manual gcloud Command

```bash
gcloud run deploy finance-tracker \
    --image gcr.io/jinolen/finance-tracker:latest \
    --region us-central1 \
    --platform managed \
    --memory 2Gi \
    --cpu 1 \
    --timeout 3600 \
    --add-cloudsql-instances jinolen:us-central1:finance-db \
    --set-env-vars "FLASK_ENV=production,DB_USER=postgres,DB_NAME=finance,CLOUD_SQL_CONNECTION_NAME=jinolen:us-central1:finance-db" \
    --update-secrets "DB_PASSWORD=finance-db-password:latest,SECRET_KEY=flask-secret-key:latest,GOOGLE_API_KEY=gemini-api-key:latest" \
    --port 5000 \
    --project=jinolen
```

## Post-Deployment Verification

### 1. Check Service Status

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe finance-tracker \
    --region us-central1 \
    --project=jinolen \
    --format='value(status.url)')

echo "Service URL: $SERVICE_URL"
```

### 2. Test Health Endpoint

```bash
curl "$SERVICE_URL/health"
# Expected response: {"status": "healthy", "database": "connected"}
```

### 3. Check Logs

```bash
# View recent logs
gcloud run services logs read finance-tracker \
    --region us-central1 \
    --project=jinolen \
    --limit=50

# Follow logs (tail)
gcloud run services logs tail finance-tracker \
    --region us-central1 \
    --project=jinolen

# Filter for errors
gcloud run services logs read finance-tracker \
    --region us-central1 \
    --filter='severity>=ERROR' \
    --project=jinolen
```

### 4. Test Application Endpoints

```bash
# Test registration
curl -X POST "$SERVICE_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d '{"username":"testuser","email":"test@example.com","password":"TestPassword123"}'

# Test health endpoint
curl "$SERVICE_URL/health"

# Check for proper error pages
curl "$SERVICE_URL/nonexistent" | head -20
```

## Known Limitations & Future Work

### Receipt File Storage ⚠️

**Current State**: Receipt files are stored in the container's local filesystem (`data/receipts/`)

**Issue**: Cloud Run containers are ephemeral. Files are lost when:
- The service scales down (min-instances=0)
- The container restarts
- A new deployment is rolled out

**Workaround**: For now, receipt storage works within a single container session, but receipts will be lost on restart.

**Future Improvement**: Migrate to Google Cloud Storage (GCS)
- Persistent storage across container restarts
- Automatic backups
- Cost-effective for large files
- Minimal code changes required

**Migration Steps** (for future):
1. Add google-cloud-storage to requirements.txt
2. Update `app/services/receipt_ocr.py` to use GCS for production
3. Create GCS bucket: `gs://jinolen-finance-receipts`
4. Update cloudbuild.yaml with `GCS_BUCKET_NAME` environment variable
5. Update receipt retrieval to serve files from GCS

### Costs

**Estimated Monthly Costs**:
- Cloud Run: ~$0-50 (pay-per-use with cold starts)
- Cloud SQL (always-on): ~$50-70
- Container Registry: ~$5-10
- Cloud Storage (if implemented): ~$5-20

## Troubleshooting

### Build Fails: "Module not found"

**Symptom**: Build error during pip install

**Solution**:
```bash
# Check if requirements.txt has all dependencies
pip install -r requirements.txt

# If pip install fails locally, something is wrong with requirements
# Build in verbose mode:
gcloud builds submit --config cloudbuild.yaml . --project=jinolen --log-streaming
```

### Cloud Run: "Health check failed"

**Symptom**: Service marked as unhealthy, repeatedly restarting

**Solution**:
```bash
# Check logs
gcloud run services logs read finance-tracker --region=us-central1 --limit=50

# Common causes:
# 1. SECRET_KEY not set -> "No SECRET_KEY set for Flask application"
# 2. Cloud SQL not reachable -> psycopg2.OperationalError
# 3. Migrations failed -> "relation does not exist"
```

### Cloud SQL: "Connection refused"

**Symptom**: psycopg2.OperationalError when connecting

**Solution**:
```bash
# Verify Cloud SQL instance is running
gcloud sql instances describe finance-db --project=jinolen | grep -i status

# Check connection name format
# Should match: jinolen:us-central1:finance-db

# Verify CLOUD_SQL_CONNECTION_NAME env var is set
gcloud run services describe finance-tracker \
    --region=us-central1 \
    --format='get(spec.template.spec.containers[0].env)' \
    --project=jinolen
```

### Database Migration Error

**Symptom**: "relation already exists" or schema conflicts

**Solution**:
```bash
# Test migrations locally first
export DATABASE_URL="sqlite:///test.db"
flask db upgrade

# If issues found, create new migration
flask db migrate -m "fix: description"
flask db upgrade

# Verify migrations in production
gcloud run services logs read finance-tracker --filter='flask db upgrade' --region=us-central1 --project=jinolen
```

## Environment Variables Reference

**Required (via cloudbuild.yaml)**:
- `FLASK_ENV=production` - Flask environment mode
- `DB_USER=postgres` - Cloud SQL user
- `DB_NAME=finance` - Database name
- `CLOUD_SQL_CONNECTION_NAME=jinolen:us-central1:finance-db` - Cloud SQL connection string

**Secrets (via Secret Manager)**:
- `DB_PASSWORD` - Cloud SQL password (finance-db-password)
- `SECRET_KEY` - Flask session key (flask-secret-key)
- `GOOGLE_API_KEY` - Gemini API key (gemini-api-key)

## Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud SQL Documentation](https://cloud.google.com/sql/docs)
- [Cloud Logging](https://cloud.google.com/logging/docs)
- [Secret Manager](https://cloud.google.com/secret-manager/docs)
