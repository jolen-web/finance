# Credit Card Deals Service - Supervision Agent Integration Guide

**Document Purpose**: Complete reference for how the autonomous supervision agent works and integrates with your team workflow.

**Status**: ✅ Ready for Deployment
**Created**: 2025-11-09
**Next Review**: Weekly (Fridays)

---

## 📋 What is the Supervision Agent?

The **Autonomous Project Supervision Agent** is a Python-based system that:

1. **Tracks Project Progress** - Monitors all 8 phases from pre-development to production
2. **Enforces Quality Gates** - Verifies exit criteria before phase advancement
3. **Manages Risks** - Identifies integration risks and isolation violations
4. **Automates Checks** - Runs tests, coverage analysis, and security verification
5. **Generates Reports** - Weekly status updates and decision logs
6. **Escalates Issues** - Alerts team when blockers arise or rollback criteria met

### Why This Matters for Your Project

Your team will develop the **deals service in parallel with the main product** without any integration risk. The supervisor agent ensures:

- ✅ **Zero downtime** - Main product never impacted
- ✅ **Independent deployment** - Deals service can deploy without main product
- ✅ **Easy rollback** - Can disable deals instantly if issues arise
- ✅ **Continuous verification** - All isolation principles maintained

---

## 🎯 Agent Architecture

### Three Core Components

#### 1. **Supervisor Script** (`scripts/deals_supervisor.py`)
The CLI interface and core logic:
- Tracks project state (`.deals_project_state.json`)
- Logs all decisions (`.deals_decision_log.json`)
- Runs quality checks and verifications
- Generates reports and alerts

#### 2. **Supervision Document** (`DEALS_PROJECT_SUPERVISOR.md`)
The master plan containing:
- 8 complete phases with tasks and exit criteria
- Website scraper implementation details (6 sources)
- Testing strategy with coverage requirements
- Risk management matrix
- Decision escalation tree
- Success criteria

#### 3. **Quick Start Guide** (`DEALS_PROJECT_QUICK_START.md`)
Team-friendly reference with:
- Phase workflows
- Daily tasks and commands
- Key metrics to track
- Escalation procedures
- Success definitions

---

## 🚀 Quick Start (5 minutes)

### 1. View Current Status
```bash
python scripts/deals_supervisor.py dashboard
```
**Output**: Current phase, timeline, and metrics

### 2. Verify Phase Requirements
```bash
python scripts/deals_supervisor.py verify-phase
```
**Output**: Checklist of tasks for current phase

### 3. Check Service Isolation
```bash
python scripts/deals_supervisor.py check-isolation
```
**Output**: ✓/✗ for isolation verification

### 4. Generate Weekly Report
```bash
python scripts/deals_supervisor.py weekly-report
```
**Output**: Weekly status report template

---

## 📊 How the Agent Supervises Your Project

### Phase 0: PRE-DEVELOPMENT (Week 1)

**Agent Role**: Infrastructure verification
- Verify Cloud SQL instance created
- Verify Secret Manager secrets configured
- Verify Cloud Build triggers set up
- Verify Git feature branch exists

**Team Tasks**:
```
☐ Create finance-deals-db Cloud SQL instance
☐ Create credit-card-deals-api-key secret
☐ Create deals-cache-credentials secret
☐ Set up cloudbuild-deals.yaml trigger
☐ Create feature/credit-card-deals branch
```

**Agent Verification**:
```bash
python scripts/deals_supervisor.py verify-phase
```

**Phase Complete When**: ✅ All infrastructure ready

---

### Phase 1: FOUNDATION (Week 1-2)

**Agent Role**: Code quality and isolation enforcement
- Run unit tests (target: 90%+ coverage)
- Check main product integration layer
- Verify error handling and timeouts
- Ensure deals service builds independently

**Team Tasks**:
```
☐ Create services/deals/ scaffold
☐ Implement deals models and services
☐ Create deals_client.py integration layer
☐ Write unit tests (90%+ coverage)
☐ Verify Docker builds successfully
```

**Agent Verification**:
```bash
python scripts/deals_supervisor.py test-coverage
python scripts/deals_supervisor.py check-isolation
```

**Phase Complete When**: ✅ Tests > 90%, isolation verified, Docker builds

---

### Phase 2: SCRAPER IMPLEMENTATION (Week 2-3)

