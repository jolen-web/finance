#!/usr/bin/env python3
"""
Test feedback system after AJAX fix.
Verifies form submission, success handling, and list display.
"""
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

# Configuration
BASE_URL = "http://localhost:5001"
USERNAME = "testuser3"
PASSWORD = "TestPass123!"
SCREENSHOTS_DIR = Path("/Users/njpinton/projects/git/finance/screenshots")

# Test data
FEEDBACK_TITLE = "Bug Fix Verification"
FEEDBACK_DESCRIPTION = "Testing the feedback system after AJAX fix"
FEEDBACK_TYPE = "bug"
FEEDBACK_PRIORITY = "high"

def setup_screenshots_dir():
    """Create screenshots directory if it doesn't exist."""
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Screenshots will be saved to: {SCREENSHOTS_DIR}")

def capture_console_logs(page):
    """Set up console log capturing."""
    console_logs = []

    def handle_console(msg):
        console_logs.append({
            'type': msg.type,
            'text': msg.text,
            'location': msg.location
        })

    page.on('console', handle_console)
    return console_logs

def capture_network_responses(page):
    """Set up network response capturing."""
    responses = []

    def handle_response(response):
        responses.append({
            'url': response.url,
            'status': response.status,
            'method': response.request.method
        })

    page.on('response', handle_response)
    return responses

