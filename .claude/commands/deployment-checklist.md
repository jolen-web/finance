# /deployment-checklist

**Purpose**: Run pre-deployment and post-deployment verification checklists for the finance-tracker application.

**Usage**:
```
/deployment-checklist pre-deployment
/deployment-checklist post-deployment
/deployment-checklist diagnose-failure
```

## Available Checklist Types

### 1. Pre-Deployment Checklist
Run this before deploying to production to verify all prerequisites are met.

**Command**: `/deployment-checklist pre-deployment`

**What It Checks**:
- ✅ Git status (working tree clean, commits pushed)
- ✅ Database migrations (files exist and are current)
- ✅ Environment variables & secrets (all required secrets configured)
- ✅ Docker image (built, pushed to GCR, correct architecture)
- ✅ Cloud infrastructure (Cloud Run service and Cloud SQL database)
- ✅ Security configuration (FLASK_ENV, CSRF, security headers)
- ✅ Code validation (imports work, config loads, DB URI correct)

**Output**:
- Pass/fail status for each check
- Any critical blockers
- GO or NO-GO decision for deployment
- Exact deployment command if GO

---

### 2. Post-Deployment Checklist
Run this after deploying to verify the service is healthy and functional.

**Command**: `/deployment-checklist post-deployment`

**What It Checks**:
- ✅ Service is in Ready state
- ✅ Service URL is accessible
- ✅ No critical errors in recent logs
- ✅ Health endpoint responds
- ✅ Registration and login pages load
- ✅ Database connectivity works
- ✅ Security headers are present
- ✅ Performance is acceptable

**Output**:
- Service health status
- Log scan results
- Functional test results
- Overall readiness assessment
- Any issues requiring attention

---

### 3. Failure Diagnosis
Run this when a deployment fails to identify the root cause.

**Command**: `/deployment-checklist diagnose-failure`

**What It Does**:
- Scans Cloud Build logs for build errors
- Reads Cloud Run service logs for runtime errors
- Identifies failure pattern (build, config, database, permissions)
- Suggests specific remediation steps
- Provides rollback command if needed

**Output**:
- Exact error message
- Failed component
- Root cause analysis
- Recommended fix
- Rollback procedure (if applicable)

---

## Detailed Verification Steps

### Pre-Deployment: Code & Git Status
```bash
git status                    # Should show "nothing to commit, working tree clean"
git log --oneline -5          # Show recent commits
git push --dry-run origin master  # Verify push possible
```

**Checks**:
- ✅ No uncommitted changes
- ✅ Latest commits pushed to origin/master
- ✅ Git history is clean

---

### Pre-Deployment: Database Migrations
```bash
ls -la migrations/versions/    # Verify migration files exist
grep -r "Migrate" app/__init__.py  # Verify Flask-Migrate configured
cat alembic.ini | grep script_location  # Verify alembic.ini setup
```

**Checks**:
- ✅ Migrations directory exists
- ✅ Recent migration files present
- ✅ Flask-Migrate is initialized
- ✅ Alembic is configured

---

### Pre-Deployment: Environment Variables & Secrets
```bash
# List all secrets
gcloud secrets list --project=jinolen

# Check each secret has proper permissions
gcloud secrets get-iam-policy flask-secret-key --project=jinolen
gcloud secrets get-iam-policy finance-db-password --project=jinolen
gcloud secrets get-iam-policy gemini-api-key --project=jinolen

# Verify service account has access
SA="jinolen@appspot.gserviceaccount.com"
```

**Required Secrets**:
- `flask-secret-key` - Flask session encryption
- `finance-db-password` - PostgreSQL password
- `gemini-api-key` - Receipt OCR API key

**Checks**:
- ✅ All secrets exist in Secret Manager
- ✅ Service account can access all secrets
- ✅ No hardcoded secrets in source code
- ✅ No .env files committed to git

---

### Pre-Deployment: Docker Image
```bash
# Verify image in GCR
gcloud container images list --project=jinolen

# Check image details
gcloud container images describe gcr.io/jinolen/finance-tracker:latest

# Verify architecture (should be amd64)
docker inspect gcr.io/jinolen/finance-tracker:latest | grep -i architecture
```

**Checks**:
- ✅ Image exists at `gcr.io/jinolen/finance-tracker:latest`
- ✅ Image is built for amd64 (required for Cloud Run)
- ✅ Image has reasonable size (< 2GB)
- ✅ Gunicorn is installed and configured

---

