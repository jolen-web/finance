#!/usr/bin/env python
"""
UI Flow Test - Test homepage and all navigation buttons/pages
"""

import requests
import time
import re

BASE_URL = 'http://127.0.0.1:5001'

class UITester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'TestBot/1.0'})
        self.username = f'uitest_{int(time.time())}'
        self.email = f'{self.username}@test.com'
        self.password = 'TestPass123!'

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

        # Test all main pages
        pages_to_test = [
            ('/accounts', 'Accounts', ['account']),
            ('/transactions', 'Transactions', ['transaction']),
            ('/categories', 'Categories', ['category']),
            ('/investments', 'Investments', ['investment']),
            ('/assets', 'Assets', ['asset']),
            ('/receipts', 'Receipts', ['receipt']),
            ('/settings', 'Settings', ['setting']),
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
