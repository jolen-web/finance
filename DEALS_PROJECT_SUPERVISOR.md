# Credit Card Deals Service - Project Supervision Agent

**Status**: Active Supervision
**Project Start Date**: 2025-11-09
**Estimated Completion**: 2025-12-20 (6 weeks)
**Team Size**: 2-3 engineers
**Risk Level**: Low (isolated service)

---

## AGENT RESPONSIBILITIES

This document defines the autonomous supervisor agent for the Credit Card Deals Service integration project.

### Core Duties:
1. **Project Planning** - Break down work into sprints and tasks
2. **Code Review** - Ensure isolation principles are maintained
3. **Testing Oversight** - Verify test coverage and quality
4. **CI/CD Management** - Monitor pipeline health and deployments
5. **Risk Mitigation** - Identify and flag integration risks
6. **Quality Gates** - Enforce phase completion criteria
7. **Reporting** - Track progress and blockers
8. **Communication** - Alert team to issues immediately

---

## PHASE 0: PRE-DEVELOPMENT SETUP (Week 1)

### 0.1 Infrastructure Setup Tasks
- [ ] Create separate Cloud SQL instance: `finance-deals-db` (PostgreSQL 15)
- [ ] Create secret: `credit-card-deals-api-key` in Secret Manager
- [ ] Create secret: `deals-cache-credentials` in Secret Manager
- [ ] Create secret: `website-scraper-headers` in Secret Manager (User-Agent, etc)
- [ ] Set up Cloud Build trigger for `cloudbuild-deals.yaml`
- [ ] Create staging environment: `finance-deals-staging` Cloud Run service
- [ ] Create production environment: `finance-deals-prod` Cloud Run service
- [ ] Set up Redis instance for caching (Cloud Memorystore)
- [ ] Configure Cloud Scheduler for periodic scraping jobs

### 0.2 Repository Setup Tasks
- [ ] Create feature branch: `feature/credit-card-deals`
- [ ] Set up branch protection rules
- [ ] Create `.cloudbuild-deals.yaml` configuration file
- [ ] Update `docker-compose.yml` with deals services
- [ ] Create `services/deals/` directory structure
- [ ] Create `services/deals/scrapers/` for website scraper modules

### 0.3 Team Setup Tasks
- [ ] Define team ownership (who owns deals service)
- [ ] Create communication channel (Slack/Teams)
- [ ] Schedule daily standup (15 min)
- [ ] Schedule integration checkpoint (weekly)
- [ ] Document escalation path for blockers

---

## PHASE 1: FOUNDATION (Week 1-2)

### Milestone: Deals Service Skeleton Ready

**Exit Criteria:**
- ✓ Isolated deals service scaffold created
- ✓ Service runs independently in Docker
- ✓ All tests passing (100% coverage for skeleton)
- ✓ CI/CD pipeline configured
- ✓ Zero impact on main product confirmed

### 1.1 Service Architecture
```
Create files:
✓ services/deals/Dockerfile
✓ services/deals/requirements.txt
✓ services/deals/config.py
✓ services/deals/run.py
✓ services/deals/app/__init__.py
✓ services/deals/app/models/deals.py
✓ services/deals/app/models/scraper_status.py
✓ services/deals/app/services/deals_service.py
✓ services/deals/app/routes/__init__.py
✓ services/deals/app/routes/deals.py
✓ services/deals/app/cache/__init__.py
✓ services/deals/tests/conftest.py
✓ cloudbuild-deals.yaml
```

**Quality Checks:**
- Dockerfile builds successfully: `docker build services/deals -t deals-test`
- Service starts: `docker run deals-test`
- Python imports work: No circular dependencies
- Tests pass: `pytest services/deals/tests`

### 1.2 Main Product Integration Layer
```
Create files:
✓ app/services/deals/deals_client.py (NEW)
✓ app/config/feature_flags.py (UPDATED)
✓ tests/integration/test_main_unaffected.py (NEW)
```

**Quality Checks:**
- Main product imports don't fail if deals_client missing
- Feature flag controls all deals functionality
- Main app tests pass regardless of deals service state
- Timeout/exception handling verified

### 1.3 Database Schema

#### Main Deals Table (deals-db):
```sql
-- In finance-deals-db:
CREATE TABLE deals (
    id SERIAL PRIMARY KEY,
    card_type VARCHAR(50) NOT NULL,
    card_issuer VARCHAR(100),
    merchant_name VARCHAR(255),
    deal_description TEXT,
    cashback_percent DECIMAL(5,2),
    reward_points INTEGER,
    discount_amount DECIMAL(10,2),
    discount_percent DECIMAL(5,2),
    min_purchase_amount DECIMAL(10,2),
    promotion_start_date TIMESTAMP,
    promotion_end_date TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    api_source VARCHAR(50),
    scraper_source VARCHAR(50),
    data_quality_score DECIMAL(3,2),
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_deals_card_type ON deals(card_type);
CREATE INDEX idx_deals_active ON deals(promotion_end_date) WHERE is_active = TRUE;
CREATE INDEX idx_deals_card_issuer ON deals(card_issuer);
CREATE INDEX idx_deals_merchant ON deals(merchant_name);
CREATE INDEX idx_deals_source ON deals(api_source, scraper_source);
```

