"""
Improved comprehensive web application testing for BDO Deals application.
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
            screenshot_path = '/tmp/v2_step1_registration_page.png'
            page.screenshot(path=screenshot_path, full_page=True)
            report['screenshot_paths'].append(screenshot_path)
            print(f"  Screenshot saved: {screenshot_path}")

            # Fill registration form using placeholder text
            try:
                # Fill using placeholder attributes
                page.fill('input[placeholder*="username"]', 'testdeals2')
                page.fill('input[placeholder*="email"]', 'testdeals2@example.com')
                page.fill('input[placeholder*="password"][placeholder*="strong"]', 'TestPass123!')
                page.fill('input[placeholder*="Re-enter"]', 'TestPass123!')

                # Click register button
                page.click('button:has-text("Create Account")')
                page.wait_for_load_state('networkidle', timeout=10000)
                time.sleep(2)

                # Take screenshot after registration
                screenshot_path = '/tmp/v2_step1_registration_result.png'
                page.screenshot(path=screenshot_path, full_page=True)
                report['screenshot_paths'].append(screenshot_path)

                current_url = page.url
                print(f"  Current URL after registration: {current_url}")

                # Check for success - should be on login page or dashboard
                if 'login' in current_url or 'dashboard' in current_url:
                    report['registration_success'] = True
                    print("  Registration appears successful")
                else:
                    print("  Registration result unclear")

            except Exception as e:
                report['errors'].append(f"Registration error: {str(e)}")
                print(f"  Registration error: {str(e)}")

            # Step 2: Login
            print("\nStep 2: Testing login...")
            try:
                page.goto('http://localhost:5001/auth/login', wait_until='networkidle')
                time.sleep(1)

                # Fill login form
                page.fill('input[placeholder*="username"]', 'testdeals2')
                page.fill('input[placeholder*="password"]', 'TestPass123!')
                page.click('button:has-text("Login")')
                page.wait_for_load_state('networkidle', timeout=10000)
                time.sleep(3)

                # Take screenshot of login result
                screenshot_path = '/tmp/v2_step2_login_result.png'
                page.screenshot(path=screenshot_path, full_page=True)
                report['screenshot_paths'].append(screenshot_path)

                current_url = page.url
                print(f"  Current URL after login: {current_url}")

                # Check if login succeeded
                if '/login' not in current_url or 'dashboard' in current_url or page.locator('text=Login').count() == 0:
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
            time.sleep(5)
            page.wait_for_load_state('networkidle')

            # Wait for any lazy-loaded images
            page.wait_for_timeout(3000)

            # Take full-page screenshot
            screenshot_path = '/tmp/v2_step3_deals_page.png'
            page.screenshot(path=screenshot_path, full_page=True)
            report['screenshot_paths'].append(screenshot_path)
            print(f"  Screenshot saved: {screenshot_path}")

            # Step 4: Verify Real BDO Data
            print("\nStep 4: Verifying real BDO data...")

            # Get page HTML for detailed inspection
            page_html = page.content()
            page_text = page.inner_text('body')

            # Count deal cards - try multiple selectors
            deal_count = 0
            for selector in ['.deal-card', '.card', '.campaign-card', '[class*="campaign"]', '[class*="deal"]']:
                try:
                    count = page.locator(selector).count()
                    if count > deal_count:
                        deal_count = count
                        print(f"  Found {count} elements with selector: {selector}")
                except:
                    pass

            report['deals_count'] = deal_count
            print(f"  Total deal cards found: {deal_count}")

            # Search for BDO keywords
            keywords = ["JCB", "Cashback", "Rebate", "Spend", "Raffle", "BDO", "Mastercard", "Visa"]
            for keyword in keywords:
                if keyword in page_text or keyword in page_html:
                    report['bdo_keywords_found'].append(keyword)
                    print(f"  Found keyword: {keyword}")

            # Check for cdn.perxtech.net images
            cdn_images = []
            if 'cdn.perxtech.net' in page_html:
                import re
                # Extract image URLs
                urls = re.findall(r'https?://cdn\.perxtech\.net[^\s"\'<>]+', page_html)
                cdn_images = list(set(urls))  # Remove duplicates
                report['images_from_cdn'] = len(cdn_images) > 0

            report['cdn_image_urls'] = cdn_images[:5]
            print(f"  Images from cdn.perxtech.net: {len(cdn_images)}")
            if cdn_images:
                print(f"  Sample CDN URL: {cdn_images[0][:100]}...")

            # Extract deal titles - try multiple approaches
            titles_found = []

            # Method 1: Look for specific heading tags
            for selector in ['h2', 'h3', 'h4', 'h5']:
                try:
                    elements = page.locator(selector).all()
                    for elem in elements:
                        try:
                            text = elem.inner_text().strip()
                            if text and len(text) > 5 and len(text) < 200 and text not in titles_found:
                                # Filter out navigation/header text
                                if text.lower() not in ['finance tracker', 'login', 'register', 'deals', 'logout']:
                                    titles_found.append(text)
                        except:
                            pass
                except:
                    pass

            # Method 2: Look for text with specific patterns (merchant names, promotions)
            import re
            promotion_patterns = [
                r'(?i)(get|earn|enjoy|receive|win)\s+[^.]{10,100}',
                r'(?i)[A-Z][^.]{20,150}(?:cashback|rebate|discount|promo|raffle)',
            ]
            for pattern in promotion_patterns:
                matches = re.findall(pattern, page_text)
                for match in matches[:10]:
                    match_text = match if isinstance(match, str) else match[0]
                    if len(match_text) > 10 and match_text not in titles_found:
                        titles_found.append(match_text.strip())

            report['deal_titles'] = titles_found[:15]
            print(f"  Deal titles/descriptions found: {len(titles_found)}")
            for i, title in enumerate(titles_found[:5], 1):
                print(f"    {i}. {title[:100]}...")

            # Step 5: Open Deal Detail Modal
            print("\nStep 5: Opening deal detail modal...")
            try:
                # Find and click first clickable element
                first_deal = None
                selectors_to_try = [
                    '.deal-card',
                    '.card',
                    '.campaign-card',
                    'a[href*="deal"]',
                    'div[onclick]',
                    'button:has-text("View")',
                ]

                for selector in selectors_to_try:
                    try:
                        elements = page.locator(selector).all()
                        if elements and len(elements) > 0:
                            first_deal = elements[0]
                            print(f"  Found clickable deal using selector: {selector}")
                            break
                    except:
                        continue

                if first_deal:
                    first_deal.click()
                    time.sleep(3)
                    page.wait_for_load_state('networkidle', timeout=5000)

                    # Take screenshot of detail view
                    screenshot_path = '/tmp/v2_step5_deal_detail.png'
                    page.screenshot(path=screenshot_path, full_page=True)
                    report['screenshot_paths'].append(screenshot_path)
                    print(f"  Detail view screenshot saved: {screenshot_path}")

                    # Extract detail view data
                    detail_html = page.content()
                    detail_text = page.inner_text('body')

                    detail_data = {}

                    # Extract title from modal/detail page
                    for selector in ['h1', 'h2', '.modal-title', '.detail-title', '[class*="title"]']:
                        try:
                            title_elem = page.locator(selector).first
                            if title_elem:
                                title = title_elem.inner_text().strip()
                                if title and len(title) > 5:
                                    detail_data['title'] = title
                                    break
                        except:
                            pass

                    # Check for card types
                    card_types = ['JCB', 'Mastercard', 'Visa', 'AMEX', 'American Express']
                    found_card_types = [ct for ct in card_types if ct in detail_text]
                    if found_card_types:
                        detail_data['card_types'] = found_card_types

                    # Check for categories/merchants
                    if any(word in detail_text.lower() for word in ['category', 'merchant', 'store', 'restaurant']):
                        detail_data['has_merchant_info'] = True

                    # Check for terms and conditions
                    if any(word in detail_text.lower() for word in ['terms', 'conditions', 'mechanics', 'how to avail']):
                        detail_data['has_terms'] = True

                    # Check for dates
                    import re
                    date_pattern = r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}'
                    dates_found = re.findall(date_pattern, detail_text)
                    if dates_found:
                        detail_data['dates'] = dates_found[:3]

                    # Look for description text
                    description_length = len(detail_text)
                    detail_data['description_length'] = description_length

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
                assessment_reasons.append(f"✓ Images from cdn.perxtech.net (found {len(cdn_images)} images)")

            if len(report['bdo_keywords_found']) >= 3:
                assessment_score += 2
                assessment_reasons.append(f"✓ Multiple BDO keywords: {', '.join(report['bdo_keywords_found'])}")

            if report['deals_count'] >= 5:
                assessment_score += 2
                assessment_reasons.append(f"✓ Good number of deals ({report['deals_count']})")
            elif report['deals_count'] >= 1:
                assessment_score += 1
                assessment_reasons.append(f"~ Some deals found ({report['deals_count']})")

            # Check if titles look real
            generic_words = ['sample', 'test', 'deal 1', 'deal 2', 'placeholder', 'lorem', 'ipsum']
            real_looking_titles = [t for t in report['deal_titles']
                                   if not any(generic in t.lower() for generic in generic_words)]
            if len(real_looking_titles) >= 3:
                assessment_score += 2
                assessment_reasons.append(f"✓ Authentic-looking titles found")

            # Check detail view
            if report['detail_view_data']:
                if report['detail_view_data'].get('card_types'):
                    assessment_score += 1
                    assessment_reasons.append(f"✓ Card types in details: {report['detail_view_data']['card_types']}")
                if report['detail_view_data'].get('has_terms'):
                    assessment_score += 1
                    assessment_reasons.append("✓ Terms and conditions present")

            if assessment_score >= 7:
                report['real_bdo_campaigns'] = "YES - High confidence these are real BDO campaigns"
            elif assessment_score >= 4:
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
    print("BDO DEALS WEB APPLICATION TEST REPORT (v2)")
    print("="*80)
    print(f"Timestamp: {report['timestamp']}")
    print()

    print("AUTHENTICATION RESULTS:")
    print(f"  Registration Success: {'✓' if report['registration_success'] else '✗'}")
    print(f"  Login Success: {'✓' if report['login_success'] else '✗'}")
    print()

    print("DEALS PAGE RESULTS:")
    print(f"  Number of Deals Displayed: {report['deals_count']} (Expected: 10)")
    print(f"  Images from cdn.perxtech.net: {'✓ YES' if report['images_from_cdn'] else '✗ NO'}")
    if report['cdn_image_urls']:
        print(f"  CDN Images Found: {len(report['cdn_image_urls'])}")
        print(f"  Sample CDN URL: {report['cdn_image_urls'][0][:80]}...")
    print()

    print("BDO KEYWORDS FOUND:")
    if report['bdo_keywords_found']:
        print(f"  {', '.join(report['bdo_keywords_found'])}")
    else:
        print("  None found")
    print()

    print("SAMPLE DEAL TITLES/DESCRIPTIONS:")
    if report['deal_titles']:
        for i, title in enumerate(report['deal_titles'][:8], 1):
            print(f"  {i}. {title[:100]}")
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
    print(f"  Result: {report['real_bdo_campaigns']}")
    print(f"  Score: {report.get('assessment_score', 0)}/10")
    if 'assessment_reasons' in report:
        print("  Evidence:")
        for reason in report['assessment_reasons']:
            print(f"    {reason}")
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
    print("Starting BDO Deals Web Application Test (v2)...")
    print("Target: http://localhost:5001")
    print()

    report = test_bdo_deals()
    print_report(report)