**Agent Role**: Scraper health monitoring
- Track 6 website scrapers (Chase, Amex, Capital One, Discover, Bankrate, Credit Karma)
- Verify data extraction
- Monitor success rate (target: >90%)
- Check error handling

**Team Tasks**:
```
☐ Implement chase_scraper.py
☐ Implement amex_scraper.py
☐ Implement capital_one_scraper.py
☐ Implement discover_scraper.py
☐ Implement bankrate_scraper.py
☐ Implement credit_karma_scraper.py
☐ Implement proxy_manager.py (rotation)
☐ Implement headers_rotator.py
☐ Write scraper tests (90%+ coverage)
```

**Agent Verification**:
```bash
python scripts/deals_supervisor.py scraper-health
python scripts/deals_supervisor.py test-coverage
```

**Phase Complete When**: ✅ All 6 scrapers working, >90% success rate, tests passing

---

### Phase 3: API INTEGRATION (Week 3-4)

**Agent Role**: Integration verification
- Verify optional APIs (Rakuten)
- Check Redis caching layer
- Monitor data quality scoring
- Verify error handling

**Team Tasks**:
```
☐ Implement Rakuten API client (optional)
☐ Implement Redis caching
☐ Implement data quality scoring
☐ Implement error handling for API failures
☐ Write integration tests
☐ Deploy to staging
```

**Agent Verification**:
```bash
python scripts/deals_supervisor.py test-coverage
python scripts/deals_supervisor.py check-isolation
```

**Phase Complete When**: ✅ APIs working, caching verified, staging live

---

### Phase 4: UI INTEGRATION (Week 4)

**Agent Role**: Performance and accessibility verification
- Check page load time (no degradation)
- Verify feature flag functionality
- Check accessibility (WCAG 2.1 AA)
- Verify mobile responsiveness

**Team Tasks**:
```
☐ Create deals widget template
☐ Implement deals routes
☐ Implement feature flag controls
☐ Write accessibility tests
☐ Write UI tests
☐ Verify responsive design
```

**Agent Verification**:
```bash
python scripts/deals_supervisor.py test-coverage
python scripts/deals_supervisor.py check-isolation
```

**Phase Complete When**: ✅ Widget works, no performance impact, accessibility verified

---

### Phase 5: TESTING & QA (Week 4-5)

**Agent Role**: Comprehensive quality assurance
- Verify test coverage (>80%)
- Run main product regression tests
- Performance benchmarking
- Security review

**Team Tasks**:
```
☐ Expand unit test coverage to 80%+
☐ Write integration tests
☐ Write main product regression tests
☐ Run performance benchmarks
☐ Conduct security review
☐ Verify scraper reliability (>90%)
```

**Agent Verification**:
```bash
python scripts/deals_supervisor.py test-coverage
python scripts/deals_supervisor.py verify-phase
```

**Phase Complete When**: ✅ Coverage 80%+, all tests passing, security approved

---

### Phase 6: STAGING DEPLOYMENT (Week 5)

**Agent Role**: Production-readiness verification
- Monitor deployed service health
- Run 48-hour stability test
- Verify main product stability
- Check scraper execution

**Team Tasks**:
```
☐ Deploy to finance-deals-staging
☐ Verify database connectivity
☐ Run scrapers on schedule
☐ Monitor for 48 hours
☐ Verify main product staging stable
☐ Prepare production deployment
```

**Agent Verification**:
```bash
# During 48-hour test:
python scripts/deals_supervisor.py rollback-check
```

**Phase Complete When**: ✅ 48-hour stability test passed, metrics green

---

### Phase 7: CANARY DEPLOYMENT (Week 5-6)

**Agent Role**: Production rollout supervision
- Monitor main product metrics
- Track deals service performance
- Verify user feedback
- Auto-rollback if criteria met

**Team Tasks**:
```
☐ Deploy to finance-deals-prod
☐ Enable feature flag for 10% users
☐ Monitor for 1-2 days
☐ Expand to 25% (if green)
☐ Expand to 50% (if green)
☐ Expand to 100% (if green)
```

**Agent Verification** (automated):
```
Monitored continuously:
- Main product error rate (must stay same)
- Main product latency (must stay same)
- Deals service error rate (target: <1%)
- Scraper health (target: >90%)

If any threshold exceeded → Agent recommends rollback
```

**Phase Complete When**: ✅ 100% rollout, all metrics green

---

### Phase 8: PRODUCTION MONITORING (Week 6+)