### Pre-Deployment: Cloud Infrastructure
```bash
# Check Cloud Run service
gcloud run services describe finance-tracker \
  --region=us-central1 \
  --project=jinolen

# Check Cloud SQL instance
gcloud sql instances describe finance-db --project=jinolen

# Check database exists
gcloud sql databases list --instance=finance-db --project=jinolen

# Check recent backups
gcloud sql backups list --instance=finance-db --project=jinolen --limit=3
```

**Checks**:
- ✅ Cloud Run service exists
- ✅ Cloud SQL instance exists and is running
- ✅ Database `finance` exists
- ✅ Recent backups exist (safety net)
- ✅ Service account has Cloud SQL Client role

---

### Pre-Deployment: Security Configuration
```bash
# Check environment variables in config.py
grep -E "SESSION_COOKIE_SECURE|SESSION_COOKIE_HTTPONLY|SESSION_COOKIE_SAMESITE" config.py

# Check Talisman configuration
grep -r "Talisman\|CSRFProtect" app/__init__.py

# Check rate limiting
grep -r "limiter\|rate_limit" app/ --include="*.py"
```

**Checks**:
- ✅ FLASK_ENV can be set to 'production'
- ✅ SESSION_COOKIE_SECURE = True (HTTPS only)
- ✅ SESSION_COOKIE_HTTPONLY = True (XSS prevention)
- ✅ SESSION_COOKIE_SAMESITE = 'Lax' (CSRF protection)
- ✅ Talisman configured for production
- ✅ CSRF tokens on all forms
- ✅ Rate limiting on sensitive endpoints

---

### Pre-Deployment: Code Validation
```bash
# Test Python syntax and imports
python -c "from app import create_app; print('✓ App imports successfully')"

# Test config loads
python -c "from config import Config; print('✓ Config valid')"

# Verify database URL format
python -c "from config import Config; print(Config.SQLALCHEMY_DATABASE_URI)"

# Check requirements.txt
grep -E "flask|sqlalchemy|psycopg2" requirements.txt
```

**Checks**:
- ✅ Python syntax is valid
- ✅ All imports resolve correctly
- ✅ Config file loads without errors
- ✅ Database URL format is correct
- ✅ All required packages in requirements.txt

---

### Post-Deployment: Service Health
```bash
# Check service is Ready
gcloud run services describe finance-tracker \
  --region=us-central1 \
  --format='value(status.conditions[0].status)' \
  --project=jinolen

# Get service URL
SERVICE_URL=$(gcloud run services describe finance-tracker \
  --region=us-central1 \
  --format='value(status.url)' \
  --project=jinolen)

# Test URL is accessible
curl -I "$SERVICE_URL"

# Check for critical errors in logs
gcloud run services logs read finance-tracker \
  --limit=50 \
  --filter='severity>=ERROR' \
  --region=us-central1 \
  --project=jinolen
```

**Checks**:
- ✅ Service is in 'Ready' state
- ✅ Service URL responds to requests
- ✅ No critical errors in recent logs
- ✅ Response time is acceptable

---

### Post-Deployment: Functional Testing
```bash
# Test registration page
curl "$SERVICE_URL/auth/register" | grep -q "register" && echo "✓ Registration loads"

# Test login page
curl "$SERVICE_URL/auth/login" | grep -q "login" && echo "✓ Login loads"

# Check security headers
curl -I "$SERVICE_URL" | grep -i "strict-transport-security"
curl -I "$SERVICE_URL" | grep -i "content-security-policy"
```

**Checks**:
- ✅ Registration page loads
- ✅ Login page loads
- ✅ Dashboard accessible after login
- ✅ HTTPS headers present
- ✅ CSP header configured
- ✅ No sensitive data in error pages

---

### Post-Deployment: Database Connectivity
```bash
# Check for database connection messages in logs
gcloud run services logs read finance-tracker \
  --filter='postgresql|database|connection' \
  --limit=50 \
  --region=us-central1 \
  --project=jinolen

# Check for pool errors
gcloud run services logs read finance-tracker \
  --filter='pool|timeout|refused' \
  --limit=50 \
  --region=us-central1 \
  --project=jinolen
```

**Checks**:
- ✅ Successful database connections in logs
- ✅ No connection pool exhaustion errors
- ✅ No timeout errors
- ✅ Data persists across requests

---

### Failure Diagnosis: Error Identification
```bash
# Get latest build ID
BUILD_ID=$(gcloud builds list --project=jinolen --limit=1 --format='value(id)')

# Read Cloud Build logs
gcloud builds log $BUILD_ID --project=jinolen

# Read Cloud Run service logs for errors
gcloud run services logs read finance-tracker \
  --limit=100 \
  --filter='severity>=ERROR' \
  --region=us-central1 \
  --project=jinolen

# Check service status
gcloud run services describe finance-tracker \
  --region=us-central1 \
  --format='value(status)' \
  --project=jinolen
```

