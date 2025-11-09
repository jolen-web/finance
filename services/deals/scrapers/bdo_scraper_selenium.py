#!/usr/bin/env python3
"""
BDO Credit Card Deals Scraper - Selenium Version

Uses Selenium for JavaScript-heavy pages that require browser rendering.
Handles dynamic content loading, infinite scroll, etc.

Requirements:
    pip install selenium webdriver-manager

Usage:
    python bdo_scraper_selenium.py --headless  # Run in background
    python bdo_scraper_selenium.py --debug     # Show browser
"""

import logging
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
import re
from urllib.parse import urljoin
import sys

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
except ImportError:
    print("❌ Selenium not installed. Install with: pip install selenium webdriver-manager")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BDOScraperSelenium:
    """Selenium-based BDO scraper for JavaScript-rendered content"""

    def __init__(self, base_url="https://deals.bdo.com.ph", headless=True, timeout=15):
        """
        Initialize Selenium scraper

        Args:
            base_url: Website URL
            headless: Run browser in headless mode
            timeout: Element wait timeout
        """
        self.base_url = base_url
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.deals = []

    def _initialize_driver(self):
        """Initialize Chrome WebDriver"""
        logger.info("Initializing Chrome WebDriver")

        try:
            options = Options()

            if self.headless:
                options.add_argument("--headless")
                logger.info("Running in headless mode")

            # Performance options
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("start-maximized")

            # User agent to avoid detection
            options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )

            # Install and use ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)

            # Set timeouts
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)

            logger.info("WebDriver initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            return False

    def _wait_for_element(self, by: By, value: str, timeout: int = None) -> bool:
        """
        Wait for element to be present

        Args:
            by: Selenium By selector
            value: Element selector value
            timeout: Custom timeout

        Returns:
            True if element found, False otherwise
        """
        timeout = timeout or self.timeout
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return True
        except Exception as e:
            logger.warning(f"Timeout waiting for element {value}: {e}")
            return False

    def _scroll_to_load_content(self):
        """Scroll page to trigger lazy-loading"""
        logger.info("Scrolling page to load dynamic content")

        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scrolls = 0
        max_scrolls = 10

        while scrolls < max_scrolls:
            # Scroll down
            self.driver.execute_script("window.scrollBy(0, window.innerHeight);")
            time.sleep(2)  # Wait for content to load

            # Check new height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                logger.info("Reached end of page")
                break

            last_height = new_height
            scrolls += 1
            logger.info(f"Scroll {scrolls}/{max_scrolls}")

    def fetch_and_render(self) -> bool:
        """
        Fetch page and render JavaScript

        Returns:
            True if successful
        """
        try:
            logger.info(f"Navigating to {self.base_url}")
            self.driver.get(self.base_url)

            # Wait for page to load
            self._wait_for_element(By.TAG_NAME, 'body', timeout=20)
            logger.info("Page loaded")

            # Scroll to load dynamic content
            self._scroll_to_load_content()

            return True

        except Exception as e:
            logger.error(f"Error fetching page: {e}")
            return False

    def extract_deals_from_page(self) -> List[Dict]:
        """
        Extract deals from rendered page

        Returns:
            List of deal dictionaries
        """
        logger.info("Extracting deals from rendered page")
        deals = []

        # Selectors to try
        selectors = [
            '.deal',
            '.offer',
            '.card.promotion',
            '[data-deal-id]',
            '.promotion-card',
            '.deal-item',
            '[class*="deal"]',
            '[class*="offer"]',
        ]

        deal_elements = []
        found_selector = None

        for selector in selectors:
            try:
                deal_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if deal_elements:
                    found_selector = selector
                    logger.info(f"Found {len(deal_elements)} elements with selector: {selector}")
                    break
            except Exception:
                continue

        if not deal_elements:
            logger.warning("No deal elements found")
            return deals

        # Extract each deal
        for idx, element in enumerate(deal_elements):
            try:
                deal = self._extract_deal_from_element(element, idx)
                if deal:
                    deals.append(deal)
                    logger.info(f"Extracted deal {idx + 1}: {deal.get('title', 'Untitled')}")
            except Exception as e:
                logger.warning(f"Error extracting deal {idx}: {e}")
                continue

        logger.info(f"Total deals extracted: {len(deals)}")
        return deals

    def _extract_deal_from_element(self, element, index: int) -> Optional[Dict]:
        """Extract individual deal from element"""
        deal = {
            'source': 'bdo_website_selenium',
            'scraped_at': datetime.now().isoformat(),
            'card_issuer': 'BDO',
        }

        try:
            # Title
            for selector in ['h2', 'h3', '.title', '[class*="title"]']:
                try:
                    title = element.find_element(By.CSS_SELECTOR, selector).text
                    if title:
                        deal['title'] = title
                        break
                except:
                    continue

            # Description (short)
            for selector in ['p', '.description', '[class*="description"]']:
                try:
                    desc = element.find_element(By.CSS_SELECTOR, selector).text
                    if desc:
                        deal['description'] = desc
                        break
                except:
                    continue

            # Image URL
            for selector in ['img', 'img.deal-image', '[class*="image"] img', '[class*="thumbnail"] img']:
                try:
                    img = element.find_element(By.CSS_SELECTOR, selector)
                    img_src = img.get_attribute('src') or img.get_attribute('data-src')
                    if img_src:
                        deal['image_url'] = urljoin(self.base_url, img_src)
                        logger.info(f"Found image: {deal['image_url']}")
                        break
                except:
                    continue

            # Detailed description (full text)
            try:
                # Get all text from the element as detailed description
                full_text = element.text
                if len(full_text) > len(deal.get('description', '')):
                    deal['detailed_description'] = full_text
            except:
                pass

            # Get all text for pattern matching
            text = element.text

            # Cashback percentage
            cashback_match = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
            if cashback_match:
                deal['cashback_percent'] = float(cashback_match.group(1))

            # Reward points
            points_match = re.search(r'(\d+)\s*(?:points|pts)', text, re.IGNORECASE)
            if points_match:
                deal['reward_points'] = int(points_match.group(1))

            # URL
            try:
                link = element.find_element(By.TAG_NAME, 'a')
                href = link.get_attribute('href')
                if href:
                    deal['url'] = urljoin(self.base_url, href)
            except:
                pass

            # Data quality
            deal['data_quality_score'] = self._calculate_quality_score(deal)

            return deal

        except Exception as e:
            logger.warning(f"Error extracting deal: {e}")
            return None

    def _calculate_quality_score(self, deal: Dict) -> float:
        """Calculate data quality score"""
        score = 0.0
        max_score = 0.0

        if deal.get('title'):
            score += 0.15
        if deal.get('description'):
            score += 0.15
        if deal.get('image_url'):
            score += 0.15
        if deal.get('detailed_description'):
            score += 0.15
        max_score += 0.6

        if deal.get('cashback_percent'):
            score += 0.15
        if deal.get('url'):
            score += 0.15
        max_score += 0.3

        if deal.get('card_type'):
            score += 0.1
        max_score += 0.1

        return min(score / max_score, 1.0) if max_score > 0 else 0.0

    def scrape(self) -> List[Dict]:
        """Main scraping method"""
        logger.info("Starting BDO Selenium scraper")

        try:
            # Initialize driver
            if not self._initialize_driver():
                return []

            # Fetch and render
            if not self.fetch_and_render():
                return []

            # Extract deals
            self.deals = self.extract_deals_from_page()

            logger.info(f"Scraping complete. Found {len(self.deals)} deals")
            return self.deals

        except Exception as e:
            logger.error(f"Scraping error: {e}")
            return []

        finally:
            self.cleanup()

    def cleanup(self):
        """Close WebDriver"""
        if self.driver:
            logger.info("Closing WebDriver")
            self.driver.quit()

    def save_to_json(self, filepath: str) -> bool:
        """Save deals to JSON"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.deals, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.deals)} deals to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error saving JSON: {e}")
            return False

    def print_deals(self):
        """Print formatted deals"""
        if not self.deals:
            print("No deals found")
            return

        print(f"\n{'=' * 80}")
        print(f"BDO CREDIT CARD DEALS (Selenium) - {len(self.deals)} Total")
        print(f"{'=' * 80}\n")

        for idx, deal in enumerate(self.deals, 1):
            print(f"DEAL #{idx}")
            print(f"{'─' * 80}")
            for key, value in deal.items():
                if value:
                    print(f"  {key:.<30} {value}")
            print()


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='BDO Selenium Scraper')
    parser.add_argument('--url', default='https://deals.bdo.com.ph')
    parser.add_argument('--headless', action='store_true', default=True)
    parser.add_argument('--debug', action='store_true', help='Show browser window')
    parser.add_argument('--output', choices=['json', 'print'], default='print')
    parser.add_argument('--filepath', default='bdo_deals_selenium.json')

    args = parser.parse_args()

    # Create scraper
    scraper = BDOScraperSelenium(
        base_url=args.url,
        headless=not args.debug
    )

    # Run scraper
    deals = scraper.scrape()

    # Output
    if not deals:
        print("❌ No deals found")
        return 1

    if args.output == 'json':
        scraper.save_to_json(args.filepath)
        print(f"✅ Saved to {args.filepath}")
    else:
        scraper.print_deals()

    return 0


if __name__ == '__main__':
    sys.exit(main())
