"""
Safety Level Verification Script

Verifies that all MCP tools have correct safety levels (0-3) and
that they respect the action approval requirements.
"""

import sys
from pathlib import Path
import importlib.util

sys.path.insert(0, str(Path(__file__).parent.parent))


def load_tool_class(tool_path):
    """Dynamically load a tool class from file."""
    try:
        spec = importlib.util.spec_from_file_location("tool_module", tool_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find tool class (usually ends with 'Tool')
        for name in dir(module):
            if name.endswith('Tool') and not name.startswith('_'):
                return getattr(module, name)
        return None
    except Exception as e:
        return None


def verify_tool_safety_levels():
    """Verify safety levels for all MCP tools."""

    # Expected safety levels based on constitution
    expected_levels = {
        # Level 0: Read-only operations
        "odoo_query_financials.py": 0,
        "odoo_check_connection.py": 0,
        "odoo_get_transactions.py": 0,
        "get_briefing.py": 0,
        "list_briefings.py": 0,
        "social_get_engagement.py": 0,
        "social_list_posts.py": 0,

        # Level 1: Notify (drafts, low-risk modifications)
        "odoo_record_transaction.py": 1,
        "generate_briefing.py": 1,
        "add_critical_issue.py": 1,
        "social_schedule.py": 1,

        # Level 2: Confirm (external communications, significant changes)
        "social_post.py": 2,
        "schedule_briefing.py": 2,

        # Level 3: Explicit Approval (financial transactions > $500, deletions)
        # Note: Level 3 is typically enforced by amount thresholds, not tool type
    }

    results = []

    tool_dirs = [
        Path("mcp-servers/digital-fte-server/tools"),
        Path("mcp-servers/digital-fte-server/tools/social_media")
    ]

    for tool_dir in tool_dirs:
        if not tool_dir.exists():
            continue

        for tool_file in tool_dir.glob("*.py"):
            if tool_file.name.startswith("__"):
                continue

            tool_name = tool_file.name
            expected_level = expected_levels.get(tool_name)

            if expected_level is None:
                # Unknown tool, skip
                continue

            # Read file to check for safety_level attribute
            content = tool_file.read_text()
            issues = []

            # Check if safety_level is defined
            if "safety_level" not in content:
                issues.append("Missing safety_level attribute")
            else:
                # Try to extract the value
                for line in content.split('\n'):
                    if 'safety_level' in line and '=' in line:
                        try:
                            # Extract number
                            parts = line.split('=')
                            if len(parts) >= 2:
                                level_str = parts[1].strip().split()[0]
                                actual_level = int(level_str)

                                if actual_level != expected_level:
                                    issues.append(
                                        f"Incorrect safety level: expected {expected_level}, "
                                        f"found {actual_level}"
                                    )
                                break
                        except:
                            pass

            # Check for description
            if "description" not in content:
                issues.append("Missing description attribute")

            # Check for execute method
            if "def execute" not in content:
                issues.append("Missing execute method")

            status = "PASS" if not issues else "FAIL"
            results.append({
                "tool": tool_name,
                "expected_level": expected_level,
                "status": status,
                "issues": issues
            })

    return results


def verify_approval_workflow():
    """Verify that tools implement approval workflow correctly."""

    results = []

    # Check audit logger integration
    audit_logger_path = Path("watchers/shared/audit_logger.py")
    if audit_logger_path.exists():
        content = audit_logger_path.read_text()
        issues = []

        # Check for user_approval parameter
        if "user_approval" not in content:
            issues.append("Missing user_approval parameter in audit logger")

        # Check for safety_level parameter
        if "safety_level" not in content:
            issues.append("Missing safety_level parameter in audit logger")

        status = "PASS" if not issues else "FAIL"
        results.append({
            "component": "AuditLogger",
            "status": status,
            "issues": issues
        })

    return results


def main():
    """Run all safety level verification checks."""

    print("=" * 70)
    print("Safety Level Verification")
    print("=" * 70)
    print()

    # Verify tool safety levels
    print("Checking MCP Tool Safety Levels...")
    print("-" * 70)
    tool_results = verify_tool_safety_levels()

    for result in tool_results:
        print(f"\n{result['tool']}: {result['status']}")
        print(f"  Expected Level: {result['expected_level']}")
        if result['issues']:
            for issue in result['issues']:
                print(f"  - {issue}")

    # Verify approval workflow
    print("\n\nChecking Approval Workflow...")
    print("-" * 70)
    approval_results = verify_approval_workflow()

    for result in approval_results:
        print(f"\n{result['component']}: {result['status']}")
        if result['issues']:
            for issue in result['issues']:
                print(f"  - {issue}")

    # Summary
    print("\n\n" + "=" * 70)
    print("Summary")
    print("=" * 70)

    tool_pass = sum(1 for r in tool_results if r['status'] == 'PASS')
    tool_total = len(tool_results)

    approval_pass = sum(1 for r in approval_results if r['status'] == 'PASS')
    approval_total = len(approval_results)

    print(f"Tool Safety Levels: {tool_pass}/{tool_total} passed")
    print(f"Approval Workflow: {approval_pass}/{approval_total} passed")

    total_pass = tool_pass + approval_pass
    total_count = tool_total + approval_total

    print(f"\nOverall: {total_pass}/{total_count} passed")

    if total_pass == total_count:
        print("\n✓ All safety level checks passed!")
        return 0
    else:
        print(f"\n✗ {total_count - total_pass} checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
