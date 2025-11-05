#!/usr/bin/env python3
"""
Test script to verify digital wallets are included in total assets calculation.

This script:
1. Logs in to the finance application
2. Records initial Total Assets value
3. Creates a new digital wallet account
4. Verifies the digital wallet appears in accounts list
5. Verifies Total Assets includes the digital wallet balance
6. Takes screenshots for verification
"""

from playwright.sync_api import sync_playwright
import time

def test_digital_wallet_assets():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            print("Step 1: Navigating to http://localhost:5001/")
            page.goto('http://localhost:5001/')
            page.wait_for_load_state('networkidle')

            # Take screenshot of login page
            page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/01_login_page.png', full_page=True)
            print("  Screenshot saved: 01_login_page.png")

            print("\nStep 2: Logging in with testuser3")
            # Fill login form
            page.fill('input[name="username"]', 'testuser3')
            page.fill('input[name="password"]', 'TestPass123!')
            page.click('button[type="submit"]')
            page.wait_for_load_state('networkidle')

            # Wait a moment for redirect
            time.sleep(1)
            page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/02_after_login.png', full_page=True)
            print("  Screenshot saved: 02_after_login.png")
            print(f"  Current URL: {page.url}")

            print("\nStep 3: Navigating to Accounts section")
            # Look for Accounts link/button
            accounts_link = page.locator('a:has-text("Accounts"), button:has-text("Accounts")').first
            if accounts_link.is_visible():
                accounts_link.click()
            else:
                # Try navigating directly
                page.goto('http://localhost:5001/accounts')

            page.wait_for_load_state('networkidle')
            time.sleep(1)

            # Record initial Total Assets
            total_assets_locator = page.locator('text=/Total Assets/i').locator('..').locator('text=/\\$[\\d,]+\\.\\d{2}/')
            initial_total_text = ""

            try:
                # Try to find Total Assets value
                if total_assets_locator.count() > 0:
                    initial_total_text = total_assets_locator.first.inner_text()
                else:
                    # Try alternative selectors
                    alt_locator = page.locator('.total-assets, [class*="total"], [id*="total"]')
                    if alt_locator.count() > 0:
                        initial_total_text = alt_locator.first.inner_text()
                    else:
                        # Get all text to find it manually
                        page_text = page.content()
                        print("  Could not find Total Assets with standard selectors")
            except Exception as e:
                print(f"  Warning: Could not read initial Total Assets: {e}")

            page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/03_accounts_page_before.png', full_page=True)
            print("  Screenshot saved: 03_accounts_page_before.png")
            print(f"  Initial Total Assets: {initial_total_text if initial_total_text else 'Not found'}")

            print("\nStep 4: Creating new Digital Wallet account")
            # Look for "Add Account" or "New Account" button
            add_button = page.locator('button:has-text("Add"), button:has-text("New"), a:has-text("Add"), a:has-text("New")').first

            if add_button.is_visible():
                add_button.click()
                page.wait_for_load_state('networkidle')
                time.sleep(1)
            else:
                print("  Add button not found, looking for form...")

            page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/04_add_account_form.png', full_page=True)
            print("  Screenshot saved: 04_add_account_form.png")

            # Fill in the form
            print("  Filling form fields:")
            print("    Name: Bitcoin Wallet")
            page.fill('input[name="name"], input[id="name"], input[placeholder*="name" i]', 'Bitcoin Wallet')

            print("    Type: Digital Wallet")
            # Try different selectors for type dropdown
            type_selectors = [
                'select[name="type"]',
                'select[id="type"]',
                'select[name="account_type"]',
                'select[id="account_type"]'
            ]

            for selector in type_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        page.select_option(selector, label='Digital Wallet')
                        break
                except Exception:
                    continue

            print("    Starting Balance: 2500.50")
            page.fill('input[name="balance"], input[id="balance"], input[name="starting_balance"], input[placeholder*="balance" i]', '2500.50')

            page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/05_form_filled.png', full_page=True)
            print("  Screenshot saved: 05_form_filled.png")

            # Submit the form
            print("  Submitting form...")
            submit_button = page.locator('button[type="submit"], input[type="submit"], button:has-text("Create"), button:has-text("Add"), button:has-text("Save")').first
            submit_button.click()
            page.wait_for_load_state('networkidle')
            time.sleep(2)  # Give it extra time to update

            page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/06_after_creation.png', full_page=True)
            print("  Screenshot saved: 06_after_creation.png")

            print("\nStep 5: Verifying digital wallet appears in accounts list")
            # Check if "Bitcoin Wallet" appears
            bitcoin_wallet = page.locator('text="Bitcoin Wallet"')
            if bitcoin_wallet.count() > 0:
                print("  ✓ Bitcoin Wallet account found in list")
            else:
                print("  ✗ Bitcoin Wallet account NOT found in list")

            # Check if Digital Wallet type appears
            digital_wallet_type = page.locator('text=/Digital Wallet/i')
            if digital_wallet_type.count() > 0:
                print("  ✓ Digital Wallet type found")
            else:
                print("  ✗ Digital Wallet type NOT found")

            # Check if the balance appears
            balance_2500 = page.locator('text=/2,?500\\.50/')
            if balance_2500.count() > 0:
                print("  ✓ Balance $2,500.50 found")
            else:
                print("  ✗ Balance $2,500.50 NOT found")

            print("\nStep 6: Checking updated Total Assets on Accounts page")
            # Read new Total Assets value
            new_total_text = ""
            try:
                if total_assets_locator.count() > 0:
                    new_total_text = total_assets_locator.first.inner_text()
                else:
                    alt_locator = page.locator('.total-assets, [class*="total"], [id*="total"]')
                    if alt_locator.count() > 0:
                        new_total_text = alt_locator.first.inner_text()
            except Exception as e:
                print(f"  Warning: Could not read new Total Assets: {e}")

            print(f"  Updated Total Assets on Accounts page: {new_total_text if new_total_text else 'Not found'}")

            page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/07_accounts_updated_total.png', full_page=True)
            print("  Screenshot saved: 07_accounts_updated_total.png")

            print("\nStep 7: Navigating to Dashboard to verify total assets")
            # Navigate to dashboard
            dashboard_link = page.locator('a:has-text("Dashboard"), button:has-text("Dashboard")').first
            if dashboard_link.is_visible():
                dashboard_link.click()
            else:
                page.goto('http://localhost:5001/dashboard')

            page.wait_for_load_state('networkidle')
            time.sleep(1)

            # Read Total Assets on dashboard
            dashboard_total_text = ""
            try:
                if total_assets_locator.count() > 0:
                    dashboard_total_text = total_assets_locator.first.inner_text()
                else:
                    alt_locator = page.locator('.total-assets, [class*="total"], [id*="total"]')
                    if alt_locator.count() > 0:
                        dashboard_total_text = alt_locator.first.inner_text()
            except Exception as e:
                print(f"  Warning: Could not read Dashboard Total Assets: {e}")

            print(f"  Total Assets on Dashboard: {dashboard_total_text if dashboard_total_text else 'Not found'}")

            page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/08_dashboard_total_assets.png', full_page=True)
            print("  Screenshot saved: 08_dashboard_total_assets.png")

            print("\n" + "="*60)
            print("SUMMARY REPORT")
            print("="*60)
            print(f"Initial Total Assets:           {initial_total_text if initial_total_text else 'Not captured'}")
            print(f"Total Assets after creation:    {new_total_text if new_total_text else 'Not captured'}")
            print(f"Dashboard Total Assets:         {dashboard_total_text if dashboard_total_text else 'Not captured'}")
            print(f"\nDigital Wallet Balance Added:   $2,500.50")
            print("="*60)

            if initial_total_text and new_total_text:
                # Try to parse and compare
                try:
                    import re
                    initial_val = float(re.sub(r'[^\d.]', '', initial_total_text))
                    new_val = float(re.sub(r'[^\d.]', '', new_total_text))
                    difference = new_val - initial_val
                    print(f"\nCalculated difference: ${difference:.2f}")
                    if abs(difference - 2500.50) < 0.01:
                        print("✓ PASS: Digital wallet balance correctly added to Total Assets")
                    else:
                        print(f"✗ FAIL: Expected difference of $2,500.50, but got ${difference:.2f}")
                except Exception as e:
                    print(f"Could not calculate difference: {e}")

        except Exception as e:
            print(f"\nError during test: {e}")
            page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/error_screenshot.png', full_page=True)
            print("Error screenshot saved: error_screenshot.png")
            raise

        finally:
            browser.close()
            print("\nBrowser closed")

if __name__ == '__main__':
    test_digital_wallet_assets()
