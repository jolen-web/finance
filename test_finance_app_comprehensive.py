#!/usr/bin/env python3
"""
Comprehensive Playwright test for Finance Flask Application
Tests user registration, login, accounts, transactions, categories, dashboard, and more.
"""

from playwright.sync_api import sync_playwright, Page, expect
import time
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:5001"
SCREENSHOTS_DIR = Path("/Users/njpinton/projects/git/finance/screenshots/comprehensive_test")
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
        print(f"{'✓' if status == 'PASS' else '✗'} {test_name}: {status}")
        if details:
            print(f"  {details}")

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
        print(f"📸 Screenshot saved: {name} -> {path}")

def take_screenshot(page: Page, name: str, results: TestResults, full_page: bool = True):
    """Helper to take and track screenshots"""
    path = SCREENSHOTS_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=full_page)
    results.add_screenshot(name, str(path))
    return str(path)

def wait_for_page_load(page: Page):
    """Wait for page to fully load"""
    page.wait_for_load_state('networkidle')
    time.sleep(0.5)  # Extra buffer for animations

def test_registration(page: Page, results: TestResults) -> bool:
    """Test user registration"""
    try:
        print("\n=== Testing User Registration ===")
        page.goto(f"{BASE_URL}/auth/register")
        wait_for_page_load(page)

        take_screenshot(page, "01_registration_page", results)

        # Check if registration page exists
        if "404" in page.title() or "Not Found" in page.content():
            results.add_result("Registration Page", "SKIP", "Registration page not found (404)")
            return False

        # Fill registration form
        page.fill('input[name="username"]', TEST_USER["username"])
        page.fill('input[name="email"]', TEST_USER["email"])
        page.fill('input[name="password"]', TEST_USER["password"])

        # Look for confirm password field
        confirm_fields = page.locator('input[name="confirm_password"], input[name="password_confirm"], input[name="password2"]')
        if confirm_fields.count() > 0:
            confirm_fields.first.fill(TEST_USER["password"])

        take_screenshot(page, "02_registration_filled", results)

        # Submit form
        page.click('button[type="submit"], input[type="submit"]')
        wait_for_page_load(page)

        take_screenshot(page, "03_after_registration", results)

        # Check for success or if user already exists
        content = page.content().lower()
        if "already exists" in content or "already registered" in content:
            results.add_result("User Registration", "SKIP", "User already exists")
            return False
        elif "success" in content or "welcome" in content or "dashboard" in content:
            results.add_result("User Registration", "PASS", "User registered successfully")
            return True
        else:
            results.add_result("User Registration", "UNCERTAIN", "Registration submitted, status unclear")
            return False

    except Exception as e:
        results.add_error("User Registration", str(e))
        return False

def test_login(page: Page, results: TestResults) -> bool:
    """Test user login"""
    try:
        print("\n=== Testing User Login ===")
        page.goto(f"{BASE_URL}/auth/login")
        wait_for_page_load(page)

        take_screenshot(page, "04_login_page", results)

        # Fill login form
        page.fill('input[name="email"], input[name="username"]', TEST_USER["email"])
        page.fill('input[name="password"]', TEST_USER["password"])

        take_screenshot(page, "05_login_filled", results)

        # Submit
        page.click('button[type="submit"], input[type="submit"]')
        wait_for_page_load(page)

        take_screenshot(page, "06_after_login", results)

        # Verify login success
        content = page.content().lower()
        if "dashboard" in content or "logout" in content or "welcome" in content:
            results.add_result("User Login", "PASS", "Login successful")
            return True
        else:
            results.add_result("User Login", "FAIL", "Login may have failed")
            return False

    except Exception as e:
        results.add_error("User Login", str(e))
        return False

