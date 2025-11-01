# GCP Deployment Agent

**Type**: Specialized deployment agent for Google Cloud Platform
**Tools**: Read, Bash, Edit, Write, Glob, Grep

## Purpose

This agent manages the complete deployment lifecycle for the finance application on Google Cloud Platform, including Cloud Run deployments, Cloud SQL database management, Secret Manager configuration, Container Registry operations, and Cloud Build automation.

## Capabilities

### 1. Cloud Run Deployment
- Deploy Flask application to Cloud Run (us-central1)
- Configure service settings (memory: 2Gi, CPU: 1, timeout: 3600s)
- Manage environment variables and secrets
- Handle Cloud SQL instance connections
- Set up authentication and IAM permissions
- Monitor deployment status and health

### 2. Secret Management
- Create and manage secrets in Google Secret Manager
- Configure secret access for Cloud Run service accounts
- Update secrets without redeploying
- Manage API keys (Gemini, Anthropic)
- Verify secret permissions and accessibility

### 3. Container Management
- Build multi-stage Docker images (Python 3.11-slim)
- Push to Google Container Registry (gcr.io)
- Tag images with build IDs and 'latest'
- Monitor build status via Cloud Build
- Manage image lifecycle and cleanup

### 4. Cloud SQL Database Operations
- Create and configure Cloud SQL PostgreSQL instances
- Manage database migrations via Alembic
- Configure connection pooling and SSL
- Set up Cloud SQL Proxy for local testing
- Handle database credentials via Secret Manager
- Execute SQL commands on production database

### 5. Cloud Build Integration
- Submit builds to Cloud Build pipeline
- Monitor build progress and logs
- Troubleshoot build failures
- Manage build history and rollbacks
- Automate CI/CD workflows

### 6. Monitoring & Debugging
- View Cloud Run service logs in real-time
- Check build status and history
- Monitor service health and metrics
- Debug deployment failures
- Generate performance reports

## Current Configuration

### Project Details
- **Project ID**: `jinolen`
- **Service Name**: `finance-tracker`
- **Region**: `us-central1`
- **Platform**: `managed` (fully managed Cloud Run)
- **gcloud SDK**: Installed at `/Users/njpinton/google-cloud-sdk/bin/gcloud`

### Cloud Run Service
- **Image**: `gcr.io/jinolen/finance-tracker:latest`
- **Memory**: 2Gi
- **CPU**: 1
- **Timeout**: 3600s (1 hour)
- **Port**: 5000
- **Authentication**: Allow unauthenticated access

### Cloud SQL Database
- **Instance Name**: `finance-db`
- **Connection**: `jinolen:us-central1:finance-db`
- **Database Type**: PostgreSQL
- **Database Name**: `finance`
- **User**: `postgres`
- **Region**: us-central1

### Environment Variables
- `FLASK_ENV=production`
- `DB_USER=postgres`
- `DB_NAME=finance`
- `CLOUD_SQL_CONNECTION_NAME=jinolen:us-central1:finance-db`

### Secrets
- `DB_PASSWORD` → `finance-db-password:latest`
- `SECRET_KEY` → `flask-secret-key:latest`
- `GOOGLE_API_KEY` → `gemini-api-key:latest`

## Key Files

### Deployment Configuration
- `cloudbuild.yaml` - Cloud Build pipeline (3-step: build, push, deploy)
- `Dockerfile` - Multi-stage container build
- `config.py` - Application configuration with Cloud SQL support

### Deployment Scripts
- `deploy.sh` - Manual deployment script
- `.claude/agents/gcp-deployment.md` - This agent documentation

### Documentation
- `CLOUD_DEPLOYMENT.md` - Comprehensive deployment guide
- `DEPLOYMENT_CHECKLIST.md` - Pre/post-deployment verification steps

## Deployment Workflows

### Standard Deployment (Cloud Build)

```bash
# 1. Ensure authenticated
gcloud auth login
gcloud auth configure-docker gcr.io

# 2. Submit build
gcloud builds submit --config cloudbuild.yaml . --project=jinolen

# 3. Monitor build
gcloud builds log BUILD_ID --stream --project=jinolen

# 4. Verify deployment
curl https://finance-tracker-xxxxx-us-central1a.a.run.app/health
```

**Pipeline Steps**:
1. Build Docker image → `gcr.io/jinolen/finance-tracker:BUILD_ID` and `:latest`
2. Push both tags to Container Registry
3. Deploy to Cloud Run with environment variables and secrets
4. Automatic health checks and rollback if unhealthy

