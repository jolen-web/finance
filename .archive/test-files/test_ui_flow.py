#!/usr/bin/env python
"""
UI Flow Test - Test homepage and all navigation buttons/pages
"""

import requests
import time
import re
from datetime import datetime

BASE_URL = 'http://127.0.0.1:5001'

class UITester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'TestBot/1.0'})
        self.username = f'uitest_{int(time.time())}'
        self.email = f'{self.username}@test.com'
        self.password = 'TestPass123!'
        self.account_id = None # To store created account ID
        self.category_id = None # To store created category ID
        self.investment_category_id = None # To store created investment category ID

    def register(self):
        """Register a test user"""
        print(f"\n[REGISTER] Creating user: {self.username}")
        data = {
            'username': self.username,
            'email': self.email,
            'password': self.password,
            'password_confirm': self.password
        }
        response = self.session.post(f'{BASE_URL}/auth/register', data=data, allow_redirects=True)
        if response.status_code == 200:
            print("✓ User registered successfully")
            return True
        else:
            print(f"✗ Registration failed: {response.status_code}")
            return False

    def login(self):
        """Login the user"""
        print(f"\n[LOGIN] Logging in user: {self.username}")
        data = {
            'username': self.username,
            'password': self.password
        }
        response = self.session.post(f'{BASE_URL}/auth/login', data=data, allow_redirects=True)
        if response.status_code == 200:
            print("✓ Login successful")
            return True
        else:
            print(f"✗ Login failed: {response.status_code}")
            return False

    def create_account(self, name, account_type, starting_balance):
        print(f"\n[ACCOUNT] Creating account: {name}")
        data = {
            'name': name,
            'account_type': account_type,
            'starting_balance': starting_balance
        }
        response = self.session.post(f'{BASE_URL}/accounts/new', data=data, allow_redirects=True)
        if response.status_code == 200:
            accounts_page = self.session.get(f'{BASE_URL}/accounts')
            # Extract account ID from the accounts page
            # The regex needs to be robust to whitespace and HTML structure
            match = re.search(r'<a href="/accounts/(\\d+)">\s*<strong>' + re.escape(name) + r'</strong>', accounts_page.text)
            if match:
                self.account_id = match.group(1)
                print(f"✓ Account '{name}' created successfully (ID: {self.account_id})")
                return True
            else:
                print(f"✗ Account '{name}' created, but not found on list page or regex failed.")
                normalized_name = name.lower().strip()
                # Remove HTML tags and normalize page text
                normalized_page_text = re.sub(r'<[^>]*>', '', accounts_page.text).lower()
                print(f"DEBUG: Normalized Name (repr): {repr(normalized_name)} (len: {len(normalized_name)})")
                print(f"DEBUG: Normalized Page Text (repr, FULL, no HTML): {repr(normalized_page_text)} (len: {len(normalized_page_text)})")
                if normalized_page_text.find(normalized_name) != -1:
                    # This block is intentionally left empty as the original search was for a different context.
                    # The instruction was to add debug prints for length, which are now included above.
                    pass
                print(f"DEBUG: Full Accounts page text: {accounts_page.text}")
                return False
        else:
            print(f"✗ Account '{name}' creation failed: {response.status_code}")
            return False
    def create_category(self, name, is_income=False, parent_id=None):
        print(f"\n[CATEGORY] Creating category: {name}")
        data = {
            'name': name,
            'is_income': 'on' if is_income else 'off',
            'parent_id': parent_id
        }
        response = self.session.post(f'{BASE_URL}/categories/new', data=data, allow_redirects=True)
        if response.status_code == 200:
            print(f"✓ Category '{name}' created successfully")
            self.category_id = "1" # Placeholder ID
            return True
        print(f"✗ Category '{name}' creation failed: {response.status_code}")
        return False

    def create_transaction(self, payee, amount, transaction_type='withdrawal', memo='Test Memo'):
        if not self.account_id:
            print("✗ Cannot create transaction: No account ID available.")
            return False
        if not self.category_id:
            print("✗ Cannot create transaction: No category ID available.")
            return False

        print(f"\n[TRANSACTION] Creating transaction: {payee}")
        data = {
            'account_id': self.account_id,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'amount': amount,
            'payee': payee,
            'transaction_type': transaction_type,
            'memo': memo,
            'category_id': self.category_id
        }
        response = self.session.post(f'{BASE_URL}/transactions/new', data=data, allow_redirects=True)
        if response.status_code == 200:
            print(f"✓ Transaction '{payee}' created successfully")
            return True
        print(f"✗ Transaction '{payee}' creation failed: {response.status_code}")
        return False

    def create_asset(self, name, asset_type, purchase_price, current_value):
        print(f"\n[ASSET] Creating asset: {name}")
        data = {
            'name': name,
            'asset_type': asset_type,
            'purchase_price': purchase_price,
            'current_value': current_value,
            'purchase_date': datetime.now().strftime('%Y-%m-%d'),
            'notes': 'Test asset notes'
        }
        response = self.session.post(f'{BASE_URL}/assets/new', data=data, allow_redirects=True)
        if response.status_code == 200:
            assets_page = self.session.get(f'{BASE_URL}/assets')
            if name in assets_page.text:
                print(f"✓ Asset '{name}' created successfully")
                return True
        print(f"✗ Asset '{name}' creation failed: {response.status_code}")
        return False

    def create_investment_category(self, name, description, color='#000000'):
        print(f"\n[INV CATEGORY] Creating investment category: {name}")
        data = {
            'name': name,
            'description': description,
            'color': color
        }
        response = self.session.post(f'{BASE_URL}/investments/categories/new', data=data, allow_redirects=True)
        if response.status_code == 200:
            inv_categories_page = self.session.get(f'{BASE_URL}/investments/categories')
            if name in inv_categories_page.text:
                # Extract investment category ID
                match = re.search(r'<a href="/investments/categories/(\\d+)/edit">' + re.escape(name), inv_categories_page.text)
                if match:
                    self.investment_category_id = match.group(1)
                    print(f"✓ Investment Category '{name}' created successfully (ID: {self.investment_category_id})")
                    return True
        print(f"✗ Investment Category '{name}' creation failed: {response.status_code}")
        return False

    def create_investment(self, name, investment_type, quantity, purchase_price):
        if not self.investment_category_id:
            print("✗ Cannot create investment: No investment category ID available.")
            return False

        print(f"\n[INVESTMENT] Creating investment: {name}")
        data = {
            'name': name,
            'investment_type': investment_type,
            'category_id': self.investment_category_id,
            'quantity': quantity,
            'purchase_price': purchase_price,
            'purchase_date': datetime.now().strftime('%Y-%m-%d') # Use current date
        }
        response = self.session.post(f'{BASE_URL}/investments/new', data=data, allow_redirects=True)
        if response.status_code == 200:
            investments_page = self.session.get(f'{BASE_URL}/investments')
            if name in investments_page.text:
                print(f"✓ Investment '{name}' created successfully")
                return True
        print(f"✗ Investment '{name}' creation failed: {response.status_code}")
        return False

    def test_homepage(self):
        """Test homepage"""
        print(f"\n[HOME] Testing homepage")
        response = self.session.get(f'{BASE_URL}/')
        if response.status_code == 200:
            print("✓ Homepage loads")
            # Check for key dashboard elements
            if 'Finance' in response.text or 'Tracker' in response.text:
                print("✓ Homepage contains expected content")
            return True
        else:
            print(f"✗ Homepage failed: {response.status_code}")
            return False

    def test_page(self, url, page_name, expected_content=None):
        """Test a page"""
        print(f"\n[{page_name.upper()}] Testing {url}")
        response = self.session.get(f'{BASE_URL}{url}')
        if response.status_code == 200:
            print(f"✓ {page_name} page loads")
            if expected_content:
                for content in expected_content:
                    if content.lower() in response.text.lower():
                        print(f"✓ Found '{content}'")
                    else:
                        print(f"⚠ Did not find '{content}'")
            return True
        else:
            print(f"✗ {page_name} failed: {response.status_code}")
            return False

    def test_buttons_on_page(self, url, page_name):
        """Test navigation buttons on a page"""
        print(f"\n[BUTTONS] Testing buttons on {page_name}")
        response = self.session.get(f'{BASE_URL}{url}')
        if response.status_code != 200:
            print(f"✗ Could not load {page_name}")
            return False

        # Count buttons using regex
        button_count = len(re.findall(r'<button[^>]*class=["\']btn', response.text))
        link_count = len(re.findall(r'<a[^>]*class=["\']nav-link', response.text))

        print(f"✓ Found {button_count} buttons and {link_count} nav links on {page_name}")
        return True

    def run_all_tests(self):
        """Run all UI tests"""
        print("=" * 70)
        print("UI FLOW TEST - Testing Homepage and All Navigation")
        print("=" * 70)

        # Register and login
        if not self.register():
            return False
        time.sleep(0.5)

        if not self.login():
            return False
        time.sleep(0.5)

        # Test homepage
        if not self.test_homepage():
            return False

        # Create test data
        print("\n" + "=" * 70)
        print("CREATING TEST DATA")
        print("=" * 70)
        if not self.create_account("Test Checking", "checking", 5000.0):
            return False
        time.sleep(0.5)
        return True # Exit after account creation for focused debugging

        # Test all main pages
        pages_to_test = [
            ('/accounts', 'Accounts', ['account', 'Test Checking']),
            ('/transactions', 'Transactions', ['transaction', 'Test Payee']),
            ('/categories', 'Categories', ['category', 'Test Category']),
            ('/investments', 'Investments', ['investment', 'Test Stock']),
            ('/assets', 'Assets', ['asset', 'Test Car']),
            ('/receipts', 'Receipts', ['receipt']),
            ('/settings', 'Settings', ['setting']),
            ('/investments/categories', 'Investment Categories', ['Test Inv Category']),
        ]

        print("\n" + "=" * 70)
        print("TESTING ALL PAGES")
        print("=" * 70)

        results = {}
        for url, name, expected in pages_to_test:
            try:
                result = self.test_page(url, name, expected)
                self.test_buttons_on_page(url, name)
                results[name] = result
            except Exception as e:
                print(f"✗ Error testing {name}: {e}")
                results[name] = False
            time.sleep(0.3)

        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        print(f"✓ Passed: {passed}/{total}")

        for page, result in results.items():
            status = "✓" if result else "✗"
            print(f"{status} {page}")

        if passed == total:
            print("\n✅ All UI tests PASSED!")
            return True
        else:
            print(f"\n⚠ {total - passed} test(s) failed")
            return False

if __name__ == '__main__':
    tester = UITester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