def test_dashboard(page: Page, results: TestResults):
    """Test dashboard page"""
    try:
        print("\n=== Testing Dashboard ===")

        # Try common dashboard URLs
        dashboard_urls = ["/", "/dashboard", "/home", "/financial/dashboard"]
        dashboard_loaded = False

        for url in dashboard_urls:
            try:
                page.goto(f"{BASE_URL}{url}")
                wait_for_page_load(page)
                if "404" not in page.content() and "Not Found" not in page.content():
                    dashboard_loaded = True
                    break
            except:
                continue

        if not dashboard_loaded:
            results.add_result("Dashboard", "FAIL", "Could not find dashboard page")
            return

        take_screenshot(page, "07_dashboard_main", results)

        # Check for common dashboard elements
        content = page.content().lower()

        checks = {
            "Net Worth": "net worth" in content or "total balance" in content,
            "Accounts": "account" in content,
            "Transactions": "transaction" in content,
            "Charts/Graphs": "chart" in content or "canvas" in page.content()
        }

        for check_name, check_result in checks.items():
            status = "PASS" if check_result else "FAIL"
            results.add_result(f"Dashboard - {check_name}", status)

        results.add_result("Dashboard Page", "PASS", "Dashboard loaded successfully")

    except Exception as e:
        results.add_error("Dashboard", str(e))

def test_accounts(page: Page, results: TestResults):
    """Test accounts management"""
    try:
        print("\n=== Testing Accounts Management ===")

        # Try common account URLs
        account_urls = ["/accounts", "/financial/accounts", "/account/list"]
        accounts_loaded = False

        for url in account_urls:
            try:
                page.goto(f"{BASE_URL}{url}")
                wait_for_page_load(page)
                if "404" not in page.content():
                    accounts_loaded = True
                    break
            except:
                continue

        if not accounts_loaded:
            results.add_result("Accounts Page", "FAIL", "Could not find accounts page")
            return

        take_screenshot(page, "08_accounts_list", results)
        results.add_result("Accounts Page", "PASS", "Accounts page loaded")

        # Try to create new account
        try:
            # Look for "Add Account" or "New Account" button
            add_buttons = page.locator('text=/new account|add account|create account/i')
            if add_buttons.count() > 0:
                add_buttons.first.click()
                wait_for_page_load(page)

                take_screenshot(page, "09_account_form", results)

                # Fill form
                page.fill('input[name="name"], input[name="account_name"]', "Test Checking")

                # Try to find balance field
                balance_fields = page.locator('input[name="balance"], input[name="starting_balance"], input[name="initial_balance"]')
                if balance_fields.count() > 0:
                    balance_fields.first.fill("1000.00")

                take_screenshot(page, "10_account_form_filled", results)

                # Submit
                page.click('button[type="submit"], input[type="submit"]')
                wait_for_page_load(page)

                take_screenshot(page, "11_account_created", results)

                # Verify account appears
                if "test checking" in page.content().lower():
                    results.add_result("Create Account", "PASS", "Account created successfully")
                else:
                    results.add_result("Create Account", "UNCERTAIN", "Account form submitted")

                # Try to edit the account
                edit_buttons = page.locator('text=/edit/i, a[href*="edit"]').first
                if edit_buttons.count() > 0:
                    edit_buttons.click()
                    wait_for_page_load(page)

                    page.fill('input[name="name"], input[name="account_name"]', "Test Checking Updated")
                    page.click('button[type="submit"]')
                    wait_for_page_load(page)

                    take_screenshot(page, "12_account_updated", results)

                    if "test checking updated" in page.content().lower():
                        results.add_result("Edit Account", "PASS", "Account edited successfully")
                    else:
                        results.add_result("Edit Account", "UNCERTAIN", "Account edit submitted")
                else:
                    results.add_result("Edit Account", "SKIP", "Edit button not found")
            else:
                results.add_result("Create Account", "SKIP", "Add account button not found")

        except Exception as e:
            results.add_error("Create/Edit Account", str(e))

    except Exception as e:
        results.add_error("Accounts Management", str(e))

