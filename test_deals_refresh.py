from playwright.sync_api import sync_playwright
import json
import time

def test_deals_refresh():
    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Capture console logs and errors
        console_messages = []
        page.on('console', lambda msg: console_messages.append({
            'type': msg.type,
            'text': msg.text
        }))

        # Capture network requests to the refresh endpoint
        refresh_response = {'status': None, 'body': None, 'headers': None}

        def handle_response(response):
            if '/api/deals-admin/refresh' in response.url:
                refresh_response['status'] = response.status
                refresh_response['url'] = response.url
                try:
                    refresh_response['body'] = response.json()
                except:
                    try:
                        refresh_response['body'] = response.text()
                    except:
                        refresh_response['body'] = 'Could not parse response'
                refresh_response['headers'] = dict(response.headers)

        page.on('response', handle_response)

        print("=" * 80)
        print("TESTING DEALS ADMIN REFRESH ENDPOINT")
        print("=" * 80)

        try:
            # Step 1: Navigate to login page
            print("\n1. Navigating to login page...")
            page.goto('http://localhost:5001/auth/login', wait_until='networkidle')
            page.screenshot(path='/tmp/step1_login_page.png', full_page=True)
            print("   ✓ Login page loaded")

            # Step 2: Log in
            print("\n2. Logging in with testuser@example.com...")
            page.fill('input[name="email"]', 'testuser@example.com')
            page.fill('input[name="password"]', 'password123')

            # Click login button and wait for navigation
            page.click('button[type="submit"]')
            page.wait_for_load_state('networkidle')
            page.screenshot(path='/tmp/step2_after_login.png', full_page=True)
            print(f"   ✓ Login submitted, redirected to: {page.url}")

            # Step 3: Navigate to deals-admin
            print("\n3. Navigating to deals-admin page...")
            page.goto('http://localhost:5001/deals-admin', wait_until='networkidle')
            page.screenshot(path='/tmp/step3_deals_admin.png', full_page=True)
            print("   ✓ Deals admin page loaded")

            # Give the page a moment to fully render
            page.wait_for_timeout(1000)

            # Step 4: Find and click the "Refresh Deals Now" button
            print("\n4. Looking for 'Refresh Deals Now' button...")

            # Try multiple selectors to find the button
            refresh_button = None
            selectors = [
                'button:has-text("Refresh Deals Now")',
                'button:has-text("Refresh")',
                'text=Refresh Deals Now',
                '[id*="refresh"]',
                '[class*="refresh"]'
            ]

            for selector in selectors:
                try:
                    if page.locator(selector).count() > 0:
                        refresh_button = page.locator(selector).first
                        print(f"   ✓ Found button using selector: {selector}")
                        break
                except:
                    continue

            if not refresh_button:
                print("   ✗ Could not find 'Refresh Deals Now' button")
                print("\n   Available buttons on page:")
                buttons = page.locator('button').all()
                for i, btn in enumerate(buttons):
                    try:
                        text = btn.inner_text()
                        print(f"     - Button {i+1}: '{text}'")
                    except:
                        print(f"     - Button {i+1}: (could not get text)")
                page.screenshot(path='/tmp/error_no_button.png', full_page=True)
                return

            # Step 5: Click the refresh button
            print("\n5. Clicking 'Refresh Deals Now' button...")
            refresh_button.click()

            # Wait for the network request to complete
            page.wait_for_timeout(3000)  # Wait 3 seconds for response
            page.screenshot(path='/tmp/step5_after_refresh.png', full_page=True)
            print("   ✓ Button clicked")

            # Step 6: Check the response
            print("\n" + "=" * 80)
            print("RESULTS")
            print("=" * 80)

            if refresh_response['status']:
                print(f"\n✓ HTTP Response Received:")
                print(f"  Status Code: {refresh_response['status']}")
                print(f"  URL: {refresh_response['url']}")

                if refresh_response['status'] == 200:
                    print(f"  Result: SUCCESS")
                else:
                    print(f"  Result: ERROR (status {refresh_response['status']})")

                print(f"\n  Response Body:")
                print(f"  {json.dumps(refresh_response['body'], indent=4)}")

            else:
                print("\n✗ No HTTP response captured")
                print("  The refresh endpoint may not have been called")

            # Check for success/error messages on the page
            print("\n" + "-" * 80)
            print("PAGE MESSAGES:")
            print("-" * 80)

            # Look for common message elements
            message_selectors = [
                '.alert',
                '.message',
                '.notification',
                '.success',
                '.error',
                '[role="alert"]',
                '.toast'
            ]

            messages_found = False
            for selector in message_selectors:
                elements = page.locator(selector).all()
                if elements:
                    for elem in elements:
                        try:
                            text = elem.inner_text()
                            if text.strip():
                                print(f"  {selector}: {text}")
                                messages_found = True
                        except:
                            pass

            if not messages_found:
                print("  No message elements found on page")

            # Check console logs
            print("\n" + "-" * 80)
            print("CONSOLE LOGS:")
            print("-" * 80)

            if console_messages:
                errors = [msg for msg in console_messages if msg['type'] == 'error']
                warnings = [msg for msg in console_messages if msg['type'] == 'warning']
                others = [msg for msg in console_messages if msg['type'] not in ['error', 'warning']]

                if errors:
                    print(f"\n  ERRORS ({len(errors)}):")
                    for msg in errors:
                        print(f"    - {msg['text']}")

                if warnings:
                    print(f"\n  WARNINGS ({len(warnings)}):")
                    for msg in warnings:
                        print(f"    - {msg['text']}")

                if others:
                    print(f"\n  OTHER ({len(others)}):")
                    for msg in others[:10]:  # Limit to first 10
                        print(f"    - [{msg['type']}] {msg['text']}")
            else:
                print("  No console messages captured")

            # Check if statistics updated
            print("\n" + "-" * 80)
            print("STATISTICS ON PAGE:")
            print("-" * 80)

            # Try to find statistics elements
            stats_selectors = [
                '.stat',
                '.statistic',
                '[class*="stat"]',
                'td',
                'th'
            ]

            page_content = page.content()
            if 'Last Refresh' in page_content or 'Total Deals' in page_content:
                print("  Statistics elements found on page:")
                # Try to extract key stats
                try:
                    stats = page.locator('table, .stats, .statistics').first.inner_text()
                    print(f"  {stats[:500]}")  # First 500 chars
                except:
                    print("  (Could not extract statistics)")
            else:
                print("  No obvious statistics found on page")

            print("\n" + "=" * 80)
            print("SCREENSHOTS SAVED:")
            print("=" * 80)
            print("  /tmp/step1_login_page.png")
            print("  /tmp/step2_after_login.png")
            print("  /tmp/step3_deals_admin.png")
            print("  /tmp/step5_after_refresh.png")
            print("=" * 80)

        except Exception as e:
            print(f"\n✗ ERROR during testing: {str(e)}")
            import traceback
            traceback.print_exc()
            page.screenshot(path='/tmp/error_screenshot.png', full_page=True)
            print("\nError screenshot saved to: /tmp/error_screenshot.png")

        finally:
            browser.close()

if __name__ == '__main__':
    test_deals_refresh()