def test_feedback_system():
    """Main test function."""
    results = {
        'login_success': False,
        'form_loaded': False,
        'submission_success': False,
        'redirect_success': False,
        'feedback_in_list': False,
        'errors': [],
        'http_status': None,
        'console_errors': []
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        # Set up monitoring
        console_logs = capture_console_logs(page)
        responses = capture_network_responses(page)

        try:
            # Step 1: Navigate to home page
            print("\n🔄 Step 1: Navigating to home page...")
            page.goto(BASE_URL)
            page.wait_for_load_state('networkidle')
            page.screenshot(path=str(SCREENSHOTS_DIR / "01_home_page.png"), full_page=True)
            print("✅ Home page loaded")

            # Step 2: Click Sign In button
            print("\n🔄 Step 2: Clicking Sign In button...")
            page.click('text=Sign In')
            page.wait_for_load_state('networkidle')
            page.screenshot(path=str(SCREENSHOTS_DIR / "02_login_page.png"), full_page=True)
            print("✅ Login page loaded")

            # Step 3: Log in
            print("\n🔄 Step 3: Logging in...")
            page.fill('input[name="username"]', USERNAME)
            page.fill('input[name="password"]', PASSWORD)
            page.screenshot(path=str(SCREENSHOTS_DIR / "03_login_filled.png"), full_page=True)

            page.click('button[type="submit"]')
            page.wait_for_load_state('networkidle')
            page.screenshot(path=str(SCREENSHOTS_DIR / "04_after_login.png"), full_page=True)

            # Verify login success
            if '/dashboard' in page.url or 'logout' in page.content().lower():
                results['login_success'] = True
                print("✅ Login successful")
            else:
                results['errors'].append("Login failed - not redirected to dashboard")
                print("❌ Login failed")
                return results

            # Step 4: Navigate to feedback form
            print("\n🔄 Step 4: Navigating to feedback form...")
            page.goto(f"{BASE_URL}/feedback/new")
            page.wait_for_load_state('networkidle')
            page.screenshot(path=str(SCREENSHOTS_DIR / "05_feedback_form.png"), full_page=True)

            # Verify form loaded
            if page.locator('form').count() > 0:
                results['form_loaded'] = True
                print("✅ Feedback form loaded")
            else:
                results['errors'].append("Feedback form not found")
                print("❌ Feedback form not found")
                return results

            # Step 5: Fill out the form
            print("\n🔄 Step 5: Filling out feedback form...")
            page.fill('input[name="title"]', FEEDBACK_TITLE)
            page.fill('textarea[name="description"]', FEEDBACK_DESCRIPTION)
            page.select_option('select[name="feedback_type"]', FEEDBACK_TYPE)
            page.select_option('select[name="priority"]', FEEDBACK_PRIORITY)
            page.screenshot(path=str(SCREENSHOTS_DIR / "06_form_filled.png"), full_page=True)
            print("✅ Form filled out")

            # Step 6: Submit the form
            print("\n🔄 Step 6: Submitting form...")
            # Wait for any potential response
            with page.expect_response(lambda response: '/feedback' in response.url) as response_info:
                page.click('button[type="submit"]')

            response = response_info.value
            results['http_status'] = response.status
            print(f"📊 HTTP Status: {response.status}")

            # Wait for navigation or AJAX response
            time.sleep(2)  # Give time for any redirects or AJAX updates
            page.wait_for_load_state('networkidle')
            page.screenshot(path=str(SCREENSHOTS_DIR / "07_after_submit.png"), full_page=True)

            # Step 7: Check for success
            print("\n🔄 Step 7: Verifying submission...")
            current_url = page.url
            print(f"📍 Current URL: {current_url}")

            # Check for success indicators
            page_content = page.content().lower()

            if response.status == 200 or response.status == 302:
                results['submission_success'] = True
                print(f"✅ Submission returned status {response.status}")
            else:
                results['errors'].append(f"Unexpected status code: {response.status}")
                print(f"❌ Unexpected status: {response.status}")

            # Check if redirected to feedback list
            if '/feedback' in current_url and '/new' not in current_url:
                results['redirect_success'] = True
                print("✅ Redirected to feedback list")
            else:
                print(f"⚠️  Not redirected to list (current: {current_url})")

            # Step 8: Navigate to feedback list and verify
            print("\n🔄 Step 8: Checking feedback list...")
            if not results['redirect_success']:
                page.goto(f"{BASE_URL}/feedback/")
                page.wait_for_load_state('networkidle')

            page.screenshot(path=str(SCREENSHOTS_DIR / "08_feedback_list.png"), full_page=True)

            # Look for our feedback in the list
            page_text = page.content()
            if FEEDBACK_TITLE in page_text and FEEDBACK_DESCRIPTION in page_text:
                results['feedback_in_list'] = True
                print(f"✅ Feedback '{FEEDBACK_TITLE}' found in list")
            else:
                results['errors'].append("Feedback not found in list")
                print(f"❌ Feedback '{FEEDBACK_TITLE}' not found in list")

            # Step 9: Capture browser console
            print("\n🔄 Step 9: Checking browser console...")
            page.screenshot(path=str(SCREENSHOTS_DIR / "09_console_check.png"), full_page=True)

            # Filter console errors
            for log in console_logs:
                if log['type'] == 'error':
                    results['console_errors'].append(log['text'])
                    print(f"❌ Console error: {log['text']}")

            if not results['console_errors']:
                print("✅ No console errors detected")

            # Print all network responses for debugging
            print("\n📡 Network Responses:")
            for resp in responses:
                if '/feedback' in resp['url']:
                    print(f"  {resp['method']} {resp['url']} -> {resp['status']}")

        except Exception as e:
            results['errors'].append(f"Exception: {str(e)}")
            print(f"\n❌ Exception occurred: {e}")
            page.screenshot(path=str(SCREENSHOTS_DIR / "error_state.png"), full_page=True)

        finally:
            browser.close()

    return results

def print_summary(results):
    """Print test results summary."""
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)

    print("\n✓ Successful Steps:")
    if results['login_success']:
        print("  • Login successful")
    if results['form_loaded']:
        print("  • Feedback form loaded")
    if results['submission_success']:
        print(f"  • Form submitted (HTTP {results['http_status']})")
    if results['redirect_success']:
        print("  • Redirected to feedback list")
    if results['feedback_in_list']:
        print("  • Feedback appears in list")
    if not results['console_errors']:
        print("  • No console errors")

    if results['errors']:
        print("\n✗ Issues Found:")
        for error in results['errors']:
            print(f"  • {error}")

    if results['console_errors']:
        print("\n⚠️  Console Errors:")
        for error in results['console_errors']:
            print(f"  • {error}")

    print(f"\n📊 HTTP Status Code: {results['http_status']}")
    print(f"📁 Screenshots saved to: {SCREENSHOTS_DIR}")

    # Overall result
    print("\n" + "="*60)
    all_success = (
        results['login_success'] and
        results['form_loaded'] and
        results['submission_success'] and
        results['feedback_in_list'] and
        not results['errors'] and
        not results['console_errors']
    )

    if all_success:
        print("🎉 ALL TESTS PASSED - Feedback system is working correctly!")
    else:
        print("⚠️  SOME TESTS FAILED - Review issues above")
    print("="*60 + "\n")

    return 0 if all_success else 1

if __name__ == "__main__":
    print("🧪 Testing Feedback System After AJAX Fix")
    print("="*60)

    setup_screenshots_dir()
    results = test_feedback_system()
    exit_code = print_summary(results)

    sys.exit(exit_code)
