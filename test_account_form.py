#!/usr/bin/env python3
"""
Test script for account creation form with updated starting balance field.
Tests that the field is a text input without spinner buttons and accepts decimal values.
"""

from playwright.sync_api import sync_playwright
import time

def test_account_form():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            print("Step 1: Navigating to http://localhost:5001/")
            page.goto('http://localhost:5001/')
            page.wait_for_load_state('networkidle')

            print("Step 2: Clicking Login and logging in...")
            # Navigate directly to login page
            page.goto('http://localhost:5001/auth/login')
            page.wait_for_load_state('networkidle')

            # Fill in login form
            print("  - Entering credentials...")
            username_field = page.locator('input[name="username"], input#username').first
            password_field = page.locator('input[name="password"], input#password').first

            username_field.fill('automation_test')
            password_field.fill('TestPass123!')

            # Take screenshot before login
            page.screenshot(path='/tmp/before_login.png', full_page=True)
            print("  - Screenshot before login: /tmp/before_login.png")

            # Submit login
            page.locator('button[type="submit"]').first.click()
            page.wait_for_load_state('networkidle')
            time.sleep(1)  # Give time for redirect

            # Check if login was successful
            current_url = page.url
            print(f"  - URL after login: {current_url}")

            # Take screenshot after login
            page.screenshot(path='/tmp/after_login.png', full_page=True)
            print("  - Screenshot after login: /tmp/after_login.png")

            # Check if we're still on login page (failed login)
            if '/auth/login' in current_url:
                error_msg = page.locator('.alert-danger, .error, [class*="error"]').first
                if error_msg.is_visible():
                    print(f"  ✗ Login failed: {error_msg.text_content()}")
                    print("\n  Attempting to register new user instead...")

                    # Try to register a new user
                    page.goto('http://localhost:5001/auth/register')
                    page.wait_for_load_state('networkidle')

                    import random
                    test_username = f"testuser_{int(time.time())}"
                    test_password = "TestPass123!"

                    page.fill('input[name="username"]', test_username)
                    page.fill('input[name="password"]', test_password)
                    page.fill('input[name="password2"], input[name="confirm_password"]', test_password)
                    page.locator('button[type="submit"]').first.click()
                    page.wait_for_load_state('networkidle')
                    time.sleep(1)

                    print(f"  - Registered new user: {test_username}")
            else:
                print("  - Login successful")

            print("\nStep 3: Navigating to Add Account page...")
            # Take screenshot of dashboard to see navigation
            page.screenshot(path='/tmp/dashboard.png', full_page=True)
            print("  - Dashboard screenshot: /tmp/dashboard.png")

            # Click the "Create Account" button visible on the dashboard
            create_account_btn = page.locator('button:has-text("Create Account"), a:has-text("Create Account")').first
            if create_account_btn.is_visible():
                print("  - Clicking 'Create Account' button...")
                create_account_btn.click()
                page.wait_for_load_state('networkidle')
                time.sleep(0.5)
            else:
                # Try the + button in the Accounts section
                plus_button = page.locator('button:has-text("+")').first
                if plus_button.is_visible():
                    print("  - Clicking '+' button...")
                    plus_button.click()
                    page.wait_for_load_state('networkidle')
                    time.sleep(0.5)

            print(f"  - Current URL: {page.url}")

            print("\nStep 4: Inspecting Starting Balance field...")
            # Take screenshot of the form
            page.screenshot(path='/tmp/account_form_before.png', full_page=True)
            print("  - Screenshot saved: /tmp/account_form_before.png")

            # Find the starting balance input
            balance_input = page.locator('input[name*="balance" i], input[id*="balance" i]').first

            if balance_input.is_visible():
                # Get the input type
                input_type = balance_input.get_attribute('type')
                print(f"  - Input type: {input_type}")

                # Check if it has step attribute (number inputs typically have this)
                step_attr = balance_input.get_attribute('step')
                print(f"  - Step attribute: {step_attr if step_attr else 'None'}")

                # Get computed styles to check for spinner buttons
                spinner_check = page.evaluate('''(selector) => {
                    const input = document.querySelector(selector);
                    if (!input) return 'Input not found';

                    const type = input.getAttribute('type');
                    const computedStyle = window.getComputedStyle(input);

                    // Check for WebKit spinner button styles
                    const webkitAppearance = computedStyle.webkitAppearance || computedStyle.appearance;

                    return {
                        type: type,
                        webkitAppearance: webkitAppearance,
                        hasSpinnerHidden: input.style.appearance === 'textfield' ||
                                         input.style.webkitAppearance === 'textfield'
                    };
                }''', 'input[name*="balance" i], input[id*="balance" i]')

                print(f"  - Field properties: {spinner_check}")

                # Determine if spinner buttons are present
                has_spinners = input_type == 'number' and not (
                    spinner_check.get('hasSpinnerHidden') or
                    input_type == 'text'
                )

                print(f"\n✓ Spinner buttons present: {'YES' if has_spinners else 'NO'}")

                print("\nStep 5: Testing decimal value entry...")
                # Clear and enter decimal value
                balance_input.clear()
                balance_input.fill('1500.75')
                entered_value = balance_input.input_value()
                print(f"  - Entered value: {entered_value}")
                print(f"  ✓ Can type decimal values: {'YES' if '1500.75' in entered_value else 'NO'}")

                # Fill in other required fields
                print("\nStep 6: Filling out rest of form...")

                # Try to find and fill account name
                account_name = page.locator('input[name*="name" i], input[id*="name" i]').first
                if account_name.is_visible():
                    account_name.fill('Test Account - Balance Field Test')
                    print("  - Account name filled")

                # Try to find and fill account type
                account_type = page.locator('select[name*="type" i], select[id*="type" i]').first
                if account_type.is_visible():
                    account_type.select_option(index=1)  # Select first non-empty option
                    print("  - Account type selected")

                # Take screenshot before submit
                page.screenshot(path='/tmp/account_form_filled.png', full_page=True)
                print("  - Screenshot saved: /tmp/account_form_filled.png")

                print("\nStep 7: Submitting form...")
                # Find and click submit button
                submit_button = page.locator('button[type="submit"], input[type="submit"]').first

                # Set up response listener to catch validation errors
                validation_messages = []

                def handle_console(msg):
                    if msg.type in ['error', 'warning']:
                        validation_messages.append(f"{msg.type}: {msg.text}")

                page.on('console', handle_console)

                submit_button.click()
                page.wait_for_load_state('networkidle')
                time.sleep(1)

                # Take final screenshot
                page.screenshot(path='/tmp/account_form_result.png', full_page=True)
                print("  - Screenshot saved: /tmp/account_form_result.png")

                print(f"\n  - Final URL: {page.url}")

                # Check for success or error messages
                success_msg = page.locator('.alert-success, .success, [class*="success"]').all()
                error_msg = page.locator('.alert-error, .error, [class*="error"], .alert-danger').all()

                if success_msg:
                    print("  ✓ Success message found")
                    for msg in success_msg:
                        if msg.is_visible():
                            print(f"    - {msg.text_content()}")

                if error_msg:
                    print("  ✗ Error messages found:")
                    for msg in error_msg:
                        if msg.is_visible():
                            print(f"    - {msg.text_content()}")

                if validation_messages:
                    print("  - Console messages:")
                    for msg in validation_messages:
                        print(f"    - {msg}")

                # Check if we were redirected to accounts list (success indicator)
                if 'account' in page.url.lower() and 'add' not in page.url.lower():
                    print("\n  ✓ Redirected to accounts page (likely successful)")

                print("\n" + "="*60)
                print("SUMMARY")
                print("="*60)
                print(f"✓ Starting Balance field type: {input_type}")
                print(f"✓ Spinner buttons removed: {'YES' if not has_spinners else 'NO'}")
                print(f"✓ Accepts decimal values: {'YES' if '1500.75' in entered_value else 'NO'}")
                print(f"✓ Form submission: {'Appears successful' if not error_msg else 'Had errors'}")
                print("="*60)

            else:
                print("  ✗ Could not find starting balance input field")
                page.screenshot(path='/tmp/account_form_not_found.png', full_page=True)
                print("  - Screenshot saved: /tmp/account_form_not_found.png")

        except Exception as e:
            print(f"\n✗ Error during test: {e}")
            page.screenshot(path='/tmp/account_form_error.png', full_page=True)
            print("  - Error screenshot saved: /tmp/account_form_error.png")
            raise

        finally:
            browser.close()
            print("\nTest completed.")

if __name__ == '__main__':
    test_account_form()
