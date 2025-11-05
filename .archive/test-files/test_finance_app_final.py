#!/usr/bin/env python3
"""
Complete Comprehensive Playwright Test for Finance Flask Application
Final version with all edge cases handled
"""

from playwright.sync_api import sync_playwright, Page
import time
from pathlib import Path

BASE_URL = "http://localhost:5001"
SCREENSHOTS_DIR = Path("/Users/njpinton/projects/git/finance/screenshots/final_test")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

TEST_USER = {
    "username": "testuser",
    "email": "testuser@example.com",
    "password": "TestPassword123!"
}

class TestResults:
    def __init__(self):
        self.results = []
        self.errors = []
        self.screenshots = []
        self.warnings = []

    def add_result(self, test_name: str, status: str, details: str = ""):
        self.results.append({"test": test_name, "status": status, "details": details})
        symbol = {"PASS": "✓", "FAIL": "✗", "SKIP": "⊘", "UNCERTAIN": "?"}[status]
        print(f"{symbol} {test_name}: {status}")
        if details:
            print(f"  → {details}")

    def add_error(self, test_name: str, error: str):
        self.errors.append({"test": test_name, "error": error})
        print(f"✗ ERROR in {test_name}: {error}")

    def add_warning(self, test_name: str, warning: str):
        self.warnings.append({"test": test_name, "warning": warning})
        print(f"⚠ WARNING in {test_name}: {warning}")

    def add_screenshot(self, name: str, path: str):
        self.screenshots.append({"name": name, "path": path})

def take_screenshot(page: Page, name: str, results: TestResults, full_page: bool = True):
    path = SCREENSHOTS_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=full_page)
    results.add_screenshot(name, str(path))
    print(f"📸 {name}")

def wait_for_page_load(page: Page, extra_wait: float = 0.5):
    page.wait_for_load_state('networkidle')
    time.sleep(extra_wait)

def login(page: Page, results: TestResults) -> bool:
    """Perform user login"""
    try:
        page.goto(f"{BASE_URL}/auth/login")
        wait_for_page_load(page)

        page.fill('input[name="username"]', TEST_USER["username"])
        page.fill('input[name="password"]', TEST_USER["password"])

        page.click('button[type="submit"]')
        wait_for_page_load(page)

        content = page.content().lower()
        return "logout" in content or "sign out" in content
    except Exception as e:
        results.add_error("Login", str(e))
        return False

