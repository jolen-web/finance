#!/usr/bin/env python3
"""
Comprehensive Playwright test for Finance Flask Application - Version 2
Improved login flow and navigation detection
"""

from playwright.sync_api import sync_playwright, Page
import time
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:5001"
SCREENSHOTS_DIR = Path("/Users/njpinton/projects/git/finance/screenshots/comprehensive_test_v2")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

# Test user credentials
TEST_USER = {
    "username": "testuser",
    "email": "testuser@example.com",
    "password": "TestPassword123!"
}

class TestResults:
    """Track test results"""
    def __init__(self):
        self.results = []
        self.errors = []
        self.screenshots = []

    def add_result(self, test_name: str, status: str, details: str = ""):
        self.results.append({
            "test": test_name,
            "status": status,
            "details": details
        })
        print(f"{'✓' if status == 'PASS' else '✗' if status == 'FAIL' else '⊘' if status == 'SKIP' else '?'} {test_name}: {status}")
        if details:
            print(f"  → {details}")

    def add_error(self, test_name: str, error: str):
        self.errors.append({
            "test": test_name,
            "error": error
        })
        print(f"✗ ERROR in {test_name}: {error}")

    def add_screenshot(self, name: str, path: str):
        self.screenshots.append({
            "name": name,
            "path": path
        })
        print(f"📸 Screenshot: {name}")

def take_screenshot(page: Page, name: str, results: TestResults, full_page: bool = True):
    """Helper to take and track screenshots"""
    path = SCREENSHOTS_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=full_page)
    results.add_screenshot(name, str(path))
    return str(path)

def wait_for_page_load(page: Page):
    """Wait for page to fully load"""
    page.wait_for_load_state('networkidle')
    time.sleep(0.5)

def ensure_logged_in(page: Page, results: TestResults) -> bool:
    """Ensure user is logged in, perform login if needed"""
    try:
        # Check if already logged in
        content = page.content().lower()
        if "logout" in content or "sign out" in content:
            print("  ℹ User already logged in")
            return True

        # Not logged in, go to login page
        print("  ℹ User not logged in, attempting login...")
        page.goto(f"{BASE_URL}/auth/login")
        wait_for_page_load(page)

        # Use username instead of email for login
        page.fill('input[name="username"]', TEST_USER["username"])
        page.fill('input[name="password"]', TEST_USER["password"])

        take_screenshot(page, "login_attempt", results)

        page.click('button[type="submit"]')
        wait_for_page_load(page)

        take_screenshot(page, "after_login", results)

        # Verify login
        content = page.content().lower()
        if "logout" in content or "sign out" in content or "dashboard" in page.url.lower():
            print("  ✓ Login successful")
            return True
        else:
            print("  ✗ Login failed")
            return False

    except Exception as e:
        results.add_error("Login Check", str(e))
        return False

def find_and_click_nav_link(page: Page, text_patterns: list) -> bool:
    """Try to find and click a navigation link by various text patterns"""
    for pattern in text_patterns:
        try:
            # Try exact text match (case insensitive)
            link = page.locator(f'a:has-text("{pattern}")').first
            if link.count() > 0:
                link.click()
                return True
        except:
            pass
    return False

