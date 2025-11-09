# Credit Card Deals Service - Quick Start Guide

**Supervisor Agent Activated** ✓
**Project Status**: Ready to begin Phase 0

---

## 🚀 Getting Started

### 1. Initialize Project Supervision
```bash
python scripts/deals_supervisor.py dashboard
```

**Output**: Current project status, phase timeline, and metrics

---

## 📋 Phase Workflow

### Phase 0: PRE-DEVELOPMENT SETUP (Week 1)

**Duration**: 1 week
**Owner**: DevOps + Team Lead

**Key Tasks**:
1. Create Cloud SQL instance: `finance-deals-db`
2. Create secrets in Secret Manager
3. Set up Cloud Build triggers
4. Create feature branch
5. Configure Docker Compose

**Verification**:
```bash
python scripts/deals_supervisor.py verify-phase
```

**Advancement**:
```bash
python scripts/deals_supervisor.py advance-phase FOUNDATION
```

---

### Phase 1: FOUNDATION (Week 1-2)

**Duration**: 2 weeks
**Owner**: Senior Backend Engineer

**Key Deliverables**:
- [ ] Service scaffold created (`services/deals/`)
- [ ] Docker builds successfully
- [ ] Main product integration layer (`app/services/deals/deals_client.py`)
- [ ] Database schema implemented
- [ ] Tests passing (>90% coverage)

**Quality Checks**:
```bash
# Check test coverage
python scripts/deals_supervisor.py test-coverage

# Verify isolation from main product
python scripts/deals_supervisor.py check-isolation
```

**Exit Criteria**:
```
✓ Service builds
✓ Tests > 90% coverage
✓ Isolation verified
✓ Main product unaffected
```

---

### Phase 2: SCRAPER IMPLEMENTATION (Week 2-3)

**Duration**: 2 weeks
**Owner**: Backend Engineer (Scraper Specialist)

**Key Deliverables**:
- [ ] 6+ website scrapers implemented
  - Chase
  - American Express
  - Capital One
  - Discover
  - Bankrate
  - Credit Karma

- [ ] Proxy rotation system
- [ ] Header rotation system
- [ ] Data extraction tested
- [ ] Scraper tests passing (>90%)

**Scraper Health Check**:
```bash
python scripts/deals_supervisor.py scraper-health
```

**Exit Criteria**:
```
✓ All 6 scrapers implemented
✓ Data extraction verified
✓ Tests > 90% coverage
✓ Success rate > 90% per scraper
✓ Staging pulling live data
```

---

### Phase 3: API INTEGRATION (Week 3-4)

**Duration**: 2 weeks
**Owner**: Backend Engineer (Integration Specialist)

**Key Deliverables**:
- [ ] Optional: Rakuten API integration
- [ ] Redis caching layer
- [ ] Error handling & fallbacks
- [ ] Data quality scoring
- [ ] Monitoring & alerts

**Exit Criteria**:
```
✓ APIs integrated (if applicable)
✓ Cache working
✓ Error handling verified
✓ Data quality scoring implemented
✓ Staging stable
```

---

### Phase 4: UI INTEGRATION (Week 4)

**Duration**: 1 week
**Owner**: Frontend Engineer

**Key Deliverables**:
- [ ] Deals widget on accounts page
- [ ] Responsive design
- [ ] Feature flag working
- [ ] Accessibility compliance (WCAG 2.1 AA)

**Exit Criteria**:
```
✓ Widget displays correctly
✓ Page load time unchanged
✓ Mobile responsive
✓ Feature flag functional
```

---

### Phase 5: TESTING & QA (Week 4-5)

**Duration**: 2 weeks
**Owner**: QA Engineer + Team

**Key Deliverables**:
- [ ] Unit tests (80%+ coverage)
- [ ] Integration tests (all passing)
- [ ] Regression tests (main product)
- [ ] Performance benchmarks
- [ ] Security review

**Run Tests**:
```bash
python scripts/deals_supervisor.py test-coverage
```

**Exit Criteria**:
```
✓ Coverage > 80%
✓ All integration tests pass
✓ Main product unaffected
✓ Performance benchmarks met
✓ Security review passed
✓ Scraper reliability > 90%
```

---

### Phase 6: STAGING DEPLOYMENT (Week 5)

**Duration**: 1 week
**Owner**: DevOps + Engineering Lead

**Deployment Command**:
```bash
gcloud run deploy finance-deals-staging \
  --source services/deals \
  --region us-central1 \
  --set-env-vars DEALS_CACHE_TTL=3600,SCRAPER_SCHEDULE="0 */6 * * *" \
  --set-secrets DB_PASSWORD=credit-card-deals-db-password:latest \
  --memory 2Gi \
  --cpu 1 \
  --timeout 300
```

**Health Check**:
```bash
curl https://finance-deals-staging-xxxxx.run.app/health
```

**48-Hour Stability Test**:
- Monitor error rate (target: < 0.1%)
- Monitor response time (target: < 2s)
- Monitor memory growth (target: < 500MB)
- Verify scraper success rate (target: > 90%)

**Exit Criteria**:
```
✓ Deployed to staging
✓ Database working
✓ Scrapers running
✓ 48-hour stability test passed
✓ Main product staging stable
```

---

### Phase 7: CANARY DEPLOYMENT (Week 5-6)

**Duration**: 1 week
**Owner**: Engineering Lead + DevOps