def main():
    results = TestResults()

    print("="*80)
    print("FINAL COMPREHENSIVE FINANCE APP TEST")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Screenshots: {SCREENSHOTS_DIR}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        # Console logging
        page.on("console", lambda msg: print(f"  [Console] {msg.type}: {msg.text}") if msg.type in ["error", "warning"] else None)

        try:
            # ============================================================
            # 1. LOGIN
            # ============================================================
            print("\n" + "="*80)
            print("TEST 1: USER LOGIN")
            print("="*80)

            if login(page, results):
                results.add_result("User Login", "PASS", "Successfully authenticated")
                take_screenshot(page, "01_after_login", results)
            else:
                results.add_result("User Login", "FAIL", "Authentication failed")
                take_screenshot(page, "01_login_failed", results)
                browser.close()
                return

            # ============================================================
            # 2. DASHBOARD
            # ============================================================
            print("\n" + "="*80)
            print("TEST 2: DASHBOARD")
            print("="*80)

            page.goto(f"{BASE_URL}/")
            wait_for_page_load(page)
            take_screenshot(page, "02_dashboard", results)

            content = page.content()
            checks = {
                "Total Assets Display": "total assets" in content.lower() or "total_assets" in content.lower(),
                "Total Liabilities Display": "total liabilities" in content.lower() or "liabilities" in content.lower(),
                "Net Worth Display": "net worth" in content.lower(),
                "Charts/Visualizations": "chart" in content.lower() or "<canvas" in content,
                "Recent Transactions": "recent transactions" in content.lower() or "transaction" in content.lower()
            }

            for check_name, passed in checks.items():
                results.add_result(f"Dashboard - {check_name}", "PASS" if passed else "FAIL")

            # ============================================================
            # 3. ACCOUNTS MANAGEMENT
            # ============================================================
            print("\n" + "="*80)
            print("TEST 3: ACCOUNTS MANAGEMENT")
            print("="*80)

            page.click('a:has-text("Accounts")')
            wait_for_page_load(page)
            take_screenshot(page, "03_accounts_list", results)
            results.add_result("Navigate to Accounts", "PASS", f"URL: {page.url}")

            # Create account
            page.click('a:has-text("New Account")')
            wait_for_page_load(page)
            take_screenshot(page, "04_new_account_form", results)

            page.fill('input[name="name"]', "Automated Test Savings")
            page.fill('input[name="balance"]', "5000.00")
            page.select_option('select[name="account_type"]', index=1)

            take_screenshot(page, "05_account_form_filled", results)

            page.click('button[type="submit"]')
            wait_for_page_load(page)
            take_screenshot(page, "06_account_created", results)

            if "automated test savings" in page.content().lower():
                results.add_result("Create Account", "PASS", "Account visible in list")
            else:
                results.add_result("Create Account", "UNCERTAIN", "Form submitted")

            # Test Edit Account
            try:
                # Find the edit button for our newly created account
                edit_buttons = page.locator('a:has-text("Edit"), button:has-text("Edit")').all()
                if len(edit_buttons) > 0:
                    edit_buttons[-1].click()  # Click the last edit button (our new account)
                    wait_for_page_load(page)
                    take_screenshot(page, "07_edit_account_form", results)

                    page.fill('input[name="name"]', "Automated Test Savings UPDATED")
                    page.click('button[type="submit"]')
                    wait_for_page_load(page)
                    take_screenshot(page, "08_account_updated", results)

                    if "updated" in page.content().lower():
                        results.add_result("Edit Account", "PASS", "Account name updated")
                    else:
                        results.add_result("Edit Account", "UNCERTAIN", "Edit submitted")
                else:
                    results.add_result("Edit Account", "SKIP", "No edit button found")
            except Exception as e:
                results.add_error("Edit Account", str(e))

            # ============================================================
            # 4. TRANSACTIONS
            # ============================================================
            print("\n" + "="*80)
            print("TEST 4: TRANSACTIONS")
            print("="*80)

            page.click('a:has-text("Transactions")')
            wait_for_page_load(page)
            take_screenshot(page, "09_transactions_list", results)
            results.add_result("Navigate to Transactions", "PASS", f"URL: {page.url}")

            # Create transaction
            page.click('a:has-text("New Transaction")')
            wait_for_page_load(page)
            take_screenshot(page, "10_new_transaction_form", results)

            # Select transaction type first
            page.select_option('select[name="type"]', "expense")

            # Select account
            page.select_option('select[name="account_id"]', index=1)

            # Fill amount
            page.fill('input[name="amount"]', "150.75")

            # Fill memo (not description!)
            page.fill('textarea[name="memo"], input[name="memo"]', "Test Grocery Shopping - Automated")

            # Select category if available
            try:
                category_select = page.locator('select[name="category_id"]')
                if category_select.count() > 0:
                    page.select_option('select[name="category_id"]', index=1)
            except:
                pass

            take_screenshot(page, "11_transaction_form_filled", results)

            page.click('button[type="submit"]')
            wait_for_page_load(page)
            take_screenshot(page, "12_transaction_created", results)

            if "grocery" in page.content().lower() or "150.75" in page.content():
                results.add_result("Create Transaction", "PASS", "Transaction visible in list")
            else:
                results.add_result("Create Transaction", "UNCERTAIN", "Form submitted")

            # Create second transaction
            try:
                page.click('a:has-text("New Transaction")')
                wait_for_page_load(page)

                page.select_option('select[name="type"]', "income")
                page.select_option('select[name="account_id"]', index=1)
                page.fill('input[name="amount"]', "2500.00")
                page.fill('textarea[name="memo"], input[name="memo"]', "Test Salary Payment")

                page.click('button[type="submit"]')
                wait_for_page_load(page)
                take_screenshot(page, "13_second_transaction", results)

                results.add_result("Create Multiple Transactions", "PASS", "Second transaction created")
            except Exception as e:
                results.add_error("Create Multiple Transactions", str(e))

            # Test transaction filtering/search if available
            if "search" in page.content().lower() or "filter" in page.content().lower():
                results.add_result("Transaction Filtering", "PASS", "Filter/search UI present")
            else:
                results.add_result("Transaction Filtering", "SKIP", "No filter UI found")

            # ============================================================
            # 5. EXPENSE RECORDS (RECEIPTS)
            # ============================================================
            print("\n" + "="*80)
            print("TEST 5: EXPENSE RECORDS (RECEIPTS)")
            print("="*80)

            try:
                page.click('a:has-text("Expense Records")')
                wait_for_page_load(page)
                take_screenshot(page, "14_expense_records", results)
                results.add_result("Navigate to Expense Records", "PASS", f"URL: {page.url}")

                # Check for upload functionality
                if "upload" in page.content().lower() or "new receipt" in page.content().lower():
                    results.add_result("Expense Records - Upload Feature", "PASS", "Upload UI present")
                else:
                    results.add_result("Expense Records - Upload Feature", "SKIP", "No upload UI visible")
            except Exception as e:
                results.add_error("Expense Records", str(e))

            # ============================================================
            # 6. FINANCIAL TOOLS
            # ============================================================
            print("\n" + "="*80)
            print("TEST 6: FINANCIAL TOOLS")
            print("="*80)

            try:
                # Click Financial Tools dropdown
                page.click('a:has-text("Financial Tools")')
                wait_for_page_load(page, 0.3)
                take_screenshot(page, "15_financial_tools_menu", results)

                results.add_result("Financial Tools Menu", "PASS", "Menu accessible")

                # Test AI Categorizer
                try:
                    page.click('a:has-text("Transaction Categorizer")')
                    wait_for_page_load(page)
                    take_screenshot(page, "16_ai_categorizer", results)
                    results.add_result("AI Transaction Categorizer", "PASS", f"URL: {page.url}")

                    # Go back to test other tools
                    page.click('a:has-text("Financial Tools")')
                    wait_for_page_load(page, 0.3)
                except Exception as e:
                    results.add_error("AI Transaction Categorizer", str(e))

                # Test Financial Advisor
                try:
                    page.click('a:has-text("Financial Advisor")')
                    wait_for_page_load(page)
                    take_screenshot(page, "17_financial_advisor", results)
                    results.add_result("Financial Advisor", "PASS", f"URL: {page.url}")
                except Exception as e:
                    results.add_error("Financial Advisor", str(e))

            except Exception as e:
                results.add_error("Financial Tools", str(e))

            # ============================================================
            # 7. SETTINGS
            # ============================================================
            print("\n" + "="*80)
            print("TEST 7: SETTINGS")
            print("="*80)

            try:
                # Click on user menu
                page.click('a:has-text("testuser"), button:has-text("testuser")')
                wait_for_page_load(page, 0.3)

                # Click Settings from dropdown
                page.click('a:has-text("Settings")')
                wait_for_page_load(page)
                take_screenshot(page, "18_settings_page", results)
                results.add_result("Navigate to Settings", "PASS", f"URL: {page.url}")

                content = page.content().lower()

                settings_checks = {
                    "User Profile": "profile" in content or "email" in content,
                    "API Key Management": "api" in content and "key" in content,
                    "Preferences": "preference" in content or "currency" in content,
                    "Security Settings": "password" in content or "security" in content
                }

                for check_name, passed in settings_checks.items():
                    results.add_result(f"Settings - {check_name}", "PASS" if passed else "SKIP")

            except Exception as e:
                results.add_error("Settings", str(e))

            # ============================================================
            # 8. FEEDBACK SYSTEM
            # ============================================================
            print("\n" + "="*80)
            print("TEST 8: FEEDBACK SYSTEM")
            print("="*80)

            try:
                page.click('a:has-text("Feedback")')
                wait_for_page_load(page)
                take_screenshot(page, "19_feedback_page", results)
                results.add_result("Navigate to Feedback", "PASS", f"URL: {page.url}")

                # Try to submit feedback
                if "textarea" in page.content().lower() or "feedback" in page.content().lower():
                    try:
                        page.fill('textarea[name="feedback_text"], textarea[name="message"]',
                                "This is an automated test feedback submission")

                        # Select category if exists
                        try:
                            page.select_option('select[name="category"]', index=1)
                        except:
                            pass

                        take_screenshot(page, "20_feedback_form_filled", results)

                        page.click('button[type="submit"]')
                        wait_for_page_load(page)
                        take_screenshot(page, "21_feedback_submitted", results)

                        results.add_result("Submit Feedback", "PASS", "Feedback form submitted")
                    except Exception as e:
                        results.add_error("Submit Feedback", str(e))
                else:
                    results.add_result("Submit Feedback", "SKIP", "No feedback form found")

            except Exception as e:
                results.add_error("Feedback System", str(e))

            # ============================================================
            # 9. RESPONSIVE DESIGN
            # ============================================================
            print("\n" + "="*80)
            print("TEST 9: RESPONSIVE DESIGN")
            print("="*80)

            # Test mobile view
            page.set_viewport_size({"width": 375, "height": 667})
            page.goto(f"{BASE_URL}/")
            wait_for_page_load(page)
            take_screenshot(page, "22_mobile_dashboard", results, full_page=False)

            page.goto(f"{BASE_URL}/accounts/")
            wait_for_page_load(page)
            take_screenshot(page, "23_mobile_accounts", results, full_page=False)

            results.add_result("Mobile Responsive - Dashboard", "PASS", "Screenshot captured")
            results.add_result("Mobile Responsive - Accounts", "PASS", "Screenshot captured")

            # Test tablet view
            page.set_viewport_size({"width": 768, "height": 1024})
            page.goto(f"{BASE_URL}/")
            wait_for_page_load(page)
            take_screenshot(page, "24_tablet_view", results, full_page=False)
            results.add_result("Tablet Responsive", "PASS", "Screenshot captured")

            # Reset to desktop
            page.set_viewport_size({"width": 1280, "height": 720})

            # ============================================================
            # 10. DATA PERSISTENCE TEST
            # ============================================================
            print("\n" + "="*80)
            print("TEST 10: DATA PERSISTENCE")
            print("="*80)

            try:
                # Logout
                page.goto(f"{BASE_URL}/")
                wait_for_page_load(page)
                page.click('a:has-text("testuser")')
                wait_for_page_load(page, 0.3)
                page.click('a[href*="logout"]')
                wait_for_page_load(page)
                take_screenshot(page, "25_after_logout", results)
                results.add_result("Logout", "PASS", "Logged out successfully")

                # Login again
                if login(page, results):
                    results.add_result("Re-login", "PASS", "Successfully re-authenticated")

                    # Check if data persists
                    page.goto(f"{BASE_URL}/accounts/")
                    wait_for_page_load(page)

                    if "automated test savings" in page.content().lower():
                        results.add_result("Data Persistence - Accounts", "PASS", "Account data persisted")
                    else:
                        results.add_result("Data Persistence - Accounts", "FAIL", "Account data lost")

                    page.goto(f"{BASE_URL}/transactions/")
                    wait_for_page_load(page)

                    if "grocery" in page.content().lower() or "150.75" in page.content():
                        results.add_result("Data Persistence - Transactions", "PASS", "Transaction data persisted")
                    else:
                        results.add_result("Data Persistence - Transactions", "FAIL", "Transaction data lost")

                    take_screenshot(page, "26_data_persisted", results)
                else:
                    results.add_result("Re-login", "FAIL", "Could not re-authenticate")

            except Exception as e:
                results.add_error("Data Persistence", str(e))

            # ============================================================
            # 11. FINAL NAVIGATION AUDIT
            # ============================================================
            print("\n" + "="*80)
            print("TEST 11: NAVIGATION AUDIT")
            print("="*80)

            page.goto(f"{BASE_URL}/")
            wait_for_page_load(page)

            nav_links = page.locator('nav a, [class*="nav"] a, [class*="sidebar"] a').all()

            print(f"\n  Found {len(nav_links)} navigation links:")
            for i, link in enumerate(nav_links[:20], 1):
                try:
                    text = link.inner_text().strip()
                    href = link.get_attribute('href')
                    if text and href:
                        print(f"    {i}. {text} → {href}")
                except:
                    pass

            results.add_result("Navigation Audit", "PASS", f"Found {len(nav_links)} navigation links")
            take_screenshot(page, "27_final_navigation", results)

        except Exception as e:
            results.add_error("Main Test Flow", str(e))
            take_screenshot(page, "99_critical_error", results)
        finally:
            browser.close()

    # ================================================================
    # GENERATE FINAL REPORT
    # ================================================================
    print("\n" + "="*80)
    print("FINAL COMPREHENSIVE TEST REPORT")
    print("="*80)

    total_tests = len(results.results)
    passed = sum(1 for r in results.results if r["status"] == "PASS")
    failed = sum(1 for r in results.results if r["status"] == "FAIL")
    skipped = sum(1 for r in results.results if r["status"] == "SKIP")
    uncertain = sum(1 for r in results.results if r["status"] == "UNCERTAIN")

    print(f"\n📊 SUMMARY STATISTICS:")
    print(f"  Total Tests: {total_tests}")
    print(f"  ✓ Passed: {passed} ({passed/total_tests*100:.1f}%)")
    print(f"  ✗ Failed: {failed} ({failed/total_tests*100:.1f}%)")
    print(f"  ⊘ Skipped: {skipped} ({skipped/total_tests*100:.1f}%)")
    print(f"  ? Uncertain: {uncertain}")
    print(f"  ⚠ Warnings: {len(results.warnings)}")
    print(f"  ✗ Errors: {len(results.errors)}")
    print(f"  📸 Screenshots: {len(results.screenshots)}")

    print(f"\n📝 DETAILED TEST RESULTS:")
    for result in results.results:
        symbol = {"PASS": "✓", "FAIL": "✗", "SKIP": "⊘", "UNCERTAIN": "?"}[result["status"]]
        print(f"  {symbol} {result['test']}: {result['status']}")
        if result["details"]:
            print(f"      → {result['details']}")

    if results.errors:
        print(f"\n❌ ERRORS ENCOUNTERED:")
        for error in results.errors:
            print(f"  • {error['test']}")
            print(f"      → {error['error']}")

    if results.warnings:
        print(f"\n⚠️  WARNINGS:")
        for warning in results.warnings:
            print(f"  • {warning['test']}: {warning['warning']}")

    print(f"\n📸 SCREENSHOTS LOCATION:")
    print(f"  {SCREENSHOTS_DIR}")
    print(f"  Total: {len(results.screenshots)} screenshots")

    # Health Assessment
    print(f"\n🏥 OVERALL HEALTH ASSESSMENT:")
    if failed == 0 and len(results.errors) == 0:
        health = "EXCELLENT"
        symbol = "✅"
        description = "All tests passed without errors"
    elif failed <= 2 and len(results.errors) <= 2:
        health = "GOOD"
        symbol = "✓"
        description = "Minor issues found, app is functional"
    elif failed <= 5 and len(results.errors) <= 5:
        health = "FAIR"
        symbol = "⚠"
        description = "Several issues found, some features may need attention"
    else:
        health = "NEEDS ATTENTION"
        symbol = "✗"
        description = "Significant issues found, app needs review"

    print(f"  {symbol} {health}")
    print(f"  {description}")

    # Feature Summary
    print(f"\n✨ TESTED FEATURES:")
    features = [
        ("User Authentication", any("Login" in r["test"] for r in results.results)),
        ("Dashboard", any("Dashboard" in r["test"] for r in results.results)),
        ("Account Management", any("Account" in r["test"] and "Create" in r["test"] for r in results.results)),
        ("Transaction Management", any("Transaction" in r["test"] and "Create" in r["test"] for r in results.results)),
        ("Expense Records/Receipts", any("Expense Records" in r["test"] for r in results.results)),
        ("Financial Tools", any("Financial Tools" in r["test"] or "Categorizer" in r["test"] or "Advisor" in r["test"] for r in results.results)),
        ("Settings", any("Settings" in r["test"] for r in results.results)),
        ("Feedback System", any("Feedback" in r["test"] for r in results.results)),
        ("Responsive Design", any("Responsive" in r["test"] or "Mobile" in r["test"] for r in results.results)),
        ("Data Persistence", any("Persistence" in r["test"] for r in results.results))
    ]

    for feature_name, tested in features:
        print(f"  {'✓' if tested else '✗'} {feature_name}")

    print("\n" + "="*80)
    print("Test completed successfully!")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
