"""
Comprehensive web application testing for BDO Deals application.
Tests user registration, login, and verifies real BDO deal data is displaying.
"""
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
from datetime import datetime

def test_bdo_deals():
    report = {
        'timestamp': datetime.now().isoformat(),
        'registration_success': False,
        'login_success': False,
        'deals_count': 0,
        'bdo_keywords_found': [],
        'deal_titles': [],
        'images_from_cdn': False,
        'cdn_image_urls': [],
        'real_bdo_campaigns': None,
        'screenshot_paths': [],
        'errors': [],
        'detail_view_data': {}
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        try:
            # Step 1: User Registration
            print("Step 1: Testing user registration...")
            page.goto('http://localhost:5001/auth/register', wait_until='networkidle')
            time.sleep(2)

            # Take screenshot of registration page
            screenshot_path = '/tmp/step1_registration_page.png'
            page.screenshot(path=screenshot_path, full_page=True)
            report['screenshot_paths'].append(screenshot_path)
            print(f"  Screenshot saved: {screenshot_path}")

            # Fill registration form
            try:
                page.fill('input[name="username"]', 'testdeals')
                page.fill('input[name="email"]', 'testdeals@example.com')
                page.fill('input[name="password"]', 'TestPass123!')
                page.fill('input[name="confirm_password"]', 'TestPass123!')

                # Click register button
                page.click('button[type="submit"]')
                page.wait_for_load_state('networkidle', timeout=10000)
                time.sleep(2)

                # Check if registration succeeded
                current_url = page.url
                print(f"  Current URL after registration: {current_url}")

                # Take screenshot after registration
                screenshot_path = '/tmp/step1_registration_result.png'
                page.screenshot(path=screenshot_path, full_page=True)
                report['screenshot_paths'].append(screenshot_path)

                # Check for success indicators
                page_content = page.content().lower()
                if 'error' not in page_content or 'success' in page_content or 'login' in current_url:
                    report['registration_success'] = True
                    print("  Registration appears successful")
                else:
                    # Registration might have failed if user exists, try login instead
                    print("  Registration may have failed (user might already exist)")

            except Exception as e:
                report['errors'].append(f"Registration error: {str(e)}")
                print(f"  Registration error: {str(e)}")

            # Step 2: Login
            print("\nStep 2: Testing login...")
            try:
                page.goto('http://localhost:5001/auth/login', wait_until='networkidle')
                time.sleep(1)

                page.fill('input[name="username"]', 'testdeals')
                page.fill('input[name="password"]', 'TestPass123!')
                page.click('button[type="submit"]')
                page.wait_for_load_state('networkidle', timeout=10000)
                time.sleep(2)

                # Take screenshot of login result
                screenshot_path = '/tmp/step2_login_result.png'
                page.screenshot(path=screenshot_path, full_page=True)
                report['screenshot_paths'].append(screenshot_path)

                current_url = page.url
                print(f"  Current URL after login: {current_url}")

                # Check if login succeeded (should redirect away from login page)
                if '/login' not in current_url or 'dashboard' in current_url or 'deals' in current_url:
                    report['login_success'] = True
                    print("  Login successful")
                else:
                    print("  Login may have failed")

            except Exception as e:
                report['errors'].append(f"Login error: {str(e)}")
                print(f"  Login error: {str(e)}")

            # Step 3: Navigate to Deals Page
            print("\nStep 3: Navigating to deals page...")
            page.goto('http://localhost:5001/deals', wait_until='networkidle')

            # Wait for images to load
            time.sleep(3)
            page.wait_for_load_state('networkidle')

            # Take full-page screenshot
            screenshot_path = '/tmp/step3_deals_page.png'
            page.screenshot(path=screenshot_path, full_page=True)
            report['screenshot_paths'].append(screenshot_path)
            print(f"  Screenshot saved: {screenshot_path}")

            # Step 4: Verify Real BDO Data
            print("\nStep 4: Verifying real BDO data...")

            # Count deal cards
            deal_cards = page.locator('.deal-card, .card, [class*="deal"]').all()
            report['deals_count'] = len(deal_cards)
            print(f"  Deal cards found: {len(deal_cards)}")

            # Get page content for keyword search
            page_text = page.content()
            page_visible_text = page.inner_text('body')

            # Search for BDO keywords
            keywords = ["JCB", "Cashback", "Rebate", "Spend", "Raffle", "BDO", "Mastercard", "Visa"]
            for keyword in keywords:
                if keyword in page_visible_text:
                    report['bdo_keywords_found'].append(keyword)
                    print(f"  Found keyword: {keyword}")

            # Check for cdn.perxtech.net images
            image_elements = page.locator('img').all()
            cdn_images = []
            for img in image_elements:
                src = img.get_attribute('src')
                if src and 'cdn.perxtech.net' in src:
                    cdn_images.append(src)
                    report['images_from_cdn'] = True

            report['cdn_image_urls'] = cdn_images[:5]  # Store first 5 for report
            print(f"  Images from cdn.perxtech.net: {len(cdn_images)}")
            if cdn_images:
                print(f"  Sample CDN URL: {cdn_images[0]}")

            # Extract deal titles
            title_selectors = ['h3', 'h4', '.deal-title', '.card-title', '[class*="title"]']
            titles_found = []
            for selector in title_selectors:
                try:
                    elements = page.locator(selector).all()
                    for elem in elements[:10]:  # Limit to first 10
                        text = elem.inner_text().strip()
                        if text and len(text) > 5 and text not in titles_found:
                            titles_found.append(text)
                except:
                    pass

            report['deal_titles'] = titles_found[:10]
            print(f"  Deal titles found: {len(titles_found)}")
            for i, title in enumerate(titles_found[:5], 1):
                print(f"    {i}. {title}")

            # Step 5: Open Deal Detail Modal
            print("\nStep 5: Opening deal detail modal...")
            try:
                # Find and click first deal card
                first_deal = None
                selectors_to_try = [
                    '.deal-card',
                    '.card',
                    '[class*="deal"]',
                    'a[href*="deal"]',
                    '.campaign-card'
                ]

                for selector in selectors_to_try:
                    try:
                        deals = page.locator(selector).all()
                        if deals and len(deals) > 0:
                            first_deal = deals[0]
                            print(f"  Found clickable deal using selector: {selector}")
                            break
                    except:
                        continue

                if first_deal:
                    first_deal.click()
                    time.sleep(2)
                    page.wait_for_load_state('networkidle', timeout=5000)

                    # Take screenshot of detail view
                    screenshot_path = '/tmp/step5_deal_detail.png'
                    page.screenshot(path=screenshot_path, full_page=True)
                    report['screenshot_paths'].append(screenshot_path)
                    print(f"  Detail view screenshot saved: {screenshot_path}")

                    # Extract detail view data
                    detail_content = page.content()
                    detail_text = page.inner_text('body')

                    # Look for common detail fields
                    detail_data = {}

                    # Try to extract title
                    for selector in ['h1', 'h2', '.modal-title', '.detail-title']:
                        try:
                            title_elem = page.locator(selector).first
                            if title_elem:
                                detail_data['title'] = title_elem.inner_text().strip()
                                break
                        except:
                            pass

                    # Check for various detail fields
                    if 'JCB' in detail_text or 'Mastercard' in detail_text or 'Visa' in detail_text:
                        detail_data['has_card_type'] = True
                    if 'Category' in detail_text or 'category' in detail_text:
                        detail_data['has_category'] = True
                    if 'Merchant' in detail_text or 'merchant' in detail_text:
                        detail_data['has_merchant'] = True
                    if 'Terms' in detail_text or 'Conditions' in detail_text:
                        detail_data['has_terms'] = True

                    # Check for dates
                    import re
                    date_pattern = r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2}'
                    dates_found = re.findall(date_pattern, detail_text)
                    if dates_found:
                        detail_data['has_dates'] = True
                        detail_data['sample_dates'] = dates_found[:2]

                    report['detail_view_data'] = detail_data
                    print(f"  Detail view data extracted: {detail_data}")
                else:
                    print("  Could not find clickable deal element")
                    report['errors'].append("Could not find clickable deal element")

            except Exception as e:
                report['errors'].append(f"Detail view error: {str(e)}")
                print(f"  Detail view error: {str(e)}")

            # Assessment: Real BDO campaigns or placeholder?
            print("\nStep 6: Assessment...")
            assessment_score = 0
            assessment_reasons = []

            if report['images_from_cdn']:
                assessment_score += 3
                assessment_reasons.append("Images are from cdn.perxtech.net (authentic Perx CDN)")

            if len(report['bdo_keywords_found']) >= 3:
                assessment_score += 2
                assessment_reasons.append(f"Multiple BDO-related keywords found: {', '.join(report['bdo_keywords_found'])}")

            if report['deals_count'] >= 5:
                assessment_score += 1
                assessment_reasons.append(f"Reasonable number of deals ({report['deals_count']})")

            # Check if titles look real (not generic like "Deal 1", "Sample Deal")
            real_looking_titles = [t for t in report['deal_titles']
                                   if not any(generic in t.lower() for generic in ['sample', 'test', 'deal 1', 'deal 2', 'placeholder'])]
            if len(real_looking_titles) >= 3:
                assessment_score += 2
                assessment_reasons.append(f"Titles appear authentic: {real_looking_titles[:3]}")

            if assessment_score >= 5:
                report['real_bdo_campaigns'] = "YES - High confidence these are real BDO campaigns"
            elif assessment_score >= 3:
                report['real_bdo_campaigns'] = "LIKELY - Evidence suggests real BDO data"
            else:
                report['real_bdo_campaigns'] = "UNCERTAIN - May be placeholder data"

            report['assessment_score'] = assessment_score
            report['assessment_reasons'] = assessment_reasons

        except Exception as e:
            report['errors'].append(f"Critical error: {str(e)}")
            print(f"Critical error: {str(e)}")

        finally:
            browser.close()

    return report

