# Git Workflow for Credit Card Deals Service

**Project**: Credit Card Deals Service Integration
**Duration**: 6 weeks (Weeks 1-6 of development)
**Start Date**: 2025-11-09

---

## Branch Structure

```
master (production - protected)
  ↓ (merges at Phase 7 only)

feature/credit-card-deals (development - main feature branch)
  ├─ feature/deals-scrapers (website scraper implementation)
  ├─ feature/deals-ui (deals widget and routes)
  ├─ feature/deals-api (external API integration)
  └─ feature/deals-caching (Redis caching layer)
```

---

## Branches Overview

### `master` (Production)
- **Status**: Protected branch
- **Purpose**: Production code only
- **When to merge**: Phase 7 (Canary Deployment - after team approval)
- **Requirements**:
  - ✓ All tests passing (80%+ coverage)
  - ✓ Security review completed
  - ✓ Code review approved (1+ approvers)
  - ✓ Staging deployment successful
  - ✓ Canary testing passed

### `feature/credit-card-deals` (Development)
- **Status**: Main development branch
- **Purpose**: Integrate all deals service components
- **When created**: Phase 0 (2025-11-09)
- **When merged to master**: Phase 7 (week 5-6)
- **Requirements**:
  - ✓ Code review: 1 approval
  - ✓ CI/CD tests: Passing
  - ✓ Can be deployed to staging independently
- **Who uses it**: All team members (team lead as primary)

### `feature/deals-scrapers` (Website Scrapers)
- **Status**: Sub-branch for parallel development
- **Purpose**: Implement 6 website scrapers
- **Scrapers**:
  1. Chase credit cards
  2. American Express
  3. Capital One
  4. Discover
  5. Bankrate
  6. Credit Karma
- **When merged**: Phase 2 completion → `feature/credit-card-deals`
- **Who uses it**: Backend scraper specialist

### `feature/deals-ui` (User Interface)
- **Status**: Sub-branch for UI development
- **Purpose**: Deals widget, routes, templates
- **Components**:
  - Deals widget HTML/CSS/JS
  - Deals routes in Flask
  - Feature flag integration
  - Mobile responsive design
- **When merged**: Phase 4 completion → `feature/credit-card-deals`
- **Who uses it**: Frontend/Full-stack engineer

### `feature/deals-api` (API Integration)
- **Status**: Sub-branch for API work
- **Purpose**: External API clients (Rakuten, etc)
- **Components**:
  - Rakuten API client
  - Error handling
  - Rate limiting
  - Retry logic
- **When merged**: Phase 3 completion → `feature/credit-card-deals`
- **Who uses it**: Integration specialist

### `feature/deals-caching` (Caching Layer)
- **Status**: Sub-branch for caching
- **Purpose**: Redis integration and caching logic
- **Components**:
  - Redis connection setup
  - Cache decorators
  - TTL management
  - Cache invalidation
- **When merged**: Phase 3 completion → `feature/credit-card-deals`
- **Who uses it**: Backend engineer (caching specialist)

---

## Workflow: Week by Week

### Week 1: Phase 0 (Pre-Development)
```bash
# Create main branch (DONE)
git checkout -b feature/credit-card-deals

# Create sub-branches (DONE)
git branch feature/deals-scrapers
git branch feature/deals-ui
git branch feature/deals-api
git branch feature/deals-caching

# Team members branch off for their work
git checkout feature/deals-scrapers
# OR
git checkout feature/deals-ui
```

---

### Week 2-3: Phase 2 (Scraper Implementation)

**Scraper team workflow**:
```bash
# Start work on scrapers
git checkout feature/deals-scrapers

# Create local branches for individual scrapers
git branch local/chase-scraper
git branch local/amex-scraper
# ... etc for all 6

# Work and commit
git add app/scrapers/chase_scraper.py
git commit -m "feat: Implement Chase website scraper"

# Push and create PR
git push origin feature/deals-scrapers
# Create PR: feature/deals-scrapers → feature/credit-card-deals
```

**When complete**:
```bash
# Merge scrapers to main feature branch
# (via PR review, not direct merge)
```

---

### Week 3-4: Phase 3 (API Integration)

