# PHASE 0 INFRASTRUCTURE REQUIREMENTS

**Project**: Credit Card Deals Service Integration
**Phase**: 0 - Pre-Development Setup
**Timeline**: November 9-15, 2025
**Owner**: DevOps/Infrastructure Lead

---

## GCP SERVICES & QUOTAS REQUIRED

### Cloud SQL
```
Service:          Cloud SQL for PostgreSQL
Version:          PostgreSQL 15.14
Tier:             Production (High Availability)
Instances:        3
  - finance-deals-prod    (production)
  - finance-deals-staging (staging)
  - finance-deals-dev     (development)

Specs per Instance:
  - Machine Type:   db-g1-small (or larger for prod)
  - Storage:        100GB SSD
  - Backups:        Daily (7-day retention)
  - HA:             Enabled for prod/staging
  - SSL/TLS:        Required
  - Private IP:     Yes (if using VPC)

Estimated Cost: $150-200/month
```

### Cloud Run
```
Service:          Cloud Run
Services:         2
  - finance-deals-staging
  - finance-deals-prod

Specs per Service:
  - Memory:        2Gi
  - CPU:           1 vCPU
  - Timeout:       300 seconds
  - Auto-scaling:  Min 1, Max 10
  - Concurrency:   80
  - Environment:   Production

Estimated Cost: $50-100/month
```

### Cloud Storage
```
Buckets:          2
  - finance-deals-backups    (database backups, private)
  - finance-deals-assets     (static files, CDN-enabled)

Configuration:
  - Versioning:    Enabled for backups
  - Lifecycle:     Delete after 30 days (auto-cleanup)
  - Access:        Private with service account access
  - Region:        us-central1 (multi-regional for redundancy)

Estimated Cost: $10-20/month
```

### Secret Manager
```
Service:          Google Secret Manager
Secrets:          5-10
  - finance-deals-db-password
  - flask-secret-key
  - gemini-api-key
  - plaid-api-key-sandbox
  - plaid-api-key-prod (when available)
  - website-scraper-headers
  - ...others as needed

Configuration:
  - Versions:      Keep last 3 versions
  - Rotation:      Manual initially, automated later
  - Access:        Cloud Run service account only
  - Audit:         All access logged

Estimated Cost: Minimal (~$6/month)
```

### Cloud Build
```
Service:          Google Cloud Build
Triggers:         3
  1. PR Validation (run tests on every PR)
  2. Staging Deployment (deploy on merge to develop)
  3. Production Deploy (manual trigger)

Configuration:
  - Build Timeout:  1200 seconds (20 minutes)
  - Build Cache:    Enabled
  - Logging:        Cloud Logging
  - Notification:   Slack/Email

Estimated Cost: Free tier includes 120 build-minutes/day
```

### Cloud Logging & Monitoring
```
Service:          Cloud Logging
Retention:        30 days
Log Sinks:        Cloud Storage (archival)

Service:          Cloud Monitoring
Dashboards:       5
  - App Performance
  - Database Health
  - API Usage
  - Infrastructure
  - Business Metrics

Alerts:           4+
  - High error rate
  - High latency
  - Database issues
  - API failures

Estimated Cost: Free tier sufficient for Phase 0
```

---

## API KEYS & CREDENTIALS REQUIRED

### Plaid API
```
Required For:    Payment integration (for deals eligibility checking)
Sandbox Keys:    Needed immediately (for testing)
Production Keys: Apply on Day 1, 1-2 week approval
Cost:            Free tier available

What to Request:
  - Client ID
  - Secret (keep secure!)
  - Public Key (for frontend)
```

### Google Gemini API (Already Have)
```
Purpose:         Receipt OCR, transaction categorization
Status:          Already configured
Key:             In Secret Manager
Cost:            Pay-per-use (~$0.005-0.02 per request)
```

### Optional: Third-Party Services
```
Error Tracking:   Sentry or Cloud Error Reporting
  - Sentry Free: $0
  - Cloud Error Reporting: Free

Monitoring:       Datadog or Cloud Monitoring
  - Cloud Monitoring: Free tier sufficient

Logging:          ELK Stack or Cloud Logging
  - Cloud Logging: Free tier sufficient
```