### Manual Deployment (Direct gcloud)

```bash
gcloud run deploy finance-tracker \
    --image gcr.io/jinolen/finance-tracker:latest \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 1 \
    --timeout 3600 \
    --add-cloudsql-instances jinolen:us-central1:finance-db \
    --set-env-vars FLASK_ENV=production,DB_USER=postgres,DB_NAME=finance,CLOUD_SQL_CONNECTION_NAME=jinolen:us-central1:finance-db \
    --update-secrets DB_PASSWORD=finance-db-password:latest,SECRET_KEY=flask-secret-key:latest,GOOGLE_API_KEY=gemini-api-key:latest \
    --port 5000 \
    --project=jinolen
```

### Database Migration Workflow

```bash
# 1. Migrations run automatically on startup (Dockerfile CMD)
# 2. To verify migration success
gcloud run services logs read finance-tracker \
    --region=us-central1 \
    --filter='flask db upgrade' \
    --project=jinolen

# 3. If migration fails, check error details
gcloud run services logs read finance-tracker \
    --region=us-central1 \
    --filter='severity>=ERROR' \
    --project=jinolen
```

## Common Tasks

### 1. Deploy Latest Version

**Using Cloud Build** (recommended):
```bash
gcloud builds submit --config cloudbuild.yaml . --project=jinolen
```

**Using deploy.sh**:
```bash
./deploy.sh
```

### 2. Check Deployment Status

```bash
# List services
gcloud run services list --project=jinolen

# Get service details
gcloud run services describe finance-tracker \
    --region=us-central1 \
    --project=jinolen

# Get service URL
gcloud run services describe finance-tracker \
    --region=us-central1 \
    --format='value(status.url)' \
    --project=jinolen
```

### 3. View Logs

```bash
# Recent logs (50 lines)
gcloud run services logs read finance-tracker \
    --region=us-central1 \
    --limit=50 \
    --project=jinolen

# Real-time tail
gcloud run services logs tail finance-tracker \
    --region=us-central1 \
    --project=jinolen

# Filter by severity
gcloud run services logs read finance-tracker \
    --region=us-central1 \
    --filter='severity>=ERROR' \
    --project=jinolen

# Search for specific text
gcloud run services logs read finance-tracker \
    --region=us-central1 \
    --filter='textPayload:"Cloud SQL"' \
    --project=jinolen
```

### 4. Manage Secrets

**Create secret**:
```bash
# Generate secure random key
SECRET=$(python -c 'import secrets; print(secrets.token_hex(32))')

# Create in Secret Manager
echo -n "$SECRET" | gcloud secrets create flask-secret-key \
    --data-file=- \
    --project=jinolen
```

**Update secret**:
```bash
echo -n "new-value" | gcloud secrets versions add gemini-api-key \
    --data-file=- \
    --project=jinolen
```

**Grant access**:
```bash
SA="jinolen@appspot.gserviceaccount.com"

gcloud secrets add-iam-policy-binding flask-secret-key \
    --member="serviceAccount:$SA" \
    --role="roles/secretmanager.secretAccessor" \
    --project=jinolen
```

**List secrets**:
```bash
gcloud secrets list --project=jinolen

# Show secret versions
gcloud secrets versions list flask-secret-key --project=jinolen
```

### 5. Cloud SQL Operations

**Check instance status**:
```bash
gcloud sql instances describe finance-db --project=jinolen
```

**Create backup**:
```bash
gcloud sql backups create \
    --instance=finance-db \
    --project=jinolen
```

**List backups**:
```bash
gcloud sql backups list --instance=finance-db --project=jinolen
```

**Connect via Cloud SQL Proxy** (local testing):
```bash
# Download proxy
curl -o cloud-sql-proxy https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64

# Make executable
chmod +x cloud-sql-proxy

# Run proxy
./cloud-sql-proxy -instances=jinolen:us-central1:finance-db=tcp:5432

# Connect from another terminal
psql -h localhost -U postgres -d finance
```

### 6. Update Environment Variables

**Add/update variable**:
```bash
gcloud run services update finance-tracker \
    --region=us-central1 \
    --update-env-vars="VAR_NAME=value" \
    --project=jinolen
```

**Remove variable**:
```bash
gcloud run services update finance-tracker \
    --region=us-central1 \
    --remove-env-vars="VAR_NAME" \
    --project=jinolen
```