#### Scraper Status Tracking Table:
```sql
-- Track scraping job health
CREATE TABLE scraper_status (
    id SERIAL PRIMARY KEY,
    scraper_name VARCHAR(100) NOT NULL UNIQUE,
    last_run_at TIMESTAMP,
    next_scheduled_run TIMESTAMP,
    last_success_at TIMESTAMP,
    last_error_message TEXT,
    deals_found INTEGER,
    deals_processed INTEGER,
    deals_stored INTEGER,
    error_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2),
    last_http_status_code INTEGER,
    is_healthy BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_scraper_health ON scraper_status(is_healthy, last_run_at);
```

#### Cache Management Table:
```sql
-- Track cache keys and expiry
CREATE TABLE cache_keys (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    ttl_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX idx_cache_expires ON cache_keys(expires_at);
```

**Verification:**
- Schema created successfully
- Indexes created
- Can connect from local + Cloud Run
- No impact on main finance database

---

## PHASE 2: WEBSITE SCRAPER IMPLEMENTATION (Week 2-3)

### Milestone: Credit Card Deals Data Flowing In

**Exit Criteria:**
- ✓ Website scraper implemented and tested
- ✓ Data parsing verified with real websites
- ✓ Error handling for scraping failures
- ✓ Rotating proxies / headers implemented
- ✓ Staging service pulling live scraped data
- ✓ Rate limiting to avoid blocking

### 2.1 Website Scraper Architecture

```
services/deals/app/scrapers/
├── __init__.py
├── base_scraper.py (Abstract base class)
├── credit_karma_scraper.py
├── capital_one_scraper.py
├── chase_scraper.py
├── amex_scraper.py
├── discover_scraper.py
├── bankrate_scraper.py
├── nerdwallet_scraper.py
├── common_deal_sites_scraper.py
├── proxy_manager.py
├── headers_rotator.py
└── tests/
    ├── test_base_scraper.py
    ├── test_credit_karma_scraper.py
    ├── test_proxy_manager.py
    └── fixtures/
        ├── sample_credit_karma_html.html
        ├── sample_chase_html.html
        └── ...
```

### 2.2 Scraper Framework Design

#### Base Scraper (Abstract):
```python
# services/deals/app/scrapers/base_scraper.py

class BaseScraper:
    """Abstract base class for all deal scrapers"""

    def __init__(self, name, timeout=10, retries=3):
        self.name = name
        self.timeout = timeout
        self.retries = retries
        self.session = requests.Session()
        self.logger = logging.getLogger(f'scrapers.{name}')

    def scrape(self):
        """Main scraping method - implemented by subclasses"""
        raise NotImplementedError

    def extract_deals(self, html):
        """Extract deals from HTML - implemented by subclasses"""
        raise NotImplementedError

    def validate_deal(self, deal):
        """Validate deal data before storing"""
        # Check required fields
        # Validate data types
        # Calculate quality score

    def store_deals(self, deals):
        """Store deals in database"""
        # Insert/update in database
        # Update scraper_status table

    def handle_error(self, error):
        """Handle scraping errors gracefully"""
        # Log error
        # Update scraper_status
        # Notify monitoring system

    def get_headers(self):
        """Get rotated headers to avoid detection"""
        return headers_rotator.get_random_headers()

    def get_proxy(self):
        """Get proxy to distribute requests"""
        return proxy_manager.get_next_proxy()
```

#### Specific Scraper Example (Chase):
```python
# services/deals/app/scrapers/chase_scraper.py

class ChaseScraper(BaseScraper):
    """Scrape Chase credit card benefits"""

    def __init__(self):
        super().__init__(name='chase', timeout=15)
        self.base_url = 'https://www.chase.com/personal/credit-cards'

    def scrape(self):
        """Fetch and parse Chase deals"""
        try:
            for retry in range(self.retries):
                try:
                    response = self.session.get(
                        self.base_url,
                        headers=self.get_headers(),
                        proxies={'http': self.get_proxy()},
                        timeout=self.timeout
                    )
                    response.raise_for_status()
                    break
                except requests.RequestException as e:
                    if retry == self.retries - 1:
                        raise
                    time.sleep(2 ** retry)  # Exponential backoff

            html = response.text
            deals = self.extract_deals(html)

            # Validate and store
            valid_deals = [d for d in deals if self.validate_deal(d)]
            self.store_deals(valid_deals)

            return {'status': 'success', 'deals_found': len(valid_deals)}

        except Exception as e:
            self.handle_error(e)
            return {'status': 'error', 'message': str(e)}

    def extract_deals(self, html):
        """Extract deals from Chase website HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        deals = []

        # Parse specific CSS selectors for Chase
        for card_element in soup.find_all('div', class_='credit-card-offer'):
            deal = {
                'card_issuer': 'Chase',
                'card_type': card_element.find('h2').text.strip(),
                'cashback_percent': self._extract_cashback(card_element),
                'reward_points': self._extract_points(card_element),
                'deal_description': self._extract_description(card_element),
                'promotion_end_date': self._extract_expiry(card_element),
                'scraper_source': 'chase_website'
            }
            deals.append(deal)

        return deals

    def _extract_cashback(self, element):
        """Extract cashback percentage"""
        text = element.find('span', class_='cashback').text
        match = re.search(r'(\d+\.?\d*)', text)
        return float(match.group(1)) if match else None

    # More extraction methods...
```