**Canary Rollout Plan**:
```
Day 1-2: Deploy to production (10% users)
Day 2-3: Expand to 25% (if metrics green)
Day 3-4: Expand to 50% (if metrics green)
Day 4-5: Expand to 100% (if metrics green)
```

**Deploy to Production**:
```bash
gcloud run deploy finance-deals-prod \
  --source services/deals \
  --region us-central1 \
  --memory 2Gi \
  --cpu 1
```

**Enable Feature Flag (10%)**:
```bash
gcloud run services update finance-tracker \
  --set-env-vars DEALS_ROLLOUT_PERCENTAGE=10
```

**Monitor Metrics**:
- Main product error rate (must stay same)
- Deals service error rate (target: < 1%)
- User feedback (check support tickets)

**Exit Criteria**:
```
✓ 100% of users have deals
✓ Main product error rate unchanged
✓ Deals service stable
✓ User feedback positive
✓ Ready for monitoring phase
```

---

### Phase 8: PRODUCTION MONITORING (Week 6+)

**Duration**: Ongoing
**Owner**: DevOps + Engineering Team

**Monitoring Dashboard**:
- Service health (99.9% availability)
- Scraper health (success rate per source)
- Data quality metrics
- User engagement (CTR, views)
- Integration health (latency, errors)

**Alerting Rules**:
- Service down → Page on-call
- Error rate > 5% → Alert team
- Scraper health < 2 healthy → Alert team
- Main product regression → ROLLBACK immediately

**Post-Launch Review** (1 week):
```bash
python scripts/deals_supervisor.py weekly-report
```

**Success Metrics**:
```
✓ 99.9% availability
✓ 30%+ user engagement
✓ 10%+ CTR on deals
✓ Main product stable
✓ Scraper data fresh
```

---

## 🛠️ Supervisor Agent Commands

### Dashboard
See current status and timeline:
```bash
python scripts/deals_supervisor.py dashboard
```

### Verify Phase
Check exit criteria for current phase:
```bash
python scripts/deals_supervisor.py verify-phase
```

### Test Coverage
Run test coverage checks:
```bash
python scripts/deals_supervisor.py test-coverage
```

### Check Isolation
Verify deals service isolation:
```bash
python scripts/deals_supervisor.py check-isolation
```

### Scraper Health
Check all scrapers:
```bash
python scripts/deals_supervisor.py scraper-health
```

### Weekly Report
Generate status report:
```bash
python scripts/deals_supervisor.py weekly-report
```

### Advance Phase
Advance to next phase (requires verification):
```bash
python scripts/deals_supervisor.py advance-phase FOUNDATION
```

### Escalate Blocker
Escalate issue to team lead:
```bash
python scripts/deals_supervisor.py escalate "Scraper blocked" "High"
```

### Rollback Check
Check if rollback criteria are met:
```bash
python scripts/deals_supervisor.py rollback-check
```

---

## 📊 Key Metrics to Track

### Code Quality
- Unit test coverage: 80%+
- Integration test pass rate: 100%
- Code review approval rate: 100%

### Service Health
- Scraper success rate: > 90% per source
- Scraper response time: < 10s
- Cache hit rate: > 95%
- API response time: < 2s

### Main Product Impact
- Error rate change: 0% (no change allowed)
- Latency change: < 5% (minimal)
- User-reported issues: 0

### Deployment Progress
- Phase completion: On schedule
- Tests passing: 100%
- Security issues: 0
- Blockers: Escalated immediately

---

## 🚨 Risk Management

### High-Risk Items
1. **Website scraper blocking** → Use proxy rotation & rate limiting
2. **Integration impacting main product** → Async calls with timeout
3. **Data quality issues** → Validation layer + quality scoring
4. **Deployment disaster** → Staging → Canary → Gradual rollout

### Escalation Triggers
- Integration test failure
- Performance regression
- Security issue discovered
- Scraper health < 2 sources
- Main product error rate increase

### Rollback Criteria
- Main product error rate > 10%
- Main product latency > 10%
- Deals service error rate > 20%
- Data corruption detected
- Security incident

---

## 📝 Team Checklist

### Pre-Phase Start
- [ ] Team trained on phase objectives
- [ ] Dependencies identified
- [ ] Blockers escalated
- [ ] Resources allocated

### During Phase
- [ ] Daily standup completed
- [ ] Code reviews happening
- [ ] Tests written/passing
- [ ] Documentation updated

### Phase Completion
- [ ] All exit criteria verified
- [ ] Tests passing (80%+)
- [ ] Security review done
- [ ] Team sign-off obtained
- [ ] Stakeholders informed

---

## 🎯 Success Definition

### Go-Live Success (6 weeks)
```
✓ Deals service deployed to production
✓ 6+ website scrapers running
✓ Zero impact on main product
✓ Deals service 99.9% availability
✓ All tests passing (80%+ coverage)
✓ On schedule, on budget
```

### Post-Launch Success (1 month)
```
✓ 30%+ user engagement
✓ 10%+ CTR on deals
✓ Positive user feedback
✓ Main product stable
✓ Scraper data fresh (< 6 hours old)
✓ No production incidents
```

---

## 📞 Support & Escalation

**Daily Standup**: 9:00 AM
**Weekly Checkpoint**: Friday 3:00 PM
**Critical Issues**: Immediate escalation to CTO

**Supervisor Agent**: Available 24/7
```bash
python scripts/deals_supervisor.py help
```

---

**Document Status**: Active - Updated 2025-11-09
**Next Checkpoint**: Phase 0 Completion (end of Week 1)
**Supervisor**: Autonomous Project Management Agent
