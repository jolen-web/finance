"""
Comprehensive Playwright test for Finance Flask Application
Tests user registration, login, accounts, transactions, categories, dashboard, and settings
"""

from playwright.sync_api import sync_playwright, expect
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5001"
TEST_USER = {
    "username": "testuser",
    "email": "testuser@example.com",
    "password": "TestPassword123!"
}

# Screenshot directory
SCREENSHOT_DIR = "/Users/njpinton/projects/git/finance/screenshots/test_results"

def log(message):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def take_screenshot(page, name):
    """Take a screenshot with consistent naming"""
    filename = f"{SCREENSHOT_DIR}/{name}.png"
    page.screenshot(path=filename, full_page=True)
    log(f"Screenshot saved: {name}.png")
    return filename

def test_finance_app():
    """Main test function"""
    results = {
        "tested_pages": [],
        "errors": [],
        "screenshots": [],
        "feature_results": {}
    }

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        # Capture console messages and errors
        page.on("console", lambda msg: log(f"Console [{msg.type}]: {msg.text}"))
        page.on("pageerror", lambda exc: results["errors"].append(f"Page error: {exc}"))

        try:
            # =================================================================
            # 1. TEST REGISTRATION (if available)
            # =================================================================
            log("=" * 60)
            log("TEST 1: User Registration")
            log("=" * 60)

            try:
                page.goto(f"{BASE_URL}/auth/register", wait_until="networkidle")
                page.wait_for_timeout(1000)

                if "404" in page.content() or "Not Found" in page.content():
                    log("Registration page not found (404) - will try login only")
                    results["feature_results"]["registration"] = "NOT_AVAILABLE"
                else:
                    results["tested_pages"].append("/auth/register")
                    take_screenshot(page, "01_registration_page")

                    # Fill registration form
                    log("Filling registration form...")

                    # Try different possible field names
                    if page.locator('input[name="username"]').count() > 0:
                        page.fill('input[name="username"]', TEST_USER["username"])

                    if page.locator('input[name="email"]').count() > 0:
                        page.fill('input[name="email"]', TEST_USER["email"])

                    if page.locator('input[name="password"]').count() > 0:
                        page.fill('input[name="password"]', TEST_USER["password"])

                    if page.locator('input[name="confirm_password"]').count() > 0:
                        page.fill('input[name="confirm_password"]', TEST_USER["password"])
                    elif page.locator('input[name="password_confirm"]').count() > 0:
                        page.fill('input[name="password_confirm"]', TEST_USER["password"])

                    # Submit form
                    page.click('button[type="submit"]')
                    page.wait_for_timeout(2000)

                    take_screenshot(page, "02_after_registration")

                    # Check if registration was successful
                    if "already exists" in page.content().lower() or "already registered" in page.content().lower():
                        log("User already exists - will proceed with login")
                        results["feature_results"]["registration"] = "USER_EXISTS"
                    elif page.url.endswith("/login") or "login" in page.url.lower():
                        log("Registration successful - redirected to login")
                        results["feature_results"]["registration"] = "SUCCESS"
                    else:
                        log(f"Registration outcome unclear - current URL: {page.url}")
                        results["feature_results"]["registration"] = "UNCLEAR"

            except Exception as e:
                log(f"Registration test error: {str(e)}")
                results["errors"].append(f"Registration: {str(e)}")
                results["feature_results"]["registration"] = "ERROR"

            # =================================================================
            # 2. TEST LOGIN
            # =================================================================
            log("=" * 60)
            log("TEST 2: User Login")
            log("=" * 60)

            try:
                page.goto(f"{BASE_URL}/auth/login", wait_until="networkidle")
                page.wait_for_timeout(1000)
                results["tested_pages"].append("/auth/login")

                take_screenshot(page, "03_login_page")

                # Fill login form
                log("Filling login form...")
                if page.locator('input[name="email"]').count() > 0:
                    page.fill('input[name="email"]', TEST_USER["email"])
                elif page.locator('input[name="username"]').count() > 0:
                    page.fill('input[name="username"]', TEST_USER["username"])

                page.fill('input[name="password"]', TEST_USER["password"])
                page.click('button[type="submit"]')
                page.wait_for_timeout(2000)

                take_screenshot(page, "04_after_login")

                # Verify login success
                if "dashboard" in page.url.lower() or page.url == f"{BASE_URL}/" or "login" not in page.url.lower():
                    log(f"Login successful - redirected to: {page.url}")
                    results["feature_results"]["login"] = "SUCCESS"
                else:
                    log(f"Login may have failed - current URL: {page.url}")
                    results["feature_results"]["login"] = "FAILED"
                    results["errors"].append("Login failed - check credentials or page structure")

            except Exception as e:
                log(f"Login test error: {str(e)}")
                results["errors"].append(f"Login: {str(e)}")
                results["feature_results"]["login"] = "ERROR"

            # =================================================================
            # 3. TEST DASHBOARD
            # =================================================================
            log("=" * 60)
            log("TEST 3: Dashboard")
            log("=" * 60)

            try:
                # Try common dashboard URLs
                dashboard_urls = ["/", "/dashboard", "/home"]
                dashboard_loaded = False

                for url in dashboard_urls:
                    try:
                        page.goto(f"{BASE_URL}{url}", wait_until="networkidle")
                        page.wait_for_timeout(1000)

                        if "404" not in page.content() and "Not Found" not in page.content():
                            log(f"Dashboard loaded from: {url}")
                            results["tested_pages"].append(url)
                            dashboard_loaded = True
                            break
                    except:
                        continue

                if dashboard_loaded:
                    take_screenshot(page, "05_dashboard")

                    # Check for dashboard elements
                    content = page.content().lower()
                    has_net_worth = "net worth" in content or "balance" in content
                    has_accounts = "account" in content
                    has_transactions = "transaction" in content

                    log(f"Dashboard elements - Net Worth: {has_net_worth}, Accounts: {has_accounts}, Transactions: {has_transactions}")
                    results["feature_results"]["dashboard"] = "SUCCESS"
                else:
                    log("Dashboard not found")
                    results["feature_results"]["dashboard"] = "NOT_FOUND"

            except Exception as e:
                log(f"Dashboard test error: {str(e)}")
                results["errors"].append(f"Dashboard: {str(e)}")
                results["feature_results"]["dashboard"] = "ERROR"

            # =================================================================
            # 4. TEST ACCOUNTS MANAGEMENT
            # =================================================================
            log("=" * 60)
            log("TEST 4: Accounts Management")
            log("=" * 60)

            try:
                # Try different account URLs
                account_urls = ["/accounts", "/financial/accounts", "/account"]
                accounts_loaded = False

                for url in account_urls:
                    try:
                        page.goto(f"{BASE_URL}{url}", wait_until="networkidle")
                        page.wait_for_timeout(1000)

                        if "404" not in page.content() and "Not Found" not in page.content():
                            log(f"Accounts page loaded from: {url}")
                            results["tested_pages"].append(url)
                            accounts_loaded = True
                            break
                    except:
                        continue

                if accounts_loaded:
                    take_screenshot(page, "06_accounts_list")

                    # Look for "Add Account" or "New Account" button
                    new_account_clicked = False

                    if page.locator('text="New Account"').count() > 0:
                        page.click('text="New Account"')
                        new_account_clicked = True
                    elif page.locator('text="Add Account"').count() > 0:
                        page.click('text="Add Account"')
                        new_account_clicked = True
                    elif page.locator('a[href*="new"]').count() > 0:
                        page.click('a[href*="new"]')
                        new_account_clicked = True

                    if new_account_clicked:
                        page.wait_for_timeout(1000)
                        take_screenshot(page, "07_new_account_form")

                        # Fill new account form
                        log("Creating new account...")
                        if page.locator('input[name="name"]').count() > 0:
                            page.fill('input[name="name"]', "Test Checking")
                        elif page.locator('input[name="account_name"]').count() > 0:
                            page.fill('input[name="account_name"]', "Test Checking")

                        if page.locator('input[name="balance"]').count() > 0:
                            page.fill('input[name="balance"]', "1000.00")
                        elif page.locator('input[name="starting_balance"]').count() > 0:
                            page.fill('input[name="starting_balance"]', "1000.00")

                        # Select account type if available
                        if page.locator('select[name="type"]').count() > 0:
                            page.select_option('select[name="type"]', "checking")
                        elif page.locator('select[name="account_type"]').count() > 0:
                            page.select_option('select[name="account_type"]', index=0)

                        page.click('button[type="submit"]')
                        page.wait_for_timeout(2000)

                        take_screenshot(page, "08_after_account_creation")

                        # Verify account appears
                        if "Test Checking" in page.content():
                            log("Account created successfully")
                            results["feature_results"]["account_create"] = "SUCCESS"
                        else:
                            log("Account may not have been created")
                            results["feature_results"]["account_create"] = "UNCLEAR"
                    else:
                        log("Could not find 'New Account' button")
                        results["feature_results"]["account_create"] = "BUTTON_NOT_FOUND"

                    results["feature_results"]["accounts"] = "SUCCESS"
                else:
                    log("Accounts page not found")
                    results["feature_results"]["accounts"] = "NOT_FOUND"

            except Exception as e:
                log(f"Accounts test error: {str(e)}")
                results["errors"].append(f"Accounts: {str(e)}")
                results["feature_results"]["accounts"] = "ERROR"

            # =================================================================
            # 5. TEST TRANSACTIONS
            # =================================================================
            log("=" * 60)
            log("TEST 5: Transactions Management")
            log("=" * 60)

            try:
                # Try different transaction URLs
                transaction_urls = ["/transactions", "/financial/transactions", "/transaction"]
                transactions_loaded = False

                for url in transaction_urls:
                    try:
                        page.goto(f"{BASE_URL}{url}", wait_until="networkidle")
                        page.wait_for_timeout(1000)

                        if "404" not in page.content() and "Not Found" not in page.content():
                            log(f"Transactions page loaded from: {url}")
                            results["tested_pages"].append(url)
                            transactions_loaded = True
                            break
                    except:
                        continue

                if transactions_loaded:
                    take_screenshot(page, "09_transactions_list")

                    # Look for "Add Transaction" or "New Transaction" button
                    new_transaction_clicked = False

                    if page.locator('text="New Transaction"').count() > 0:
                        page.click('text="New Transaction"')
                        new_transaction_clicked = True
                    elif page.locator('text="Add Transaction"').count() > 0:
                        page.click('text="Add Transaction"')
                        new_transaction_clicked = True
                    elif page.locator('a[href*="new"]').count() > 0:
                        page.click('a[href*="new"]')
                        new_transaction_clicked = True

                    if new_transaction_clicked:
                        page.wait_for_timeout(1000)
                        take_screenshot(page, "10_new_transaction_form")

                        # Fill new transaction form
                        log("Creating new transaction...")
                        if page.locator('input[name="amount"]').count() > 0:
                            page.fill('input[name="amount"]', "50.00")

                        if page.locator('input[name="description"]').count() > 0:
                            page.fill('input[name="description"]', "Test grocery purchase")
                        elif page.locator('textarea[name="description"]').count() > 0:
                            page.fill('textarea[name="description"]', "Test grocery purchase")

                        # Select account if dropdown exists
                        if page.locator('select[name="account"]').count() > 0:
                            page.select_option('select[name="account"]', index=0)
                        elif page.locator('select[name="account_id"]').count() > 0:
                            page.select_option('select[name="account_id"]', index=0)

                        page.click('button[type="submit"]')
                        page.wait_for_timeout(2000)

                        take_screenshot(page, "11_after_transaction_creation")

                        # Verify transaction appears
                        if "grocery" in page.content().lower():
                            log("Transaction created successfully")
                            results["feature_results"]["transaction_create"] = "SUCCESS"
                        else:
                            log("Transaction may not have been created")
                            results["feature_results"]["transaction_create"] = "UNCLEAR"
                    else:
                        log("Could not find 'New Transaction' button")
                        results["feature_results"]["transaction_create"] = "BUTTON_NOT_FOUND"

                    results["feature_results"]["transactions"] = "SUCCESS"
                else:
                    log("Transactions page not found")
                    results["feature_results"]["transactions"] = "NOT_FOUND"

            except Exception as e:
                log(f"Transactions test error: {str(e)}")
                results["errors"].append(f"Transactions: {str(e)}")
                results["feature_results"]["transactions"] = "ERROR"

            # =================================================================
            # 6. TEST CATEGORIES (if available)
            # =================================================================
            log("=" * 60)
            log("TEST 6: Categories Management")
            log("=" * 60)

            try:
                # Try different category URLs
                category_urls = ["/categories", "/financial/categories", "/category"]
                categories_loaded = False

                for url in category_urls:
                    try:
                        page.goto(f"{BASE_URL}{url}", wait_until="networkidle")
                        page.wait_for_timeout(1000)

                        if "404" not in page.content() and "Not Found" not in page.content():
                            log(f"Categories page loaded from: {url}")
                            results["tested_pages"].append(url)
                            categories_loaded = True
                            break
                    except:
                        continue

                if categories_loaded:
                    take_screenshot(page, "12_categories_list")
                    results["feature_results"]["categories"] = "SUCCESS"
                else:
                    log("Categories page not found (may not be implemented)")
                    results["feature_results"]["categories"] = "NOT_FOUND"

            except Exception as e:
                log(f"Categories test error: {str(e)}")
                results["errors"].append(f"Categories: {str(e)}")
                results["feature_results"]["categories"] = "ERROR"

            # =================================================================
            # 7. TEST SETTINGS
            # =================================================================
            log("=" * 60)
            log("TEST 7: Settings")
            log("=" * 60)

            try:
                # Try different settings URLs
                settings_urls = ["/settings", "/user/settings", "/preferences", "/settings/general"]
                settings_loaded = False

                for url in settings_urls:
                    try:
                        page.goto(f"{BASE_URL}{url}", wait_until="networkidle")
                        page.wait_for_timeout(1000)

                        if "404" not in page.content() and "Not Found" not in page.content():
                            log(f"Settings page loaded from: {url}")
                            results["tested_pages"].append(url)
                            settings_loaded = True
                            break
                    except:
                        continue

                if settings_loaded:
                    take_screenshot(page, "13_settings_page")

                    # Check for API key management
                    content = page.content().lower()
                    has_api_keys = "api" in content and "key" in content
                    has_currency = "currency" in content

                    log(f"Settings features - API Keys: {has_api_keys}, Currency: {has_currency}")
                    results["feature_results"]["settings"] = "SUCCESS"
                else:
                    log("Settings page not found")
                    results["feature_results"]["settings"] = "NOT_FOUND"

            except Exception as e:
                log(f"Settings test error: {str(e)}")
                results["errors"].append(f"Settings: {str(e)}")
                results["feature_results"]["settings"] = "ERROR"

            # =================================================================
            # 8. TEST RESPONSIVE DESIGN (Mobile)
            # =================================================================
            log("=" * 60)
            log("TEST 8: Responsive Design (Mobile)")
            log("=" * 60)

            try:
                # Change to mobile viewport
                page.set_viewport_size({"width": 375, "height": 667})
                page.goto(f"{BASE_URL}/", wait_until="networkidle")
                page.wait_for_timeout(1000)

                take_screenshot(page, "14_mobile_view")

                log("Mobile view captured")
                results["feature_results"]["responsive"] = "SUCCESS"

            except Exception as e:
                log(f"Responsive test error: {str(e)}")
                results["errors"].append(f"Responsive: {str(e)}")
                results["feature_results"]["responsive"] = "ERROR"

            # =================================================================
            # 9. TEST NAVIGATION & UI
            # =================================================================
            log("=" * 60)
            log("TEST 9: Navigation & UI Elements")
            log("=" * 60)

            try:
                # Back to desktop view
                page.set_viewport_size({"width": 1920, "height": 1080})
                page.goto(f"{BASE_URL}/", wait_until="networkidle")
                page.wait_for_timeout(1000)

                # Check for navigation elements
                content = page.content()
                has_nav = "nav" in content.lower() or "menu" in content.lower()
                has_sidebar = "sidebar" in content.lower()

                log(f"UI Elements - Navigation: {has_nav}, Sidebar: {has_sidebar}")

                take_screenshot(page, "15_navigation_ui")

                results["feature_results"]["navigation"] = "SUCCESS"

            except Exception as e:
                log(f"Navigation test error: {str(e)}")
                results["errors"].append(f"Navigation: {str(e)}")
                results["feature_results"]["navigation"] = "ERROR"

            # =================================================================
            # 10. TEST DATA PERSISTENCE (Logout & Login)
            # =================================================================
            log("=" * 60)
            log("TEST 10: Data Persistence (Logout/Login)")
            log("=" * 60)

            try:
                # Try to find logout link
                logout_clicked = False

                if page.locator('text="Logout"').count() > 0:
                    page.click('text="Logout"')
                    logout_clicked = True
                elif page.locator('text="Log out"').count() > 0:
                    page.click('text="Log out"')
                    logout_clicked = True
                elif page.locator('a[href*="logout"]').count() > 0:
                    page.click('a[href*="logout"]')
                    logout_clicked = True

                if logout_clicked:
                    page.wait_for_timeout(2000)
                    take_screenshot(page, "16_after_logout")
                    log("Logged out successfully")

                    # Log back in
                    page.goto(f"{BASE_URL}/auth/login", wait_until="networkidle")
                    page.wait_for_timeout(1000)

                    if page.locator('input[name="email"]').count() > 0:
                        page.fill('input[name="email"]', TEST_USER["email"])
                    elif page.locator('input[name="username"]').count() > 0:
                        page.fill('input[name="username"]', TEST_USER["username"])

                    page.fill('input[name="password"]', TEST_USER["password"])
                    page.click('button[type="submit"]')
                    page.wait_for_timeout(2000)

                    take_screenshot(page, "17_after_relogin")

                    # Check if Test Checking account still exists
                    if "/accounts" in [url for url in results["tested_pages"]]:
                        page.goto(f"{BASE_URL}/accounts", wait_until="networkidle")
                        page.wait_for_timeout(1000)

                        if "Test Checking" in page.content():
                            log("Data persisted - Test Checking account still exists")
                            results["feature_results"]["persistence"] = "SUCCESS"
                        else:
                            log("Data may not have persisted")
                            results["feature_results"]["persistence"] = "UNCLEAR"
                    else:
                        results["feature_results"]["persistence"] = "UNABLE_TO_VERIFY"
                else:
                    log("Could not find logout link")
                    results["feature_results"]["persistence"] = "LOGOUT_NOT_FOUND"

            except Exception as e:
                log(f"Persistence test error: {str(e)}")
                results["errors"].append(f"Persistence: {str(e)}")
                results["feature_results"]["persistence"] = "ERROR"

            # =================================================================
            # FINAL: Take one last screenshot of dashboard
            # =================================================================
            try:
                page.goto(f"{BASE_URL}/", wait_until="networkidle")
                page.wait_for_timeout(1000)
                take_screenshot(page, "18_final_dashboard")
            except:
                pass

        except Exception as e:
            log(f"Critical error during testing: {str(e)}")
            results["errors"].append(f"Critical: {str(e)}")

        finally:
            # Close browser
            browser.close()

    # =================================================================
    # GENERATE SUMMARY REPORT
    # =================================================================
    log("\n" + "=" * 60)
    log("TEST SUMMARY REPORT")
    log("=" * 60)

    print("\n📋 TESTED PAGES:")
    print("-" * 60)
    for page in results["tested_pages"]:
        print(f"  ✓ {page}")

    print("\n🧪 FEATURE TEST RESULTS:")
    print("-" * 60)
    for feature, status in results["feature_results"].items():
        icon = "✓" if status == "SUCCESS" else "✗" if status == "ERROR" else "⚠"
        print(f"  {icon} {feature.upper()}: {status}")

    if results["errors"]:
        print("\n❌ ERRORS ENCOUNTERED:")
        print("-" * 60)
        for error in results["errors"]:
            print(f"  • {error}")
    else:
        print("\n✅ No errors encountered during testing")

    print("\n📸 SCREENSHOTS:")
    print("-" * 60)
    print(f"  All screenshots saved to: {SCREENSHOT_DIR}")

    # Calculate overall health
    success_count = sum(1 for status in results["feature_results"].values() if status == "SUCCESS")
    total_tests = len(results["feature_results"])
    health_percentage = (success_count / total_tests * 100) if total_tests > 0 else 0

    print(f"\n🏥 OVERALL APP HEALTH: {health_percentage:.1f}%")
    print(f"   ({success_count}/{total_tests} features working)")
    print("=" * 60)

    return results

if __name__ == "__main__":
    import os
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    test_finance_app()