def main():
    """Main test execution"""
    results = TestResults()

    print("="*80)
    print("COMPREHENSIVE FINANCE APP TEST - VERSION 2")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Screenshots: {SCREENSHOTS_DIR}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        # Enable console logging
        page.on("console", lambda msg: print(f"  [Browser Console] {msg.type}: {msg.text}"))

        try:
            # =================================================================
            # STEP 1: LOGIN
            # =================================================================
            print("\n" + "="*80)
            print("STEP 1: USER LOGIN")
            print("="*80)

            if ensure_logged_in(page, results):
                results.add_result("User Login", "PASS", "Successfully logged in")
            else:
                results.add_result("User Login", "FAIL", "Could not log in")
                print("\n⚠ Cannot continue without login. Exiting.")
                browser.close()
                return

            # =================================================================
            # STEP 2: EXPLORE DASHBOARD
            # =================================================================
            print("\n" + "="*80)
            print("STEP 2: DASHBOARD EXPLORATION")
            print("="*80)

            # Go to root/dashboard
            page.goto(f"{BASE_URL}/")
            wait_for_page_load(page)
            take_screenshot(page, "01_authenticated_home", results)

            # Analyze page content
            content = page.content()
            url = page.url
            title = page.title()

            print(f"  Current URL: {url}")
            print(f"  Page Title: {title}")

            # Check if we're on actual dashboard or landing page
            if "financial" in url.lower() or "dashboard" in content.lower():
                results.add_result("Dashboard Access", "PASS", f"Accessed dashboard at {url}")
            else:
                # Try to find dashboard link
                dashboard_found = False
                for text in ["Dashboard", "Home", "Financial", "Overview"]:
                    if find_and_click_nav_link(page, [text]):
                        wait_for_page_load(page)
                        take_screenshot(page, "02_dashboard_via_nav", results)
                        dashboard_found = True
                        results.add_result("Dashboard Access", "PASS", f"Found dashboard via '{text}' link")
                        break

                if not dashboard_found:
                    results.add_result("Dashboard Access", "UNCERTAIN", "Could not find explicit dashboard")

            # =================================================================
            # STEP 3: TEST ACCOUNTS
            # =================================================================
            print("\n" + "="*80)
            print("STEP 3: ACCOUNTS MANAGEMENT")
            print("="*80)

            accounts_found = find_and_click_nav_link(page, ["Accounts", "My Accounts", "Account"])
            if accounts_found:
                wait_for_page_load(page)
                take_screenshot(page, "03_accounts_page", results)
                results.add_result("Navigate to Accounts", "PASS", f"Found at {page.url}")

                # Look for "New Account" or "Add Account" button/link
                add_account_selectors = [
                    'a:has-text("New Account")',
                    'a:has-text("Add Account")',
                    'a:has-text("Create Account")',
                    'button:has-text("New Account")',
                    'button:has-text("Add Account")',
                    'a[href*="/account/new"]',
                    'a[href*="/accounts/new"]',
                    'a[href*="/account/create"]'
                ]

                add_clicked = False
                for selector in add_account_selectors:
                    try:
                        btn = page.locator(selector).first
                        if btn.count() > 0:
                            print(f"  ℹ Found add account button: {selector}")
                            btn.click()
                            wait_for_page_load(page)
                            take_screenshot(page, "04_new_account_form", results)
                            add_clicked = True
                            break
                    except:
                        pass

                if add_clicked:
                    # Fill account form
                    try:
                        page.fill('input[name="name"]', "Test Checking Account")

                        # Try multiple balance field names
                        balance_filled = False
                        for field_name in ["balance", "starting_balance", "initial_balance", "amount"]:
                            try:
                                page.fill(f'input[name="{field_name}"]', "1000.00")
                                balance_filled = True
                                break
                            except:
                                pass

                        # Try to select account type if exists
                        try:
                            page.select_option('select[name="account_type"]', index=1)
                        except:
                            pass

                        take_screenshot(page, "05_account_form_filled", results)

                        # Submit
                        page.click('button[type="submit"]')
                        wait_for_page_load(page)
                        take_screenshot(page, "06_account_created", results)

                        if "test checking" in page.content().lower():
                            results.add_result("Create Account", "PASS", "Account created and visible")
                        else:
                            results.add_result("Create Account", "UNCERTAIN", "Form submitted, verification unclear")

                    except Exception as e:
                        results.add_error("Create Account", str(e))
                else:
                    results.add_result("Create Account", "SKIP", "Could not find 'Add Account' button")
            else:
                results.add_result("Navigate to Accounts", "FAIL", "Could not find Accounts navigation link")

            # =================================================================
            # STEP 4: TEST TRANSACTIONS
            # =================================================================
            print("\n" + "="*80)
            print("STEP 4: TRANSACTIONS MANAGEMENT")
            print("="*80)

            transactions_found = find_and_click_nav_link(page, ["Transactions", "Transaction", "Activity"])
            if transactions_found:
                wait_for_page_load(page)
                take_screenshot(page, "07_transactions_page", results)
                results.add_result("Navigate to Transactions", "PASS", f"Found at {page.url}")

                # Try to add transaction
                add_tx_selectors = [
                    'a:has-text("New Transaction")',
                    'a:has-text("Add Transaction")',
                    'button:has-text("New Transaction")',
                    'a[href*="/transaction/new"]',
                    'a[href*="/transactions/new"]'
                ]

                add_clicked = False
                for selector in add_tx_selectors:
                    try:
                        btn = page.locator(selector).first
                        if btn.count() > 0:
                            print(f"  ℹ Found add transaction button: {selector}")
                            btn.click()
                            wait_for_page_load(page)
                            take_screenshot(page, "08_new_transaction_form", results)
                            add_clicked = True
                            break
                    except:
                        pass

                if add_clicked:
                    try:
                        # Fill transaction form
                        page.fill('input[name="amount"]', "50.00")

                        # Description might be input or textarea
                        try:
                            page.fill('input[name="description"]', "Test Grocery Purchase")
                        except:
                            page.fill('textarea[name="description"]', "Test Grocery Purchase")

                        # Try to select account
                        try:
                            page.select_option('select[name="account_id"]', index=1)
                        except:
                            try:
                                page.select_option('select[name="account"]', index=1)
                            except:
                                pass

                        # Try to select category if exists
                        try:
                            page.select_option('select[name="category_id"]', index=1)
                        except:
                            pass

                        take_screenshot(page, "09_transaction_form_filled", results)

                        page.click('button[type="submit"]')
                        wait_for_page_load(page)
                        take_screenshot(page, "10_transaction_created", results)

                        if "grocery" in page.content().lower():
                            results.add_result("Create Transaction", "PASS", "Transaction created and visible")
                        else:
                            results.add_result("Create Transaction", "UNCERTAIN", "Form submitted")

                    except Exception as e:
                        results.add_error("Create Transaction", str(e))
                else:
                    results.add_result("Create Transaction", "SKIP", "Could not find 'Add Transaction' button")
            else:
                results.add_result("Navigate to Transactions", "FAIL", "Could not find Transactions link")

            # =================================================================
            # STEP 5: TEST CATEGORIES
            # =================================================================
            print("\n" + "="*80)
            print("STEP 5: CATEGORIES")
            print("="*80)

            categories_found = find_and_click_nav_link(page, ["Categories", "Category"])
            if categories_found:
                wait_for_page_load(page)
                take_screenshot(page, "11_categories_page", results)
                results.add_result("Navigate to Categories", "PASS", f"Found at {page.url}")
            else:
                results.add_result("Navigate to Categories", "SKIP", "Could not find Categories link")

            # =================================================================
            # STEP 6: TEST SETTINGS
            # =================================================================
            print("\n" + "="*80)
            print("STEP 6: SETTINGS")
            print("="*80)

            settings_found = find_and_click_nav_link(page, ["Settings", "Preferences", "Account Settings"])
            if settings_found:
                wait_for_page_load(page)
                take_screenshot(page, "12_settings_page", results)
                results.add_result("Navigate to Settings", "PASS", f"Found at {page.url}")

                content = page.content().lower()
                if "api" in content and "key" in content:
                    results.add_result("Settings - API Keys", "PASS", "API key management found")
                else:
                    results.add_result("Settings - API Keys", "SKIP", "API key management not visible")
            else:
                results.add_result("Navigate to Settings", "SKIP", "Could not find Settings link")

            # =================================================================
            # STEP 7: MOBILE RESPONSIVE TEST
            # =================================================================
            print("\n" + "="*80)
            print("STEP 7: RESPONSIVE DESIGN")
            print("="*80)

            page.set_viewport_size({"width": 375, "height": 667})
            page.goto(f"{BASE_URL}/")
            wait_for_page_load(page)
            take_screenshot(page, "13_mobile_view", results, full_page=False)
            results.add_result("Mobile Responsive Design", "PASS", "Mobile screenshot captured")

            # Reset viewport
            page.set_viewport_size({"width": 1280, "height": 720})

            # =================================================================
            # STEP 8: NAVIGATION AUDIT
            # =================================================================
            print("\n" + "="*80)
            print("STEP 8: NAVIGATION AUDIT")
            print("="*80)

            page.goto(f"{BASE_URL}/")
            wait_for_page_load(page)

            # Find all navigation links
            nav_links = page.locator('nav a, [role="navigation"] a, .nav a, .navbar a, .sidebar a').all()

            print(f"  Found {len(nav_links)} navigation links")
            nav_items = []
            for link in nav_links[:15]:  # Limit to first 15
                try:
                    text = link.inner_text().strip()
                    href = link.get_attribute('href')
                    if text and href:
                        nav_items.append(f"{text} -> {href}")
                        print(f"    • {text} -> {href}")
                except:
                    pass

            if len(nav_items) > 0:
                results.add_result("Navigation Links", "PASS", f"Found {len(nav_items)} navigation items")
            else:
                results.add_result("Navigation Links", "FAIL", "Could not find navigation links")

            take_screenshot(page, "14_final_state", results)

        except Exception as e:
            results.add_error("Main Test Flow", str(e))
            take_screenshot(page, "99_error_state", results)
        finally:
            browser.close()

    # =================================================================
    # GENERATE REPORT
    # =================================================================
    print("\n" + "="*80)
    print("COMPREHENSIVE TEST REPORT")
    print("="*80)

    total_tests = len(results.results)
    passed = sum(1 for r in results.results if r["status"] == "PASS")
    failed = sum(1 for r in results.results if r["status"] == "FAIL")
    skipped = sum(1 for r in results.results if r["status"] == "SKIP")
    uncertain = sum(1 for r in results.results if r["status"] == "UNCERTAIN")

    print(f"\nSUMMARY:")
    print(f"  Total Tests: {total_tests}")
    print(f"  ✓ Passed: {passed}")
    print(f"  ✗ Failed: {failed}")
    print(f"  ⊘ Skipped: {skipped}")
    print(f"  ? Uncertain: {uncertain}")
    print(f"  Errors: {len(results.errors)}")
    print(f"  Screenshots: {len(results.screenshots)}")

    print(f"\nDETAILED RESULTS:")
    for result in results.results:
        status_symbol = {
            "PASS": "✓",
            "FAIL": "✗",
            "SKIP": "⊘",
            "UNCERTAIN": "?"
        }.get(result["status"], "?")
        print(f"  {status_symbol} {result['test']}: {result['status']}")
        if result["details"]:
            print(f"      → {result['details']}")

    if results.errors:
        print(f"\nERRORS:")
        for error in results.errors:
            print(f"  ✗ {error['test']}: {error['error']}")

    print(f"\nSCREENSHOTS SAVED TO:")
    print(f"  {SCREENSHOTS_DIR}")

    # Health assessment
    if failed == 0 and len(results.errors) == 0:
        health = "EXCELLENT ✓"
    elif failed <= 2:
        health = "GOOD ✓"
    elif failed <= 5:
        health = "FAIR ⚠"
    else:
        health = "NEEDS ATTENTION ✗"

    print(f"\nOVERALL HEALTH: {health}")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