### 2.3 Proxy & Headers Management

```python
# services/deals/app/scrapers/proxy_manager.py

class ProxyManager:
    """Rotate proxies to avoid blocking"""

    def __init__(self):
        self.proxies = [
            'http://proxy1.example.com:8080',
            'http://proxy2.example.com:8080',
            'http://proxy3.example.com:8080',
        ]
        self.current_index = 0

    def get_next_proxy(self):
        """Get next proxy in rotation"""
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy

# services/deals/app/scrapers/headers_rotator.py

class HeadersRotator:
    """Rotate user agents and headers"""

    HEADERS_LIST = [
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
        },
        # More realistic headers...
    ]

    def get_random_headers(self):
        return random.choice(self.HEADERS_LIST)
```

### 2.4 Scraping Schedule & Management

```python
# services/deals/app/services/scraping_orchestrator.py

class ScrapingOrchestrator:
    """Manage all scraping jobs"""

    def __init__(self):
        self.scrapers = {
            'chase': ChaseScraper(),
            'amex': AmexScraper(),
            'capital_one': CapitalOneScraper(),
            'discover': DiscoverScraper(),
            'bankrate': BankrateScraper(),
            'credit_karma': CreditKarmaScraper(),
        }

    def run_all_scrapers(self):
        """Run all scrapers in parallel"""
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(self._run_scraper, name, scraper): name
                for name, scraper in self.scrapers.items()
            }

            results = {}
            for future in as_completed(futures):
                name = futures[future]
                try:
                    results[name] = future.result()
                except Exception as e:
                    logger.error(f'Scraper {name} failed: {e}')
                    results[name] = {'status': 'error', 'message': str(e)}

            return results

    def _run_scraper(self, name, scraper):
        """Run single scraper with error handling"""
        try:
            logger.info(f'Starting scraper: {name}')
            result = scraper.scrape()
            logger.info(f'Scraper {name} completed: {result}')
            return result
        except Exception as e:
            logger.error(f'Scraper {name} error: {e}')
            return {'status': 'error', 'message': str(e)}

    def schedule_periodic_scraping(self):
        """Schedule scrapers to run at intervals"""
        # Run every 6 hours
        schedule.every(6).hours.do(self.run_all_scrapers)

        # Keep schedule running
        while True:
            schedule.run_pending()
            time.sleep(60)
```

### 2.5 Data Extraction & Validation

```python
# services/deals/app/services/deal_extractor.py

class DealExtractor:
    """Extract and validate deal data"""

    REQUIRED_FIELDS = {
        'card_issuer': str,
        'card_type': str,
        'deal_description': str,
        'promotion_end_date': datetime,
    }

    OPTIONAL_FIELDS = {
        'cashback_percent': float,
        'reward_points': int,
        'discount_amount': float,
        'discount_percent': float,
        'min_purchase_amount': float,
    }

    def validate_deal(self, deal):
        """Validate deal data and assign quality score"""
        errors = []

        # Check required fields
        for field, field_type in self.REQUIRED_FIELDS.items():
            if field not in deal or not deal[field]:
                errors.append(f'Missing required field: {field}')
            elif not isinstance(deal[field], field_type):
                errors.append(f'Invalid type for {field}')

        # Validate optional fields
        for field, field_type in self.OPTIONAL_FIELDS.items():
            if field in deal and deal[field] is not None:
                if not isinstance(deal[field], field_type):
                    errors.append(f'Invalid type for {field}')

        # Check if promotion is not expired
        if deal.get('promotion_end_date') < datetime.now():
            errors.append('Promotion already expired')

        # Calculate quality score
        quality_score = self._calculate_quality_score(deal, errors)

        return {
            'valid': len(errors) == 0,
            'quality_score': quality_score,
            'errors': errors
        }

    def _calculate_quality_score(self, deal, errors):
        """Calculate deal quality score (0-1)"""
        score = 1.0

        # Deduct points for errors
        score -= len(errors) * 0.1

        # Bonus for having more detail
        if 'cashback_percent' in deal and deal['cashback_percent']:
            score += 0.1
        if 'reward_points' in deal and deal['reward_points']:
            score += 0.1

        # Recent deals score higher
        if deal.get('promotion_end_date'):
            days_until_expiry = (deal['promotion_end_date'] - datetime.now()).days
            if days_until_expiry < 7:
                score -= 0.2  # Expiring soon
            elif days_until_expiry > 90:
                score += 0.1  # Long validity

        return max(0, min(1, score))  # Clamp between 0-1
```