**API team workflow**:
```bash
# Work on API clients
git checkout feature/deals-api

# Implement API client
git add app/api_clients/rakuten_api.py
git commit -m "feat: Add Rakuten API client with error handling"

# Push and create PR
git push origin feature/deals-api
# Create PR: feature/deals-api → feature/credit-card-deals
```

**Caching team workflow**:
```bash
# Work on Redis caching
git checkout feature/deals-caching

# Implement caching layer
git add app/cache/redis_cache.py
git commit -m "feat: Implement Redis caching with TTL management"

# Push and create PR
git push origin feature/deals-caching
# Create PR: feature/deals-caching → feature/credit-card-deals
```

---

### Week 4: Phase 4 (UI Integration)

**UI team workflow**:
```bash
# Work on deals widget
git checkout feature/deals-ui

# Create widget
git add app/templates/deals/
git add app/routes/deals.py
git commit -m "feat: Add deals widget and integration routes"

# Push and create PR
git push origin feature/deals-ui
# Create PR: feature/deals-ui → feature/credit-card-deals
```

---

### Week 4-5: Phase 5 (Testing & QA)

**All branches merged to `feature/credit-card-deals`**:
```bash
# Everyone's work is now in main feature branch
git checkout feature/credit-card-deals
git log --oneline | head -20

# Staging deployment tests against feature/credit-card-deals
```

---

### Week 5-6: Phase 6-7 (Staging → Canary → Production)

```bash
# When ready for production
git checkout master
git pull origin master

# Merge feature branch to master
git merge feature/credit-card-deals

# Create release tag
git tag v1.0.0-deals-service

# Push to production
git push origin master
git push origin v1.0.0-deals-service
```

---

## Git Commands Reference

### Create and Switch to Branch
```bash
# Create branch
git branch feature/deals-scrapers

# Switch to branch
git checkout feature/deals-scrapers

# Or create and switch in one command
git checkout -b feature/deals-scrapers
```

### Check Current Branch
```bash
git branch --show-current
```

### See All Branches
```bash
git branch -a
```

### Push Branch to Remote
```bash
git push origin feature/deals-scrapers
```

### Create Pull Request
```bash
# After pushing branch
gh pr create --title "feat: Implement Chase scraper" \
  --body "Implements Chase website scraper with proxy rotation"
```

### Merge Branch (via PR - preferred)
```bash
# After PR review and approval
gh pr merge feature/deals-scrapers --merge
```

### Merge Branch (local)
```bash
# If merging locally (not recommended, use PR instead)
git checkout feature/credit-card-deals
git merge feature/deals-scrapers
```

---

## Commit Message Convention

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring
- `test`: Adding tests
- `docs`: Documentation
- `style`: Code style changes
- `perf`: Performance improvements
- `chore`: Build, dependency updates

### Scope
- `deals-scraper`: Website scraper changes
- `deals-ui`: UI/widget changes
- `deals-api`: API integration changes
- `deals-cache`: Caching changes

### Examples
```bash
git commit -m "feat(deals-scraper): Implement Chase website scraper with proxy rotation"
git commit -m "feat(deals-cache): Add Redis caching layer with TTL management"
git commit -m "test(deals-scraper): Add unit tests for scraper data extraction"
git commit -m "fix(deals-api): Handle Rakuten API timeouts gracefully"
```

---

## Pull Request Process

### 1. Create Branch
```bash
git checkout -b feature/deals-scrapers
```

### 2. Make Changes
```bash
git add app/scrapers/
git commit -m "feat: Implement scrapers"
```

### 3. Push to Remote
```bash
git push origin feature/deals-scrapers
```

### 4. Create Pull Request
```bash
gh pr create \
  --title "feat: Implement website scrapers" \
  --body "Implements 6 website scrapers for credit card deals

- Chase scraper
- Amex scraper
- Capital One scraper
- Discover scraper
- Bankrate scraper
- Credit Karma scraper

All with proxy rotation and error handling."
```

### 5. Wait for Review
- Code review: 1+ approval required
- CI/CD: All tests must pass
- No conflicts with target branch

### 6. Merge
```bash
# Via GitHub PR UI or
gh pr merge <pr-number> --merge
```

---

## Branch Protection Rules

