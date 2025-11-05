#!/usr/bin/env python3
"""
Test script for Finance Tracker receipt upload functionality.
Tests the complete flow from login to receipt upload and verification.
"""

from playwright.sync_api import sync_playwright
import sys
import time
import random

# Generate a unique username to avoid conflicts
UNIQUE_ID = int(time.time())
USERNAME = f'testuser_{UNIQUE_ID}'
PASSWORD = 'TestPass123!@#'
EMAIL = f'{USERNAME}@example.com'

def test_receipt_upload():
    """Test the receipt upload flow."""

    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Enable console logging
        page.on("console", lambda msg: print(f"[CONSOLE] {msg.type}: {msg.text}"))

        # Track responses
        responses = []
        def log_response(response):
            responses.append({
                'url': response.url,
                'status': response.status,
                'status_text': response.status_text
            })
            print(f"[RESPONSE] {response.status} {response.url}")

        page.on("response", log_response)

        try:
            print("\n=== Step 1: Navigate to homepage ===")
            page.goto('http://localhost:5001/')
            page.wait_for_load_state('networkidle')
            page.screenshot(path='/tmp/screenshot_1_homepage.png', full_page=True)
            print(f"Page title: {page.title()}")

            print("\n=== Step 2: Register new user ===")
            print(f"Creating user: {USERNAME}")
            # Try to register the user first
            page.goto('http://localhost:5001/auth/register')
            page.wait_for_load_state('networkidle')

            # Fill registration form
            page.locator('input[name="username"]').fill(USERNAME)
            page.locator('input[name="email"]').fill(EMAIL)
            page.locator('input[name="password"]').fill(PASSWORD)
            page.locator('input[name="password_confirm"]').fill(PASSWORD)

            page.screenshot(path='/tmp/screenshot_2_register.png', full_page=True)

            # Submit registration
            page.locator('button[type="submit"]').click()
            page.wait_for_load_state('networkidle')
            page.screenshot(path='/tmp/screenshot_2b_after_register.png', full_page=True)

            # Check result
            if "already exists" in page.content().lower():
                print("WARNING: User already exists (shouldn't happen with timestamp)")
            elif "registration successful" in page.content().lower() or page.url.endswith('/auth/login'):
                print("✓ Registration successful")
            else:
                print("Registration response unclear, checking URL...")
                print(f"Current URL: {page.url}")

            print("\n=== Step 3: Navigate to login page ===")
            # Direct navigation to login page (simpler than clicking link)
            page.goto('http://localhost:5001/auth/login')
            page.wait_for_load_state('networkidle')
            page.screenshot(path='/tmp/screenshot_3_login.png', full_page=True)

            print("\n=== Step 4: Fill in login credentials ===")
            # Fill username
            username_input = page.locator('input[name="username"]')
            username_input.fill(USERNAME)

            # Fill password
            password_input = page.locator('input[name="password"]')
            password_input.fill(PASSWORD)

            page.screenshot(path='/tmp/screenshot_4_login_filled.png', full_page=True)

            print("\n=== Step 5: Submit login form ===")
            # Submit the form
            submit_button = page.locator('button[type="submit"]')
            submit_button.click()

            page.wait_for_load_state('networkidle')
            page.screenshot(path='/tmp/screenshot_5_after_login.png', full_page=True)

            # Check if login was successful
            current_url = page.url
            print(f"Current URL after login: {current_url}")

            # Check if we were redirected away from login page (success)
            if current_url.endswith('/auth/login'):
                print("ERROR: Login failed - still on login page!")
                # Check for error message
                error_alerts = page.locator('.alert-danger, .error').all()
                for alert in error_alerts:
                    print(f"Error message: {alert.text_content()}")
                print("Cannot proceed with receipt upload test")
                return 1
            else:
                print("✓ Login successful!")

            print("\n=== Step 6: Navigate to receipt upload page ===")
            page.goto('http://localhost:5001/receipts/upload-new')
            page.wait_for_load_state('networkidle')
            page.screenshot(path='/tmp/screenshot_6_upload_page.png', full_page=True)

            print(f"Upload page URL: {page.url}")
            print(f"Upload page title: {page.title()}")

            print("\n=== Step 7: Fill in receipt upload form ===")

            # Upload the test receipt image
            file_input = page.locator('input[type="file"]')
            if file_input.count() > 0:
                file_input.set_input_files('/tmp/test_receipt.png')
                print("✓ File uploaded")
            else:
                print("ERROR: File input not found")
                page.screenshot(path='/tmp/screenshot_error_no_file_input.png', full_page=True)

            # Select account dropdown - try to find "Cash"
            account_select = page.locator('select[name="account_id"]')
            if account_select.count() > 0:
                # Get all options
                options = account_select.locator('option').all()
                print(f"Available account options: {len(options)}")
                for option in options:
                    option_text = option.text_content()
                    print(f"  - {option_text}")

                # Try to select Cash
                try:
                    account_select.select_option(label="Cash")
                    print("✓ Selected 'Cash' account")
                except Exception as e:
                    print(f"Could not select 'Cash', trying by value: {e}")
                    # Try to get the first non-empty option
                    account_select.select_option(index=1)
            else:
                print("ERROR: Account select dropdown not found")

            page.screenshot(path='/tmp/screenshot_7_form_filled.png', full_page=True)

            print("\n=== Step 8: Submit upload form ===")

            # Find and click submit button
            submit_button = page.locator('button[type="submit"]')
            if submit_button.count() == 0:
                # Try input type submit
                submit_button = page.locator('input[type="submit"]')

            if submit_button.count() > 0:
                print("Clicking submit button...")
                submit_button.click()

                # Wait for initial page load
                print("Waiting for page to process upload (this may take a moment)...")
                page.wait_for_load_state('networkidle', timeout=30000)

                page.screenshot(path='/tmp/screenshot_8_initial_processing.png', full_page=True)

                # The processing happens via AJAX, so we need to wait for completion
                # Look for either success indicators or the processing to finish
                print("Waiting for AI processing to complete (up to 30 seconds)...")
                try:
                    # Wait for the processing button to disappear or change
                    page.wait_for_selector('button:has-text("Processing")', state='hidden', timeout=30000)
                    print("✓ Processing completed")
                except:
                    print("Processing may still be ongoing or completed differently")

                # Give it a moment to render results
                page.wait_for_timeout(2000)

                page.screenshot(path='/tmp/screenshot_8_after_submit.png', full_page=True)

                print(f"\nFinal URL: {page.url}")

                # Analyze the result
                print("\n=== Step 9: Analyze response ===")
                page_text = page.inner_text('body')

                # Check for various response types
                if "rate limit" in page_text.lower() or "quota" in page_text.lower():
                    print("✓ RESULT: Rate limit message detected")
                    print("The Gemini API is currently rate limited")
                elif "no transactions" in page_text.lower() or "could not extract" in page_text.lower():
                    print("✓ RESULT: No transactions extracted")
                    print("The form was processed but no line items were found")
                elif "line item" in page_text.lower() or "transaction" in page_text.lower():
                    print("✓ RESULT: Extracted line items found")
                    print("The receipt was successfully processed with extracted transactions")
                elif "error" in page_text.lower():
                    print("⚠ RESULT: Error message detected")
                    # Try to find error details
                    error_elements = page.locator('.error, .alert-danger, .message.error').all()
                    for elem in error_elements:
                        print(f"Error: {elem.text_content()}")
                else:
                    print("? RESULT: Unknown response type")

                # Look for any flash messages or alerts
                alerts = page.locator('.alert, .message, .flash').all()
                if alerts:
                    print("\nMessages found on page:")
                    for alert in alerts:
                        print(f"  - {alert.text_content().strip()}")

                # Take final screenshot
                page.screenshot(path='/tmp/screenshot_final.png', full_page=True)
                print("\n✓ Final screenshot saved to /tmp/screenshot_final.png")

            else:
                print("ERROR: Submit button not found")
                page.screenshot(path='/tmp/screenshot_error_no_submit.png', full_page=True)

            print("\n=== Summary of HTTP Responses ===")
            for resp in responses:
                print(f"{resp['status']} - {resp['url']}")

            print("\n=== Test Complete ===")

        except Exception as e:
            print(f"\n!!! ERROR: {e}")
            import traceback
            traceback.print_exc()
            page.screenshot(path='/tmp/screenshot_error.png', full_page=True)
            return 1
        finally:
            browser.close()

        return 0

if __name__ == '__main__':
    sys.exit(test_receipt_upload())