### 2.6 Testing Scrapers

```python
# services/deals/tests/unit/scrapers/test_chase_scraper.py

@pytest.fixture
def sample_chase_html():
    """Load sample HTML from Chase website"""
    with open('tests/fixtures/sample_chase_html.html') as f:
        return f.read()

def test_chase_scraper_extract_deals(sample_chase_html):
    """Test extracting deals from Chase HTML"""
    scraper = ChaseScraper()
    deals = scraper.extract_deals(sample_chase_html)

    assert len(deals) > 0
    assert all('card_type' in d for d in deals)
    assert all('deal_description' in d for d in deals)

def test_chase_scraper_validation():
    """Test deal validation"""
    deal = {
        'card_issuer': 'Chase',
        'card_type': 'Sapphire Reserve',
        'deal_description': '10x points on travel',
        'promotion_end_date': datetime.now() + timedelta(days=30)
    }

    validation = scraper.validate_deal(deal)
    assert validation['valid'] == True
    assert validation['quality_score'] > 0.7

def test_proxy_rotation():
    """Test proxy manager rotates correctly"""
    manager = ProxyManager()
    proxies = [manager.get_next_proxy() for _ in range(6)]

    # Should cycle through list
    assert len(set(proxies)) == 3

def test_scraper_timeout():
    """Test scraper handles timeouts gracefully"""
    with patch('requests.Session.get') as mock_get:
        mock_get.side_effect = requests.Timeout()
        scraper = ChaseScraper()

        result = scraper.scrape()
        assert result['status'] == 'error'

def test_scraper_html_parsing_failure():
    """Test scraper handles parsing errors"""
    scraper = ChaseScraper()
    invalid_html = "<html><body>No deals here</body></html>"

    deals = scraper.extract_deals(invalid_html)
    assert len(deals) == 0  # Empty but doesn't crash
```

### 2.7 Monitoring Scraper Health

```python
# services/deals/app/services/scraper_health_monitor.py

class ScraperHealthMonitor:
    """Monitor scraper health and performance"""

    def __init__(self, db):
        self.db = db
        self.logger = logging.getLogger('scraper_health')

    def update_scraper_status(self, scraper_name, result):
        """Update scraper status after run"""
        status = ScraperStatus.query.filter_by(
            scraper_name=scraper_name
        ).first_or_404()

        status.last_run_at = datetime.now()
        status.next_scheduled_run = datetime.now() + timedelta(hours=6)

        if result['status'] == 'success':
            status.last_success_at = datetime.now()
            status.deals_found = result.get('deals_found', 0)
            status.deals_stored = result.get('deals_stored', 0)
            status.error_count = 0
            status.is_healthy = True
        else:
            status.last_error_message = result.get('message')
            status.error_count += 1
            status.is_healthy = status.error_count < 3

        status.success_rate = self._calculate_success_rate(status)
        status.updated_at = datetime.now()

        self.db.session.commit()

        # Alert if unhealthy
        if not status.is_healthy:
            self._alert_unhealthy_scraper(status)

    def _alert_unhealthy_scraper(self, status):
        """Send alert if scraper unhealthy"""
        self.logger.error(
            f'Scraper {status.scraper_name} unhealthy: '
            f'{status.error_count} consecutive errors'
        )
        # Send to monitoring system (PagerDuty, etc)

---

## PHASE 3: EXTERNAL API INTEGRATION (Week 3-4)

### Milestone: Multiple Data Sources Live

**Exit Criteria:**
- ✓ Website scrapers running successfully (6+ sites)
- ✓ Optional API integration (Rakuten, if available)
- ✓ Data fetching tested with real sources
- ✓ Caching layer working (Redis)
- ✓ Error handling for scraper/API failures
- ✓ Staging service pulling live data

### 3.1 API Integration (Optional Enhancement)

```python
# services/deals/app/api_clients/rakuten_api_client.py

class RakutenAPIClient:
    """Fetch deals from Rakuten API"""

    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = 'https://api.rakuten.com/deals'

    def get_deals(self, category=None):
        """Fetch deals from Rakuten"""
        try:
            response = requests.get(
                self.base_url,
                headers={'Authorization': f'Bearer {self.api_key}'},
                params={'category': category},
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f'Rakuten API error: {e}')
            return {'deals': []}
```

### 3.2 Caching Strategy

```python
# services/deals/app/cache/redis_cache.py

class RedisCache:
    """Cache deals in Redis"""

    def __init__(self, redis_url):
        self.redis = redis.from_url(redis_url)
        self.ttl = 3600  # 1 hour

    def get_deals(self, category):
        """Get cached deals"""
        key = f'deals:{category}'
        cached = self.redis.get(key)

        if cached:
            logger.info(f'Cache hit: {key}')
            return json.loads(cached)

        return None

    def set_deals(self, category, deals, ttl=None):
        """Cache deals"""
        key = f'deals:{category}'
        ttl = ttl or self.ttl

        self.redis.setex(key, ttl, json.dumps(deals))
        logger.info(f'Cached {len(deals)} deals: {key}')

    def invalidate_category(self, category):
        """Invalidate cache for category"""
        key = f'deals:{category}'
        self.redis.delete(key)
        logger.info(f'Invalidated cache: {key}')
