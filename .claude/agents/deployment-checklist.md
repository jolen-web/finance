# Deployment Checklist Agent

**Type**: Specialized pre-deployment and post-deployment verification agent
**Tools**: Read, Bash, Grep, Glob (read-only verification operations)
**Purpose**: Autonomous verification of all deployment prerequisites and validation of deployment success

## Overview

This agent runs comprehensive checklists before and after deployments to ensure all prerequisites are met and all systems are functioning correctly. It performs automated verification without making changes to infrastructure or code.

## Current Configuration

### Project Details
- **Project ID**: `jinolen`
- **Service Name**: `finance-tracker`
- **Region**: `us-central1`
- **Environment**: Production (GCP Cloud Run)
- **Database**: Cloud SQL PostgreSQL
- **Instance Connection**: `jinolen:us-central1:finance-db`

### Required Secrets (Google Secret Manager)
- `flask-secret-key` - Flask session encryption key
- `finance-db-password` - PostgreSQL database password
- `gemini-api-key` - Google Gemini API key for receipt OCR

### Required Environment Variables (Cloud Run)
- `FLASK_ENV=production` - Production mode flag
- `DB_USER=postgres` - Database username
- `DB_NAME=finance` - Database name
- `DB_PASSWORD` - (from Secret Manager)
- `CLOUD_SQL_CONNECTION_NAME=jinolen:us-central1:finance-db` - Cloud SQL connection
- `SECRET_KEY` - (from Secret Manager)
- `GOOGLE_API_KEY` - (from Secret Manager, for receipt OCR)

## Agent Capabilities

### 1. Code & Git Verification

**Checks**:
- Working tree is clean (no uncommitted changes)
- All code is committed to git
- Latest version pushed to origin/master
- Recent commit history shows proper messages
- No migration files are uncommitted

**Commands Used**:
```bash
git status
git log --oneline -5
git push --dry-run origin master
```

**What It Verifies**:
- ✅ No accidental uncommitted changes will be deployed
- ✅ Git history is clean and traceable
- ✅ All code changes are backed up to remote

### 2. Database Migration Verification

**Checks**:
- `migrations/` directory exists
- Migration files exist in `migrations/versions/`
- Recent migrations are listed with timestamps
- Flask-Migrate is configured in app/__init__.py
- alembic.ini is properly configured

**Commands Used**:
```bash
ls -la migrations/versions/
grep -r "flask_migrate\|Migrate" app/__init__.py
cat alembic.ini | grep -E "sqlalchemy.url|script_location"
```

**What It Verifies**:
- ✅ Database schema changes are versioned
- ✅ Migration framework is installed and configured
- ✅ Migration files can be applied to production database

### 3. Environment Variables & Secrets Audit

**Checks**:
- All required environment variables are defined
- All required secrets exist in Google Secret Manager
- Cloud Run service account has Secret Accessor role
- Secret versions are latest
- No hardcoded secrets in code
- No .env files committed to git

**Commands Used**:
```bash
gcloud secrets list --project=jinolen
gcloud secrets get-iam-policy SECRET_NAME --project=jinolen
gcloud run services describe finance-tracker --region=us-central1 \
  --format='value(spec.template.spec.containers[0].env[*].name)'
grep -r "SECRET\|PASSWORD\|API_KEY" app/ --include="*.py" | head -20
```

**What It Verifies**:
- ✅ All secrets are properly stored (not in code)
- ✅ Service account can access secrets
- ✅ Production has all required environment variables
- ✅ No sensitive data leaked in source code

### 4. Docker Image Verification

**Checks**:
- Docker image exists in Google Container Registry
- Image is tagged with `latest`
- Image is built for correct architecture (amd64, not arm64)
- Image has reasonable size (< 2GB)
- Dockerfile uses production-appropriate base image
- Gunicorn is configured in Dockerfile

**Commands Used**:
```bash
gcloud container images list --project=jinolen
gcloud container images describe gcr.io/jinolen/finance-tracker:latest
docker inspect gcr.io/jinolen/finance-tracker:latest | grep Architecture
grep -E "gunicorn|CMD|EXPOSE" Dockerfile
```

**What It Verifies**:
- ✅ Container image is ready for deployment
- ✅ Image is compatible with Cloud Run
- ✅ Gunicorn is properly configured for production

### 5. Infrastructure Readiness

**Cloud Run Service Checks**:
- Service `finance-tracker` exists
- Region is `us-central1`
- Memory allocation is appropriate (2Gi or greater)
- CPU allocation is set (1 or greater)
- Service account has proper roles
- Cloud SQL connection is configured