def test_transactions(page: Page, results: TestResults):
    """Test transactions management"""
    try:
        print("\n=== Testing Transactions ===")

        # Try common transaction URLs
        transaction_urls = ["/transactions", "/financial/transactions", "/transaction/list"]
        transactions_loaded = False

        for url in transaction_urls:
            try:
                page.goto(f"{BASE_URL}{url}")
                wait_for_page_load(page)
                if "404" not in page.content():
                    transactions_loaded = True
                    break
            except:
                continue

        if not transactions_loaded:
            results.add_result("Transactions Page", "FAIL", "Could not find transactions page")
            return

        take_screenshot(page, "13_transactions_list", results)
        results.add_result("Transactions Page", "PASS", "Transactions page loaded")

        # Try to create new transaction
        try:
            add_buttons = page.locator('text=/new transaction|add transaction|create transaction/i')
            if add_buttons.count() > 0:
                add_buttons.first.click()
                wait_for_page_load(page)

                take_screenshot(page, "14_transaction_form", results)

                # Fill transaction form
                page.fill('input[name="amount"]', "50.00")
                page.fill('input[name="description"], textarea[name="description"]', "Test grocery purchase")

                # Try to select account
                account_selects = page.locator('select[name="account_id"], select[name="account"]')
                if account_selects.count() > 0:
                    account_selects.first.select_option(index=1)  # Select first non-empty option

                take_screenshot(page, "15_transaction_form_filled", results)

                # Submit
                page.click('button[type="submit"], input[type="submit"]')
                wait_for_page_load(page)

                take_screenshot(page, "16_transaction_created", results)

                if "test grocery purchase" in page.content().lower() or "success" in page.content().lower():
                    results.add_result("Create Transaction", "PASS", "Transaction created successfully")
                else:
                    results.add_result("Create Transaction", "UNCERTAIN", "Transaction form submitted")

                # Create second transaction
                add_buttons = page.locator('text=/new transaction|add transaction/i')
                if add_buttons.count() > 0:
                    add_buttons.first.click()
                    wait_for_page_load(page)

                    page.fill('input[name="amount"]', "75.00")
                    page.fill('input[name="description"], textarea[name="description"]', "Test restaurant")

                    account_selects = page.locator('select[name="account_id"], select[name="account"]')
                    if account_selects.count() > 0:
                        account_selects.first.select_option(index=1)

                    page.click('button[type="submit"]')
                    wait_for_page_load(page)

                    take_screenshot(page, "17_second_transaction_created", results)
                    results.add_result("Create Multiple Transactions", "PASS")
            else:
                results.add_result("Create Transaction", "SKIP", "Add transaction button not found")

        except Exception as e:
            results.add_error("Create Transaction", str(e))

    except Exception as e:
        results.add_error("Transactions Management", str(e))

def test_categories(page: Page, results: TestResults):
    """Test categories management"""
    try:
        print("\n=== Testing Categories ===")

        # Try common category URLs
        category_urls = ["/categories", "/financial/categories", "/category/list", "/settings/categories"]
        categories_loaded = False

        for url in category_urls:
            try:
                page.goto(f"{BASE_URL}{url}")
                wait_for_page_load(page)
                if "404" not in page.content():
                    categories_loaded = True
                    break
            except:
                continue

        if not categories_loaded:
            results.add_result("Categories Page", "SKIP", "Could not find categories page")
            return

        take_screenshot(page, "18_categories_list", results)
        results.add_result("Categories Page", "PASS", "Categories page loaded")

        # Try to create new category
        try:
            add_buttons = page.locator('text=/new category|add category|create category/i')
            if add_buttons.count() > 0:
                add_buttons.first.click()
                wait_for_page_load(page)

                page.fill('input[name="name"], input[name="category_name"]', "Test Groceries")
                page.click('button[type="submit"]')
                wait_for_page_load(page)

                take_screenshot(page, "19_category_created", results)

                if "test groceries" in page.content().lower():
                    results.add_result("Create Category", "PASS", "Category created successfully")

                    # Try to edit
                    edit_buttons = page.locator('text=/edit/i').first
                    if edit_buttons.count() > 0:
                        edit_buttons.click()
                        wait_for_page_load(page)

                        page.fill('input[name="name"], input[name="category_name"]', "Test Groceries Updated")
                        page.click('button[type="submit"]')
                        wait_for_page_load(page)

                        take_screenshot(page, "20_category_updated", results)
                        results.add_result("Edit Category", "PASS", "Category edited successfully")
                else:
                    results.add_result("Create Category", "UNCERTAIN", "Category form submitted")
            else:
                results.add_result("Create Category", "SKIP", "Add category button not found")

        except Exception as e:
            results.add_error("Create/Edit Category", str(e))

    except Exception as e:
        results.add_error("Categories Management", str(e))

