# Finance Tracker - Project Restructuring Plan

**Version:** 1.0
**Date:** November 2025
**Status:** In Progress

---

## Table of Contents
1. [Current State Analysis](#current-state-analysis)
2. [Phase 1: Models Restructuring](#phase-1-models-restructuring)
3. [Phase 2: Services Layer Expansion](#phase-2-services-layer-expansion)
4. [Phase 3: Routes Reorganization](#phase-3-routes-reorganization)
5. [Phase 4: Templates Restructuring](#phase-4-templates-restructuring)
6. [Phase 5: Test Suite Structure](#phase-5-test-suite-structure)
7. [Implementation Strategy](#implementation-strategy)
8. [Migration Checklist](#migration-checklist)

---

## Current State Analysis

### Problems with Current Structure

1. **Monolithic models.py** (500+ lines)
   - All database models in single file
   - Difficult to locate specific models
   - Creates import complexity
   - Makes collaboration harder

2. **Thin Services Layer**
   - Only 6 service files
   - Business logic mixed with routes
   - Limited reusability
   - Hard to test independently

3. **Many Single-Purpose Route Files**
   - 23 route files (some handling just 1-2 endpoints)
   - Related features scattered across files
   - High cognitive load for developers
   - Harder to see feature relationships

4. **Flat Template Structure**
   - All templates in one directory
   - ~80+ template files
   - No clear organization by feature
   - Hard to find related templates

5. **Minimal Test Structure**
   - Few test files
   - No clear test organization
   - Low test coverage
   - No clear testing patterns

### Current Directory Structure
```
app/
├── routes/          (23 files)
├── services/        (6 files)
├── templates/       (80+ files, all at root level)
├── static/          (CSS, JS, images)
├── seeds/           (initialization scripts)
├── models.py        (monolithic, 500+ lines)
└── ...
```

---

## Phase 1: Models Restructuring

### Target Structure
```
app/models/
├── __init__.py              # Export all models
├── base.py                  # Base classes, timestamps
├── user.py                  # User, Role, Permission
├── account.py               # Account, AccountType
├── transaction.py           # Transaction, TransactionTag
├── category.py              # Category (parent-child)
├── asset.py                 # Asset, AssetType
├── investment.py            # Investment, InvestmentType
├── receipt.py               # Receipt, ReceiptItem
├── feedback.py              # Feedback, FeedbackCategory
├── regex_pattern.py         # RegexPattern
├── categorization.py        # CategorizationRule
├── financial.py             # FinancialInsights, TaxTag, ScenarioResult
└── utils.py                 # Model utilities, validators
```

### Implementation Steps

1. **Create base.py** - Common functionality
   ```python
   from datetime import datetime
   from app import db

   class TimestampMixin:
       created_at = db.Column(db.DateTime, default=datetime.utcnow)
       updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

   class BaseModel(db.Model):
       __abstract__ = True
       id = db.Column(db.Integer, primary_key=True)
   ```

2. **Extract each model file** - Move related models
   - Extract User → user.py
   - Extract Account, AccountType → account.py
   - Extract Transaction, TransactionTag → transaction.py
   - Continue for all models

3. **Update __init__.py** - Central exports
   ```python
   from app.models.user import User, Role, Permission
   from app.models.account import Account, AccountType
   # ... export all models
   ```

4. **Update imports** - Throughout codebase
   - Old: `from app.models import User`
   - New: `from app.models.user import User`

### Benefits
- ✓ Easier to find specific models
- ✓ Clear dependencies between entities
- ✓ Simplified for team collaboration
- ✓ Better for code reviews

### Timeline: 2-3 days

---

## Phase 2: Services Layer Expansion

### Target Structure
```
app/services/
├── __init__.py
├── auth/
│   ├── __init__.py
│   ├── user_service.py          # User CRUD, validation
│   └── auth_service.py           # Login, permissions, JWT
├── financial/
│   ├── __init__.py
│   ├── account_service.py        # Account operations
│   ├── transaction_service.py    # Transaction logic, categorization
│   ├── category_service.py       # Category management
│   └── dashboard_service.py      # Dashboard aggregation
├── assets/
│   ├── __init__.py
│   ├── asset_service.py          # Asset CRUD
│   └── investment_service.py     # Investment tracking, performance
├── ai_tools/
│   ├── __init__.py
│   ├── categorizer_service.py    # AI categorization
│   ├── advisor_service.py        # Financial insights
│   ├── tax_service.py            # Tax assistant
│   └── planner_service.py        # Scenario planning
├── utils/
│   ├── __init__.py
│   ├── receipt_ocr.py            # Gemini OCR (keep as-is)
│   ├── chart_service.py          # Chart generation (move from services)
│   ├── backup_service.py         # Create new - backup/restore
│   ├── validation_service.py     # Create new - validators
│   └── notification_service.py   # Create new - email, alerts
└── exceptions.py                 # Custom service exceptions
```

### Service Pattern Template
```python
# app/services/financial/account_service.py
from app.models.account import Account
from app import db

class AccountService:
    @staticmethod
    def create_account(user_id, name, type, balance):
        """Create new account for user"""
        account = Account(user_id=user_id, name=name, type=type, current_balance=balance)
        db.session.add(account)
        db.session.commit()
        return account

    @staticmethod
    def get_user_accounts(user_id):
        """Get all accounts for user"""
        return Account.query.filter_by(user_id=user_id).all()

    @staticmethod
    def update_balance(account_id, new_balance):
        """Update account balance"""
        account = Account.query.get_or_404(account_id)
        account.current_balance = new_balance
        db.session.commit()
        return account

    @staticmethod
    def calculate_net_worth(user_id):
        """Calculate total net worth"""
        accounts = Account.query.filter_by(user_id=user_id).all()
        return sum(account.current_balance for account in accounts)
```

### Key Services to Create

| Service | Purpose | Methods |
|---------|---------|---------|
| AccountService | Account CRUD | create, read, update, delete, calculate_balance |
| TransactionService | Transaction logic | create, categorize, reconcile, bulk_operations |
| DashboardService | Dashboard data | get_summary, get_charts, get_insights |
| CategoryService | Category mgmt | create, get_hierarchy, suggest_for_transaction |
| BackupService | Data backup | export_data, import_data, schedule_backup |
| ValidationService | Input validation | validate_account, validate_amount, validate_category |

### Benefits
- ✓ Reusable business logic
- ✓ Easy to unit test
- ✓ Thin route handlers (4-8 lines)
- ✓ Clear separation of concerns

### Timeline: 1 week

---

## Phase 3: Routes Reorganization

### Target Structure
```
app/routes/
├── __init__.py                  # Blueprint registration
├── auth.py                      # Auth routes (login, register, logout)
├── financial.py                 # Accounts, transactions, categories
├── assets.py                    # Assets, investments
├── ai.py                        # AI tools (categorizer, advisor, tax, planner)
├── receipts.py                  # Receipt upload, list, detail
├── settings.py                  # User settings, workflows, preferences
├── feedback.py                  # Feedback submission
├── admin.py                     # Backup, diagnostics
└── utils.py                     # Common route helpers
```

### New Route Handler Pattern
```python
# app/routes/financial.py
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app.services.financial.account_service import AccountService
from app.services.financial.transaction_service import TransactionService

bp = Blueprint('financial', __name__, url_prefix='/api')
account_service = AccountService()
transaction_service = TransactionService()

@bp.route('/accounts', methods=['GET'])
@login_required
def list_accounts():
    """Get all accounts for user"""
    accounts = account_service.get_user_accounts(current_user.id)
    return render_template('financial/accounts/list.html', accounts=accounts)

@bp.route('/accounts', methods=['POST'])
@login_required
def create_account():
    """Create new account"""
    data = request.form
    account = account_service.create_account(
        user_id=current_user.id,
        name=data['name'],
        type=data['type'],
        balance=data['balance']
    )
    return redirect(url_for('financial.list_accounts'))
```

### Feature Grouping

| Blueprint | Routes | Purpose |
|-----------|--------|---------|
| auth | /login, /register, /logout | Authentication |
| financial | /accounts, /transactions, /categories | Core financial features |
| assets | /assets, /investments | Asset tracking |
| ai | /categorizer, /advisor, /tax, /planner | AI-powered tools |
| receipts | /receipts, /receipts/<id> | Receipt processing |
| settings | /settings, /workflows | User configuration |
| feedback | /feedback | User feedback |
| admin | /backup, /diagnostics | Admin features |

### Benefits
- ✓ Related features grouped together
- ✓ Clear feature ownership
- ✓ Easier to locate related endpoints
- ✓ Simpler to add new features

### Timeline: 3-4 days

---

## Phase 4: Templates Restructuring

### Target Structure
```
app/templates/
├── base.html                    # Main layout
├── layouts/
│   ├── admin.html              # Admin-specific layout
│   └── auth.html               # Auth layout
├── components/
│   ├── navbar.html
│   ├── sidebar.html
│   ├── breadcrumb.html
│   ├── pagination.html
│   ├── forms/
│   │   ├── account_form.html
│   │   ├── transaction_form.html
│   │   └── category_form.html
│   └── cards/
│       ├── account_card.html
│       ├── transaction_card.html
│       └── investment_card.html
├── auth/
│   ├── login.html
│   ├── register.html
│   └── reset_password.html
├── financial/
│   ├── accounts/
│   │   ├── list.html
│   │   ├── detail.html
│   │   └── form.html
│   ├── transactions/
│   │   ├── list.html
│   │   ├── detail.html
│   │   └── form.html
│   ├── categories/
│   │   ├── list.html
│   │   ├── form.html
│   │   └── tree.html
│   └── dashboard.html
├── assets/
│   ├── list.html
│   ├── detail.html
│   └── form.html
├── investments/
│   ├── list.html
│   ├── detail.html
│   └── form.html
├── ai/
│   ├── categorizer.html
│   ├── advisor.html
│   ├── tax_assistant.html
│   └── scenario_planner.html
├── receipts/
│   ├── upload.html
│   ├── list.html
│   ├── detail.html
│   └── extract.html
├── settings/
│   ├── index.html
│   ├── workflows.html          # Already done!
│   ├── preferences.html
│   ├── account_types.html
│   └── categories.html
├── feedback/
│   ├── form.html
│   └── thank_you.html
├── admin/
│   ├── backup.html
│   └── diagnostics.html
└── errors/
    ├── 400.html
    ├── 403.html
    ├── 404.html
    └── 500.html
```

### Benefits
- ✓ Easy to locate related templates
- ✓ Better component reusability
- ✓ Clearer structure for new developers
- ✓ Simplified maintenance

### Timeline: 2-3 days

---

## Phase 5: Test Suite Structure

### Target Structure
```
tests/
├── conftest.py                          # Pytest fixtures, config
├── test_config.py
├── fixtures/
│   ├── __init__.py
│   ├── users.py                        # Test users
│   ├── accounts.py                     # Test accounts
│   ├── transactions.py                 # Test transactions
│   └── ...
├── unit/
│   ├── services/
│   │   ├── test_account_service.py
│   │   ├── test_transaction_service.py
│   │   ├── test_categorizer_service.py
│   │   └── ...
│   ├── models/
│   │   ├── test_account.py
│   │   ├── test_transaction.py
│   │   └── ...
│   └── utils/
│       ├── test_validators.py
│       └── test_formatters.py
├── integration/
│   ├── test_account_workflow.py        # Full workflows
│   ├── test_transaction_workflow.py
│   ├── test_ai_features.py
│   └── test_backup_workflow.py
├── routes/
│   ├── test_auth_routes.py
│   ├── test_financial_routes.py
│   ├── test_asset_routes.py
│   └── test_ai_routes.py
├── e2e/
│   ├── test_user_journey.py            # End-to-end scenarios
│   └── test_dashboard_workflow.py
└── performance/
    └── test_large_dataset.py           # Load testing
```

### Test Example

```python
# tests/unit/services/test_account_service.py
import pytest
from app.services.financial.account_service import AccountService
from app.models.account import Account

@pytest.fixture
def account_service():
    return AccountService()

@pytest.fixture
def test_user(db):
    from app.models.user import User
    user = User(username='testuser', email='test@test.com')
    db.session.add(user)
    db.session.commit()
    return user

def test_create_account(account_service, test_user, db):
    """Test account creation"""
    account = account_service.create_account(
        user_id=test_user.id,
        name="Checking",
        type="checking",
        balance=1000.00
    )

    assert account.name == "Checking"
    assert account.current_balance == 1000.00
    assert Account.query.count() == 1

def test_calculate_net_worth(account_service, test_user, db):
    """Test net worth calculation"""
    account_service.create_account(test_user.id, "Checking", "checking", 500.00)
    account_service.create_account(test_user.id, "Savings", "savings", 1000.00)

    net_worth = account_service.calculate_net_worth(test_user.id)
    assert net_worth == 1500.00
```

### Test Coverage Goals
- Unit tests: 80% of services
- Integration tests: 60% of workflows
- Route tests: 70% of endpoints
- Overall: 70%+ code coverage

### Timeline: 1 week

---

## Implementation Strategy

### Recommended Approach: Gradual Refactoring

**DO NOT** refactor everything at once. Follow this phased approach:

### Phase Sequence
1. **Phase 1 (Days 1-3):** Models - Foundation
2. **Phase 2 (Days 4-10):** Services - Business Logic
3. **Phase 3 (Days 11-14):** Routes - API Layer
4. **Phase 4 (Days 15-17):** Templates - Views
5. **Phase 5 (Days 18-24):** Tests - Quality Assurance
6. **Final (Days 25-28):** Documentation & Polish

### Key Principles

1. **Update Imports After Each Phase**
   ```bash
   # After moving models, update all imports
   grep -r "from app.models import" app/ | head -20
   ```

2. **Run Tests After Each Change**
   ```bash
   pytest tests/ -v
   ```

3. **Update __init__.py Files**
   ```python
   # app/models/__init__.py
   from app.models.user import User, Role
   from app.models.account import Account, AccountType
   # ... export everything needed
   ```

4. **Maintain Git History**
   - One commit per file/component move
   - Clear commit messages: "refactor: move User model to models/user.py"

### Tools & Scripts

Create helper scripts for migration:

```bash
# scripts/refactor_models.sh - Auto-update imports
# scripts/find_imports.py - Find all import statements
# scripts/test_coverage.py - Check test coverage
```

---

## Migration Checklist

### Phase 1: Models
- [ ] Create app/models/ directory
- [ ] Create app/models/base.py with base classes
- [ ] Extract User model → user.py
- [ ] Extract Account models → account.py
- [ ] Extract Transaction models → transaction.py
- [ ] Extract Category model → category.py
- [ ] Extract Asset models → asset.py
- [ ] Extract Investment models → investment.py
- [ ] Extract Receipt model → receipt.py
- [ ] Extract Feedback model → feedback.py
- [ ] Extract RegexPattern model → regex_pattern.py
- [ ] Extract CategorizationRule → categorization.py
- [ ] Extract FinancialInsights, TaxTag → financial.py
- [ ] Create app/models/__init__.py with all exports
- [ ] Update all imports throughout app/ (routes, services)
- [ ] Run full test suite
- [ ] Verify all features work
- [ ] Update documentation

### Phase 2: Services
- [ ] Create organized app/services/ subdirectories
- [ ] Create auth/ directory and services
- [ ] Create financial/ directory and services
- [ ] Create assets/ directory and services
- [ ] Create ai_tools/ directory and services
- [ ] Create utils/ directory and services
- [ ] Move existing services to new locations
- [ ] Extract business logic from routes into services
- [ ] Update route files to use new services
- [ ] Run full test suite
- [ ] Verify all API endpoints work
- [ ] Update documentation

### Phase 3: Routes
- [ ] Consolidate routes into logical blueprints
- [ ] Create auth.py (auth routes)
- [ ] Create financial.py (accounts, transactions, categories)
- [ ] Create assets.py (assets, investments)
- [ ] Create ai.py (AI tools)
- [ ] Create receipts.py (receipts)
- [ ] Create settings.py (settings)
- [ ] Create feedback.py (feedback)
- [ ] Create admin.py (admin features)
- [ ] Update app/__init__.py to register blueprints
- [ ] Run full test suite
- [ ] Test all endpoints
- [ ] Update API documentation

### Phase 4: Templates
- [ ] Create organized template directories
- [ ] Move auth templates
- [ ] Move financial templates
- [ ] Move asset templates
- [ ] Move AI tool templates
- [ ] Move receipt templates
- [ ] Move settings templates
- [ ] Move feedback templates
- [ ] Move admin templates
- [ ] Update all template paths in routes
- [ ] Test all pages in browser
- [ ] Verify CSS/JS still works
- [ ] Update documentation

### Phase 5: Tests
- [ ] Create tests/ directory structure
- [ ] Create conftest.py with fixtures
- [ ] Write unit tests for services
- [ ] Write unit tests for models
- [ ] Write integration tests for workflows
- [ ] Write route/endpoint tests
- [ ] Achieve 70%+ coverage
- [ ] Document test patterns
- [ ] Set up CI/CD for tests

### Final Steps
- [ ] Update ARCHITECTURE.md
- [ ] Update CONTRIBUTING.md
- [ ] Update README.md with new structure
- [ ] Remove this RESTRUCTURING_PLAN.md (move to docs/)
- [ ] Final full test run
- [ ] Final review of all changes
- [ ] Tag as v2.0.0 in git

---

## Benefits Summary

| Aspect | Before | After |
|--------|--------|-------|
| **Code Organization** | Mixed concerns | Clear separation |
| **Testability** | Hard to test | Easy to test independently |
| **Reusability** | Low | High |
| **Maintainability** | Difficult | Easy |
| **Onboarding** | 2-3 weeks | Few days |
| **Feature Addition** | 2-3 days | Few hours |
| **Bug Fixing** | Hard to locate | Easy to find |
| **Code Reviews** | Large diffs | Focused changes |

---

## Questions & Decisions

### Decision: Use Service Classes or Functions?

**Chosen: Service Classes** ✓

```python
# ✓ Better: Service Classes
class AccountService:
    @staticmethod
    def create_account(...): pass
    @staticmethod
    def get_user_accounts(...): pass

# Routes use it:
accounts = AccountService.get_user_accounts(user_id)
```

**Reason:** Better organization, easier mocking in tests, room for state if needed later.

---

## Status Tracking

| Phase | Status | Start Date | End Date | Notes |
|-------|--------|-----------|----------|-------|
| 1. Models | ⏳ Pending | TBD | TBD | Foundation for other phases |
| 2. Services | ⏳ Pending | TBD | TBD | Enables thin routes |
| 3. Routes | ⏳ Pending | TBD | TBD | Consolidates blueprints |
| 4. Templates | ⏳ Pending | TBD | TBD | Improves organization |
| 5. Tests | ⏳ Pending | TBD | TBD | Quality assurance |

---

## Contact & Questions

For questions about this plan, refer to:
- Architecture decisions: See Phase headers
- Implementation details: See specific sections
- Migration help: See migration checklist

---

**Next Step:** Start Phase 1 - Models Restructuring

