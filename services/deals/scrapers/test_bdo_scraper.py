#!/usr/bin/env python3
"""
Test script for BDO scrapers

Tests both BeautifulSoup and Selenium approaches to help identify
which one works best for the current BDO website structure.

Usage:
    python test_bdo_scraper.py --mode static    # Test BeautifulSoup
    python test_bdo_scraper.py --mode js        # Test Selenium
    python test_bdo_scraper.py --mode all       # Test both
"""

import sys
import logging
from bdo_scraper import BDOScraper

try:
    from bdo_scraper_selenium import BDOScraperSelenium
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False
    print("⚠️  Selenium not available. Install with: pip install selenium webdriver-manager")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_beautifulsoup_scraper():
    """Test BeautifulSoup-based scraper"""
    print("\n" + "=" * 80)
    print("TESTING BEAUTIFULSOUP SCRAPER")
    print("=" * 80)

    scraper = BDOScraper()

    # Fetch page
    html = scraper.fetch_page()
    if not html:
        print("❌ Failed to fetch page")
        return False

    # Extract deals
    deals = scraper.extract_deals_from_html(html)

    if not deals:
        print("❌ No deals found (possible issues):")
        print("  1. Website structure different than expected")
        print("  2. Content is JavaScript-rendered")
        print("  3. Website is blocking requests")
        return False

    print(f"\n✅ Successfully extracted {len(deals)} deals\n")
    scraper.print_deals()

    # Save results
    scraper.save_to_json('/tmp/bdo_deals_beautifulsoup.json')
    scraper.save_to_csv('/tmp/bdo_deals_beautifulsoup.csv')

    return True


def test_selenium_scraper():
    """Test Selenium-based scraper"""
    if not HAS_SELENIUM:
        print("⚠️  Selenium not available. Skipping Selenium test")
        return None

    print("\n" + "=" * 80)
    print("TESTING SELENIUM SCRAPER")
    print("=" * 80)

    scraper = BDOScraperSelenium(headless=True)

    # Run scraper
    deals = scraper.scrape()

    if not deals:
        print("❌ No deals found with Selenium")
        return False

    print(f"\n✅ Successfully extracted {len(deals)} deals with Selenium\n")
    scraper.print_deals()

    # Save results
    scraper.save_to_json('/tmp/bdo_deals_selenium.json')

    return True


def compare_results():
    """Compare results from both scrapers"""
    import json

    print("\n" + "=" * 80)
    print("COMPARING RESULTS")
    print("=" * 80)

    try:
        with open('/tmp/bdo_deals_beautifulsoup.json') as f:
            bs_deals = json.load(f)
        print(f"BeautifulSoup: {len(bs_deals)} deals")
    except:
        bs_deals = []
        print("BeautifulSoup: Not available")

    try:
        with open('/tmp/bdo_deals_selenium.json') as f:
            sel_deals = json.load(f)
        print(f"Selenium: {len(sel_deals)} deals")
    except:
        sel_deals = []
        print("Selenium: Not available")

    if bs_deals and sel_deals:
        print(f"\n✅ Both methods work! BeautifulSoup: {len(bs_deals)}, Selenium: {len(sel_deals)}")
        print("Recommendation: Use BeautifulSoup for better performance")
    elif bs_deals:
        print("\n✅ BeautifulSoup works! Use this method")
    elif sel_deals:
        print("\n⚠️  Only Selenium works. Website likely uses JavaScript")
    else:
        print("\n❌ Neither method found deals. Check website manually")


def main():
    """Main test runner"""
    import argparse

    parser = argparse.ArgumentParser(description='Test BDO scrapers')
    parser.add_argument(
        '--mode',
        choices=['static', 'js', 'all'],
        default='all',
        help='Which scraper to test'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Show Selenium browser window'
    )

    args = parser.parse_args()

    results = {
        'beautifulsoup': None,
        'selenium': None,
    }

    # Test BeautifulSoup
    if args.mode in ['static', 'all']:
        results['beautifulsoup'] = test_beautifulsoup_scraper()

    # Test Selenium
    if args.mode in ['js', 'all']:
        results['selenium'] = test_selenium_scraper()

    # Compare if both tested
    if args.mode == 'all':
        compare_results()

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    working = [name for name, result in results.items() if result is True]
    failed = [name for name, result in results.items() if result is False]
    skipped = [name for name, result in results.items() if result is None]

    if working:
        print(f"✅ Working: {', '.join(working)}")
    if failed:
        print(f"❌ Failed: {', '.join(failed)}")
    if skipped:
        print(f"⏭️  Skipped: {', '.join(skipped)}")

    if working:
        print(f"\n🎉 Success! Use {working[0]} scraper")
        return 0
    else:
        print("\n❌ No working scrapers")
        return 1


if __name__ == '__main__':
    sys.exit(main())
