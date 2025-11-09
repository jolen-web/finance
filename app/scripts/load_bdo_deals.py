#!/usr/bin/env python3
"""
Script to load BDO deals into the database

Usage:
    python load_bdo_deals.py <json_filepath>

Example:
    python load_bdo_deals.py /tmp/bdo_credit_card_dining_deals.json
"""
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app import create_app, db
from app.models import Deal
from app.services.deals_cache import DealsCacheService


def load_deals_from_file(filepath):
    """Load deals from JSON file into database"""
    app = create_app()

    with app.app_context():
        result = DealsCacheService.load_deals_from_json(filepath)
        print(f"Result: {result}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python load_bdo_deals.py <json_filepath>")
        print("\nExample:")
        print("  python load_bdo_deals.py /tmp/bdo_deals.json")
        sys.exit(1)

    filepath = sys.argv[1]

    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    print(f"Loading deals from: {filepath}")
    load_deals_from_file(filepath)
    print("Done!")


if __name__ == '__main__':
    main()
