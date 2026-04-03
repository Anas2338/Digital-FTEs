"""
Error Handling and Logging Verification Script

Verifies that all watchers have consistent error handling and logging.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def verify_watcher_error_handling():
    """Verify error handling in all watchers."""

    watchers = [
        "watchers/odoo_watcher/watcher.py",
        "watchers/social_media_watcher/watcher.py",
        "watchers/briefing_watcher/watcher.py"
    ]

    results = []

    for watcher_path in watchers:
        path = Path(watcher_path)
        if not path.exists():
            results.append({
                "watcher": watcher_path,
                "status": "MISSING",
                "issues": ["File does not exist"]
            })
            continue

        content = path.read_text()
        issues = []

        # Check for try-except blocks
        if "try:" not in content or "except" not in content:
            issues.append("Missing try-except error handling")

        # Check for logging
        if "import logging" not in content:
            issues.append("Missing logging import")

        if "logger." not in content:
            issues.append("No logger usage found")

        # Check for circuit breaker integration
        if "circuit_breaker" not in content.lower():
            issues.append("Missing circuit breaker integration")

        # Check for audit logging
        if "audit" not in content.lower():
            issues.append("Missing audit logging")

        status = "PASS" if not issues else "FAIL"
        results.append({
            "watcher": watcher_path,
            "status": status,
            "issues": issues
        })

    return results


def verify_mcp_tool_error_handling():
    """Verify error handling in MCP tools."""

    tool_dirs = [
        "mcp-servers/digital-fte-server/tools",
        "mcp-servers/digital-fte-server/tools/social_media"
    ]

    results = []

    for tool_dir in tool_dirs:
        dir_path = Path(tool_dir)
        if not dir_path.exists():
            continue

        for tool_file in dir_path.glob("*.py"):
            if tool_file.name.startswith("__"):
                continue

            content = tool_file.read_text()
            issues = []

            # Check for error handling
            if "try:" not in content or "except" not in content:
                issues.append("Missing try-except error handling")

            # Check for result dict with success field
            if '"success"' not in content and "'success'" not in content:
                issues.append("Missing success field in result")

            # Check for error field in result
            if '"error"' not in content and "'error'" not in content:
                issues.append("Missing error field in result")

            status = "PASS" if not issues else "FAIL"
            results.append({
                "tool": str(tool_file),
                "status": status,
                "issues": issues
            })

    return results


def main():
    """Run all verification checks."""

    print("=" * 70)
    print("Error Handling and Logging Verification")
    print("=" * 70)
    print()

    # Verify watchers
    print("Checking Watchers...")
    print("-" * 70)
    watcher_results = verify_watcher_error_handling()

    for result in watcher_results:
        print(f"\n{result['watcher']}: {result['status']}")
        if result['issues']:
            for issue in result['issues']:
                print(f"  - {issue}")

    # Verify MCP tools
    print("\n\nChecking MCP Tools...")
    print("-" * 70)
    tool_results = verify_mcp_tool_error_handling()

    for result in tool_results:
        print(f"\n{result['tool']}: {result['status']}")
        if result['issues']:
            for issue in result['issues']:
                print(f"  - {issue}")

    # Summary
    print("\n\n" + "=" * 70)
    print("Summary")
    print("=" * 70)

    watcher_pass = sum(1 for r in watcher_results if r['status'] == 'PASS')
    watcher_total = len(watcher_results)

    tool_pass = sum(1 for r in tool_results if r['status'] == 'PASS')
    tool_total = len(tool_results)

    print(f"Watchers: {watcher_pass}/{watcher_total} passed")
    print(f"MCP Tools: {tool_pass}/{tool_total} passed")

    total_pass = watcher_pass + tool_pass
    total_count = watcher_total + tool_total

    print(f"\nOverall: {total_pass}/{total_count} passed")

    if total_pass == total_count:
        print("\n✓ All checks passed!")
        return 0
    else:
        print(f"\n✗ {total_count - total_pass} checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