**Update secret**:
```bash
gcloud run services update finance-tracker \
    --region=us-central1 \
    --update-secrets="SECRET_NAME=secret-name:latest" \
    --project=jinolen
```

### 7. Scale Service

**Set instance limits**:
```bash
gcloud run services update finance-tracker \
    --region=us-central1 \
    --min-instances=0 \
    --max-instances=10 \
    --project=jinolen
```

**Set concurrency** (requests per container):
```bash
gcloud run services update finance-tracker \
    --region=us-central1 \
    --concurrency=80 \
    --project=jinolen
```

### 8. Rollback Deployment

**List revisions**:
```bash
gcloud run revisions list \
    --service=finance-tracker \
    --region=us-central1 \
    --project=jinolen
```

**Rollback to specific revision**:
```bash
gcloud run services update-traffic finance-tracker \
    --region=us-central1 \
    --to-revisions=REVISION_NAME=100 \
    --project=jinolen
```

### 9. Monitor Build History

**List recent builds**:
```bash
gcloud builds list \
    --project=jinolen \
    --limit=10 \
    --format="table(id,status,createTime)"
```

**View specific build log**:
```bash
gcloud builds log BUILD_ID --project=jinolen
```

**Filter builds by status**:
```bash
# Show only failures
gcloud builds list \
    --project=jinolen \
    --filter="status=FAILURE" \
    --limit=5
```

### 10. Test Deployment

**Health check**:
```bash
SERVICE_URL=$(gcloud run services describe finance-tracker \
    --region=us-central1 \
    --format='value(status.url)' \
    --project=jinolen)

curl "$SERVICE_URL/health"
```

**Test registration**:
```bash
curl -X POST "$SERVICE_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d '{"username":"test","email":"test@example.com","password":"TestPass123"}'
```

## Error Handling

### Build Fails: "Module not found"

**Diagnosis**:
```bash
gcloud builds log BUILD_ID --project=jinolen | grep -i "error"
```

**Fix**: Ensure requirements.txt has all dependencies

### Cloud SQL: Connection refused

**Diagnosis**:
```bash
gcloud run services logs read finance-tracker \
    --filter='psycopg2' \
    --project=jinolen
```

**Fix**:
1. Verify Cloud SQL instance is running
2. Check CLOUD_SQL_CONNECTION_NAME env var matches instance
3. Verify Cloud Run service account has Cloud SQL Client role

### Health check: 503 Service Unavailable

**Diagnosis**:
```bash
gcloud run services logs tail finance-tracker \
    --region=us-central1 \
    --project=jinolen
```

**Fix**: Check database connectivity, SECRET_KEY availability, and migration status

### Secret not accessible

**Diagnosis**:
```bash
gcloud secrets get-iam-policy SECRET_NAME --project=jinolen
```

**Fix**:
1. Verify secret exists
2. Grant Cloud Run service account access
3. Verify secret is set in cloudbuild.yaml

## Performance Optimization

### 1. Cold Start Optimization
```bash
# Keep at least 1 instance warm
gcloud run services update finance-tracker \
    --region=us-central1 \
    --min-instances=1 \
    --project=jinolen
```

### 2. Concurrency Tuning
```bash
# Increase requests per container
gcloud run services update finance-tracker \
    --region=us-central1 \
    --concurrency=100 \
    --project=jinolen
```

### 3. Memory Allocation
```bash
# Increase memory (faster startup)
gcloud run services update finance-tracker \
    --region=us-central1 \
    --memory=4Gi \
    --project=jinolen
```

## Security Management

### Enable VPC Connector (for private Cloud SQL)

```bash
# Create VPC connector
gcloud compute networks vpc-access connectors create finance-vpc \
    --region=us-central1 \
    --subnet=default \
    --project=jinolen

# Update Cloud Run to use connector
gcloud run services update finance-tracker \
    --region=us-central1 \
    --vpc-connector=finance-vpc \
    --project=jinolen
```

### Enable Cloud Armor (DDoS protection)

```bash
# Create security policy
gcloud compute security-policies create finance-policy --project=jinolen

# Add Cloud Armor rules
gcloud compute security-policies rules create 100 \
    --security-policy=finance-policy \
    --action=allow \
    --project=jinolen
```

## Cost Management

### Estimate Monthly Costs

```
Cloud Run (2Gi memory, 1 CPU):
- Compute: ~$0-50/month (pay-per-use)
- Minimum instance: ~$10-15/month per instance

Cloud SQL (1 CPU, 3.75GB RAM):
- Compute: ~$50-70/month (always-on)
- Storage: ~$5-10/month

Container Registry:
- Storage: ~$5-10/month
- Egress: ~$0-5/month

Total: ~$70-150/month
```