---

## INFRASTRUCTURE ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────────┐
│                    INTERNET / USERS                         │
└────────────────────────────┬────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   Cloud Run     │
                    │ finance-deals   │ (2-10 instances)
                    │    (Port 5000)  │
                    └────────┬────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
         ┌──────▼────┐  ┌───▼────┐  ┌────▼──────┐
         │   Cloud   │  │ Cloud  │  │  Cloud    │
         │    SQL    │  │Storage │  │  Logging  │
         │ (Private  │  │(Backup)│  │ (Logs)    │
         │   IP)     │  │        │  │           │
         └───────────┘  └────────┘  └─────┬─────┘
                                           │
                              ┌────────────▼────────────┐
                              │ Cloud Monitoring Alerts │
                              │  (Slack/Email)          │
                              └─────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    SECRET MANAGER                           │
│  - DB Passwords                                             │
│  - API Keys (Gemini, Plaid)                                 │
│  - Signing Keys                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    CLOUD BUILD (CI/CD)                      │
│  - Git Trigger → Tests → Build → Push → Deploy              │
└─────────────────────────────────────────────────────────────┘
```

---

## NETWORK CONFIGURATION

### IP Addressing
```
Development:
  - Cloud Run: Public IP (testing)
  - Cloud SQL: Public IP (for local testing via Cloud SQL proxy)

Staging:
  - Cloud Run: Public IP (testing)
  - Cloud SQL: Private IP (within VPC)

Production:
  - Cloud Run: Public IP (user-facing)
  - Cloud SQL: Private IP (Cloud SQL sidecar)
  - VPC Connector: Required for Cloud Run → Cloud SQL
```

### Security Groups / Firewall Rules
```
Cloud SQL:
  - Allow: Cloud Run service account
  - Allow: Development machine IP (for local testing, temporary)
  - Deny: Everything else

Cloud Run:
  - Allow: HTTPS from any source (public)
  - Deny: SSH (no SSH access to serverless)

Cloud Storage:
  - Bucket versioning: Enabled for disaster recovery
  - Public access: Disabled
```

---

## BACKUP & DISASTER RECOVERY

### Database Backups
```
Schedule:          Daily automated backups
Retention:         7 days
Location:          Google Cloud Storage (geo-redundant)
RPO (Recovery Point Objective): < 24 hours
RTO (Recovery Time Objective):   < 4 hours

Backup Verification:
  - Test restore monthly
  - Document restore procedure
  - Time restore procedure
```

### Application Deployment Backups
```
Docker Images:     Tagged and stored in Container Registry
  - Latest
  - By commit SHA
  - By release version

Rollback:          Can revert to any previous image in seconds
```

---

## QUOTAS & LIMITS

### Cloud SQL Quotas
```
Max Databases per Instance:    Unlimited (recommended: < 100)
Max Connections:              50 (default, can increase)
Storage:                      Sufficient (100GB allocated)
Backup Storage:               Sufficient (auto-managed)
```

### Cloud Run Quotas
```
Max Concurrent Requests:      80 per instance
Max Instances:                10 (configurable)
Max Memory per Instance:       2Gi
Max Execution Time:            3600 seconds (needed, set to 300s)
Request Size:                  32MB
```

### Cloud Build Quotas
```
Free Build-Minutes:            120/day (sufficient for Phase 0)
Build Timeout:                 1200 seconds (20 min)
Concurrent Builds:             15 (sufficient)
```

### Networking Quotas
```
VPC Connectors:               10 per region (need 1)
Static IPs:                   Depends on tier (need 0-1)
Cloud NAT:                    Depends on tier (not needed Phase 0)
```

---

## COST ESTIMATION

### Monthly Cost Breakdown

| Service | Estimation | Notes |
|---------|-----------|-------|
| Cloud SQL | $150-200 | db-g1-small × 3 instances |
| Cloud Run | $50-100 | 1-10 instances, 2Gi memory |
| Cloud Storage | $10-20 | Backups + assets |
| Secret Manager | $5-10 | Nominal |
| Cloud Logging | $0 | Free tier sufficient |
| Cloud Monitoring | $0 | Free tier sufficient |
| Cloud Build | $0 | Free tier (120 min/day) |
| Gemini API | $20-50 | Pay-per-use (~0.005 per call) |
| **TOTAL** | **$235-380** | Per month |

### Cost Optimization
```
Phase 0: Use smaller instance types (db-g1-small)
Phase 1: Scale up as needed
Phase 2+: Consider committed discounts

