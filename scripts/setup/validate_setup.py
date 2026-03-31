"""Quickstart validation script.

Runs all verification tests to validate Digital FTE setup:
1. Database connectivity
2. Watcher health checks
3. MCP server availability
4. Obsidian vault structure
5. Agent skills registration
6. Scheduler functionality
"""

import sys
from pathlib import Path
from typing import Dict, Any, List
import subprocess

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from watchers.shared.database import Database
from watchers.shared.health_aggregator import WatcherHealthAggregator
from scripts.scheduler.schedule_storage import ScheduleStorage


class SetupValidator:
    """Validator for Digital FTE setup."""

    def __init__(self):
        """Initialize validator."""
        self.results = []
        self.vault_path = Path("obsidian-vault")

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all validation tests.

        Returns:
            Validation results dict
        """
        print("Digital FTE Setup Validation")
        print("=" * 60)
        print()

        # Run tests
        self.test_database()
        self.test_vault_structure()
        self.test_watcher_health()
        self.test_mcp_server()
        self.test_scheduler()
        self.test_agent_skills()

        # Summary
        passed = sum(1 for r in self.results if r["passed"])
        failed = len(self.results) - passed

        print()
        print("=" * 60)
        print(f"SUMMARY: {passed}/{len(self.results)} tests passed")

        if failed > 0:
            print(f"\n{failed} test(s) failed:")
            for result in self.results:
                if not result["passed"]:
                    print(f"  - {result['name']}: {result['error']}")

        return {
            "total_tests": len(self.results),
            "passed": passed,
            "failed": failed,
            "results": self.results,
            "overall_status": "PASS" if failed == 0 else "FAIL"
        }

    def test_database(self):
        """Test database connectivity and schema."""
        print("Test 1: Database Connectivity")

        try:
            db = Database()

            # Check tables exist
            cursor = db.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            required_tables = ["watchers", "events", "actions"]
            missing_tables = [t for t in required_tables if t not in tables]

            if missing_tables:
                self._record_result(
                    "Database Connectivity",
                    False,
                    f"Missing tables: {', '.join(missing_tables)}"
                )
                print("  [FAIL] Missing tables")
            else:
                self._record_result("Database Connectivity", True)
                print("  [PASS] Database connected, all tables present")

        except Exception as e:
            self._record_result("Database Connectivity", False, str(e))
            print(f"  [FAIL] {e}")

    def test_vault_structure(self):
        """Test Obsidian vault directory structure."""
        print("\nTest 2: Obsidian Vault Structure")

        required_dirs = [
            "Inbox",
            "Needs_Action",
            "Done",
            "Approvals",
            "Content_Queue",
            "Schedules"
        ]

        missing_dirs = []

        for dir_name in required_dirs:
            dir_path = self.vault_path / dir_name
            if not dir_path.exists():
                missing_dirs.append(dir_name)

        if missing_dirs:
            self._record_result(
                "Vault Structure",
                False,
                f"Missing directories: {', '.join(missing_dirs)}"
            )
            print(f"  [FAIL] Missing directories: {', '.join(missing_dirs)}")
        else:
            self._record_result("Vault Structure", True)
            print("  [PASS] All required directories present")

    def test_watcher_health(self):
        """Test watcher health check system."""
        print("\nTest 3: Watcher Health Checks")

        try:
            aggregator = WatcherHealthAggregator()
            status = aggregator.get_aggregate_status()

            # Check if health records exist
            if status["total_watchers"] == 0:
                self._record_result(
                    "Watcher Health",
                    False,
                    "No watchers registered"
                )
                print("  [FAIL] No watchers registered")
            else:
                self._record_result("Watcher Health", True)
                print(f"  [PASS] Health check system operational ({status['total_watchers']} watchers)")
                print(f"    Status: {status['overall_status']}")

        except Exception as e:
            self._record_result("Watcher Health", False, str(e))
            print(f"  [FAIL] {e}")

    def test_mcp_server(self):
        """Test MCP server availability."""
        print("\nTest 4: MCP Server")

        try:
            # Check if server is running
            result = subprocess.run(
                ["curl", "-s", "http://localhost:8000/health"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and "healthy" in result.stdout:
                self._record_result("MCP Server", True)
                print("  [PASS] MCP server is running and healthy")
            else:
                self._record_result(
                    "MCP Server",
                    False,
                    "Server not responding or unhealthy"
                )
                print("  [FAIL] Server not responding")
                print("    Start with: uvicorn mcp_servers.digital_fte_server.server:app")

        except subprocess.TimeoutExpired:
            self._record_result("MCP Server", False, "Connection timeout")
            print("  [FAIL] Connection timeout")
        except FileNotFoundError:
            self._record_result("MCP Server", False, "curl not found")
            print("  [WARN] curl not found, skipping MCP server test")
        except Exception as e:
            self._record_result("MCP Server", False, str(e))
            print(f"  [FAIL] {e}")

    def test_scheduler(self):
        """Test scheduler functionality."""
        print("\nTest 5: Scheduler")

        try:
            storage = ScheduleStorage()

            # Check if Schedules directory exists
            if not storage.schedules_dir.exists():
                self._record_result(
                    "Scheduler",
                    False,
                    "Schedules directory not found"
                )
                print("  [FAIL] Schedules directory not found")
                return

            # Try to list schedules
            schedules = storage.list_schedules()

            self._record_result("Scheduler", True)
            print(f"  [PASS] Scheduler operational ({len(schedules)} schedules)")

        except Exception as e:
            self._record_result("Scheduler", False, str(e))
            print(f"  [FAIL] {e}")

    def test_agent_skills(self):
        """Test agent skills registration."""
        print("\nTest 6: Agent Skills")

        skills_dir = Path(".claude/skills")

        required_skills = [
            "approval-review",
            "linkedin-draft",
            "reasoning-plan",
            "schedule-task",
            "watcher-status",
            "mcp-invoke"
        ]

        missing_skills = []

        for skill_name in required_skills:
            skill_path = skills_dir / skill_name / "SKILL.md"
            if not skill_path.exists():
                missing_skills.append(skill_name)

        if missing_skills:
            self._record_result(
                "Agent Skills",
                False,
                f"Missing skills: {', '.join(missing_skills)}"
            )
            print(f"  [FAIL] Missing skills: {', '.join(missing_skills)}")
        else:
            self._record_result("Agent Skills", True)
            print(f"  [PASS] All {len(required_skills)} agent skills registered")

    def _record_result(self, name: str, passed: bool, error: str = None):
        """Record test result.

        Args:
            name: Test name
            passed: Whether test passed
            error: Optional error message
        """
        self.results.append({
            "name": name,
            "passed": passed,
            "error": error
        })


def main():
    """Main entry point."""
    validator = SetupValidator()
    results = validator.run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if results["overall_status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