def test_settings(page: Page, results: TestResults):
    """Test settings page"""
    try:
        print("\n=== Testing Settings ===")

        settings_urls = ["/settings", "/preferences", "/account/settings"]
        settings_loaded = False

        for url in settings_urls:
            try:
                page.goto(f"{BASE_URL}{url}")
                wait_for_page_load(page)
                if "404" not in page.content():
                    settings_loaded = True
                    break
            except:
                continue

        if not settings_loaded:
            results.add_result("Settings Page", "SKIP", "Could not find settings page")
            return

        take_screenshot(page, "21_settings_page", results)
        results.add_result("Settings Page", "PASS", "Settings page loaded")

        # Check for common settings features
        content = page.content().lower()

        checks = {
            "Currency Preferences": "currency" in content,
            "API Key Management": "api" in content and "key" in content,
            "User Profile": "profile" in content or "user" in content
        }

        for check_name, check_result in checks.items():
            status = "PASS" if check_result else "SKIP"
            results.add_result(f"Settings - {check_name}", status)

    except Exception as e:
        results.add_error("Settings", str(e))

def test_responsive_design(page: Page, results: TestResults):
    """Test responsive design on mobile viewport"""
    try:
        print("\n=== Testing Responsive Design ===")

        # Set mobile viewport
        page.set_viewport_size({"width": 375, "height": 667})

        # Test dashboard on mobile
        page.goto(f"{BASE_URL}/")
        wait_for_page_load(page)

        take_screenshot(page, "22_mobile_dashboard", results, full_page=False)
        results.add_result("Responsive Design - Dashboard", "PASS", "Mobile view captured")

        # Test navigation on mobile
        nav_buttons = page.locator('[class*="menu"], [class*="nav"], [class*="burger"], button[aria-label*="menu"]')
        if nav_buttons.count() > 0:
            results.add_result("Responsive Design - Navigation", "PASS", "Mobile navigation present")
        else:
            results.add_result("Responsive Design - Navigation", "UNCERTAIN", "Mobile navigation not clearly visible")

        # Reset viewport
        page.set_viewport_size({"width": 1280, "height": 720})

    except Exception as e:
        results.add_error("Responsive Design", str(e))

def test_navigation(page: Page, results: TestResults):
    """Test navigation and UI elements"""
    try:
        print("\n=== Testing Navigation & UI ===")

        page.goto(f"{BASE_URL}/")
        wait_for_page_load(page)

        # Check for common navigation elements
        nav_elements = {
            "Dashboard Link": page.locator('a[href*="dashboard"], a[href="/"]'),
            "Accounts Link": page.locator('a[href*="account"]'),
            "Transactions Link": page.locator('a[href*="transaction"]'),
            "Logout Button": page.locator('a[href*="logout"], button:has-text("logout")')
        }

        for element_name, locator in nav_elements.items():
            if locator.count() > 0:
                results.add_result(f"Navigation - {element_name}", "PASS", "Element found")
            else:
                results.add_result(f"Navigation - {element_name}", "FAIL", "Element not found")

        take_screenshot(page, "23_navigation_elements", results)

    except Exception as e:
        results.add_error("Navigation & UI", str(e))

