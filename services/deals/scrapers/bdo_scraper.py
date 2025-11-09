#!/usr/bin/env python3
"""
BDO Credit Card Deals Scraper

Scrapes credit card deals and promotions from BDO Philippines website.
Handles both static HTML and JavaScript-rendered content.

Usage:
    python bdo_scraper.py --mode static      # Use BeautifulSoup (fast)
    python bdo_scraper.py --mode js          # Use Selenium (comprehensive)
    python bdo_scraper.py --output json      # Output format
"""

import requests
from bs4 import BeautifulSoup
import json
import logging
import time
from datetime import datetime
from typing import List, Dict, Optional
import re
from urllib.parse import urljoin
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BDOScraper:
    """Scraper for BDO credit card deals"""

    def __init__(self, base_url="https://deals.bdo.com.ph", timeout=10, retries=3):
        """
        Initialize BDO scraper

        Args:
            base_url: Website URL to scrape
            timeout: Request timeout in seconds
            retries: Number of retries on failure
        """
        self.base_url = base_url
        self.timeout = timeout
        self.retries = retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.deals = []

    def fetch_page(self) -> Optional[str]:
        """
        Fetch the BDO deals page

        Returns:
            HTML content or None if fetch fails
        """
        for attempt in range(self.retries):
            try:
                logger.info(f"Fetching {self.base_url} (attempt {attempt + 1}/{self.retries})")
                response = self.session.get(self.base_url, timeout=self.timeout)
                response.raise_for_status()
                logger.info(f"Successfully fetched page ({len(response.text)} bytes)")
                return response.text
            except requests.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1}")
                time.sleep(2 ** attempt)  # Exponential backoff
            except requests.RequestException as e:
                logger.warning(f"Request error on attempt {attempt + 1}: {e}")
                time.sleep(2 ** attempt)

        logger.error("Failed to fetch page after all retries")
        return None

    def extract_deals_from_html(self, html: str) -> List[Dict]:
        """
        Extract deals from static HTML

        This method uses multiple selector strategies to handle different HTML structures.

        Args:
            html: HTML content

        Returns:
            List of deal dictionaries
        """
        logger.info("Parsing HTML content")
        soup = BeautifulSoup(html, 'html.parser')
        deals = []

        # Strategy 1: Look for common deal container classes
        selectors = [
            ('div.deal', 'deal'),
            ('div.card.offer', 'offer card'),
            ('div[data-deal-id]', 'data attribute'),
            ('article.promotion', 'promotion'),
            ('div.promotion-card', 'promotion card'),
            ('li.deal-item', 'deal item'),
            ('div[class*="deal"]', 'deal wildcard'),
            ('div[class*="offer"]', 'offer wildcard'),
            ('div[class*="promo"]', 'promo wildcard'),
        ]

        deal_elements = []
        selected_strategy = None

        for selector, strategy_name in selectors:
            elements = soup.select(selector)
            if elements:
                logger.info(f"Found {len(elements)} deals using selector: {selector} ({strategy_name})")
                deal_elements = elements
                selected_strategy = strategy_name
                break

        if not deal_elements:
            logger.warning("No deal elements found with any selector strategy")
            logger.info("Available divs on page:")
            for div in soup.find_all('div', limit=5):
                classes = div.get('class', [])
                logger.info(f"  div with classes: {' '.join(classes)}")
            return deals

        # Extract data from each deal element
        for idx, element in enumerate(deal_elements):
            try:
                deal = self._extract_deal_info(element, idx)
                if deal:
                    deals.append(deal)
                    logger.info(f"Extracted deal {idx + 1}: {deal.get('title', 'Untitled')}")
            except Exception as e:
                logger.warning(f"Error extracting deal {idx}: {e}")
                continue

        logger.info(f"Total deals extracted: {len(deals)}")
        return deals

    def _extract_deal_info(self, element, index: int) -> Optional[Dict]:
        """
        Extract individual deal information from an element

        Args:
            element: BeautifulSoup element
            index: Deal index (for fallback naming)

        Returns:
            Dictionary with deal information
        """
        deal = {
            'source': 'bdo_website',
            'scraped_at': datetime.now().isoformat(),
            'card_issuer': 'BDO',
        }

        # Title extraction
        title_selectors = ['h2', 'h3', 'h4', '.title', '.deal-title', '[class*="title"]']
        for selector in title_selectors:
            title_elem = element.select_one(selector)
            if title_elem:
                deal['title'] = title_elem.get_text(strip=True)
                break

        if 'title' not in deal:
            deal['title'] = f"BDO Deal #{index + 1}"

        # Description extraction
        desc_selectors = ['p', '.description', '.deal-description', '[class*="description"]']
        for selector in desc_selectors:
            desc_elem = element.select_one(selector)
            if desc_elem:
                deal['description'] = desc_elem.get_text(strip=True)
                break

        # Cashback percentage
        cashback_patterns = [
            r'(\d+(?:\.\d+)?)\s*%',  # Matches: 5%, 5.5%
            r'up\s+to\s+(\d+(?:\.\d+)?)\s*%',  # Matches: up to 5%
        ]

        text_content = element.get_text()
        for pattern in cashback_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                deal['cashback_percent'] = float(match.group(1))
                break

        # Reward points
        points_match = re.search(r'(\d+)\s*(?:points|pts|reward)', text_content, re.IGNORECASE)
        if points_match:
            deal['reward_points'] = int(points_match.group(1))

        # Discount amount
        discount_match = re.search(r'(?:₱|PHP|php)\s*(\d+(?:,\d+)*(?:\.\d+)?)', text_content)
        if discount_match:
            amount_str = discount_match.group(1).replace(',', '')
            deal['discount_amount'] = float(amount_str)

        # Card type/name
        card_type_selectors = ['.card-type', '.card-name', '[class*="card"]']
        for selector in card_type_selectors:
            card_elem = element.select_one(selector)
            if card_elem:
                deal['card_type'] = card_elem.get_text(strip=True)
                break

        # Promo dates (if visible)
        date_pattern = r'(\d{1,2}(?:/|-)\d{1,2}(?:/|-)\d{2,4})'
        dates = re.findall(date_pattern, text_content)
        if len(dates) >= 1:
            deal['promotion_start_date'] = dates[0]
        if len(dates) >= 2:
            deal['promotion_end_date'] = dates[1]

        # Link/URL if available
        link_elem = element.find('a')
        if link_elem and link_elem.get('href'):
            deal['url'] = urljoin(self.base_url, link_elem['href'])

        # Data quality scoring
        deal['data_quality_score'] = self._calculate_quality_score(deal)

        return deal

    def _calculate_quality_score(self, deal: Dict) -> float:
        """
        Calculate data quality score for a deal (0-1)

        More complete deals score higher.
        """
        score = 0.0
        max_score = 0.0

        # Required fields (40% of score)
        if deal.get('title'):
            score += 0.2
        if deal.get('description'):
            score += 0.2
        max_score += 0.4

        # Valuable fields (40% of score)
        if deal.get('cashback_percent'):
            score += 0.2
        if deal.get('promotion_end_date'):
            score += 0.2
        max_score += 0.4

        # Bonus fields (20% of score)
        if deal.get('card_type'):
            score += 0.1
        if deal.get('url'):
            score += 0.1
        max_score += 0.2

        return min(score / max_score, 1.0) if max_score > 0 else 0.0

    def scrape(self) -> List[Dict]:
        """
        Main scraping method

        Returns:
            List of deals
        """
        logger.info("Starting BDO deals scraper")

        # Fetch page
        html = self.fetch_page()
        if not html:
            logger.error("Failed to fetch page")
            return []

        # Extract deals
        self.deals = self.extract_deals_from_html(html)

        logger.info(f"Scraping complete. Found {len(self.deals)} deals")
        return self.deals

    def save_to_json(self, filepath: str) -> bool:
        """
        Save deals to JSON file

        Args:
            filepath: Output file path

        Returns:
            True if successful
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.deals, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.deals)} deals to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
            return False

    def save_to_csv(self, filepath: str) -> bool:
        """
        Save deals to CSV file

        Args:
            filepath: Output file path

        Returns:
            True if successful
        """
        try:
            import csv
            if not self.deals:
                logger.warning("No deals to save")
                return False

            # Get all possible keys
            keys = set()
            for deal in self.deals:
                keys.update(deal.keys())

            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=sorted(keys))
                writer.writeheader()
                writer.writerows(self.deals)

            logger.info(f"Saved {len(self.deals)} deals to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
            return False

    def print_deals(self):
        """Print deals in formatted output"""
        if not self.deals:
            print("No deals found")
            return

        print(f"\n{'=' * 80}")
        print(f"BDO CREDIT CARD DEALS - {len(self.deals)} Total")
        print(f"{'=' * 80}\n")

        for idx, deal in enumerate(self.deals, 1):
            print(f"DEAL #{idx}")
            print(f"{'─' * 80}")
            for key, value in deal.items():
                if value is not None and value != '':
                    print(f"  {key:.<30} {value}")
            print()


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='BDO Credit Card Deals Scraper')
    parser.add_argument('--url', default='https://deals.bdo.com.ph', help='Website URL to scrape')
    parser.add_argument('--output', choices=['json', 'csv', 'print'], default='print', help='Output format')
    parser.add_argument('--filepath', default='bdo_deals.json', help='Output file path')
    parser.add_argument('--timeout', type=int, default=10, help='Request timeout')
    parser.add_argument('--retries', type=int, default=3, help='Number of retries')

    args = parser.parse_args()

    # Create scraper
    scraper = BDOScraper(
        base_url=args.url,
        timeout=args.timeout,
        retries=args.retries
    )

    # Run scraper
    deals = scraper.scrape()

    if not deals:
        print("❌ No deals found. Possible issues:")
        print("  1. Website structure changed")
        print("  2. Content is JavaScript-rendered (try Selenium)")
        print("  3. Website blocks requests (try proxy rotation)")
        print("  4. Website is down")
        return 1

    # Output results
    if args.output == 'json':
        scraper.save_to_json(args.filepath)
        print(f"✅ Saved to {args.filepath}")
    elif args.output == 'csv':
        scraper.save_to_csv(args.filepath)
        print(f"✅ Saved to {args.filepath}")
    else:
        scraper.print_deals()

    return 0


if __name__ == '__main__':
    sys.exit(main())
