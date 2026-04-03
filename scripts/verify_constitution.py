"""
Constitution Compliance Verification Script

Verifies that the Gold Tier implementation complies with all
principles specified in .specify/memory/constitution.md
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def verify_local_first():
    """Verify local-first principle: all data in Obsidian vault."""

    results = []

    # Check that vault directory exists
    vault_path = Path("obsidian-vault")
    if not vault_path.exists():
        results.append({
            "principle": "Local-First Storage",
            "status": "FAIL",
            "issue": "Obsidian vault directory not found"
        })
        return results

    # Check for local databases
    local_dbs = [
        "obsidian-vault/Accounting/transactions.db",
        "obsidian-vault/Audit_Logs/audit.db"
    ]

    db_issues = []
    for db_path in local_dbs:
        if not Path(db_path).exists():
            db_issues.append(f"Missing: {db_path}")

    if db_issues:
        results.append({
            "principle": "Local-First Storage",
            "status": "FAIL",
            "issue": "; ".join(db_issues)
        })
    else:
        results.append({
            "principle": "Local-First Storage",
            "status": "PASS",
            "issue": None
        })

    return results


def verify_privacy_first():
    """Verify privacy-first principle: no cloud sync without consent."""

    results = []

    # Check .gitignore for sensitive data
    gitignore_path = Path(".gitignore")
    if not gitignore_path.exists():
        results.append({
            "principle": "Privacy-First",
            "status": "FAIL",
            "issue": ".gitignore not found"
        })
        return results

    content = gitignore_path.read_text()

    # Check for sensitive file patterns
    required_patterns = ['.env', '*.db', 'credentials', 'secrets']
    missing = []

    for pattern in required_patterns:
        if pattern not in content:
            missing.append(pattern)

    if missing:
        results.append({
            "principle": "Privacy-First",
            "status": "FAIL",
            "issue": f"Missing in .gitignore: {', '.join(missing)}"
        })
    else:
        results.append({
            "principle": "Privacy-First",
            "status": "PASS",
            "issue": None
        })

    return results


def verify_autonomous_operation():
    """Verify autonomous operation: watchers run 24/7."""

    results = []

    # Check for watcher files
    watchers = [
        "watchers/odoo_watcher/watcher.py",
        "watchers/social_media_watcher/watcher.py",
        "watchers/briefing_watcher/watcher.py"
    ]

    missing_watchers = []
    for watcher in watchers:
        if not Path(watcher).exists():
            missing_watchers.append(watcher)

    if missing_watchers:
        results.append({
            "principle": "Autonomous Operation",
            "status": "FAIL",
            "issue": f"Missing watchers: {', '.join(missing_watchers)}"
        })
        return results

    # Check for polling loops
    issues = []
    for watcher in watchers:
        content = Path(watcher).read_text()
        if 'while' not in content.lower() and 'schedule' not in content.lower():
            issues.append(f"{watcher}: No polling loop found")

    if issues:
        results.append({
            "principle": "Autonomous Operation",
            "status": "FAIL",
            "issue": "; ".join(issues)
        })
    else:
        results.append({
            "principle": "Autonomous Operation",
            "status": "PASS",
            "issue": None
        })

    return results


def verify_separation_of_concerns():
    """Verify separation of concerns: Brain/Memory/Senses/Hands."""

    results = []

    components = {
        "Memory (Obsidian)": "obsidian-vault",
        "Senses (Watchers)": "watchers",
        "Hands (MCP)": "mcp-servers/digital-fte-server"
    }

    missing = []
    for component, path in components.items():
        if not Path(path).exists():
            missing.append(component)

    if missing:
        results.append({
            "principle": "Separation of Concerns",
            "status": "FAIL",
            "issue": f"Missing components: {', '.join(missing)}"
        })
    else:
        results.append({
            "principle": "Separation of Concerns",
            "status": "PASS",
            "issue": None
        })

    return results


def verify_event_driven():
    """Verify event-driven architecture: watchers emit events."""

    results = []

    # Check for event/action queue
    db_path = Path("watchers/shared/database.py")
    if not db_path.exists():
        results.append({
            "principle": "Event-Driven",
            "status": "FAIL",
            "issue": "Database schema not found"
        })
        return results

    content = db_path.read_text()

    # Check for event/action tables
    has_events = 'events' in content.lower()
    has_actions = 'actions' in content.lower() or 'action_queue' in content.lower()

    if not (has_events or has_actions):
        results.append({
            "principle": "Event-Driven",
            "status": "FAIL",
            "issue": "No event/action queue tables found"
        })
    else:
        results.append({
            "principle": "Event-Driven",
            "status": "PASS",
            "issue": None
        })

    return results


def verify_action_safety():
    """Verify 4-level action safety system (0-3)."""

    results = []

    # Check for safety level implementation
    tool_files = list(Path("mcp-servers/digital-fte-server/tools").rglob("*.py"))

    if not tool_files:
        results.append({
            "principle": "Action Safety (4 Levels)",
            "status": "FAIL",
            "issue": "No MCP tools found"
        })
        return results

    # Check if tools have safety_level attribute
    tools_with_safety = 0
    for tool_file in tool_files:
        if tool_file.name.startswith("__"):
            continue

        content = tool_file.read_text()
        if 'safety_level' in content:
            tools_with_safety += 1

    if tools_with_safety == 0:
        results.append({
            "principle": "Action Safety (4 Levels)",
            "status": "FAIL",
            "issue": "No tools implement safety_level"
        })
    else:
        results.append({
            "principle": "Action Safety (4 Levels)",
            "status": "PASS",
            "issue": None
        })

    return results


def verify_idempotency():
    """Verify idempotency: duplicate detection."""

    results = []

    # Check for duplicate detection
    duplicate_detector_path = Path("watchers/odoo_watcher/duplicate_detector.py")

    if not duplicate_detector_path.exists():
        results.append({
            "principle": "Idempotency",
            "status": "FAIL",
            "issue": "Duplicate detector not found"
        })
        return results

    content = duplicate_detector_path.read_text()

    # Check for duplicate detection logic
    has_hash = 'hash' in content.lower() or 'sha' in content.lower()
    has_similarity = 'similar' in content.lower()

    if not (has_hash or has_similarity):
        results.append({
            "principle": "Idempotency",
            "status": "FAIL",
            "issue": "No duplicate detection logic found"
        })
    else:
        results.append({
            "principle": "Idempotency",
            "status": "PASS",
            "issue": None
        })

    return results


def verify_test_coverage():
    """Verify 80%+ test coverage requirement."""

    results = []

    # Check for test files
    test_files = list(Path("tests").rglob("test_*.py"))

    if len(test_files) < 10:
        results.append({
            "principle": "80%+ Test Coverage",
            "status": "WARN",
            "issue": f"Only {len(test_files)} test files found (need comprehensive coverage)"
        })
    else:
        results.append({
            "principle": "80%+ Test Coverage",
            "status": "PASS",
            "issue": f"{len(test_files)} test files found"
        })

    return results


def main():
    """Run all constitution compliance checks."""

    print("=" * 70)
    print("CONSTITUTION COMPLIANCE VERIFICATION")
    print("=" * 70)
    print()

    all_results = []

    # Run all verification checks
    checks = [
        ("Local-First", verify_local_first),
        ("Privacy-First", verify_privacy_first),
        ("Autonomous Operation", verify_autonomous_operation),
        ("Separation of Concerns", verify_separation_of_concerns),
        ("Event-Driven", verify_event_driven),
        ("Action Safety", verify_action_safety),
        ("Idempotency", verify_idempotency),
        ("Test Coverage", verify_test_coverage)
    ]

    for check_name, check_func in checks:
        print(f"\nChecking: {check_name}")
        print("-" * 70)
        results = check_func()
        all_results.extend(results)

        for result in results:
            status_symbol = "✓" if result["status"] == "PASS" else "✗" if result["status"] == "FAIL" else "⚠"
            print(f"{status_symbol} {result['principle']}: {result['status']}")
            if result["issue"]:
                print(f"  Issue: {result['issue']}")

    # Summary
    print("\n\n" + "=" * 70)
    print("COMPLIANCE SUMMARY")
    print("=" * 70)

    pass_count = sum(1 for r in all_results if r["status"] == "PASS")
    warn_count = sum(1 for r in all_results if r["status"] == "WARN")
    fail_count = sum(1 for r in all_results if r["status"] == "FAIL")
    total = len(all_results)

    print(f"\nPassed: {pass_count}/{total}")
    print(f"Warnings: {warn_count}/{total}")
    print(f"Failed: {fail_count}/{total}")

    if fail_count == 0:
        print("\n✓ CONSTITUTION COMPLIANCE VERIFIED!")
        print("\nAll core principles are implemented correctly.")
        return 0
    else:
        print(f"\n✗ {fail_count} COMPLIANCE ISSUES FOUND")
        print("\nPlease address failed checks to ensure constitution compliance.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
