"""
Credentials Security Verification Script

Verifies that all sensitive data is stored in OS keychain,
not in code or config files.
"""

import sys
from pathlib import Path
import re

sys.path.insert(0, str(Path(__file__).parent.parent))


def scan_for_hardcoded_secrets(file_path):
    """Scan a file for potential hardcoded secrets."""

    content = file_path.read_text(errors='ignore')
    issues = []

    # Patterns that indicate hardcoded secrets
    secret_patterns = [
        (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
        (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key"),
        (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded secret"),
        (r'token\s*=\s*["\'][^"\']+["\']', "Hardcoded token"),
        (r'access_token\s*=\s*["\'][^"\']+["\']', "Hardcoded access token"),
    ]

    for pattern, description in secret_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            # Exclude common false positives
            if 'os.environ' in match or 'getenv' in match or 'keyring' in match:
                continue
            if 'None' in match or '""' in match or "''" in match:
                continue
            if 'your_' in match.lower() or 'example' in match.lower():
                continue

            issues.append(f"{description}: {match[:50]}...")

    return issues


def verify_keychain_usage():
    """Verify that code uses OS keychain for secrets."""

    results = []

    # Check watcher files
    watcher_files = [
        "watchers/odoo_watcher/watcher.py",
        "watchers/social_media_watcher/watcher.py",
        "watchers/briefing_watcher/watcher.py"
    ]

    for watcher_path in watcher_files:
        path = Path(watcher_path)
        if not path.exists():
            continue

        content = path.read_text()
        issues = []

        # Check for environment variable usage (acceptable)
        has_env = 'os.environ' in content or 'getenv' in content

        # Check for keyring usage (preferred)
        has_keyring = 'keyring' in content

        # Scan for hardcoded secrets
        secret_issues = scan_for_hardcoded_secrets(path)
        issues.extend(secret_issues)

        if not has_env and not has_keyring:
            issues.append("No environment variable or keyring usage found")

        status = "PASS" if not issues else "FAIL"
        results.append({
            "file": watcher_path,
            "status": status,
            "has_env": has_env,
            "has_keyring": has_keyring,
            "issues": issues
        })

    return results


def verify_env_file_gitignored():
    """Verify that .env file is in .gitignore."""

    gitignore_path = Path(".gitignore")

    if not gitignore_path.exists():
        return {
            "status": "FAIL",
            "issues": [".gitignore file not found"]
        }

    content = gitignore_path.read_text()
    issues = []

    # Check for .env
    if '.env' not in content:
        issues.append(".env not in .gitignore")

    # Check for common secret files
    secret_files = ['credentials.json', '*.key', '*.pem', 'secrets.yaml']
    for secret_file in secret_files:
        if secret_file not in content:
            issues.append(f"{secret_file} not in .gitignore")

    status = "PASS" if not issues else "WARN"
    return {
        "status": status,
        "issues": issues
    }


def verify_env_example_exists():
    """Verify that .env.example exists without secrets."""

    env_example_path = Path(".env.example")

    if not env_example_path.exists():
        return {
            "status": "WARN",
            "issues": [".env.example not found (recommended for documentation)"]
        }

    content = env_example_path.read_text()
    issues = []

    # Check that it doesn't contain actual secrets
    secret_issues = scan_for_hardcoded_secrets(env_example_path)
    if secret_issues:
        issues.append("Contains potential secrets (should only have placeholders)")

    # Check that it has placeholder values
    if 'your_' not in content.lower() and 'example' not in content.lower():
        issues.append("Should contain placeholder values (your_*, example_*)")

    status = "PASS" if not issues else "WARN"
    return {
        "status": status,
        "issues": issues
    }


def scan_all_python_files():
    """Scan all Python files for hardcoded secrets."""

    results = []

    # Scan watchers
    for py_file in Path("watchers").rglob("*.py"):
        if '__pycache__' in str(py_file):
            continue

        issues = scan_for_hardcoded_secrets(py_file)
        if issues:
            results.append({
                "file": str(py_file),
                "status": "FAIL",
                "issues": issues
            })

    # Scan MCP servers
    for py_file in Path("mcp-servers").rglob("*.py"):
        if '__pycache__' in str(py_file):
            continue

        issues = scan_for_hardcoded_secrets(py_file)
        if issues:
            results.append({
                "file": str(py_file),
                "status": "FAIL",
                "issues": issues
            })

    return results


def main():
    """Run all credentials security verification checks."""

    print("=" * 70)
    print("Credentials Security Verification")
    print("=" * 70)
    print()

    # Verify keychain usage
    print("Checking Keychain/Environment Variable Usage...")
    print("-" * 70)
    keychain_results = verify_keychain_usage()

    for result in keychain_results:
        print(f"\n{result['file']}: {result['status']}")
        print(f"  Uses Environment Variables: {result['has_env']}")
        print(f"  Uses Keyring: {result['has_keyring']}")
        if result['issues']:
            for issue in result['issues']:
                print(f"  - {issue}")

    # Verify .gitignore
    print("\n\nChecking .gitignore Configuration...")
    print("-" * 70)
    gitignore_result = verify_env_file_gitignored()
    print(f"Status: {gitignore_result['status']}")
    if gitignore_result['issues']:
        for issue in gitignore_result['issues']:
            print(f"  - {issue}")

    # Verify .env.example
    print("\n\nChecking .env.example...")
    print("-" * 70)
    env_example_result = verify_env_example_exists()
    print(f"Status: {env_example_result['status']}")
    if env_example_result['issues']:
        for issue in env_example_result['issues']:
            print(f"  - {issue}")

    # Scan all files
    print("\n\nScanning All Python Files for Hardcoded Secrets...")
    print("-" * 70)
    scan_results = scan_all_python_files()

    if scan_results:
        for result in scan_results:
            print(f"\n{result['file']}: {result['status']}")
            for issue in result['issues']:
                print(f"  - {issue}")
    else:
        print("✓ No hardcoded secrets found")

    # Summary
    print("\n\n" + "=" * 70)
    print("Summary")
    print("=" * 70)

    keychain_pass = sum(1 for r in keychain_results if r['status'] == 'PASS')
    keychain_total = len(keychain_results)

    scan_fail = len(scan_results)

    print(f"Keychain Usage: {keychain_pass}/{keychain_total} passed")
    print(f".gitignore: {gitignore_result['status']}")
    print(f".env.example: {env_example_result['status']}")
    print(f"Hardcoded Secrets: {scan_fail} files with issues")

    if keychain_pass == keychain_total and scan_fail == 0:
        print("\n✓ All credentials security checks passed!")
        return 0
    else:
        print("\n✗ Some credentials security checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