```

### 3.3 Data Quality

```python
- [ ] Validate all deal schemas before storing
- [ ] Add data_quality_score (0-1) to each deal
- [ ] Only show deals with score > 0.7
- [ ] Log low-quality deals for investigation
- [ ] Set up data quality monitoring dashboard
- [ ] Track source reliability (API vs scraper success rate)
```

---

## PHASE 4: UI INTEGRATION (Week 4)

### Milestone: Users See Deals

**Exit Criteria:**
- ✓ Deals widget appears on accounts page
- ✓ Deals display correctly
- ✓ No performance degradation (page load time same)
- ✓ Feature flag working (can toggle off)
- ✓ Mobile responsive
- ✓ Deals sorted by relevance (quality score, cashback %)

### 4.1 Frontend Components
```
Create files:
✓ app/templates/deals/deals_widget.html
✓ app/templates/deals/deals_list.html
✓ app/templates/deals/deal_card.html
✓ app/static/css/deals.css
✓ app/static/js/deals.js
✓ app/static/js/deals-tracker.js (analytics)
```

**Quality Checks:**
- Widget loads in < 100ms (cached)
- Page load time same as before (async deals)
- Mobile: responsive at 320px+ width
- Accessibility: WCAG 2.1 AA compliant
- No layout shift (CLS score)
- Deals sorted by relevance/quality

### 4.2 Routes
```python
# app/routes/deals.py (NEW)
- [ ] GET /deals/api/deals/<category> - fetch deals (async)
- [ ] GET /deals/api/deals/card/<card_type> - filter by card
- [ ] GET /deals/widget - embed widget on page
- [ ] GET /deals/health - scraper health status
- [ ] POST /deals/feedback - user likes/dislikes deal
- [ ] GET /deals/sources - show which sources have deals
```

**Testing:**
- Routes return 200 even if deals service down
- Routes handle missing category gracefully
- Rate limiting prevents abuse (100 req/minute per user)

---

## PHASE 5: TESTING & QA (Week 4-5)

### Milestone: Full Test Coverage

**Exit Criteria:**
- ✓ 80%+ code coverage (deals service)
- ✓ All integration tests passing
- ✓ Main product unaffected (regression test)
- ✓ Performance benchmarks met
- ✓ Security review passed
- ✓ Scraper reliability verified (>90% success rate)

### 5.1 Unit Tests
```python
tests/unit/services/deals/
- [ ] test_deals_service.py (80%+ coverage)
- [ ] test_deals_cache.py (100% coverage)
- [ ] test_deal_extractor.py (100% coverage)
- [ ] test_deal_validator.py (100% coverage)
- [ ] test_deals_models.py (100% coverage)

tests/unit/scrapers/
- [ ] test_base_scraper.py (100% coverage)
- [ ] test_chase_scraper.py (90%+ coverage with fixtures)
- [ ] test_amex_scraper.py (90%+ coverage)
- [ ] test_proxy_manager.py (100% coverage)
- [ ] test_headers_rotator.py (100% coverage)
```

**Coverage Requirements:**
- Service logic: 80%+
- Error handling: 100%
- Cache logic: 100%
- Scraper logic: 90%+ with fixtures
- Models: 95%+

### 5.2 Integration Tests
```python
tests/integration/
- [ ] test_deals_end_to_end.py (scraper → cache → API)
- [ ] test_main_product_unaffected.py (CRITICAL!)
- [ ] test_deals_service_isolation.py
- [ ] test_deals_performance.py (benchmarks)
- [ ] test_scraper_health_monitoring.py
```

**Main Product Regression Tests** (CRITICAL):
```python
def test_user_registration_with_deals_service_down():
    """Main product works without deals"""

def test_accounts_load_time_unchanged_with_deals():
    """Page load time not impacted by deals service"""

def test_transaction_creation_with_slow_deals_service():
    """User can create transaction even if deals API slow"""

def test_all_main_product_routes_work():
    """All existing routes still functional"""

def test_deals_widget_graceful_degradation():
    """Widget shows empty state if deals service unavailable"""