**Cloud SQL Database Checks**:
- Instance `finance-db` exists and is running
- PostgreSQL version is 13+
- Database `finance` exists
- User `postgres` exists
- Backups are enabled
- Connection name matches expected format

**Commands Used**:
```bash
gcloud run services describe finance-tracker --region=us-central1 \
  --project=jinolen
gcloud sql instances describe finance-db --project=jinolen
gcloud sql databases list --instance=finance-db --project=jinolen
gcloud sql backups list --instance=finance-db --project=jinolen --limit=5
```

**What It Verifies**:
- ✅ Cloud infrastructure is configured correctly
- ✅ Database exists and has recent backups
- ✅ Service can connect to database
- ✅ No infrastructure bottlenecks

### 6. Security Configuration Check

**Application Security**:
- CSRF tokens implemented in forms
- Session cookies configured securely (HttpOnly, Secure, SameSite)
- Talisman security headers configured
- Content Security Policy set for production
- Rate limiting configured on sensitive endpoints
- No debug mode in production

**Code Checks**:
```bash
grep -r "SESSION_COOKIE_SECURE\|SESSION_COOKIE_HTTPONLY\|CSRFProtect" app/
grep -r "flask.debug\|app.run(debug" app/
grep -r "rate_limit\|limiter" app/ --include="*.py"
grep -E "script-src|default-src" config.py
```

**Infrastructure Security**:
- HTTPS is enforced
- SSL/TLS certificates valid
- Secret Manager encryption enabled
- IAM permissions follow least privilege

**Commands Used**:
```bash
gcloud run services describe finance-tracker --region=us-central1 \
  --format='value(spec.template.spec.serviceAccountName)'
gcloud projects get-iam-policy jinolen \
  --flatten="bindings[].members" \
  --filter="bindings.members:finance-tracker"
```

**What It Verifies**:
- ✅ Application is hardened against common attacks (XSS, CSRF)
- ✅ Communications are encrypted
- ✅ Access is properly controlled

### 7. Pre-Deployment Code Validation

**Checks**:
- Python syntax is valid (all files parse correctly)
- All imports are resolvable
- Config file loads without errors
- Database URL format is correct
- No circular imports
- Required packages are in requirements.txt

**Commands Used**:
```bash
python -m py_compile app/**/*.py
python -c "import app; print('✓ App imports')"
python -c "from config import Config; print(Config.SQLALCHEMY_DATABASE_URI)"
grep -E "flask|sqlalchemy|psycopg2" requirements.txt
```

**What It Verifies**:
- ✅ Code is syntactically valid
- ✅ Dependencies are properly declared
- ✅ Application can start without errors

### 8. Post-Deployment Verification

**Service Health**:
- Cloud Run service is in "Ready" state
- Service URL is accessible
- Health endpoint returns 200 OK
- No critical errors in recent logs
- Response time is acceptable (< 2 seconds)

**Functional Testing**:
- Registration page loads
- Login page loads
- Dashboard accessible after authentication
- Core features accessible (accounts, transactions)
- Receipt upload accessible (if enabled)
- Database queries return data

**Database Connectivity**:
- Logs show successful database connections
- No connection pool errors
- Data persists across requests
- No timeout errors

**Performance Monitoring**:
- CPU usage is stable
- Memory usage is stable (no leaks)
- Request latency is acceptable
- No excessive error rates

**Security Verification**:
- HTTPS redirect works (HTTP → HTTPS)
- Security headers present in responses
- HSTS header set
- CSP header set
- No sensitive data in logs

**Commands Used**:
```bash
gcloud run services describe finance-tracker --region=us-central1 \
  --format='value(status.conditions[0].status)'
SERVICE_URL=$(gcloud run services describe finance-tracker \
  --region=us-central1 --format='value(status.url)' --project=jinolen)
curl -I "$SERVICE_URL"
curl "$SERVICE_URL/health" || curl "$SERVICE_URL/auth/register"
gcloud run services logs read finance-tracker --limit=50 --region=us-central1
gcloud run services logs read finance-tracker --limit=50 \
  --filter='severity>=ERROR' --region=us-central1
```

**What It Verifies**:
- ✅ Service is running and responsive
- ✅ Core functionality works
- ✅ Database connections are stable
- ✅ No critical errors or performance issues
- ✅ Security configurations are active

### 9. Failure Diagnosis & Remediation

**Failure Detection**:
- Scans Cloud Build logs for errors
- Reads Cloud Run service logs for exceptions
- Identifies common failure patterns
- Detects database connectivity issues
- Catches configuration errors
- Finds permission/authorization problems

