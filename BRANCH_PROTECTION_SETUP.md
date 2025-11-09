# Branch Protection Rules Setup

**Status**: Manual setup required in GitHub UI
**For**: Credit Card Deals Service Project

---

## Overview

Branch protection rules prevent accidental merges and enforce code quality. These need to be configured manually in the GitHub repository settings.

---

## Rules for `master` (Production)

### Location in GitHub
Settings → Branches → Add rule → Pattern: `master`

### Configuration

- ✅ **Require pull request reviews before merging**
  - Number of approving reviews: `1`
  - Dismiss stale pull request approvals when new commits are pushed: `Yes`
  - Require review from Code Owners: `No` (unless CODEOWNERS file exists)

- ✅ **Require status checks to pass before merging**
  - Require branches to be up to date before merging: `Yes`
  - Status checks to require: (select all)
    - `build` (if exists)
    - `tests` (if exists)
    - `coverage` (if exists)

- ✅ **Require conversation resolution before merging**: `Yes`

- ✅ **Require signed commits**: `No` (optional, can enable later)

- ✅ **Require deployments to succeed before merging**: `No` (optional)

- ✅ **Restrict who can push to matching branches**: `No`

- ✅ **Allow force pushes**: `No`
  - Who can force push: N/A (disabled)

- ✅ **Allow deletions**: `No`

---

## Rules for `feature/credit-card-deals` (Development)

### Location in GitHub
Settings → Branches → Add rule → Pattern: `feature/credit-card-deals`

### Configuration

- ✅ **Require pull request reviews before merging**
  - Number of approving reviews: `1`
  - Dismiss stale reviews: `Yes`

- ✅ **Require status checks to pass before merging**
  - Require branches to be up to date: `No` (develop faster)
  - Status checks to require: (select key ones)
    - `tests` (required)
    - `lint` (optional)

- ✅ **Require conversation resolution before merging**: `No` (optional)

- ✅ **Require signed commits**: `No`

- ✅ **Allow force pushes**: `Yes`
  - Who can force push: `Maintainers`

- ✅ **Allow deletions**: `Yes` (so team can clean up sub-branches)

---

## How to Set Up in GitHub UI

### Step 1: Go to Repository Settings
1. Navigate to your repository on GitHub
2. Click **Settings** (top menu)
3. Click **Branches** (left sidebar)

### Step 2: Add Rule for `master`
1. Click **Add rule**
2. Branch name pattern: `master`
3. Configure as shown above
4. Click **Create**

### Step 3: Add Rule for `feature/credit-card-deals`
1. Click **Add rule**
2. Branch name pattern: `feature/credit-card-deals`
3. Configure as shown above
4. Click **Create**

### Step 4: Verify Rules
- Both rules should be listed under "Branch protection rules"
- Verify all settings match the configuration above

---

## CLI Alternative (if preferred)

Using GitHub CLI (`gh`), you can set some rules programmatically:

```bash
# Require pull request reviews for master
gh repo edit \
  --add-topic "deals-service" \
  --update-field "description:Finance Tracker with Credit Card Deals"

# Note: Full branch protection still requires UI or API
# This is a partial example - GitHub doesn't have full CLI support for branch rules yet
```

**Recommendation**: Use GitHub UI for now, as it's more reliable.

---

## Verification Checklist

After setting up rules, verify:

- ✅ Cannot push directly to `master` (PR required)
- ✅ Cannot merge PR to `master` without approval
- ✅ Cannot delete `master` branch
- ✅ Cannot force-push to `master`
- ✅ Can push to `feature/credit-card-deals` (develop faster)
- ✅ Can force-push to `feature/credit-card-deals` (if needed)
- ✅ Can delete `feature/credit-card-deals` (cleanup)

---

## Testing Protection Rules

### Test 1: Verify `master` is Protected
```bash
# Try to push directly to master (should fail)
git checkout master
echo "test" >> README.md
git add README.md
git commit -m "test"
git push origin master

# Expected: Push rejected
# Error: "You can't push to this repository..."
```

### Test 2: Verify PR Required
```bash
# Create branch and PR instead (should work)
git checkout -b test-branch
git push origin test-branch

# Create PR on GitHub UI
# Cannot merge without approval
```

---

## Next Steps

1. **Manual Setup** (5 minutes):
   - Go to GitHub repository settings
   - Add branch protection rules as documented above
   - Verify rules are active

2. **Notify Team** (optional):
   - Let team know master is now protected
   - Explain that all changes require PR + review

3. **Create CODEOWNERS** (optional, advanced):
   If you want automatic reviewers:
   ```
   # CODEOWNERS file
   * @your-github-username
   /services/deals/ @deals-team-username
   ```

---

## Troubleshooting

### "I can't merge my PR"
- Check if you have 1 approval from someone else
- Check if all status checks pass
- Check if branch is up to date with master

### "I need to force-push to master"
- Don't. Create a new PR instead.
- Force-pushing to master is disabled by design.
- If you really need to, remove protection temporarily (not recommended).

### "I deleted the feature branch by accident"
- Can recover from GitHub: Settings → Branches → Recover deleted branch
- Or: Force-push your local copy back to remote

---

## Rules Summary Table

| Rule | master | feature/credit-card-deals |
|------|--------|-------------------------|
| Require PR review | ✓ (1 approval) | ✓ (1 approval) |
| Require status checks | ✓ | ✓ (less strict) |
| Status checks up to date | ✓ | ✗ (develop faster) |
| Allow force push | ✗ | ✓ (for maintainers) |
| Allow deletions | ✗ | ✓ (cleanup sub-branches) |
| Require signed commits | ✗ | ✗ |

---

**Status**: Awaiting manual GitHub UI configuration
**Estimated Time**: 5-10 minutes
**Required Permission**: Repository admin access
**Last Updated**: 2025-11-09