```

### 5.3 Performance Testing
```
Benchmarks to hit:
- [ ] Deals service startup: < 3s
- [ ] Cache hit response: < 10ms
- [ ] Scraper run (6 sources): < 60 seconds
- [ ] Widget render: < 100ms
- [ ] Database query (fetch deals): < 100ms
- [ ] No memory leaks (24-hour stability test)
- [ ] CPU usage: < 15% at idle
```

### 5.4 Security Review
```
Checklist:
- [ ] No SQL injection (parameterized queries)
- [ ] No XSS in deal display (escape HTML)
- [ ] No scraper detection (proxy/header rotation)
- [ ] API credentials in Secret Manager (not code)
- [ ] Rate limiting on public endpoints
- [ ] No sensitive data logged
- [ ] CORS properly configured
- [ ] HTTPS enforced
- [ ] Robots.txt respected for scrapers
- [ ] Terms of Service compliance for each site
```

### 5.5 Scraper Reliability Testing
```
- [ ] Test each scraper with 10 consecutive runs
- [ ] Success rate > 90% for each scraper
- [ ] Average response time < 10s per scraper
- [ ] Error handling verified (graceful degradation)
- [ ] Data quality score distribution analyzed
- [ ] Duplicate deal detection working
- [ ] Expired deal removal working
```

---

## PHASE 6: STAGING DEPLOYMENT (Week 5)

### Milestone: Production-Ready Code

**Exit Criteria:**
- ✓ Deployed to `finance-deals-staging`
- ✓ Running with real Cloud SQL database
- ✓ Scrapers running on schedule
- ✓ Real API calls working
- ✓ 48-hour stability test passed
- ✓ Performance acceptable in production environment
- ✓ Main product staging still stable

### 6.1 Staging Environment
```bash
# Deploy to staging
gcloud run deploy finance-deals-staging \
  --source services/deals \
  --region us-central1 \
  --set-env-vars DEALS_CACHE_TTL=3600,SCRAPER_SCHEDULE="0 */6 * * *" \
  --set-secrets DB_PASSWORD=credit-card-deals-db-password:latest \
  --set-secrets API_KEY=credit-card-deals-api-key:latest \
  --memory 2Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10
```

**Health Checks:**
- [ ] Service responds to /health endpoint
- [ ] Database connection working
- [ ] Cache working (Redis)
- [ ] Scrapers running on schedule
- [ ] Logs shipping to Cloud Logging

### 6.2 Staging Integration Test
```python
def test_staging_environment():
    """Full end-to-end test in staging"""

    # 1. Service is running
    assert staging_service.is_healthy()

    # 2. Can fetch deals
    deals = staging_service.get_deals('credit_cards')
    assert len(deals) > 0

    # 3. Cache is working
    deals2 = staging_service.get_deals('credit_cards')
    assert response_time(deals2) < 10ms  # Cached

    # 4. Scrapers have run recently
    status = staging_service.get_scraper_status()
    assert status['chase']['last_run_at'] < 1.hour.ago
    assert status['amex']['last_run_at'] < 1.hour.ago

    # 5. Main product integration
    main_app = connect_to_main_staging()
    response = main_app.get('/accounts')
    assert response.status == 200
    assert 'deals' in response.html or 'Credit Card Deals' in response.text
```

### 6.3 Stability Testing (48 hours)
```bash
# Run continuous load test
- [ ] 100 requests/minute for 48 hours
- [ ] Monitor:
    - Error rate (target: < 0.1%)
    - Response time (target: < 2s p95)
    - Memory growth (target: < 500MB increase)
    - CPU utilization (target: < 20% average)
    - Scraper success rate (target: > 90%)
- [ ] Verify no memory leaks
- [ ] Verify cache hit rate > 95%
- [ ] Verify scrapers complete within SLA
```

---

## PHASE 7: CANARY DEPLOYMENT (Week 5-6)

### Milestone: Safe Production Rollout

**Exit Criteria:**
- ✓ 10% of users seeing deals (canary)
- ✓ Zero increase in main product error rate
- ✓ Zero increase in main product latency
- ✓ User feedback positive
- ✓ Ready for 100% rollout

### 7.1 10% Canary Deployment
```bash
# Deploy finance-deals-prod service
gcloud run deploy finance-deals-prod \
  --source services/deals \
  --region us-central1 \
  --set-env-vars DEALS_CACHE_TTL=3600,SCRAPER_SCHEDULE="0 */6 * * *" \
  --set-secrets DB_PASSWORD=credit-card-deals-db-password:latest \
  --memory 2Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 20

# Enable feature flag for 10% of users
gcloud run services update finance-tracker \
  --set-env-vars DEALS_ROLLOUT_PERCENTAGE=10
```

**Monitoring Canary** (1-2 days):
```
Metrics to watch:
- [ ] finance-tracker error rate (should stay same)
- [ ] finance-tracker p95 latency (should stay same)
- [ ] finance-deals-prod error rate (target: < 1%)
- [ ] deals widget render time (target: < 100ms)
- [ ] scraper success rate (target: > 90%)
- [ ] User feedback (check logs/support tickets)

Alert thresholds:
- Error rate increase > 10% → ROLLBACK
- P95 latency increase > 5% → ROLLBACK
- Deals service error rate > 5% → ROLLBACK
- Scraper health degradation → INVESTIGATE
```

### 7.2 Gradual Rollout Plan
```
Day 1-2: 10% rollout
├── Monitor metrics
├── Collect user feedback
└── Decision: Continue or Rollback

Day 2-3: 25% rollout (if green)
├── Monitor metrics
├── Verify no new issues
└── Decision: Continue or Rollback