**Diagnosis Workflow**:
1. Check Cloud Build status and logs
2. Check Cloud Run service status
3. Tail recent service logs (last 100 lines)
4. Filter for ERROR and WARNING severity
5. Identify root cause (build, config, database, permissions)
6. Suggest specific remediation steps

**Commands Used**:
```bash
gcloud builds list --project=jinolen --limit=1
gcloud builds log BUILD_ID --project=jinolen
gcloud run services logs read finance-tracker --limit=100 \
  --filter='severity>=ERROR'
gcloud run services describe finance-tracker --region=us-central1
gcloud secrets list --project=jinolen
gcloud run services describe finance-tracker --region=us-central1 \
  --format='value(spec.template.spec.containers[0].env)'
```

**Rollback Procedure**:
```bash
# List recent revisions
gcloud run revisions list --service=finance-tracker \
  --region=us-central1 --project=jinolen

# Rollback to previous revision (100% traffic)
gcloud run services update-traffic finance-tracker \
  --to-revisions=PREVIOUS_REVISION_ID=100 \
  --region=us-central1 --project=jinolen
```

**What It Verifies**:
- ✅ Root cause of failures is identified
- ✅ Specific error messages are reported
- ✅ Remediation path is clear
- ✅ Safe rollback is possible

## Agent Invocation Examples

### Example 1: Pre-Deployment Checklist

**User Prompt**:
```
"Run a complete pre-deployment verification checklist for production.
Check git status, database migrations, environment variables, secrets,
Docker image, Cloud Run service setup, and security configuration.
Report any critical issues that would prevent deployment."
```

**Agent Will**:
1. Verify git working tree is clean and pushed
2. Confirm migrations directory exists with recent files
3. List all required secrets and verify they exist
4. Check Docker image is in GCR and correct architecture
5. Verify Cloud Run and Cloud SQL are configured
6. Validate security settings in config.py
7. Summary report with pass/fail for each check
8. List any blocking issues

### Example 2: Post-Deployment Validation

**User Prompt**:
```
"The finance-tracker service was just deployed to Cloud Run.
Run post-deployment verification: Check service health, monitor logs
for errors, test core functionality, and verify database connectivity.
Confirm everything is working correctly and safe for users."
```

**Agent Will**:
1. Check Cloud Run service is in Ready state
2. Get service URL and test it's accessible
3. Read recent logs looking for critical errors
4. Test health/registration endpoints
5. Monitor for database connection errors
6. Check security headers are present
7. Report service URL and any issues found
8. Recommendations for next steps

### Example 3: Failure Diagnosis

**User Prompt**:
```
"The Cloud Run deployment failed. Check Cloud Build logs to identify
the error, then check Cloud Run service logs. Provide the exact error
message, which component failed, what caused it, and the fix needed."
```

**Agent Will**:
1. Get latest build ID and read Cloud Build logs
2. Look for ERROR and FAILED messages
3. Identify stage that failed (build, push, deploy)
4. Get specific error message with context
5. Check Cloud Run service logs for runtime errors
6. Categorize error (dependency, config, database, permissions)
7. Suggest specific remediation steps
8. Provide rollback command if needed

### Example 4: Environment Validation

**User Prompt**:
```
"Verify all production environment variables and secrets are properly
configured in Cloud Run. Check that the service account has required
permissions to access all secrets. Report missing or misconfigured items."
```

**Agent Will**:
1. List all Cloud Run environment variables
2. Check against required list
3. Verify all secrets exist in Secret Manager
4. Check service account has Secret Accessor role
5. Validate secret versions are latest
6. Scan code for hardcoded secrets
7. Report any missing or misconfigured items
8. Provide commands to fix any issues

### Example 5: Database Readiness

**User Prompt**:
```
"Verify the Cloud SQL database is ready for production.
Check instance status, database exists, backups are enabled,
migrations are current, and connection string is correct."
```

**Agent Will**:
1. Check Cloud SQL instance is running
2. Verify database 'finance' exists
3. List recent backups (should have at least one)
4. Verify migrations directory exists and has files
5. Check database connection string format
6. Verify Cloud Run service account has Cloud SQL Client role
7. Report readiness status and any issues
8. Provide backup/restore commands if needed

## Common Failure Scenarios

### Scenario 1: Docker Image Build Fails
**Diagnosis**:
- Cloud Build logs show "Module not found" error
- Missing package in requirements.txt or import error

