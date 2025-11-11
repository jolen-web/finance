#!/usr/bin/env python3
"""
BPI Credit Card Promos Scraper
Fetches credit card promotional deals from BPI API endpoint
"""

import requests
import logging
from datetime import datetime
from typing import List, Dict, Optional
import argparse
import json
from bs4 import BeautifulSoup
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BPIPromosScraper:
    """Scraper for BPI credit card promotions using API endpoint"""

    def __init__(self, timeout=15):
        self.timeout = timeout
        self.promos = []
        self.api_url = "https://www.bpi.com.ph/content/bpi/ph/en/personal/rewards-and-promotions/promos/jcr:content/root/container/tabshorizontal.model.json"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def fetch_all_promos(self) -> bool:
        """Fetch all promos from API with pagination"""
        logger.info("📥 Fetching promos from BPI API...")

        try:
            page = 1
            total_fetched = 0
            max_pages = 50  # Safety limit

            while page <= max_pages:
                logger.info(f"📄 Fetching page {page}...")

                params = {
                    'sort': 'newest',
                    'page': page
                }

                response = self.session.get(
                    self.api_url,
                    params=params,
                    timeout=self.timeout
                )

                if response.status_code != 200:
                    logger.error(f"❌ HTTP {response.status_code}")
                    break

                try:
                    data = response.json()
                except json.JSONDecodeError:
                    logger.error(f"❌ Invalid JSON response on page {page}")
                    break

                # Extract items from response
                items = self._extract_items_from_response(data)

                if not items:
                    logger.info(f"✅ No more items on page {page}, reached end")
                    break

                logger.info(f"✅ Page {page}: Found {len(items)} items")
                self.promos.extend(items)
                total_fetched += len(items)

                page += 1

            logger.info(f"✅ Fetched total {total_fetched} promos from API")
            return total_fetched > 0

        except Exception as e:
            logger.error(f"❌ Error fetching promos: {e}")
            return False

    def _extract_items_from_response(self, data: Dict) -> List[Dict]:
        """Extract promo items from API response"""
        items = []

        try:
            # BPI API structure: mapArticle.All[0].listPage[]
            if 'mapArticle' in data and isinstance(data['mapArticle'], dict):
                map_article = data['mapArticle']

                # Get "All" category or first available
                category = map_article.get('All')
                if not category and map_article:
                    # Fallback to first key
                    first_key = next(iter(map_article.keys()))
                    category = map_article.get(first_key)

                if category and isinstance(category, list) and len(category) > 0:
                    # Get listPage array
                    list_page = category[0].get('listPage', [])

                    if list_page:
                        logger.info(f"Found {len(list_page)} items in mapArticle")
                        for item in list_page:
                            promo = self._parse_api_item(item)
                            if promo:
                                items.append(promo)
                        return items

            # Fallback: Look for direct items array
            if 'items' in data and isinstance(data['items'], list):
                for item in data['items']:
                    promo = self._parse_api_item(item)
                    if promo:
                        items.append(promo)

        except Exception as e:
            logger.warning(f"⚠️ Error extracting items: {e}")

        return items

    def _extract_branches_from_detail_page(self, url: str, category: str) -> List[str]:
        """Extract participating branches from deal detail page"""
        try:
            # Only fetch detail page for restaurant/dining deals to save bandwidth
            restaurant_keywords = ['restaurant', 'dining', 'food', 'cafe', 'burger', 'pizza', 'seafood']
            is_restaurant = any(keyword in category.lower() for keyword in restaurant_keywords)

            if not is_restaurant:
                return []

            logger.debug(f"📄 Fetching detail page for branch info: {url}")
            response = self.session.get(url, timeout=10)

            if response.status_code != 200:
                logger.debug(f"⚠️  Could not fetch detail page: {response.status_code}")
                return []

            soup = BeautifulSoup(response.content, 'html.parser')
            full_text = response.text

            branches = []

            # Look for branch-related content in the HTML
            # Pattern 1: Extract from structured data (JSON-LD)
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        # Check for PostalAddress or Location fields
                        if 'streetAddress' in data:
                            address = data.get('streetAddress', '')
                            if address and address not in branches:
                                branches.append(address)
                except (json.JSONDecodeError, AttributeError):
                    continue

            # Pattern 2: Look for branch list in text content
            # Search for lines containing "branch", "location", "venue" with address patterns
            lines = full_text.split('\n')
            for i, line in enumerate(lines):
                line_clean = line.strip()

                # Look for common branch indicators
                if any(keyword in line_clean.lower() for keyword in ['branch', 'venue', 'location', 'outlet']):
                    # Get surrounding context
                    context_start = max(0, i - 1)
                    context_end = min(len(lines), i + 3)

                    for j in range(context_start, context_end):
                        context_line = BeautifulSoup(lines[j], 'html.parser').get_text(strip=True)

                        # Look for address-like patterns (street names, floor numbers, etc.)
                        if context_line and len(context_line) > 10:
                            # Filter for address-like content
                            if any(addr_keyword in context_line.lower() for addr_keyword in ['st.', 'ave', 'blvd', 'floor', 'f.', '#', 'no.']):
                                if context_line not in branches and context_line not in [BeautifulSoup(b, 'html.parser').get_text() for b in branches]:
                                    branches.append(context_line)

            # Deduplicate and clean
            cleaned_branches = list(dict.fromkeys([b.strip() for b in branches if b.strip()]))

            if cleaned_branches:
                logger.debug(f"✓ Found {len(cleaned_branches)} branches: {cleaned_branches[:2]}")

            return cleaned_branches[:20]  # Limit to 20 branches per deal

        except Exception as e:
            logger.debug(f"⚠️  Error extracting branches: {e}")
            return []

    def _parse_api_item(self, item: Dict) -> Optional[Dict]:
        """Parse individual promo item from API response"""
        try:
            # Extract title from BPI API response
            title = (
                item.get('heading') or
                item.get('title') or
                item.get('name') or
                ''
            )

            if not title:
                return None

            # Extract description
            description = item.get('description', '')

            # Extract image - BPI stores it as 'image' field
            image_url = item.get('image', '')
            # Make it absolute URL if needed
            if image_url and image_url.startswith('/'):
                image_url = 'https://www.bpi.com.ph' + image_url

            # Extract link/URL
            url = 'https://www.bpi.com.ph/personal/rewards-and-promotions/promos'
            if item.get('viewArticleLink'):
                link = item['viewArticleLink']
                if link.startswith('/'):
                    url = 'https://www.bpi.com.ph' + link
                else:
                    url = link

            # Extract category from chips or primaryTags
            category = 'General'
            chips = item.get('chips', [])
            if isinstance(chips, list) and chips:
                category = chips[0]
            else:
                tags = item.get('primaryTags', [])
                if isinstance(tags, list) and tags:
                    category = tags[0]

            # Extract merchant info
            merchant = 'BPI'
            text_combined = (title + ' ' + description).lower()

            merchants_keywords = {
                'shopee': 'Shopee',
                'lazada': 'Lazada',
                'amazon': 'Amazon',
                'grab': 'Grab',
                'gojek': 'GojJek',
                'foodpanda': 'Foodpanda',
                'mcdonalds': "McDonald's",
                'starbucks': 'Starbucks',
                'sm mall': 'SM Malls',
                'department store': 'Department Stores',
            }

            for keyword, merchant_name in merchants_keywords.items():
                if keyword in text_combined:
                    merchant = merchant_name
                    break

            # Extract discount info
            discount_percent = None
            discount_type = None
            cashback_percent = None

            # Look for percentage signs
            import re
            if '%' in description or '%' in title:
                match = re.search(r'(\d+)%', description or title)
                if match:
                    percent = int(match.group(1))
                    if 'cashback' in text_combined or 'cash back' in text_combined:
                        cashback_percent = percent
                    elif 'off' in text_combined or 'discount' in text_combined:
                        discount_percent = percent
                    else:
                        discount_percent = percent

            if 'bogo' in text_combined or 'buy 1 get 1' in text_combined:
                discount_type = 'bogo'

            # Extract dates from BPI API response
            start_date = item.get('date', '')  # Publication date
            end_date = item.get('promoExpiryDate', '')  # Expiry date

            # Extract participating branches from detail page
            branches = self._extract_branches_from_detail_page(url, category)

            promo_data = {
                'source': 'bpi_promos',
                'card_issuer': 'BPI',
                'title': title,
                'description': description,
                'detailed_description': description,
                'merchant': merchant,
                'category': category,
                'card_type': 'Credit Card',
                'discount_type': discount_type or 'promotional',
                'discount_percent': discount_percent,
                'cashback_percent': cashback_percent,
                'reward_points': None,
                'promotion_start_date': start_date,
                'promotion_end_date': end_date,
                'url': url,
                'promotion_details': '',
                'image_url': image_url,
                'merchant_logo_url': '',
                'participating_branches': json.dumps(branches) if branches else None,
                'data_quality_score': 0.85,
            }

            return promo_data

        except Exception as e:
            logger.debug(f"Error parsing item: {e}")
            return None

    def scrape(self) -> List[Dict]:
        """Run full scraping process"""
        logger.info("=" * 60)
        logger.info("BPI Promos API Scraper Started")
        logger.info("=" * 60)

        # Fetch from API
        if not self.fetch_all_promos():
            logger.error("❌ Failed to fetch promos from API")
            return []

        logger.info("=" * 60)
        logger.info("Scraping Complete")
        logger.info("=" * 60)

        return self.promos

    def save_to_json(self, filepath: str) -> bool:
        """Save promos to JSON file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.promos, f, indent=2)
            logger.info(f"✅ Saved {len(self.promos)} promos to {filepath}")
            return True
        except Exception as e:
            logger.error(f"❌ Error saving JSON: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description='BPI Credit Card Promos API Scraper')
    parser.add_argument('--output', choices=['json', 'print'], default='print', help='Output format')
    parser.add_argument('--filepath', default='/tmp/bpi_promos.json', help='Output file path')

    args = parser.parse_args()

    scraper = BPIPromosScraper()
    promos = scraper.scrape()

    if promos:
        if args.output == 'json':
            scraper.save_to_json(args.filepath)
        else:
            print("\n" + "=" * 60)
            print("SCRAPED BPI PROMOS")
            print("=" * 60)
            for promo in promos[:10]:  # Show first 10
                print(f"\n✅ {promo['title']}")
                print(f"   Merchant: {promo['merchant']}")
                print(f"   Category: {promo['category']}")
                if promo.get('discount_percent'):
                    print(f"   Discount: {promo['discount_percent']}%")
                if promo.get('image_url'):
                    print(f"   Image: {promo['image_url'][:60]}...")
            print(f"\n... and {len(promos) - 10} more promos")
            print(f"\nTotal: {len(promos)} promos")
    else:
        print("❌ No promos scraped")


if __name__ == '__main__':
    main()
