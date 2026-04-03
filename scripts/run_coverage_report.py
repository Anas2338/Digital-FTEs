"""
Test Coverage Report Script

Runs pytest with coverage and verifies 80%+ coverage requirement
from the constitution.
"""

import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def run_pytest_with_coverage():
    """Run pytest with coverage reporting."""

    print("=" * 70)
    print("RUNNING TEST SUITE WITH COVERAGE")
    print("=" * 70)
    print()

    # Check if pytest is available
    try:
        result = subprocess.run(
            ["pytest", "--version"],
            capture_output=True,
            text=True
        )
        print(f"Using: {result.stdout.strip()}")
    except FileNotFoundError:
        print("✗ pytest not found. Install with: uv pip install pytest pytest-cov")
        return None

    # Run tests with coverage
    print("\nRunning tests...")
    print("-" * 70)

    try:
        result = subprocess.run(
            [
                "pytest",
                "tests/",
                "--cov=watchers",
                "--cov=mcp-servers/digital-fte-server",
                "--cov-report=term-missing",
                "--cov-report=html:coverage_report",
                "-v"
            ],
            capture_output=True,
            text=True,
            timeout=300
        )

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("✗ Tests timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"✗ Error running tests: {e}")
        return False


def parse_coverage_report():
    """Parse coverage report to extract percentage."""

    # Try to read coverage report
    coverage_file = Path(".coverage")

    if not coverage_file.exists():
        print("\n⚠ Coverage file not found")
        return None

    # Try to get coverage percentage from HTML report
    html_index = Path("coverage_report/index.html")

    if html_index.exists():
        content = html_index.read_text()

        # Look for coverage percentage in HTML
        import re
        match = re.search(r'(\d+)%', content)
        if match:
            return int(match.group(1))

    return None


def check_coverage_by_component():
    """Check coverage for each major component."""

    print("\n" + "=" * 70)
    print("COVERAGE BY COMPONENT")
    print("=" * 70)

    components = {
        "Watchers": "watchers/",
        "MCP Server": "mcp-servers/digital-fte-server/",
        "Shared Components": "watchers/shared/",
        "Odoo Integration": "watchers/odoo_watcher/",
        "Social Media": "watchers/social_media_watcher/",
        "Briefing System": "watchers/briefing_watcher/"
    }

    results = []

    for component, path in components.items():
        component_path = Path(path)

        if not component_path.exists():
            print(f"\n{component}: NOT FOUND")
            continue

        # Count Python files
        py_files = list(component_path.rglob("*.py"))
        py_files = [f for f in py_files if '__pycache__' not in str(f) and '__init__' not in f.name]

        # Count test files
        test_files = list(Path("tests").rglob(f"test_*{component_path.name}*.py"))

        coverage_estimate = "Unknown"
        if len(py_files) > 0:
            test_ratio = len(test_files) / len(py_files)
            if test_ratio >= 0.8:
                coverage_estimate = "Good (80%+)"
            elif test_ratio >= 0.5:
                coverage_estimate = "Moderate (50-80%)"
            else:
                coverage_estimate = "Low (<50%)"

        print(f"\n{component}:")
        print(f"  Source Files: {len(py_files)}")
        print(f"  Test Files: {len(test_files)}")
        print(f"  Estimated Coverage: {coverage_estimate}")

        results.append({
            "component": component,
            "source_files": len(py_files),
            "test_files": len(test_files),
            "coverage": coverage_estimate
        })

    return results


def main():
    """Run test coverage analysis."""

    print("=" * 70)
    print("TEST COVERAGE REPORT")
    print("=" * 70)
    print("\nConstitution Requirement: 80%+ test coverage")
    print()

    # Check if tests directory exists
    tests_dir = Path("tests")
    if not tests_dir.exists():
        print("✗ Tests directory not found")
        return 1

    # Count test files
    test_files = list(tests_dir.rglob("test_*.py"))
    print(f"Found {len(test_files)} test files")
    print()

    # List test categories
    print("Test Categories:")
    print("-" * 70)

    categories = {
        "Unit Tests": "tests/unit/",
        "Integration Tests": "tests/integration/",
        "Contract Tests": "tests/contract/",
        "Safety Tests": "tests/safety/"
    }

    for category, path in categories.items():
        cat_path = Path(path)
        if cat_path.exists():
            count = len(list(cat_path.glob("test_*.py")))
            print(f"  {category}: {count} files")
        else:
            print(f"  {category}: 0 files (directory not found)")

    # Run tests with coverage
    print("\n")
    test_success = run_pytest_with_coverage()

    # Check coverage by component
    component_results = check_coverage_by_component()

    # Parse overall coverage
    coverage_pct = parse_coverage_report()

    # Summary
    print("\n\n" + "=" * 70)
    print("COVERAGE SUMMARY")
    print("=" * 70)

    if coverage_pct:
        print(f"\nOverall Coverage: {coverage_pct}%")

        if coverage_pct >= 80:
            print("✓ MEETS 80% REQUIREMENT")
            status = 0
        else:
            print(f"✗ BELOW 80% REQUIREMENT (need {80 - coverage_pct}% more)")
            status = 1
    else:
        print("\n⚠ Could not determine exact coverage percentage")
        print("  Review coverage_report/index.html for details")
        status = 1

    print(f"\nTotal Test Files: {len(test_files)}")
    print(f"Test Execution: {'✓ PASS' if test_success else '✗ FAIL'}")

    print("\nCoverage Report: coverage_report/index.html")

    return status


if __name__ == "__main__":
    sys.exit(main())