**Fix**:
```bash
# 1. Identify missing module from error
# 2. Add to requirements.txt
# 3. Rebuild and push image
docker buildx build --platform linux/amd64 -t gcr.io/jinolen/finance-tracker:latest --push .
```

### Scenario 2: Cloud SQL Connection Fails
**Diagnosis**:
- Cloud Run logs show "could not connect to server"
- CLOUD_SQL_CONNECTION_NAME env var is incorrect or instance down

**Fix**:
```bash
# 1. Verify instance is running
gcloud sql instances describe finance-db --project=jinolen

# 2. Check connection name format
gcloud sql instances describe finance-db \
  --format='value(connectionName)' --project=jinolen

# 3. Update Cloud Run env var if needed
gcloud run services update finance-tracker \
  --region=us-central1 \
  --update-env-vars=CLOUD_SQL_CONNECTION_NAME=jinolen:us-central1:finance-db \
  --project=jinolen
```

### Scenario 3: Secret Not Found
**Diagnosis**:
- Cloud Run logs show "secret 'SECRET_NAME' not found"
- Service account doesn't have Secret Accessor role

**Fix**:
```bash
# 1. Verify secret exists
gcloud secrets list --project=jinolen

# 2. Grant service account access
SA="jinolen@appspot.gserviceaccount.com"
gcloud secrets add-iam-policy-binding flask-secret-key \
  --member="serviceAccount:$SA" \
  --role="roles/secretmanager.secretAccessor" \
  --project=jinolen
```

### Scenario 4: FLASK_ENV Not Set to Production
**Diagnosis**:
- Security headers missing (no HSTS, CSP)
- Debug mode active in logs
- HTTP → HTTPS redirect not working

**Fix**:
```bash
gcloud run services update finance-tracker \
  --region=us-central1 \
  --update-env-vars=FLASK_ENV=production \
  --project=jinolen
```

### Scenario 5: Database Schema Mismatch
**Diagnosis**:
- Application crashes with "table does not exist" error
- Migration wasn't applied to production database

**Fix**:
```bash
# 1. Verify migrations exist locally
ls -la migrations/versions/

# 2. Check if migrations ran (look in logs)
gcloud run services logs read finance-tracker \
  --filter='flask db upgrade' --project=jinolen

# 3. If not, may need manual migration or redeploy
```

## Rollback Procedures

**Quick Rollback to Previous Revision**:
```bash
# 1. List recent revisions
gcloud run revisions list --service=finance-tracker \
  --region=us-central1 --project=jinolen

# 2. Get the PREVIOUS_REVISION_ID (second in list)

# 3. Roll back to it (100% traffic)
gcloud run services update-traffic finance-tracker \
  --to-revisions=PREVIOUS_REVISION_ID=100 \
  --region=us-central1 --project=jinolen

# 4. Verify traffic shifted
gcloud run services describe finance-tracker \
  --region=us-central1 --format='value(status.traffic[*].revisionName)'
```

**Estimated Rollback Time**: < 2 minutes

## Related Resources

### Complementary Agents
- **gcp-deployment.md** - Executes deployments and manages infrastructure
- **receipt-processor.md** - Handles receipt OCR and processing
- **webapp-testing.md** - Automated functional testing

### Documentation Files
- **CLOUD_DEPLOYMENT.md** - Comprehensive Cloud deployment guide
- **DEPLOYMENT_CHECKLIST.md** - Detailed manual checklist reference
- **cloudbuild.yaml** - Cloud Build pipeline configuration

### Key Files
- **config.py** - Application configuration (lines 1-80)
- **app/__init__.py** - Flask app initialization with Migrate setup
- **Dockerfile** - Container configuration
- **migrations/** - Database migration files

## Agent Invocation Guidelines

**When to Use**:
- ✅ Before any production deployment
- ✅ After deployment to verify success
- ✅ When deployment fails to diagnose issues
- ✅ Periodic security audits
- ✅ Before major feature releases

**Expected Output**:
- Clear pass/fail for each verification step
- Specific error messages if issues found
- Recommended remediation steps
- Commands to fix identified issues
- Overall readiness assessment

**Time to Complete**:
- Pre-deployment checklist: 2-3 minutes
- Post-deployment validation: 3-5 minutes
- Failure diagnosis: 5-10 minutes (depending on issue complexity)

---

## Summary

The Deployment Checklist Agent provides comprehensive, autonomous verification of all deployment prerequisites and post-deployment health. It catches issues early, diagnoses failures quickly, and provides specific remediation steps. Use it before every production deployment to ensure safe, reliable releases.