---

## Common Issues & Solutions

### Issue 1: "Module not found" in Cloud Build

**Diagnosis**: Docker build fails with import error
```bash
gcloud builds log BUILD_ID | grep -i "error\|module"
```

**Solution**:
```bash
# 1. Add missing package to requirements.txt
# 2. Rebuild and push image
docker buildx build --platform linux/amd64 -t gcr.io/jinolen/finance-tracker:latest --push .
# 3. Retry deployment
```

---

### Issue 2: "Could not connect to server" (Database)

**Diagnosis**: Cloud Run logs show PostgreSQL connection error
```bash
gcloud run services logs read finance-tracker --filter='psycopg2' --project=jinolen
```

**Solution**:
```bash
# 1. Verify instance is running
gcloud sql instances describe finance-db --project=jinolen

# 2. Verify connection name
gcloud sql instances describe finance-db \
  --format='value(connectionName)' --project=jinolen

# 3. Update Cloud Run if needed
gcloud run services update finance-tracker \
  --update-env-vars=CLOUD_SQL_CONNECTION_NAME=jinolen:us-central1:finance-db \
  --region=us-central1 --project=jinolen
```

---

### Issue 3: "Secret not found"

**Diagnosis**: Cloud Run logs show secret access error
```bash
gcloud run services logs read finance-tracker --filter='secret' --project=jinolen
```

**Solution**:
```bash
# 1. Verify secret exists
gcloud secrets list --project=jinolen | grep SECRET_NAME

# 2. Grant service account access
SA="jinolen@appspot.gserviceaccount.com"
gcloud secrets add-iam-policy-binding SECRET_NAME \
  --member="serviceAccount:$SA" \
  --role="roles/secretmanager.secretAccessor" \
  --project=jinolen

# 3. Retry deployment
```

---

### Issue 4: "FLASK_ENV not production"

**Diagnosis**: Security headers missing, debug mode active
```bash
curl -I https://finance-tracker-xxxxx.run.app | grep -i "hsts"
```

**Solution**:
```bash
gcloud run services update finance-tracker \
  --update-env-vars=FLASK_ENV=production \
  --region=us-central1 \
  --project=jinolen
```

---

### Issue 5: "Database schema missing"

**Diagnosis**: "table does not exist" errors in logs
```bash
gcloud run services logs read finance-tracker --filter='table does not exist' --project=jinolen
```

**Solution**:
```bash
# Option A: Verify migrations exist
ls -la migrations/versions/

# Option B: Check if migrations ran
gcloud run services logs read finance-tracker --filter='flask db upgrade' --project=jinolen

# Option C: Manual migration via Cloud SQL Proxy (advanced)
# This requires connecting to Cloud SQL and running migrations manually
```

---

## Rollback Procedure

If deployment fails or causes issues, you can quickly rollback to the previous revision:

```bash
# 1. List recent revisions (most recent first)
gcloud run revisions list --service=finance-tracker \
  --region=us-central1 \
  --project=jinolen

# 2. Get the PREVIOUS_REVISION_ID (second in the list)

# 3. Rollback to it (100% traffic)
gcloud run services update-traffic finance-tracker \
  --to-revisions=PREVIOUS_REVISION_ID=100 \
  --region=us-central1 \
  --project=jinolen

# 4. Verify traffic shifted
gcloud run services describe finance-tracker \
  --region=us-central1 \
  --format='value(status.traffic[*].revisionName)' \
  --project=jinolen
```

**Estimated Time**: < 2 minutes

---

## Full Deployment Workflow

### Step 1: Pre-Deployment Verification
```
/deployment-checklist pre-deployment
```
Wait for GO decision before proceeding.

### Step 2: Deploy Application
Use the gcp-deployment agent to execute the actual deployment.

### Step 3: Post-Deployment Validation
```
/deployment-checklist post-deployment
```
Verify everything is working correctly.

### Step 4: If Issues Arise
```
/deployment-checklist diagnose-failure
```
Get root cause and remediation steps.

---

## Summary

This slash command provides comprehensive deployment verification at every stage:
- **Before deployment**: Catch issues early
- **After deployment**: Confirm success and health
- **On failure**: Diagnose root cause and fix path

Use it for every production deployment to ensure safe, reliable releases.