Day 3-4: 50% rollout (if green)
├── Monitor metrics
├── All metrics nominal
└── Decision: Continue or Rollback

Day 4-5: 100% rollout (if green)
├── Monitor for 24 hours
├── Declare success
└── Update documentation
```

---

## PHASE 8: PRODUCTION MONITORING (Week 6+)

### Milestone: Live in Production

**Exit Criteria:**
- ✓ 100% of users have deals enabled
- ✓ System stable for 1 week
- ✓ User engagement metrics positive
- ✓ No regression in main product
- ✓ Scrapers running reliably
- ✓ Documentation complete

### 8.1 Production Monitoring Dashboard
```
Create dashboard monitoring:

1. Service Health
   - finance-deals-prod availability (target: 99.9%)
   - Response time p50/p95/p99
   - Error rate
   - Scraper health status (6+ sources)

2. Data Quality
   - Deal freshness (last synced by source)
   - Deal count by card issuer
   - Data quality score distribution
   - Deals by promotion type

3. User Engagement
   - Deals widget views
   - Click-through rate by issuer
   - Most viewed deals
   - User feedback (likes/dislikes)

4. Integration Health
   - Main product error rate
   - Cross-service communication latency
   - Feature flag toggle success
   - Widget rendering performance

5. Scraper Performance
   - Scraper success rate per source
   - Deals extracted per source
   - Extraction time per source
   - Last run timestamp per source

6. Cost Analysis
   - Cloud Run cost (deals-prod)
   - Cloud SQL cost (deals-db)
   - Redis cache cost
   - Bandwidth cost
```

### 8.2 Alerting Rules
```yaml
Alerts (PagerDuty/Cloud Alerting):

1. Deals service down (availability < 99%)
   Severity: Critical
   Action: Page on-call engineer

2. High error rate (> 5%)
   Severity: High
   Action: Alert team, investigate

3. Scraper health degraded (> 2 sources unhealthy)
   Severity: Medium
   Action: Alert team, check sources

4. API integration failing (> 10 minutes)
   Severity: High
   Action: Alert team, investigate provider

5. Main product regression (error rate increase > 10%)
   Severity: Critical
   Action: IMMEDIATELY disable deals feature flag

6. Data quality degradation (avg score < 0.7)
   Severity: Medium
   Action: Alert team, disable low-quality deals

7. Cache hit rate dropped (< 80%)
   Severity: Low
   Action: Investigate Redis health

8. Widget rendering slow (p95 > 500ms)
   Severity: Low
   Action: Investigate frontend optimization
```

### 8.3 Post-Launch Review
```
1-week post-launch:
- [ ] Review deployment logs
- [ ] Analyze user engagement metrics
- [ ] Review scraper health and data quality
- [ ] Collect team feedback
- [ ] Document lessons learned
- [ ] Update runbooks
- [ ] Plan Phase 2 (enhancements)

2-week post-launch:
- [ ] Analyze cost efficiency
- [ ] Review security logs
- [ ] Check for any integration issues
- [ ] User feedback analysis
- [ ] Update SLA/SLO based on real data
```

---

## RISK MANAGEMENT MATRIX

| Risk | Probability | Impact | Mitigation | Owner |
|------|------------|--------|-----------|-------|
| Scraper blocked/blacklisted | Medium | Medium | Proxy rotation, rate limiting, headers | Deals Team |
| Website structure changes | High | Medium | Monitoring, quick updates, fallback APIs | Deals Team |
| Integration impacts main product | Low | Critical | Async calls, timeouts, feature flag | Project Manager |
| Database performance degrades | Low | Medium | Separate instance, indexing, monitoring | DevOps |
| Data quality issues | Medium | Low | Validation layer, quality scoring | Deals Team |
| Deployment breaks production | Low | Critical | Staging → canary → gradual rollout | DevOps |
| Team coordination issues | Low | Medium | Daily standups, clear ownership | Project Manager |
| Scope creep | Medium | Medium | Strict phase gates, definition of done | Project Manager |
| Redis cache fails | Low | Low | Graceful fallback to DB, monitoring | DevOps |
| Legal/ToS issues | Low | High | Verify scraper legality, add disclaimers | Legal |

---

## AGENT DECISION TREE

### Phase Advancement Gate
```
✓ All phase exit criteria met?
├─ YES → Approve phase advancement, schedule next phase kickoff
└─ NO → Flag blockers, identify gaps, request retesting

Before declaring phase complete:
1. Run all tests (unit + integration + regression)
2. Code review checklist (isolation, error handling, logging)
3. Performance benchmarks verified
4. Security checklist passed
5. Scraper reliability verified (>90% for all sources)
6. Documentation updated
7. Team signs off
```

### Issue Escalation Path
```
Critical Blocker Detected:
1. Notify team lead immediately
2. Context: What blocks this?
3. Options: Workaround? Scope reduction? Defer?
4. Decision: Team lead decides
5. Update plan if needed
6. Communicate to stakeholders

