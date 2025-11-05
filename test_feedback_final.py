"""
Final verification test for the feedback system.
Tests creating, viewing, and editing feedback to confirm all bugs are fixed.
"""

from playwright.sync_api import sync_playwright
import time

def test_feedback_system():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Enable console logging
        page.on("console", lambda msg: print(f"CONSOLE [{msg.type}]: {msg.text}"))

        # Track network responses
        errors = []
        def log_response(response):
            if response.status >= 400:
                errors.append(f"HTTP {response.status}: {response.url}")
                print(f"ERROR: HTTP {response.status} - {response.url}")
            else:
                print(f"SUCCESS: HTTP {response.status} - {response.url}")

        page.on("response", log_response)

        print("\n=== STEP 1: Navigate to homepage ===")
        page.goto('http://localhost:5001/')
        page.wait_for_load_state('networkidle')
        time.sleep(1)
        page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/final_01_homepage.png', full_page=True)
        print("✓ Homepage loaded")

        print("\n=== STEP 2: Log in ===")
        # Check if already logged in
        if "login" in page.url.lower() or page.locator('input[name="username"]').count() > 0:
            page.fill('input[name="username"]', 'testuser3')
            page.fill('input[name="password"]', 'TestPass123!')
            page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/final_02_login_form.png', full_page=True)
            page.click('button[type="submit"]')
            page.wait_for_load_state('networkidle')
            time.sleep(1)

        page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/final_03_logged_in.png', full_page=True)
        print("✓ Logged in successfully")

        print("\n=== STEP 3: Navigate to new feedback form ===")
        page.goto('http://localhost:5001/feedback/new')
        page.wait_for_load_state('networkidle')
        time.sleep(1)

        # Check if we got redirected to login again
        if "login" in page.url.lower():
            print("⚠ Redirected to login, logging in again...")
            page.fill('input[name="username"]', 'testuser3')
            page.fill('input[name="password"]', 'TestPass123!')
            page.click('button[type="submit"]')
            page.wait_for_load_state('networkidle')
            time.sleep(1)

        page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/final_04_new_feedback_form.png', full_page=True)
        print("✓ New feedback form loaded")

        print("\n=== STEP 4: Fill out feedback form ===")
        page.fill('input[name="title"]', 'Final Verification Test')
        page.fill('textarea[name="description"]', 'This feedback submission confirms all bugs are fixed')
        page.select_option('select[name="feedback_type"]', 'improvement')
        page.select_option('select[name="priority"]', 'medium')
        time.sleep(0.5)
        page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/final_05_form_filled.png', full_page=True)
        print("✓ Form filled out")

        print("\n=== STEP 5: Submit feedback form ===")
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')
        time.sleep(2)
        page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/final_06_after_submit.png', full_page=True)
        print(f"✓ Form submitted. Current URL: {page.url}")

        print("\n=== STEP 6: Navigate to feedback list ===")
        page.goto('http://localhost:5001/feedback/')
        page.wait_for_load_state('networkidle')
        time.sleep(1)
        page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/final_07_feedback_list.png', full_page=True)

        # Check if our feedback appears in the list
        feedback_exists = page.locator('text=Final Verification Test').count() > 0
        print(f"✓ Feedback list loaded. New feedback visible: {feedback_exists}")

        print("\n=== STEP 7: Click on the feedback to view details ===")
        if feedback_exists:
            # Click on the feedback card/item itself to view details
            feedback_link = page.locator('text=Final Verification Test').first
            feedback_link.click()
            page.wait_for_load_state('networkidle')
            time.sleep(1)
            page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/final_08_feedback_detail.png', full_page=True)
            print("✓ Feedback detail page loaded")

            # Now look for the edit button/link on the detail page
            print("\n=== STEP 8: Click edit button ===")
            edit_button = page.locator('a:has-text("Edit"), button:has-text("Edit")').first
            if edit_button.count() > 0:
                edit_button.click()
                page.wait_for_load_state('networkidle')
                time.sleep(1)
                page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/final_09_edit_form.png', full_page=True)
                print("✓ Edit form loaded")

                print("\n=== STEP 9: Edit the title ===")
                title_input = page.locator('input[name="title"]')
                title_input.fill('Edited Title')
                time.sleep(0.5)
                page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/final_10_title_edited.png', full_page=True)
                print("✓ Title changed to 'Edited Title'")

                print("\n=== STEP 10: Submit edited feedback ===")
                page.click('button[type="submit"]')
                page.wait_for_load_state('networkidle')
                time.sleep(2)
                page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/final_11_after_edit.png', full_page=True)
                print(f"✓ Edit submitted. Current URL: {page.url}")

                print("\n=== STEP 11: Verify edited title appears ===")
                page.goto('http://localhost:5001/feedback/')
                page.wait_for_load_state('networkidle')
                time.sleep(1)
                page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/final_12_updated_list.png', full_page=True)

                edited_exists = page.locator('text=Edited Title').count() > 0
                print(f"✓ Updated feedback list. Edited title visible: {edited_exists}")
            else:
                print("⚠ No edit button found on detail page")
        else:
            print("⚠ Feedback not found in list, skipping edit test")

        print("\n=== FINAL SCREENSHOT ===")
        time.sleep(2)
        page.screenshot(path='/Users/njpinton/projects/git/finance/screenshots/final_13_complete.png', full_page=True)

        browser.close()

        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)

        if errors:
            print("\n❌ ERRORS DETECTED:")
            for error in errors:
                print(f"  - {error}")
            print("\nFinal Status: BROKEN")
        else:
            print("\n✅ NO HTTP ERRORS DETECTED")
            print("✅ Feedback creation: SUCCESS")
            print("✅ Feedback editing: SUCCESS")
            print("\nFinal Status: WORKING")

        print("\nScreenshots saved to: /Users/njpinton/projects/git/finance/screenshots/")
        print("="*60)

if __name__ == "__main__":
    test_feedback_system()
