"""
Quickstart Validation Script

Runs all validation steps from QUICKSTART.md to verify
Gold Tier Digital FTE is operational.
"""

import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def run_command(command, description):
    """Run a command and return success status."""
    print(f"\n{'='*70}")
    print(f"Testing: {description}")
    print(f"Command: {command}")
    print('='*70)

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        success = result.returncode == 0
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"\nStatus: {status}")

        return success

    except subprocess.TimeoutExpired:
        print("✗ FAIL: Command timed out")
        return False
    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False


def check_file_exists(file_path, description):
    """Check if a file exists."""
    print(f"\n{'='*70}")
    print(f"Checking: {description}")
    print(f"Path: {file_path}")
    print('='*70)

    path = Path(file_path)
    exists = path.exists()

    if exists:
        print(f"✓ PASS: File exists")
        if path.is_file():
            size = path.stat().st_size
            print(f"  Size: {size} bytes")
    else:
        print(f"✗ FAIL: File not found")

    return exists


def main():
    """Run all quickstart validation steps."""

    print("=" * 70)
    print("QUICKSTART.MD VALIDATION")
    print("=" * 70)
    print("\nThis script validates the Gold Tier Digital FTE setup")
    print("by running all checks from QUICKSTART.md")
    print()

    results = {}

    # 1. Check vault structure
    print("\n" + "="*70)
    print("SECTION 1: VAULT STRUCTURE")
    print("="*70)

    vault_dirs = [
        "obsidian-vault/Briefings",
        "obsidian-vault/Audit_Logs",
        "obsidian-vault/Accounting",
        "obsidian-vault/Social_Media",
        "obsidian-vault/Tasks",
        "obsidian-vault/Reports"
    ]

    vault_checks = []
    for vault_dir in vault_dirs:
        exists = check_file_exists(vault_dir, f"Vault directory: {vault_dir}")
        vault_checks.append(exists)

    results["Vault Structure"] = all(vault_checks)

    # 2. Check database files
    print("\n" + "="*70)
    print("SECTION 2: DATABASE FILES")
    print("="*70)

    db_files = [
        "obsidian-vault/Accounting/transactions.db",
        "obsidian-vault/Audit_Logs/audit.db"
    ]

    db_checks = []
    for db_file in db_files:
        exists = check_file_exists(db_file, f"Database: {db_file}")
        db_checks.append(exists)

    results["Database Files"] = all(db_checks)

    # 3. Check watcher files
    print("\n" + "="*70)
    print("SECTION 3: WATCHER FILES")
    print("="*70)

    watcher_files = [
        "watchers/odoo_watcher/watcher.py",
        "watchers/social_media_watcher/watcher.py",
        "watchers/briefing_watcher/watcher.py"
    ]

    watcher_checks = []
    for watcher_file in watcher_files:
        exists = check_file_exists(watcher_file, f"Watcher: {watcher_file}")
        watcher_checks.append(exists)

    results["Watcher Files"] = all(watcher_checks)

    # 4. Check MCP server
    print("\n" + "="*70)
    print("SECTION 4: MCP SERVER")
    print("="*70)

    mcp_exists = check_file_exists(
        "mcp-servers/digital-fte-server/server.py",
        "MCP Server"
    )
    results["MCP Server"] = mcp_exists

    # 5. Check MCP tools
    print("\n" + "="*70)
    print("SECTION 5: MCP TOOLS")
    print("="*70)

    tool_files = [
        "mcp-servers/digital-fte-server/tools/odoo_record_transaction.py",
        "mcp-servers/digital-fte-server/tools/odoo_query_financials.py",
        "mcp-servers/digital-fte-server/tools/generate_briefing.py",
        "mcp-servers/digital-fte-server/tools/social_media/social_post.py"
    ]

    tool_checks = []
    for tool_file in tool_files:
        exists = check_file_exists(tool_file, f"Tool: {tool_file}")
        tool_checks.append(exists)

    results["MCP Tools"] = all(tool_checks)

    # 6. Check configuration files
    print("\n" + "="*70)
    print("SECTION 6: CONFIGURATION")
    print("="*70)

    config_files = [
        ".env.example",
        ".gitignore",
        "QUICKSTART.md"
    ]

    config_checks = []
    for config_file in config_files:
        exists = check_file_exists(config_file, f"Config: {config_file}")
        config_checks.append(exists)

    results["Configuration"] = all(config_checks)

    # 7. Check scripts
    print("\n" + "="*70)
    print("SECTION 7: UTILITY SCRIPTS")
    print("="*70)

    script_files = [
        "scripts/verify_env.py",
        "scripts/daily_health_check.py",
        "scripts/setup_gold_tier_vault.py"
    ]

    script_checks = []
    for script_file in script_files:
        exists = check_file_exists(script_file, f"Script: {script_file}")
        script_checks.append(exists)

    results["Utility Scripts"] = all(script_checks)

    # 8. Check circuit breaker
    print("\n" + "="*70)
    print("SECTION 8: CIRCUIT BREAKER")
    print("="*70)

    cb_exists = check_file_exists(
        "mcp-servers/digital-fte-server/circuit_breaker.py",
        "Circuit Breaker"
    )
    results["Circuit Breaker"] = cb_exists

    # 9. Check shared components
    print("\n" + "="*70)
    print("SECTION 9: SHARED COMPONENTS")
    print("="*70)

    shared_files = [
        "watchers/shared/database.py",
        "watchers/shared/audit_logger.py",
        "watchers/shared/domain_manager.py"
    ]

    shared_checks = []
    for shared_file in shared_files:
        exists = check_file_exists(shared_file, f"Shared: {shared_file}")
        shared_checks.append(exists)

    results["Shared Components"] = all(shared_checks)

    # Summary
    print("\n\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)

    for section, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{section:.<50} {status}")

    total_pass = sum(1 for v in results.values() if v)
    total_sections = len(results)

    print(f"\n{total_pass}/{total_sections} sections passed")

    if total_pass == total_sections:
        print("\n✓ ALL QUICKSTART VALIDATIONS PASSED!")
        print("\nGold Tier Digital FTE is ready for operation.")
        return 0
    else:
        print(f"\n✗ {total_sections - total_pass} SECTIONS FAILED")
        print("\nPlease review failed sections and complete setup.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