Free Options:
  - Cloud Logging (30-day retention)
  - Cloud Monitoring (free tier)
  - Cloud Build (120 build-minutes/day)
```

---

## DEPLOYMENT ENVIRONMENTS

### Development (Local)
```
Database:        SQLite or local PostgreSQL (docker-compose)
Cloud Services:  Not used (all local)
Secrets:         .env file (local development)
Testing:         Full test suite
Deployment:      Docker Compose locally
Cost:            $0
```

### Development (Cloud)
```
Database:        Cloud SQL (finance-deals-dev)
Cloud Services:  Cloud Run (finance-deals-staging)
Secrets:         Secret Manager
Testing:         Automated via Cloud Build
Deployment:      Cloud Build trigger
Cost:            Included in staging quota
```

### Staging
```
Database:        Cloud SQL HA (finance-deals-staging)
Cloud Services:  Cloud Run (finance-deals-staging)
Secrets:         Secret Manager
Testing:         Integration tests, smoke tests
Deployment:      Automated on merge to develop
Cost:            ~$100-150/month
```

### Production
```
Database:        Cloud SQL HA with backups (finance-deals-prod)
Cloud Services:  Cloud Run (finance-deals-prod, auto-scaling 1-10)
Secrets:         Secret Manager (with rotation)
Testing:         Canary deployment, monitoring
Deployment:      Manual (with approval) or automated (with gates)
Cost:            ~$150-200/month
```

---

## PERFORMANCE TARGETS

### Database Performance
```
Connection Time:               < 100ms
Query Time (average):          < 10ms
Query Time (95th percentile):  < 100ms
Backup Time (per 1GB):         5-10 minutes
Restore Time (per 1GB):        5-10 minutes
```

### Application Performance
```
API Response Time (p50):       < 100ms
API Response Time (p95):       < 500ms
API Response Time (p99):       < 1000ms
Error Rate:                    < 1%
Availability:                  > 99.5%
```

### Cloud Run Performance
```
Cold Start Time:               < 5 seconds
Warm Start Time:               < 100ms
Memory Usage:                  < 1Gi (out of 2Gi allocated)
CPU Usage:                     < 50% average
```

---

## COMPLIANCE & SECURITY

### Data Protection
```
Encryption at Rest:    Enabled (Google-managed keys)
Encryption in Transit: TLS 1.2+ (enforced)
PII/Card Data:         Not stored (Plaid tokenization)
Audit Logging:         All access logged to Cloud Audit Logs
Compliance:            SOC 2 compliant (via Google Cloud)
```

### Access Control
```
Principle of Least Privilege: Enforced via IAM roles
Service Accounts:             One per service component
API Keys:                     In Secret Manager, rotated
SSH Access:                   Disabled (Cloud Run is serverless)
```

---

## TROUBLESHOOTING RESOURCES

### Common Issues & Solutions

**Cloud SQL Connection Timeout**
```
Cause: Network/firewall issue
Solution: Check security groups, verify IP whitelisting
```

**Cloud Run Deployment Fails**
```
Cause: Secrets not accessible, out of memory
Solution: Check service account permissions, increase memory
```

**High Database CPU**
```
Cause: Inefficient queries, too many connections
Solution: Check slow queries, implement connection pooling
```

---

## NEXT STEPS (DAY 1 EXECUTION)

1. **Tech Lead**: Request GCP quota increase (if needed)
2. **DevOps Lead**: Start GCP Project Configuration (Task 2.1.1)
3. **Security Lead**: Start Security Review (Task 2.8.1)
4. **Backend Lead**: Prepare Docker Compose (Task 2.7.1)
5. **All**: Verify GCP access granted

---

**Document Status**: Ready for Phase 0 Execution
**Created**: 2025-11-09
**Last Updated**: 2025-11-09
**Owner**: DevOps/Infrastructure Lead