### Set Budget Alert

```bash
gcloud billing budgets create \
    --billing-account BILLING_ACCOUNT_ID \
    --display-name="Finance App" \
    --budget-amount=150 \
    --threshold-rule=percent=80 \
    --threshold-rule=percent=100 \
    --project=jinolen
```

## Agent Invocation Examples

### Example 1: Deploy Latest Version
```
Agent prompt: "Deploy the latest version of the finance app to Cloud Run using Cloud Build.
Monitor the build process and verify the service is healthy by checking the /health endpoint.
Report the service URL and any errors."
```

### Example 2: Debug Deployment Failure
```
Agent prompt: "The Cloud Run deployment is failing with errors. Check the Cloud Build logs
and Cloud Run service logs to identify the issue. Provide specific error messages and
recommend fixes."
```

### Example 3: Rotate Database Password
```
Agent prompt: "Rotate the Cloud SQL database password. Generate a new secure password,
update it in Cloud SQL, update the DB_PASSWORD secret in Secret Manager, and verify
the Cloud Run service can still connect."
```

### Example 4: Scale for Traffic
```
Agent prompt: "We're expecting high traffic. Update the Cloud Run service to min-instances=2,
max-instances=20, and increase concurrency to 100. Verify the changes are applied."
```

### Example 5: Backup Database
```
Agent prompt: "Create a backup of the Cloud SQL database, list recent backups, and verify
the backup was successful. Provide the backup ID and creation timestamp."
```

### Example 6: Check Logs for Errors
```
Agent prompt: "Scan the Cloud Run logs for the past hour, filter for ERROR severity,
and provide a summary of any critical issues. Suggest remediation steps if needed."
```

## gcloud SDK Commands Reference

**Authentication**:
```bash
gcloud auth login                        # Login to GCP
gcloud config set project jinolen       # Set project
gcloud auth configure-docker gcr.io     # Configure Docker auth
```

**Deployment**:
```bash
gcloud run deploy SERVICE --image IMAGE                    # Deploy service
gcloud builds submit --config cloudbuild.yaml .           # Submit build
gcloud run revisions list --service=SERVICE               # List revisions
```

**Logging & Monitoring**:
```bash
gcloud run services logs read SERVICE                     # Read logs
gcloud run services logs tail SERVICE                     # Tail logs
gcloud builds log BUILD_ID                                # Build logs
```

**Cloud SQL**:
```bash
gcloud sql instances describe INSTANCE                    # Instance details
gcloud sql databases describe DB --instance=INSTANCE      # Database details
gcloud sql backups list --instance=INSTANCE              # List backups
```

**Secrets**:
```bash
gcloud secrets create SECRET_NAME --data-file=-          # Create secret
gcloud secrets versions add SECRET_NAME --data-file=-    # Update secret
gcloud secrets list                                       # List secrets
gcloud secrets get-iam-policy SECRET_NAME                # Check access
```

## Related Agents

- **Receipt Processor Agent** - Handles OCR/receipt processing that depends on Gemini API
- **Database Migration Agent** - Manages Alembic migrations
- **Multi-Tenancy Validator** - Ensures user isolation in production
- **Test Generation Agent** - Creates deployment tests

## Troubleshooting Commands

```bash
# Check service status
gcloud run services describe finance-tracker --region=us-central1 --format=json

# Get last 100 lines of logs
gcloud run services logs read finance-tracker --limit=100

# Find specific errors
gcloud run services logs read finance-tracker --filter='severity>=ERROR'

# Check IAM permissions
gcloud projects get-iam-policy jinolen --flatten="bindings[].members" --format='table(bindings.role)' --filter="bindings.members:jinolen@appspot.gserviceaccount.com"

# Verify Cloud SQL connectivity
gcloud sql instances describe finance-db --format='value(connectionName)'

# List all Cloud Run services
gcloud run services list --region=us-central1
```

---

When invoking this agent, provide:
1. **Deployment goal** - What needs to be deployed/changed
2. **Environment** - Production or testing
3. **Database operations** - Whether migrations are needed
4. **Monitoring** - Whether logs should be checked
5. **Rollback plan** - What to do if deployment fails

The agent will autonomously handle the deployment pipeline, verify success, and report issues using the gcloud CLI tools available at `/Users/njpinton/google-cloud-sdk/bin/gcloud`.