def print_report(report):
    """Print formatted test report"""
    print("\n" + "="*80)
    print("BDO DEALS WEB APPLICATION TEST REPORT")
    print("="*80)
    print(f"Timestamp: {report['timestamp']}")
    print()

    print("AUTHENTICATION RESULTS:")
    print(f"  Registration Success: {'✓' if report['registration_success'] else '✗'}")
    print(f"  Login Success: {'✓' if report['login_success'] else '✗'}")
    print()

    print("DEALS PAGE RESULTS:")
    print(f"  Number of Deals Displayed: {report['deals_count']} (Expected: 10)")
    print(f"  Images from cdn.perxtech.net: {'✓' if report['images_from_cdn'] else '✗'}")
    if report['cdn_image_urls']:
        print(f"  Sample CDN URL: {report['cdn_image_urls'][0][:80]}...")
    print()

    print("BDO KEYWORDS FOUND:")
    if report['bdo_keywords_found']:
        print(f"  {', '.join(report['bdo_keywords_found'])}")
    else:
        print("  None found")
    print()

    print("SAMPLE DEAL TITLES:")
    if report['deal_titles']:
        for i, title in enumerate(report['deal_titles'][:5], 1):
            print(f"  {i}. {title}")
    else:
        print("  None found")
    print()

    print("DEAL DETAIL VIEW:")
    if report['detail_view_data']:
        for key, value in report['detail_view_data'].items():
            print(f"  {key}: {value}")
    else:
        print("  No detail data captured")
    print()

    print("ASSESSMENT:")
    print(f"  {report['real_bdo_campaigns']}")
    if 'assessment_reasons' in report:
        print("  Reasons:")
        for reason in report['assessment_reasons']:
            print(f"    - {reason}")
    print()

    print("SCREENSHOTS:")
    for path in report['screenshot_paths']:
        print(f"  {path}")
    print()

    if report['errors']:
        print("ERRORS ENCOUNTERED:")
        for error in report['errors']:
            print(f"  - {error}")
        print()

    print("="*80)

if __name__ == "__main__":
    print("Starting BDO Deals Web Application Test...")
    print("Target: http://localhost:5001")
    print()

    report = test_bdo_deals()
    print_report(report)
