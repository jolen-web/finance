#!/usr/bin/env python3
"""
BDO Deals Scraper - Using Perx API directly
Fetches real deal data from Perx Technology backend (api.perxtech.net)
"""

import requests
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
import argparse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BDOPerxScraper:
    """Scraper for BDO deals using official Perx API"""

    def __init__(self, timeout=15):
        self.timeout = timeout
        self.session = requests.Session()
        self.access_token = None
        self.bearer_token = None
        self.deals = []

        # BDO endpoints
        self.config_url = "https://www.deals.bdo.com.ph/assets/config/app-config.json"
        self.token_v4_url = "https://www.deals.bdo.com.ph/v4/oauth/token"
        self.api_base = "https://api.perxtech.net"

        # Headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

    def get_token(self) -> bool:
        """Get OAuth v4 bearer token from BDO"""
        logger.info("🔐 Getting OAuth v4 token from BDO...")

        try:
            # Step 1: Get app config to extract identifier
            logger.info("📋 Fetching app config...")
            config_response = self.session.get(
                self.config_url,
                timeout=self.timeout
            )

            if config_response.status_code != 200:
                logger.error(f"❌ Failed to get app config: {config_response.status_code}")
                return False

            config_data = config_response.json()
            identifier = config_data.get('custom', {}).get('pi')

            if not identifier:
                logger.error("❌ No identifier found in app config")
                return False

            logger.info(f"✅ Got identifier: {identifier[:20]}...")

            # Step 2: Get v4 bearer token with identifier
            logger.info("🔐 Requesting v4 bearer token...")
            payload = {"url": "www.deals.bdo.com.ph", "identifier": identifier}
            token_response = self.session.post(
                self.token_v4_url,
                json=payload,
                timeout=self.timeout
            )

            if token_response.status_code == 200:
                data = token_response.json()
                self.bearer_token = data.get('bearer_token')

                if self.bearer_token:
                    logger.info(f"✅ Bearer token obtained: {self.bearer_token[:30]}...")
                    # Add token to headers
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.bearer_token}'
                    })
                    return True
                else:
                    logger.warning("⚠️  No bearer_token in response")
                    logger.debug(f"Response: {data}")
                    return False
            else:
                logger.error(f"❌ Token request failed: {token_response.status_code}")
                logger.debug(f"Response: {token_response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Error getting token: {e}")
            return False

    def fetch_deals(self, category: str = "dine", card_type: str = "credit-card") -> bool:
        """Fetch rewards from Perx catalogs API with pagination"""
        logger.info(f"📥 Fetching rewards from catalogs...")

        if not self.bearer_token:
            logger.error("❌ No bearer token. Run get_token() first")
            return False

        try:
            all_deals = []
            page = 1
            total_pages = 1

            while page <= total_pages:
                # Fetch catalog items page
                endpoint = f"{self.api_base}/v4/catalogs/1/items?page={page}&size=20&category_ids=1"
                logger.info(f"📄 Fetching page {page}: {endpoint}")
                response = self.session.get(endpoint, timeout=self.timeout)

                if response.status_code != 200:
                    logger.error(f"❌ HTTP {response.status_code}: {response.text[:100]}")
                    break

                data = response.json()

                # Get pagination info
                meta = data.get('meta', {})
                total_pages = meta.get('total_pages', 1)
                items = data.get('data', [])

                logger.info(f"✅ Page {page}/{total_pages}: Found {len(items)} catalog items")

                # Fetch reward details for each catalog item
                for item in items:
                    item_id = item.get('item_id')
                    if not item_id:
                        continue

                    try:
                        # Fetch reward details
                        reward_endpoint = f"{self.api_base}/v4/rewards/{item_id}"
                        reward_response = self.session.get(reward_endpoint, timeout=self.timeout)

                        if reward_response.status_code == 200:
                            reward_data = reward_response.json().get('data', {})
                            if reward_data.get('name'):
                                all_deals.append(reward_data)
                        else:
                            logger.debug(f"⚠️  Could not fetch reward {item_id}: {reward_response.status_code}")
                    except Exception as e:
                        logger.debug(f"⚠️  Error fetching reward {item_id}: {e}")
                        continue

                page += 1

            self.deals = all_deals

            if self.deals:
                logger.info(f"✅ Found {len(self.deals)} rewards total")
                return True
            else:
                logger.warning(f"⚠️  Empty response from API")
                return False

        except Exception as e:
            logger.error(f"❌ Error fetching deals: {e}")
            return False

    def parse_deal(self, deal_data: Dict) -> Optional[Dict]:
        """Parse individual reward from Perx API response"""
        try:
            # Extract merchant name
            merchant = deal_data.get('merchant_name', '')

            # Extract category tags if available
            category = 'General'
            category_tags = deal_data.get('category_tags', [])
            if category_tags and isinstance(category_tags, list) and len(category_tags) > 0:
                category = category_tags[0].get('title', 'General')

            # Extract reward ID for direct deal link - use /deal-welcome/ for rewards
            reward_id = deal_data.get('id', '')
            direct_url = f'https://www.deals.bdo.com.ph/deal-welcome/{reward_id}' if reward_id else 'https://www.deals.bdo.com.ph'

            # Extract description - may be in accordions
            description = deal_data.get('description', '')
            if not description and deal_data.get('accordions'):
                # Try to get description from accordions
                for accordion in deal_data.get('accordions', []):
                    if accordion.get('title') == 'Promo Details':
                        description = accordion.get('body', '')
                        break

            # Extract image URL from images list
            image_url = ''
            if deal_data.get('images'):
                for img in deal_data.get('images', []):
                    if img.get('type') == 'card' or img.get('type') == 'reward_card':
                        image_url = img.get('url', '')
                        break

            # Map Perx reward fields to our schema
            parsed = {
                'source': 'bdo_perx_api',
                'card_issuer': 'BDO',
                'title': deal_data.get('name', ''),
                'description': description,
                'detailed_description': description,
                'merchant': merchant,
                'category': category,
                'card_type': 'Credit Card',
                'discount_type': 'promotional',
                'discount_percent': None,
                'discount_amount': None,
                'reward_points': None,
                'cashback_percent': None,
                'promotion_start_date': deal_data.get('valid_from', ''),
                'promotion_end_date': deal_data.get('valid_to', ''),
                'url': direct_url,
                'promotion_details': deal_data.get('terms_and_conditions', ''),
                'image_url': image_url,
                'merchant_logo_url': deal_data.get('merchant_logo_url', ''),
                'data_quality_score': 0.85,
            }

            # Only keep deals with at least a title
            if parsed['title']:
                return parsed
            return None

        except Exception as e:
            logger.warning(f"Error parsing reward: {e}")
            return None

    def process_deals(self) -> List[Dict]:
        """Process all fetched deals"""
        logger.info("⚙️  Processing deals...")

        processed = []
        for i, deal in enumerate(self.deals):
            parsed = self.parse_deal(deal)
            if parsed:
                processed.append(parsed)
                logger.info(f"✅ {i+1}. {parsed['title']}")

        logger.info(f"\n✅ Processed {len(processed)} deals")
        return processed

    def save_to_json(self, filepath: str, deals: List[Dict]) -> bool:
        """Save deals to JSON file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(deals, f, indent=2)
            logger.info(f"✅ Saved {len(deals)} deals to {filepath}")
            return True
        except Exception as e:
            logger.error(f"❌ Error saving JSON: {e}")
            return False

    def scrape(self) -> List[Dict]:
        """Run full scraping process"""
        logger.info("=" * 60)
        logger.info("BDO Perx API Scraper Started")
        logger.info("=" * 60)

        # Step 1: Get token
        if not self.get_token():
            logger.error("❌ Failed to get authentication token")
            return []

        # Step 2: Fetch deals
        if not self.fetch_deals():
            logger.error("❌ Failed to fetch deals")
            return []

        # Step 3: Process deals
        processed = self.process_deals()

        logger.info("=" * 60)
        logger.info("Scraping Complete")
        logger.info("=" * 60)

        return processed


def main():
    parser = argparse.ArgumentParser(description='BDO Perx API Deals Scraper')
    parser.add_argument('--category', default='dine', help='Deal category')
    parser.add_argument('--card-type', default='credit-card', help='Card type')
    parser.add_argument('--output', choices=['json', 'print'], default='print', help='Output format')
    parser.add_argument('--filepath', default='/tmp/bdo_perx_deals.json', help='Output file path')

    args = parser.parse_args()

    scraper = BDOPerxScraper()
    deals = scraper.scrape()

    if deals:
        if args.output == 'json':
            scraper.save_to_json(args.filepath, deals)
        else:
            print("\n" + "=" * 60)
            print("SCRAPED DEALS")
            print("=" * 60)
            for deal in deals:
                print(f"\n✅ {deal['title']}")
                print(f"   Issuer: {deal['card_issuer']}")
                print(f"   Merchant: {deal['merchant']}")
                print(f"   Category: {deal['category']}")
                if deal.get('discount_percent'):
                    print(f"   Discount: {deal['discount_percent']}%")
                if deal.get('image_url'):
                    print(f"   Image: {deal['image_url']}")
    else:
        print("❌ No deals scraped")


if __name__ == '__main__':
    main()
