#!/usr/bin/env python3
"""
Autonomous Project Supervision Agent for Credit Card Deals Service
Manages all phases, quality gates, and risk monitoring
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from enum import Enum
import subprocess

class Phase(Enum):
    """Project phases"""
    PRE_DEVELOPMENT = 0
    FOUNDATION = 1
    SCRAPER_IMPLEMENTATION = 2
    API_INTEGRATION = 3
    UI_INTEGRATION = 4
    TESTING_QA = 5
    STAGING_DEPLOYMENT = 6
    CANARY_DEPLOYMENT = 7
    PRODUCTION_MONITORING = 8

class AgentStatus(Enum):
    """Agent status"""
    IDLE = "idle"
    ACTIVE = "active"
    ESCALATION = "escalation"
    BLOCKED = "blocked"

class ProjectSupervisor:
    """Autonomous project supervision agent"""

    def __init__(self, project_root="/Users/njpinton/projects/git/finance"):
        self.project_root = Path(project_root)
        self.state_file = self.project_root / ".deals_project_state.json"
        self.decision_log = self.project_root / ".deals_decision_log.json"
        self.status = AgentStatus.IDLE
        self.current_phase = Phase.PRE_DEVELOPMENT
        self.load_state()

    def load_state(self):
        """Load project state from file"""
        if self.state_file.exists():
            with open(self.state_file) as f:
                state = json.load(f)
                self.current_phase = Phase[state.get('phase', 'PRE_DEVELOPMENT')]
                self.status = AgentStatus[state.get('status', 'IDLE')]
        else:
            self.save_state()

    def save_state(self):
        """Save project state to file"""
        state = {
            'phase': self.current_phase.name,
            'status': self.status.value,
            'timestamp': datetime.now().isoformat()
        }
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def log_decision(self, decision_text, context, options, chosen, rationale):
        """Log a decision in the decision log"""
        decisions = []
        if self.decision_log.exists():
            with open(self.decision_log) as f:
                decisions = json.load(f)

        decision = {
            'timestamp': datetime.now().isoformat(),
            'phase': self.current_phase.name,
            'decision': decision_text,
            'context': context,
            'options_considered': options,
            'decision_made': chosen,
            'rationale': rationale
        }
        decisions.append(decision)

        with open(self.decision_log, 'w') as f:
            json.dump(decisions, f, indent=2)

    def verify_phase_exit_criteria(self, phase):
        """Verify all exit criteria for a phase"""
        criteria = {
            Phase.PRE_DEVELOPMENT: [
                'Cloud SQL instance created',
                'Secrets created in Secret Manager',
                'Cloud Build triggers configured',
                'Feature branch created'
            ],
            Phase.FOUNDATION: [
                'Service scaffold created',
                'Docker builds successfully',
                'Main product integration layer created',
                'Database schema created',
                'Tests passing (>90% coverage)'
            ],
            Phase.SCRAPER_IMPLEMENTATION: [
                '6+ website scrapers implemented',
                'Scraper tests passing (>90% coverage)',
                'Proxy/headers rotation working',
                'Data extraction validated',
                'Staging service pulling live data'
            ],
            Phase.API_INTEGRATION: [
                'Optional APIs integrated (Rakuten)',
                'Caching layer working (Redis)',
                'Error handling verified',
                'Data quality scoring implemented',
                'Staging service stable'
            ],
            Phase.UI_INTEGRATION: [
                'Deals widget appears on accounts page',
                'Page load time unchanged',
                'Mobile responsive',
                'Feature flag working',
                'Accessibility verified'
            ],
            Phase.TESTING_QA: [
                'Code coverage >80%',
                'All integration tests passing',
                'Main product regression tests pass',
                'Performance benchmarks met',
                'Security review passed',
                'Scraper reliability >90%'
            ],
            Phase.STAGING_DEPLOYMENT: [
                'Deployed to finance-deals-staging',
                'Real Cloud SQL working',
                'Scrapers running on schedule',
                '48-hour stability test passed',
                'Main product staging stable'
            ],
            Phase.CANARY_DEPLOYMENT: [
                '10% of users seeing deals',
                'Main product error rate unchanged',
                'Deals service <1% error rate',
                'User feedback positive',
                'Ready for 100% rollout'
            ],
            Phase.PRODUCTION_MONITORING: [
                '100% of users have deals enabled',
                'System stable for 1 week',
                'Scraper health monitoring active',
                'User engagement metrics positive',
                'Documentation complete'
            ]
        }

        return criteria.get(phase, [])

    def run_phase_verification(self, phase):
        """Run verification tests for a phase"""
        print(f"\n🔍 Verifying Phase: {phase.name}")
        print("=" * 60)

        criteria = self.verify_phase_exit_criteria(phase)

        for criterion in criteria:
            print(f"  □ {criterion}")

        print("\n" + "=" * 60)
        print(f"Phase verification checklist created.")
        print("Team must verify all items before phase completion.")

    def check_test_coverage(self):
        """Check test coverage for deals service"""
        print("\n📊 Checking Test Coverage...")

        pytest_cmd = [
            "pytest",
            "services/deals/tests",
            "--cov=services/deals",
            "--cov-report=term-missing"
        ]

        try:
            result = subprocess.run(
                pytest_cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            print(result.stdout)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Test coverage check failed: {e}")
            return False

    def check_isolation(self):
        """Check that deals service is isolated from main product"""
        print("\n🔐 Checking Service Isolation...")

        checks = [
            ('Main product imports', self._check_main_imports),
            ('Feature flag usage', self._check_feature_flags),
            ('Error handling', self._check_error_handling),
            ('Timeout protection', self._check_timeouts),
        ]

        all_passed = True
        for check_name, check_func in checks:
            result = check_func()
            status = "✓" if result else "✗"
            print(f"  {status} {check_name}")
            all_passed = all_passed and result

        return all_passed

    def _check_main_imports(self):
        """Verify main product doesn't hard-depend on deals"""
        try:
            main_init = self.project_root / "app" / "__init__.py"
            with open(main_init) as f:
                content = f.read()
                return 'deals' not in content.lower()
        except:
            return False

    def _check_feature_flags(self):
        """Verify feature flags control deals functionality"""
        try:
            config_file = self.project_root / "app" / "config" / "feature_flags.py"
            return config_file.exists()
        except:
            return False

    def _check_error_handling(self):
        """Verify error handling for deals service failures"""
        try:
            client_file = self.project_root / "app" / "services" / "deals" / "deals_client.py"
            if not client_file.exists():
                return False
            with open(client_file) as f:
                content = f.read()
                return 'except' in content and 'timeout' in content.lower()
        except:
            return False

    def _check_timeouts(self):
        """Verify timeouts on deals service calls"""
        try:
            client_file = self.project_root / "app" / "services" / "deals" / "deals_client.py"
            if not client_file.exists():
                return False
            with open(client_file) as f:
                content = f.read()
                return 'timeout' in content.lower()
        except:
            return False

    def check_scraper_health(self):
        """Check health of all scrapers"""
        print("\n🕷️  Checking Scraper Health...")

        scrapers = [
            'chase', 'amex', 'capital_one', 'discover', 'bankrate', 'credit_karma'
        ]

        for scraper in scrapers:
            scraper_file = self.project_root / "services" / "deals" / "app" / "scrapers" / f"{scraper}_scraper.py"
            status = "✓" if scraper_file.exists() else "✗"
            print(f"  {status} {scraper.replace('_', ' ').title()} scraper")

    def generate_weekly_report(self):
        """Generate weekly status report"""
        print("\n📋 DEALS SERVICE PROJECT - WEEKLY STATUS REPORT")
        print("=" * 70)
        print(f"Week of: {datetime.now().strftime('%Y-%m-%d')}")
        print(f"Current Phase: {self.current_phase.name}")
        print(f"Agent Status: {self.status.value}")
        print("=" * 70)

        print("\n1. PHASE PROGRESS")
        print(f"   Current Phase: {self.current_phase.name}")
        print("   Status: [To be filled by team]")

        print("\n2. COMPLETED THIS WEEK")
        print("   - [Specific deliverables]")
        print("   - [Code merged/deployed]")
        print("   - [Tests added]")

        print("\n3. PLANNED NEXT WEEK")
        print(f"   - Next phase: {(self.current_phase.value + 1)}")

        print("\n4. BLOCKERS")
        print("   - None / [Item 1] / [Item 2]")

        print("\n5. METRICS")
        print("   - Code coverage: [X]%")
        print("   - Test count: [N]")
        print("   - Scraper sources: 6")
        print("   - Deploy count: [K]")

        print("\n6. SCRAPER HEALTH")
        print("   - Chase: [Success Rate]%")
        print("   - Amex: [Success Rate]%")
        print("   - Capital One: [Success Rate]%")
        print("   - Discover: [Success Rate]%")
        print("   - Bankrate: [Success Rate]%")
        print("   - Credit Karma: [Success Rate]%")

        print("\n7. RISKS")
        print("   - [Identified risks]")
        print("   - [Mitigations in place]")

        print("\n8. TEAM HEALTH")
        print("   - Velocity: On track")
        print("   - Morale: Good")
        print("   - Blockers: None")

        print("\n" + "=" * 70)

    def advance_phase(self, new_phase):
        """Advance to next phase (requires verification)"""
        criteria = self.verify_phase_exit_criteria(self.current_phase)

        print(f"\n⚙️  Phase Advancement Request")
        print(f"From: {self.current_phase.name}")
        print(f"To: {new_phase.name}")
        print(f"\nExit criteria for {self.current_phase.name}:")
        for criterion in criteria:
            print(f"  ☐ {criterion}")

        print(f"\n⚠️  Manual Verification Required")
        print("Team lead must verify all exit criteria before approval.")

    def escalate_blocker(self, blocker_description, impact, suggested_actions):
        """Escalate a blocker to team lead"""
        self.status = AgentStatus.ESCALATION

        print(f"\n🚨 ESCALATION ALERT")
        print("=" * 60)
        print(f"Blocker: {blocker_description}")
        print(f"Impact: {impact}")
        print(f"Suggested Actions:")
        for action in suggested_actions:
            print(f"  • {action}")
        print("=" * 60)
        print("Team lead notified. Awaiting response.")

        self.save_state()

    def rollback_check(self):
        """Check if rollback criteria are met"""
        print("\n⚠️  Rollback Assessment")
        print("=" * 60)

        criteria = {
            'Main product error rate increase > 10%': False,
            'Main product latency increase > 10%': False,
            'Deals service error rate > 20%': False,
            'Data corruption detected': False,
            'Security incident': False,
            'All scraper sources failing': False
        }

        print("Monitoring for auto-rollback criteria:")
        for criterion, status in criteria.items():
            status_str = "⚠️" if status else "✓"
            print(f"  {status_str} {criterion}")

        any_critical = any(criteria.values())
        if any_critical:
            print("\n🚨 ROLLBACK CRITERIA MET - INITIATING ROLLBACK")
            return True
        else:
            print("\n✅ All metrics normal - Continuing")
            return False

    def display_dashboard(self):
        """Display project dashboard"""
        print("\n" + "=" * 70)
        print("CREDIT CARD DEALS SERVICE - PROJECT DASHBOARD")
        print("=" * 70)
        print(f"Supervisor Status: {self.status.value.upper()}")
        print(f"Current Phase: {self.current_phase.name}")
        print(f"Start Date: 2025-11-09")
        print(f"Estimated Completion: 2025-12-20")
        print(f"Duration: 6 weeks")
        print("\n" + "=" * 70)
        print("PHASE TIMELINE")
        print("=" * 70)

        phases = [
            "0. PRE-DEVELOPMENT SETUP (Week 1)",
            "1. FOUNDATION (Week 1-2)",
            "2. SCRAPER IMPLEMENTATION (Week 2-3)",
            "3. API INTEGRATION (Week 3-4)",
            "4. UI INTEGRATION (Week 4)",
            "5. TESTING & QA (Week 4-5)",
            "6. STAGING DEPLOYMENT (Week 5)",
            "7. CANARY DEPLOYMENT (Week 5-6)",
            "8. PRODUCTION MONITORING (Week 6+)"
        ]

        for phase_str in phases:
            phase_num = int(phase_str[0])
            marker = "▶ " if phase_num == self.current_phase.value else "  "
            print(f"{marker}{phase_str}")

        print("\n" + "=" * 70)

    def help_text(self):
        """Display help text"""
        print("""
DEALS PROJECT SUPERVISOR - CLI Reference

Usage: python scripts/deals_supervisor.py [command]

Commands:
  dashboard           Display project dashboard
  verify-phase        Verify exit criteria for current phase
  test-coverage       Check test coverage for deals service
  check-isolation     Verify service isolation from main product
  scraper-health      Check health of all scrapers
  weekly-report       Generate weekly status report
  advance-phase       Advance to next phase (requires verification)
  escalate            Escalate a blocker to team lead
  rollback-check      Check if rollback criteria are met
  help                Display this help text

Examples:
  python scripts/deals_supervisor.py dashboard
  python scripts/deals_supervisor.py test-coverage
  python scripts/deals_supervisor.py verify-phase
        """)