Examples:
- Scraper blocked → Switch to proxy service or fallback
- Integration test failing → Debug, may indicate isolation problem
- Performance regression → Optimize, may delay phase
- Security issue → Fix before proceeding
- Data quality issues → Validate extraction logic, update selectors
```

### Rollback Decision Criteria
```
Auto-rollback if ANY of these:
1. Main product error rate increases > 10%
2. Main product p95 latency increases > 10%
3. Deals service error rate > 20% for > 10 minutes
4. Data corruption detected
5. Security incident
6. All scraper sources failing

Manual rollback if:
1. User complaints exceed threshold
2. Business logic issue discovered
3. Integration test failure
4. Team consensus to pause
5. Legal/ToS compliance issue
```

---

## SUPERVISION AGENT DELIVERABLES

### Weekly Reports (Every Friday)
```
DEALS SERVICE PROJECT - WEEKLY STATUS REPORT
Week N: [Dates]

1. PHASE PROGRESS
   Current Phase: [Phase N - Description]
   Status: ON TRACK / AT RISK / BLOCKED

2. COMPLETED THIS WEEK
   - [ ] Specific deliverables
   - [ ] Code merged/deployed
   - [ ] Tests added
   - [ ] Scrapers improved

3. PLANNED NEXT WEEK
   - [ ] Next deliverables
   - [ ] Expected phase advancement

4. BLOCKERS
   - [ ] None / Item 1 / Item 2 (with impact)

5. METRICS
   - Code coverage: X%
   - Test count: N
   - Scrapers: M sources active
   - Deploy count: K
   - Issue count: Z

6. SCRAPER HEALTH
   - Chase: [Success Rate]%
   - Amex: [Success Rate]%
   - Capital One: [Success Rate]%
   - Discover: [Success Rate]%
   - Bankrate: [Success Rate]%
   - Credit Karma: [Success Rate]%

7. RISKS
   - [ ] Identified risks
   - [ ] Mitigations in place

8. TEAM HEALTH
   - Velocity: On track
   - Morale: Good
   - Blockers: None
```

### Phase Completion Checklist
```
Before Approving Phase Completion:
- [ ] All tasks in phase completed
- [ ] All exit criteria verified
- [ ] Test coverage > 80%
- [ ] Code review approved
- [ ] Performance benchmarks met
- [ ] Security review passed
- [ ] Scraper reliability > 90%
- [ ] Documentation updated
- [ ] Team signed off
- [ ] Stakeholders informed
```

### Decision Log
```
Decision: [Description]
Date: [Date]
Context: [What led to this decision]
Options Considered: [A, B, C]
Decision: [Chosen option]
Rationale: [Why chosen]
Impact: [What changes because of this]
Owner: [Who made the decision]
```

---

## AGENT AUTONOMY & ESCALATION

### What Agent Can Do Alone:
- Verify test coverage
- Check code quality
- Monitor CI/CD status
- Flag isolation violations
- Monitor scraper health
- Generate reports
- Schedule checkpoints
- Update phase progress
- Identify blockers
- Recommend rollbacks (non-binding)
- Verify scraper success rates

### What Requires Human Approval:
- Phase advancement (team lead approval)
- Scope changes (project manager approval)
- Production deployments (eng lead approval)
- Budget changes (finance approval)
- Rollback execution (eng lead decision)
- Risk acceptance (project manager decision)
- Disabling scraper sources (data quality decision)

### Escalation Triggers:
```
Immediate escalation (notify project manager + team lead):
1. Integration test failure (may indicate isolation problem)
2. Performance regression (may affect main product)
3. Security issue discovered
4. Scraper source blocked/blacklisted
5. Blocker without clear mitigation
6. Schedule risk (phase falling behind)

Critical escalation (notify CTO/director):
1. Main product impact detected
2. Major scope change needed
3. Project viability questioned
4. Security incident
5. Deployment disaster
6. All scraper sources failing
7. Legal/ToS compliance issue
```

---

## SUCCESS CRITERIA (Project Level)

### Go-Live Success:
- ✅ Deals service deployed to production
- ✅ Website scrapers running on 6+ sources
- ✅ Zero impact on main product error rate
- ✅ Zero impact on main product latency
- ✅ Users can see credit card deals on accounts page
- ✅ Deals service 99.9% availability
- ✅ Scraper success rate > 90% per source
- ✅ All tests passing (80%+ coverage)
- ✅ On schedule (6 weeks)
- ✅ Within budget

### Post-Launch Success (1 month):
- ✅ 30%+ of users viewing deals
- ✅ 10%+ click-through rate on deals
- ✅ Positive user feedback (4+/5 rating)
- ✅ Main product still stable
- ✅ Deals data fresh (scraped < 6 hours old)
- ✅ Scraper health stable (> 90% success rate)
- ✅ No production incidents
- ✅ Cost within projections

---

**Document Status**: Active - Updated 2025-11-09
**Next Review**: Weekly (Fridays)
**Supervisor Agent**: Autonomous Credit Card Deals Project Manager
