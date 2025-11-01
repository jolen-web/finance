# Deployment Checklist - Setup & Usage

## What Was Created

Two new deployment tools have been created to ensure safe, reliable production deployments:

### 1. Deployment Checklist Agent
**File**: `.claude/agents/deployment-checklist.md`

An autonomous agent that performs comprehensive verification at every stage of deployment:

**Capabilities**:
- Code & Git verification
- Database migration validation
- Environment variables & secrets audit
- Docker image verification
- Cloud infrastructure readiness checks
- Security configuration validation
- Pre-deployment code validation
- Post-deployment health verification
- Failure diagnosis with root cause analysis

**Tools Used**: Read, Bash, Grep, Glob (read-only operations)

### 2. Deployment Checklist Slash Command
**File**: `.claude/commands/deployment-checklist.md`

User-friendly slash command interface for running deployment checklists:

**Available Commands**:
```
/deployment-checklist pre-deployment
/deployment-checklist post-deployment
/deployment-checklist diagnose-failure
```

---

## How to Use

### Before Deploying to Production

```
/deployment-checklist pre-deployment
```

This will verify:
- ✅ All code is committed and pushed
- ✅ Database migrations are present and configured
- ✅ All required secrets exist in Google Secret Manager
- ✅ Docker image is built and pushed to GCR
- ✅ Cloud Run service and Cloud SQL database are configured
- ✅ Security settings are correct for production
- ✅ Application imports and config loads correctly

**Output**: GO or NO-GO decision with specific issues if found

### After Deploying to Production

```
/deployment-checklist post-deployment
```

This will verify:
- ✅ Cloud Run service is in Ready state
- ✅ Service URL is accessible
- ✅ No critical errors in recent logs
- ✅ Registration and login pages load
- ✅ Database connectivity is working
- ✅ Security headers are present
- ✅ Performance is acceptable

**Output**: Deployment status with any issues requiring attention

### If Deployment Fails

```
/deployment-checklist diagnose-failure
```

This will:
- Scan Cloud Build logs for build errors
- Read Cloud Run service logs for runtime errors
- Identify root cause (build, config, database, permissions)
- Suggest specific remediation steps
- Provide rollback command if needed

**Output**: Exact error message, root cause, and fix path

---

## Complete Deployment Workflow

### Step 1: Verify Prerequisites
```
/deployment-checklist pre-deployment
```
↓ Wait for GO decision

### Step 2: Deploy Application
Use gcp-deployment agent or manual deploy command

### Step 3: Validate Deployment
```
/deployment-checklist post-deployment
```
↓ Verify everything is working

### Step 4: Monitor for Issues
If problems arise:
```
/deployment-checklist diagnose-failure
```

---

## Current Infrastructure Configuration

**Project**: `jinolen`
**Service**: `finance-tracker`
**Region**: `us-central1`
**Database**: Cloud SQL PostgreSQL (`finance-db`)

### Required Secrets (Google Secret Manager)
- `flask-secret-key` - Flask session encryption
- `finance-db-password` - PostgreSQL password
- `gemini-api-key` - Receipt OCR API key

### Required Environment Variables (Cloud Run)
- `FLASK_ENV=production`
- `DB_USER=postgres`
- `DB_NAME=finance`
- `DB_PASSWORD` (from Secret Manager)
- `CLOUD_SQL_CONNECTION_NAME=jinolen:us-central1:finance-db`
- `SECRET_KEY` (from Secret Manager)
- `GOOGLE_API_KEY` (from Secret Manager)

---

## Common Issues & Quick Fixes

### Issue: "Module not found" in Docker Build
**Fix**: Add missing package to requirements.txt and rebuild image
```bash
# 1. Add package to requirements.txt
# 2. Rebuild: docker buildx build --platform linux/amd64 -t gcr.io/jinolen/finance-tracker:latest --push .
# 3. Retry deployment
```

### Issue: "Could not connect to server" (Database)
**Fix**: Verify Cloud SQL instance connection
```bash
# Check instance is running
gcloud sql instances describe finance-db --project=jinolen

# Update Cloud Run connection if needed
gcloud run services update finance-tracker \
  --update-env-vars=CLOUD_SQL_CONNECTION_NAME=jinolen:us-central1:finance-db \
  --region=us-central1 --project=jinolen
```

### Issue: "Secret not found"
**Fix**: Grant service account access to secret
```bash
SA="jinolen@appspot.gserviceaccount.com"
gcloud secrets add-iam-policy-binding SECRET_NAME \
  --member="serviceAccount:$SA" \
  --role="roles/secretmanager.secretAccessor" \
  --project=jinolen
```

### Issue: Security Headers Missing
**Fix**: Ensure FLASK_ENV is set to production
```bash
gcloud run services update finance-tracker \
  --update-env-vars=FLASK_ENV=production \
  --region=us-central1 --project=jinolen
```

### Issue: Database Tables Missing
**Fix**: Verify migrations exist and ran
```bash
# Check migrations exist locally
ls -la migrations/versions/

# Check if migrations ran (look in logs)
gcloud run services logs read finance-tracker --filter='flask db upgrade' --project=jinolen
```

---

## Rollback Procedure

If something goes wrong, quickly rollback to the previous revision:

```bash
# 1. List recent revisions
gcloud run revisions list --service=finance-tracker \
  --region=us-central1 --project=jinolen

# 2. Get PREVIOUS_REVISION_ID (second in list)

# 3. Rollback to it
gcloud run services update-traffic finance-tracker \
  --to-revisions=PREVIOUS_REVISION_ID=100 \
  --region=us-central1 --project=jinolen

# 4. Verify traffic shifted
gcloud run services describe finance-tracker \
  --region=us-central1 \
  --format='value(status.traffic[*].revisionName)' \
  --project=jinolen
```

**Estimated Time**: < 2 minutes

---

## Related Resources

### Claude Code Tools
- **gcp-deployment.md** Agent - Executes deployments
- **receipt-processor.md** Agent - Handles OCR/receipt processing
- **webapp-testing.md** Agent - Automated functional testing
- **code-review.md** Agent - Security and code quality review

### Key Files
- **Dockerfile** - Container configuration
- **config.py** - Application configuration (lines 1-80)
- **app/__init__.py** - Flask app initialization with security settings
- **cloudbuild.yaml** - Cloud Build pipeline (if using Cloud Build)

### Documentation
- **CLOUD_DEPLOYMENT.md** - Comprehensive Cloud deployment guide
- **DEPLOYMENT_CHECKLIST.md** - Detailed manual reference (legacy)

---

## Summary

The deployment checklist tools provide:

✅ **Pre-deployment verification** - Catch issues before they reach production
✅ **Post-deployment validation** - Confirm everything is working correctly
✅ **Failure diagnosis** - Identify root causes and fix paths
✅ **Safe rollback** - Quickly revert to previous version if needed
✅ **Comprehensive documentation** - All verification steps documented

**Use it for every production deployment** to ensure safe, reliable releases.

---

## Git Commit

The deployment checklist tools were added in commit:
```
731cbcd feat: Add deployment checklist agent and slash command
```

Files changed:
- `.claude/agents/deployment-checklist.md` (New)
- `.claude/commands/deployment-checklist.md` (New)