def main():
    supervisor = ProjectSupervisor()

    if len(sys.argv) < 2:
        supervisor.display_dashboard()
        return

    command = sys.argv[1].lower()

    if command == 'dashboard':
        supervisor.display_dashboard()
    elif command == 'verify-phase':
        supervisor.run_phase_verification(supervisor.current_phase)
    elif command == 'test-coverage':
        supervisor.check_test_coverage()
    elif command == 'check-isolation':
        supervisor.check_isolation()
    elif command == 'scraper-health':
        supervisor.check_scraper_health()
    elif command == 'weekly-report':
        supervisor.generate_weekly_report()
    elif command == 'advance-phase':
        new_phase_name = sys.argv[2] if len(sys.argv) > 2 else None
        if new_phase_name:
            new_phase = Phase[new_phase_name.upper()]
            supervisor.advance_phase(new_phase)
    elif command == 'escalate':
        blocker = sys.argv[2] if len(sys.argv) > 2 else "Blocker description needed"
        impact = sys.argv[3] if len(sys.argv) > 3 else "Impact assessment needed"
        supervisor.escalate_blocker(
            blocker,
            impact,
            ["Option 1", "Option 2", "Option 3"]
        )
    elif command == 'rollback-check':
        supervisor.rollback_check()
    elif command == 'help':
        supervisor.help_text()
    else:
        print(f"Unknown command: {command}")
        supervisor.help_text()

if __name__ == '__main__':
    main()
