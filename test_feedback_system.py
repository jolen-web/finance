"""
Test the feedback system end-to-end:
1. Login as testuser3
2. Navigate to feedback form
3. Submit new feedback
4. Verify it appears in the list
"""
from playwright.sync_api import sync_playwright
import time

def test_feedback_system():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Track HTTP responses
        responses = []
        def log_response(response):
            responses.append({
                'url': response.url,
                'status': response.status,
                'method': response.request.method
            })
        page.on('response', log_response)

        # Track console messages
        console_messages = []
        def log_console(msg):
            console_messages.append(f"[{msg.type}] {msg.text}")
        page.on('console', log_console)

        try:
            print("Step 1: Navigating to homepage...")
            page.goto('http://localhost:5001/')
            page.wait_for_load_state('networkidle')
            page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/01_homepage.png', full_page=True)
            print("  Homepage loaded")

            print("\nStep 2: Clicking Sign In link...")
            # Try to click the "Sign In" link/button - it appears to be a link with icon in the top right
            page.click('a:has-text("Login")')
            page.wait_for_load_state('networkidle')
            page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/02_login_page.png', full_page=True)
            print(f"  Current URL: {page.url}")

            print("\nStep 3: Logging in as testuser3...")
            page.fill('input[name="username"]', 'testuser3')
            page.fill('input[name="password"]', 'TestPass123!')
            page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/03_login_filled.png', full_page=True)

            page.click('button[type="submit"]')
            page.wait_for_load_state('networkidle')
            page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/04_after_login.png', full_page=True)

            # Check if we're logged in
            current_url = page.url
            print(f"  Current URL after login: {current_url}")

            print("\nStep 4: Navigating to feedback form...")
            page.goto('http://localhost:5001/feedback/new')
            page.wait_for_load_state('networkidle')
            page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/05_feedback_form.png', full_page=True)
            print(f"  Current URL: {page.url}")

            print("\nStep 5: Filling out feedback form...")
            page.fill('input[name="title"]', 'Test Feedback After Fix')
            page.fill('textarea[name="description"]', 'This is a test to verify the feedback system works')
            page.select_option('select[name="feedback_type"]', 'feature')
            page.select_option('select[name="priority"]', 'medium')
            page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/06_feedback_filled.png', full_page=True)
            print("  Form filled")

            print("\nStep 6: Submitting feedback...")
            page.click('button[type="submit"]')
            page.wait_for_load_state('networkidle')
            page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/07_after_submit.png', full_page=True)

            current_url = page.url
            print(f"  Current URL after submit: {current_url}")

            # Check for success message
            page_content = page.content()
            if 'success' in page_content.lower() or 'feedback' in current_url.lower():
                print("  Appears to have redirected successfully")

            print("\nStep 7: Navigating to feedback list...")
            page.goto('http://localhost:5001/feedback/')
            page.wait_for_load_state('networkidle')
            page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/08_feedback_list.png', full_page=True)

            # Look for our test feedback
            page_text = page.inner_text('body')
            if 'Test Feedback After Fix' in page_text:
                print("  SUCCESS: Feedback appears in the list!")
            else:
                print("  WARNING: Feedback NOT found in the list")

            print("\n" + "="*60)
            print("HTTP RESPONSES SUMMARY:")
            print("="*60)

            # Filter and display relevant responses
            for resp in responses:
                if '/feedback' in resp['url'] or '/login' in resp['url'] or resp['method'] == 'POST':
                    status_symbol = "PASS" if resp['status'] < 400 else "FAIL"
                    print(f"  [{status_symbol}] {resp['status']} {resp['method']} {resp['url']}")

            print("\n" + "="*60)
            print("CONSOLE MESSAGES:")
            print("="*60)
            if console_messages:
                for msg in console_messages:
                    print(f"  {msg}")
            else:
                print("  No console messages")

            print("\n" + "="*60)
            print("FINAL STATUS:")
            print("="*60)

            # Check for 500 errors
            has_500 = any(r['status'] == 500 for r in responses if '/feedback' in r['url'])
            if has_500:
                print("  FAIL: Found 500 status code in feedback-related requests")
            else:
                print("  PASS: No 500 errors detected")

            # Check for successful redirects (302/303) or success (200)
            feedback_posts = [r for r in responses if '/feedback' in r['url'] and r['method'] == 'POST']
            if feedback_posts:
                post_status = feedback_posts[-1]['status']
                if post_status in [200, 302, 303]:
                    print(f"  PASS: Feedback submission returned status {post_status}")
                else:
                    print(f"  FAIL: Feedback submission returned status {post_status}")

            # Verify feedback appears in list
            if 'Test Feedback After Fix' in page_text:
                print("  PASS: Feedback successfully created and appears in list")
            else:
                print("  FAIL: Feedback not found in list")

        except Exception as e:
            print(f"\n  ERROR: {e}")
            page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/error.png', full_page=True)
            raise

        finally:
            browser.close()

if __name__ == '__main__':
    test_feedback_system()
