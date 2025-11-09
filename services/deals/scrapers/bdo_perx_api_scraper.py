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
        self.deals = []

        # BDO endpoints
        self.token_url = "https://www.deals.bdo.com.ph/v2/oauth/token"
        self.api_base = "https://api.perxtech.net"

        # Headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

    def get_token(self) -> bool:
        """Get OAuth token from BDO"""
        logger.info("🔐 Getting OAuth token from BDO...")

        try:
            payload = {"url": "www.deals.bdo.com.ph"}
            response = self.session.post(
                self.token_url,
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')

                if self.access_token:
                    logger.info(f"✅ Token obtained: {self.access_token[:20]}...")
                    # Add token to headers
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.access_token}'
                    })
                    return True
                else:
                    logger.warning("⚠️  No access_token in response")
                    logger.debug(f"Response: {data}")
                    return False
            else:
                logger.error(f"❌ Token request failed: {response.status_code}")
                logger.debug(f"Response: {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Error getting token: {e}")
            return False

    def fetch_deals(self, category: str = "dine", card_type: str = "credit-card") -> bool:
        """Fetch deals from Perx API"""
        logger.info(f"📥 Fetching deals (category={category}, card_type={card_type})...")

        if not self.access_token:
            logger.error("❌ No access token. Run get_token() first")
            return False

        try:
            # Try different Perx API endpoints
            endpoints = [
                f"{self.api_base}/v4/deals?category={category}&cardType={card_type}",
                f"{self.api_base}/v4/deals?category={category}",
                f"{self.api_base}/v4/deals",
                f"{self.api_base}/v3/deals",
            ]

            for endpoint in endpoints:
                logger.info(f"Trying: {endpoint}")
                response = self.session.get(endpoint, timeout=self.timeout)

                logger.info(f"Status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()

                    # Parse response based on structure
                    if isinstance(data, list):
                        self.deals = data
                    elif isinstance(data, dict):
                        # Could be wrapped in 'data' or 'deals' key
                        self.deals = data.get('data', data.get('deals', []))

                    if self.deals:
                        logger.info(f"✅ Found {len(self.deals)} deals")
                        return True
                    else:
                        logger.warning(f"⚠️  Empty response from {endpoint}")
                        continue

                elif response.status_code == 401:
                    logger.warning("⚠️  Unauthorized (401) - token may be expired")
                    continue

                elif response.status_code == 404:
                    logger.warning(f"⚠️  Not found (404) - trying next endpoint")
                    continue

            logger.error("❌ All endpoints failed")
            return False

        except Exception as e:
            logger.error(f"❌ Error fetching deals: {e}")
            return False

    def parse_deal(self, deal_data: Dict) -> Optional[Dict]:
        """Parse individual deal from Perx API response"""
        try:
            # Map Perx field names to our schema
            parsed = {
                'source': 'bdo_perx_api',
                'card_issuer': deal_data.get('issuer', 'BDO'),
                'title': deal_data.get('title', deal_data.get('name', '')),
                'description': deal_data.get('description', deal_data.get('shortDescription', '')),
                'detailed_description': deal_data.get('details', deal_data.get('longDescription', '')),
                'merchant': deal_data.get('merchant', deal_data.get('partnerName', '')),
                'category': deal_data.get('category', 'General'),
                'card_type': deal_data.get('cardType', deal_data.get('card_type', 'Credit Card')),
                'discount_type': deal_data.get('discountType', 'percentage'),
                'discount_percent': deal_data.get('discountPercent', deal_data.get('discount', None)),
                'discount_amount': deal_data.get('discountAmount', None),
                'reward_points': deal_data.get('rewardPoints', deal_data.get('points', None)),
                'cashback_percent': deal_data.get('cashbackPercent', deal_data.get('cashback', None)),
                'promotion_start_date': deal_data.get('startDate', deal_data.get('validFrom', '')),
                'promotion_end_date': deal_data.get('endDate', deal_data.get('validUntil', '')),
                'url': deal_data.get('url', deal_data.get('link', 'https://www.deals.bdo.com.ph')),
                'promotion_details': deal_data.get('terms', deal_data.get('conditions', '')),
                'image_url': deal_data.get('imageUrl', deal_data.get('image', deal_data.get('thumbnail', ''))),
                'merchant_logo_url': deal_data.get('partnerLogo', deal_data.get('logo', '')),
                'data_quality_score': deal_data.get('qualityScore', 0.85),
            }

            # Only keep deals with at least a title
            if parsed['title']:
                return parsed
            return None

        except Exception as e:
            logger.warning(f"Error parsing deal: {e}")
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