**Agent Role**: Ongoing health monitoring
- Daily health checks
- Weekly report generation
- Continuous risk monitoring
- Post-launch review

**Team Tasks**:
```
☐ Monitor production metrics daily
☐ Review scraper health weekly
☐ Track user engagement
☐ Update documentation
☐ Plan Phase 2 enhancements
```

**Agent Verification** (continuous):
```bash
# Every Friday:
python scripts/deals_supervisor.py weekly-report
```

**Success When**: ✅ 99.9% uptime, 30%+ engagement, no main product impact

---

## 🔍 Key Supervision Mechanisms

### 1. **Isolation Enforcement**

The agent verifies deals service is isolated:

```python
✓ Main product doesn't hard-import deals module
✓ Feature flags control all deals functionality
✓ Error handling prevents crashes if deals service down
✓ Timeouts prevent blocking if deals service slow
```

**Team Verification**:
```bash
python scripts/deals_supervisor.py check-isolation
```

### 2. **Test Coverage Tracking**

```bash
python scripts/deals_supervisor.py test-coverage
```

**Targets**:
- Deals service: 80%+
- Scrapers: 90%+
- Integration: 100% pass rate

### 3. **Performance Monitoring**

Benchmarks verified:
- Widget render: < 100ms
- Cache hit: < 10ms
- Scraper run: < 60s for 6 sources
- Page load: Zero impact on main product

### 4. **Scraper Health**

```bash
python scripts/deals_supervisor.py scraper-health
```

Tracks per-scraper:
- Success rate (target: >90%)
- Last run time
- Deals extracted
- Error count

### 5. **Rollback Safeguards**

If ANY of these trigger → Automatic rollback:
```
1. Main product error rate +10%
2. Main product latency +10%
3. Deals service error rate >20%
4. Data corruption detected
5. Security incident
6. All scrapers failing
```

---

## 📈 Weekly Workflow

### Every Monday
```bash
# Start of week - review blockers
python scripts/deals_supervisor.py dashboard
```

### Every Day (Standup)
```bash
# Quick status check
python scripts/deals_supervisor.py verify-phase
```

### Every Friday
```bash
# Weekly report for stakeholders
python scripts/deals_supervisor.py weekly-report
```

### On Phase Completion
```bash
# Verify exit criteria before advancing
python scripts/deals_supervisor.py advance-phase NEXT_PHASE_NAME
```

### On Blocker Detection
```bash
# Escalate to team lead
python scripts/deals_supervisor.py escalate "Blocker description" "High"
```

---

## 🚨 Emergency Procedures

### If Integration Test Fails
```bash
# Investigate
python scripts/deals_supervisor.py check-isolation

# If isolation broken:
# Stop, fix code, re-test before proceeding
```

### If Performance Degrades
```bash
# Check current metrics
python scripts/deals_supervisor.py rollback-check

# If main product affected:
# Disable feature flag immediately
gcloud run services update finance-tracker \
  --set-env-vars DEALS_ROLLOUT_PERCENTAGE=0
```

### If Scraper Source Blocked
```bash
# Investigate scraper health
python scripts/deals_supervisor.py scraper-health

# Options:
# 1. Switch to proxy service
# 2. Use fallback API
# 3. Disable that source temporarily
```

### If Data Quality Issues
```bash
# Lower data quality threshold temporarily
# Fix extraction logic
# Re-run scrapers
# Verify quality scores improve
```

---

## 📊 Metrics Dashboard

The agent tracks and reports:

### Code Quality
- Line count: services/deals/
- Test coverage: Current %
- Code review approvals: N
- Security issues: 0 (goal)

### Service Health
- Uptime: 99.9% (goal)
- Error rate: < 1% (goal)
- Response time p95: < 2s (goal)
- Cache hit rate: > 95% (goal)

### Scraper Performance
- Total sources: 6
- Success rate: > 90% per source
- Deals extracted: Count
- Data quality: Avg score
- Last synced: Timestamp

### Main Product Impact
- Error rate change: 0% (goal)
- Latency change: < 5% (goal)
- User complaints: 0 (goal)
- Feature flag toggle: Success (goal)

### Deployment Progress
- Current phase: [Phase Name]
- Week: [N/6]
- Tasks completed: [X/Y]
- Blockers: [Count]
- On schedule: Yes/No

---

## 🎓 Team Training