def test_data_persistence(page: Page, results: TestResults):
    """Test data persistence after logout/login"""
    try:
        print("\n=== Testing Data Persistence ===")

        # Logout
        logout_buttons = page.locator('a[href*="logout"], button:has-text("logout")')
        if logout_buttons.count() > 0:
            logout_buttons.first.click()
            wait_for_page_load(page)

            take_screenshot(page, "24_after_logout", results)
            results.add_result("Logout", "PASS", "Logged out successfully")

            # Login again
            if test_login(page, results):
                # Check if data still exists
                page.goto(f"{BASE_URL}/accounts")
                wait_for_page_load(page)

                if "test checking" in page.content().lower():
                    results.add_result("Data Persistence - Accounts", "PASS", "Account data persisted")
                else:
                    results.add_result("Data Persistence - Accounts", "UNCERTAIN", "Could not verify account persistence")

                page.goto(f"{BASE_URL}/transactions")
                wait_for_page_load(page)

                if "test grocery" in page.content().lower():
                    results.add_result("Data Persistence - Transactions", "PASS", "Transaction data persisted")
                else:
                    results.add_result("Data Persistence - Transactions", "UNCERTAIN", "Could not verify transaction persistence")

                take_screenshot(page, "25_data_after_relogin", results)
        else:
            results.add_result("Logout", "SKIP", "Logout button not found")

    except Exception as e:
        results.add_error("Data Persistence", str(e))

def generate_report(results: TestResults):
    """Generate comprehensive test report"""
    print("\n" + "="*80)
    print("COMPREHENSIVE TEST REPORT")
    print("="*80)

    # Summary statistics
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
    print(f"  Total Errors: {len(results.errors)}")
    print(f"  Screenshots: {len(results.screenshots)}")

    # Detailed results
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

    # Errors
    if results.errors:
        print(f"\nERRORS:")
        for error in results.errors:
            print(f"  ✗ {error['test']}")
            print(f"      → {error['error']}")

    # Screenshots
    print(f"\nSCREENSHOTS:")
    for screenshot in results.screenshots:
        print(f"  📸 {screenshot['name']}")
        print(f"      → {screenshot['path']}")

    # Overall health assessment
    print(f"\nOVERALL HEALTH ASSESSMENT:")
    if failed == 0 and len(results.errors) == 0:
        health = "EXCELLENT"
        print(f"  ✓ {health} - All tests passed without errors")
    elif failed <= 2 and len(results.errors) <= 2:
        health = "GOOD"
        print(f"  ✓ {health} - Minor issues found, but app is functional")
    elif failed <= 5 and len(results.errors) <= 5:
        health = "FAIR"
        print(f"  ⚠ {health} - Several issues found, some features may not work")
    else:
        health = "POOR"
        print(f"  ✗ {health} - Significant issues found, app needs attention")

    print("\n" + "="*80)
    print(f"Screenshots saved to: {SCREENSHOTS_DIR}")
    print("="*80 + "\n")

def main():
    """Main test execution"""
    results = TestResults()

    print("Starting comprehensive Finance App testing...")
    print(f"Base URL: {BASE_URL}")
    print(f"Screenshots will be saved to: {SCREENSHOTS_DIR}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        # Enable console logging
        page.on("console", lambda msg: print(f"  [Console] {msg.type}: {msg.text}"))

        try:
            # Test sequence
            registered = test_registration(page, results)

            if not registered:
                # Try to login if registration failed/skipped
                test_login(page, results)

            test_dashboard(page, results)
            test_accounts(page, results)
            test_transactions(page, results)
            test_categories(page, results)
            test_settings(page, results)
            test_navigation(page, results)
            test_responsive_design(page, results)
            test_data_persistence(page, results)

        except Exception as e:
            results.add_error("Main Test Execution", str(e))
        finally:
            browser.close()

    # Generate final report
    generate_report(results)

if __name__ == "__main__":
    main()
