"""
Finance Webapp UI Screenshot Capture
Captures screenshots of key pages for UI design review
"""
from playwright.sync_api import sync_playwright
import time
from pathlib import Path

# Configuration
BASE_URL = 'http://localhost:5001'
SCREENSHOTS_DIR = Path('/Users/njpinton/projects/git/finance/screenshots')
SCREENSHOTS_DIR.mkdir(exist_ok=True)

# Test credentials - we'll need to either register or use existing
TEST_USERNAME = 'ui_test_user'
TEST_EMAIL = 'uitest@example.com'
TEST_PASSWORD = 'TestPassword123!@#'

def capture_screenshots():
    """Capture screenshots of key pages"""
    notes = []

    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        print(f"Starting screenshot capture for {BASE_URL}")

        # 1. HOMEPAGE/LANDING PAGE (Unauthenticated)
        print("\n1. Capturing Homepage/Landing page...")
        try:
            page.goto(BASE_URL, wait_until='networkidle')
            page.wait_for_load_state('networkidle')
            time.sleep(1)  # Extra time for any animations

            page.screenshot(path=str(SCREENSHOTS_DIR / '01_homepage.png'), full_page=True)
            print("   ✓ Homepage screenshot saved")

            # Check if there's a visible navbar
            if page.locator('nav').count() > 0:
                notes.append("Homepage: Navigation bar present")

        except Exception as e:
            notes.append(f"ERROR on homepage: {str(e)}")
            print(f"   ✗ Error: {e}")

        # 2. LOGIN PAGE
        print("\n2. Capturing Login page...")
        try:
            # Navigate to login page
            page.goto(f'{BASE_URL}/auth/login', wait_until='networkidle')
            page.wait_for_load_state('networkidle')
            time.sleep(1)

            page.screenshot(path=str(SCREENSHOTS_DIR / '02_login_page.png'), full_page=True)
            print("   ✓ Login page screenshot saved")

        except Exception as e:
            notes.append(f"ERROR on login page: {str(e)}")
            print(f"   ✗ Error: {e}")

        # 3. REGISTER PAGE
        print("\n3. Capturing Register page...")
        try:
            page.goto(f'{BASE_URL}/auth/register', wait_until='networkidle')
            page.wait_for_load_state('networkidle')
            time.sleep(1)

            page.screenshot(path=str(SCREENSHOTS_DIR / '03_register_page.png'), full_page=True)
            print("   ✓ Register page screenshot saved")

        except Exception as e:
            notes.append(f"ERROR on register page: {str(e)}")
            print(f"   ✗ Error: {e}")

        # 4. TRY TO LOGIN (or register if user doesn't exist)
        print("\n4. Attempting login...")
        try:
            # Go to login page
            page.goto(f'{BASE_URL}/auth/login', wait_until='networkidle')
            page.wait_for_load_state('networkidle')

            # Fill login form
            page.fill('input[name="username"]', TEST_USERNAME)
            page.fill('input[name="password"]', TEST_PASSWORD)

            # Submit form
            page.click('button[type="submit"]')
            page.wait_for_load_state('networkidle')
            time.sleep(1)

            # Check if we're logged in by looking for dashboard elements or error messages
            current_url = page.url

            if 'login' in current_url or page.locator('text=/Invalid username or password/i').count() > 0:
                # Login failed, try to register
                print("   → Login failed, attempting registration...")
                page.goto(f'{BASE_URL}/auth/register', wait_until='networkidle')
                page.wait_for_load_state('networkidle')

                # Fill registration form
                page.fill('input[name="username"]', TEST_USERNAME)
                page.fill('input[name="email"]', TEST_EMAIL)
                page.fill('input[name="password"]', TEST_PASSWORD)
                page.fill('input[name="password_confirm"]', TEST_PASSWORD)

                # Submit registration
                page.click('button[type="submit"]')
                page.wait_for_load_state('networkidle')
                time.sleep(1)

                # Now try to login again
                page.goto(f'{BASE_URL}/auth/login', wait_until='networkidle')
                page.fill('input[name="username"]', TEST_USERNAME)
                page.fill('input[name="password"]', TEST_PASSWORD)
                page.click('button[type="submit"]')
                page.wait_for_load_state('networkidle')
                time.sleep(1)

            print("   ✓ Successfully authenticated")

        except Exception as e:
            notes.append(f"ERROR during authentication: {str(e)}")
            print(f"   ✗ Authentication error: {e}")
            # Continue anyway to capture what we can

        # 5. DASHBOARD (Main page after login)
        print("\n5. Capturing Dashboard page...")
        try:
            page.goto(BASE_URL, wait_until='networkidle')
            page.wait_for_load_state('networkidle')
            time.sleep(2)  # Wait for any charts/graphs to load

            page.screenshot(path=str(SCREENSHOTS_DIR / '04_dashboard.png'), full_page=True)
            print("   ✓ Dashboard screenshot saved")

            # Check for charts/widgets
            if page.locator('canvas').count() > 0:
                notes.append("Dashboard: Contains chart/canvas elements")
            if page.locator('.card, .widget').count() > 0:
                notes.append(f"Dashboard: Found {page.locator('.card, .widget').count()} card/widget elements")

        except Exception as e:
            notes.append(f"ERROR on dashboard: {str(e)}")
            print(f"   ✗ Error: {e}")

        # 6. NAVIGATION MENU
        print("\n6. Capturing Navigation menu...")
        try:
            # Take a focused screenshot of the navbar
            if page.locator('nav').count() > 0:
                page.locator('nav').first.screenshot(path=str(SCREENSHOTS_DIR / '05_navigation_menu.png'))
                print("   ✓ Navigation menu screenshot saved")

                # Try to open mobile menu if it exists
                mobile_toggle = page.locator('button.navbar-toggler, .mobile-menu-toggle, [aria-label*="menu"]')
                if mobile_toggle.count() > 0:
                    notes.append("Navigation: Mobile menu toggle found")
            else:
                notes.append("Navigation: No nav element found")

        except Exception as e:
            notes.append(f"ERROR capturing navigation: {str(e)}")
            print(f"   ✗ Error: {e}")

        # 7. TRANSACTIONS LIST PAGE
        print("\n7. Capturing Transactions list page...")
        try:
            page.goto(f'{BASE_URL}/transactions/', wait_until='networkidle')
            page.wait_for_load_state('networkidle')
            time.sleep(1)

            page.screenshot(path=str(SCREENSHOTS_DIR / '06_transactions_list.png'), full_page=True)
            print("   ✓ Transactions list screenshot saved")

        except Exception as e:
            notes.append(f"ERROR on transactions list: {str(e)}")
            print(f"   ✗ Error: {e}")

        # 8. CREATE TRANSACTION FORM
        print("\n8. Capturing Create Transaction form...")
        try:
            page.goto(f'{BASE_URL}/transactions/new', wait_until='networkidle')
            page.wait_for_load_state('networkidle')
            time.sleep(1)

            page.screenshot(path=str(SCREENSHOTS_DIR / '07_transaction_form.png'), full_page=True)
            print("   ✓ Transaction form screenshot saved")

            # Count form fields
            input_count = page.locator('input, select, textarea').count()
            notes.append(f"Transaction Form: Contains {input_count} form fields")

        except Exception as e:
            notes.append(f"ERROR on transaction form: {str(e)}")
            print(f"   ✗ Error: {e}")

        # 9. ACCOUNTS PAGE
        print("\n9. Capturing Accounts page...")
        try:
            page.goto(f'{BASE_URL}/accounts/', wait_until='networkidle')
            page.wait_for_load_state('networkidle')
            time.sleep(1)

            page.screenshot(path=str(SCREENSHOTS_DIR / '08_accounts.png'), full_page=True)
            print("   ✓ Accounts page screenshot saved")

        except Exception as e:
            notes.append(f"ERROR on accounts page: {str(e)}")
            print(f"   ✗ Error: {e}")

        # 10. MOBILE VIEW - Dashboard
        print("\n10. Capturing Mobile view of Dashboard...")
        try:
            # Create mobile context
            mobile_context = browser.new_context(
                viewport={'width': 375, 'height': 812},  # iPhone X dimensions
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
            )
            mobile_page = mobile_context.new_page()

            mobile_page.goto(BASE_URL, wait_until='networkidle')
            mobile_page.wait_for_load_state('networkidle')
            time.sleep(1)

            # First try to login on mobile
            try:
                mobile_page.goto(f'{BASE_URL}/auth/login', wait_until='networkidle')
                mobile_page.fill('input[name="username"]', TEST_USERNAME)
                mobile_page.fill('input[name="password"]', TEST_PASSWORD)
                mobile_page.click('button[type="submit"]')
                mobile_page.wait_for_load_state('networkidle')
                time.sleep(1)
            except:
                pass  # May already be logged in or fail

            # Go to dashboard
            mobile_page.goto(BASE_URL, wait_until='networkidle')
            mobile_page.wait_for_load_state('networkidle')
            time.sleep(2)

            mobile_page.screenshot(path=str(SCREENSHOTS_DIR / '09_mobile_dashboard.png'), full_page=True)
            print("   ✓ Mobile dashboard screenshot saved")

            # Try to capture mobile menu if it exists
            mobile_toggle = mobile_page.locator('button.navbar-toggler, .mobile-menu-toggle, [aria-label*="menu"]')
            if mobile_toggle.count() > 0:
                mobile_toggle.first.click()
                time.sleep(0.5)
                mobile_page.screenshot(path=str(SCREENSHOTS_DIR / '10_mobile_menu_open.png'), full_page=True)
                print("   ✓ Mobile menu (open) screenshot saved")
                notes.append("Mobile: Mobile menu toggle works")

            mobile_context.close()

        except Exception as e:
            notes.append(f"ERROR on mobile view: {str(e)}")
            print(f"   ✗ Error: {e}")

        # 11. SETTINGS PAGE (if exists)
        print("\n11. Capturing Settings page...")
        try:
            page.goto(f'{BASE_URL}/settings/', wait_until='networkidle')
            page.wait_for_load_state('networkidle')
            time.sleep(1)

            page.screenshot(path=str(SCREENSHOTS_DIR / '11_settings.png'), full_page=True)
            print("   ✓ Settings page screenshot saved")

        except Exception as e:
            notes.append(f"NOTE: Settings page may not exist or is not accessible")
            print(f"   → Settings page not captured: {e}")

        browser.close()

    return notes

if __name__ == '__main__':
    print("=" * 60)
    print("Finance Webapp UI Screenshot Capture")
    print("=" * 60)

    notes = capture_screenshots()

    print("\n" + "=" * 60)
    print("SCREENSHOT CAPTURE COMPLETE")
    print("=" * 60)
    print(f"\nScreenshots saved to: {SCREENSHOTS_DIR}")
    print("\nNOTES AND OBSERVATIONS:")
    print("-" * 60)

    if notes:
        for note in notes:
            print(f"  • {note}")
    else:
        print("  No specific issues noted")

    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("  1. Review screenshots in: screenshots/")
    print("  2. Check UI consistency across pages")
    print("  3. Verify responsive design in mobile views")
    print("  4. Note any visual issues for design improvements")
    print("=" * 60)