### For Developers
```bash
# Before starting Phase 1:
python scripts/deals_supervisor.py verify-phase
```
This shows you exactly what tasks to complete.

### For QA Engineers
```bash
# During Phase 5:
python scripts/deals_supervisor.py test-coverage
```
This shows coverage targets and current status.

### For DevOps
```bash
# During deployment phases:
python scripts/deals_supervisor.py rollback-check
```
This shows what metrics to monitor for rollback.

### For Project Manager
```bash
# Every Friday:
python scripts/deals_supervisor.py weekly-report
```
This generates the status report for stakeholders.

---

## 🔧 Customization

### Add Custom Check
Edit `scripts/deals_supervisor.py`:
```python
def custom_check(self):
    print("\n🔍 Custom Check...")
    # Your verification logic
    return True/False
```

### Update Phase Tasks
Edit `DEALS_PROJECT_SUPERVISOR.md`:
```markdown
### Phase N: [Name]
- [ ] Task 1
- [ ] Task 2
```

### Adjust Thresholds
Edit `scripts/deals_supervisor.py`:
```python
COVERAGE_TARGET = 0.80  # 80%
ERROR_RATE_THRESHOLD = 0.01  # 1%
UPTIME_TARGET = 0.999  # 99.9%
```

---

## 📞 Escalation Matrix

| Issue | Severity | Action | Owner |
|-------|----------|--------|-------|
| Test coverage < 80% | Medium | Extend phase, allocate time | Team Lead |
| Integration test fails | High | Debug immediately, may indicate isolation break | Tech Lead |
| Performance regression | High | Investigate, optimize, may delay phase | Backend Lead |
| Security issue | Critical | Fix immediately, security review required | CTO |
| Main product affected | Critical | ROLLBACK immediately, investigate | Engineering Lead |
| Scraper source blocked | Medium | Switch proxy, try fallback API | Backend Lead |
| Data quality < 0.7 | Low | Update extraction logic | Backend Lead |
| All scrapers failing | Critical | Investigate, may indicate IP/rate blocking | Backend Lead |

---

## ✅ Success Criteria Verification

### Project Success (Week 6)
```bash
✓ All 8 phases completed
✓ Deals service deployed to production
✓ 6+ website scrapers running
✓ Zero impact on main product
✓ 99.9% availability
✓ All tests passing
✓ On schedule, on budget
```

Run final verification:
```bash
python scripts/deals_supervisor.py weekly-report
```

### Ongoing Success (Month 1)
```bash
✓ 30%+ user engagement
✓ 10%+ CTR on deals
✓ Scraper health stable
✓ Main product still stable
✓ No production incidents
✓ Cost within projections
```

---

## 📚 Documentation Structure

```
/Users/njpinton/projects/git/finance/

├── DEALS_PROJECT_SUPERVISOR.md          ← Master plan (detailed)
├── DEALS_PROJECT_QUICK_START.md         ← Quick reference
├── DEALS_SUPERVISION_AGENT_GUIDE.md     ← This file
├── scripts/
│   └── deals_supervisor.py              ← Agent CLI
├── services/
│   └── deals/                           ← Deals microservice
│       ├── app/
│       │   ├── models/
│       │   ├── services/
│       │   ├── routes/
│       │   └── scrapers/               ← Website scrapers
│       └── tests/
└── app/
    └── services/
        └── deals/
            └── deals_client.py          ← Main product integration
```

---

## 🎯 How to Use This System

### Day 1 (Project Kickoff)
```bash
1. Read this guide
2. Read DEALS_PROJECT_QUICK_START.md
3. Run: python scripts/deals_supervisor.py dashboard
4. Assign Phase 0 tasks to team
```

### Weeks 1-6 (Active Development)
```bash
1. Daily: Review supervisor dashboard
2. Daily: Run: python scripts/deals_supervisor.py verify-phase
3. Weekly: Run: python scripts/deals_supervisor.py weekly-report
4. On blocker: Run: python scripts/deals_supervisor.py escalate "..."
```

### Week 6+ (Production)
```bash
1. Weekly: Run: python scripts/deals_supervisor.py weekly-report
2. On incident: Run: python scripts/deals_supervisor.py rollback-check
3. Monthly: Review lessons learned, plan Phase 2
```

---

**Document Status**: ✅ Ready for Production
**Last Updated**: 2025-11-09
**Next Update**: Weekly (Fridays)
**Supervisor Agent**: Autonomous Credit Card Deals Project Manager