### For `master` (Production)
```
✓ Require pull request reviews before merging (1 approval)
✓ Dismiss stale pull request approvals when new commits are pushed
✓ Require status checks to pass before merging
✓ Require branches to be up to date before merging
✓ Require code review from code owners (if applicable)
✓ Block force pushes
✓ Block deletions
```

### For `feature/credit-card-deals` (Development)
```
✓ Require pull request reviews (1 approval - less strict)
✓ Require status checks to pass
✓ Allow direct pushes (for speed during development)
✓ Allow force pushes (be careful!)
✓ Do not require up-to-date branches (develop faster)
```

---

## Team Assignments by Phase

| Phase | Branch | Owner | Other Team |
|-------|--------|-------|-----------|
| Phase 0 | feature/credit-card-deals | Team Lead | - |
| Phase 1 | feature/credit-card-deals | Senior Backend | QA |
| Phase 2 | feature/deals-scrapers | Scraper Dev | Team Lead (review) |
| Phase 3 | feature/deals-api, feature/deals-caching | Backend Dev | Team Lead (review) |
| Phase 4 | feature/deals-ui | Frontend Dev | QA (testing) |
| Phase 5 | feature/credit-card-deals | QA Lead | All (testing) |
| Phase 6-7 | feature/credit-card-deals → master | DevOps | All (monitoring) |

---

## Common Scenarios

### Scenario 1: Fix Bug in Scraper
```bash
# You're on feature/deals-scrapers
git commit -m "fix(deals-scraper): Handle Chase rate limiting"
git push origin feature/deals-scrapers

# Create/update PR with the fix
# Other developers can see it immediately
```

### Scenario 2: Merge Sub-Branch to Main
```bash
# Scraper team finished Phase 2
git checkout feature/credit-card-deals
git pull origin feature/credit-card-deals

# Create PR for review
git push origin feature/credit-card-deals

# After approval, merge via PR
```

### Scenario 3: Rebase to Get Latest Changes
```bash
# You're on feature/deals-ui
# Main feature branch got updates
git fetch origin
git rebase origin/feature/credit-card-deals

# Resolve any conflicts
git add <resolved-files>
git rebase --continue

# Force push to update PR
git push origin feature/deals-ui --force-with-lease
```

### Scenario 4: Prepare for Production Release
```bash
# All sub-branches merged to feature/credit-card-deals
# Ready to release to production

git checkout master
git pull origin master

git merge feature/credit-card-deals
git tag v1.0.0-deals-service

git push origin master
git push origin v1.0.0-deals-service

# Deploy to production
```

---

## Troubleshooting

### I'm on the wrong branch
```bash
git branch --show-current  # See where you are
git checkout feature/deals-scrapers  # Switch to correct branch
```

### I committed to the wrong branch
```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Switch to correct branch
git checkout feature/deals-scrapers

# Commit again
git commit -m "message"
```

### I need to sync my branch with latest changes
```bash
git fetch origin
git rebase origin/feature/credit-card-deals
git push origin feature/deals-scrapers --force-with-lease
```

### I want to see what's different between branches
```bash
git diff feature/credit-card-deals..feature/deals-scrapers
```

### I need to delete a local branch
```bash
git branch -d feature/deals-old  # Delete local
git push origin --delete feature/deals-old  # Delete remote
```

---

## Best Practices

✅ **DO**:
- Create PR before merging branches
- Write clear commit messages
- Keep branches focused on one feature
- Review code before merging
- Test on branch before PR
- Rebase to keep history clean
- Use `--force-with-lease` instead of `--force`

❌ **DON'T**:
- Commit directly to master
- Merge without review
- Push work-in-progress to main branch
- Use `--force` (use `--force-with-lease` instead)
- Commit large binary files
- Commit secrets or credentials

---

## Resources

- **GitHub Docs**: https://docs.github.com/en/get-started/using-git
- **Git Cheat Sheet**: https://github.github.com/training-kit/
- **Claude Code Docs**: https://docs.claude.com/en/docs/claude-code/
- **Project Plan**: See `DEALS_PROJECT_SUPERVISOR.md`

---

**Last Updated**: 2025-11-09
**Status**: Active
**Next Review**: Weekly (Fridays)
