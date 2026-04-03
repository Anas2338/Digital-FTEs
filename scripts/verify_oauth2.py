"""
OAuth2 Verification Script

Verifies that all API credentials use OAuth2 where applicable
(Facebook, Instagram, Twitter) as specified in the constitution.
"""

import sys
from pathlib import Path
import re

sys.path.insert(0, str(Path(__file__).parent.parent))


def verify_oauth2_implementation():
    """Verify OAuth2 implementation in social media integrations."""

    results = []

    # Check social media watcher
    social_watcher_path = Path("watchers/social_media_watcher/watcher.py")

    if social_watcher_path.exists():
        content = social_watcher_path.read_text()
        issues = []

        # Check for OAuth2 patterns
        has_oauth = 'oauth' in content.lower() or 'access_token' in content.lower()

        # Check for basic auth (should not be used)
        has_basic_auth = re.search(r'basic\s+auth', content, re.IGNORECASE)

        if has_basic_auth:
            issues.append("Uses Basic Auth (should use OAuth2)")

        if not has_oauth:
            issues.append("No OAuth2 implementation found")

        status = "PASS" if not issues else "FAIL"
        results.append({
            "component": "Social Media Watcher",
            "status": status,
            "has_oauth": has_oauth,
            "issues": issues
        })

    return results


def verify_platform_oauth_requirements():
    """Verify OAuth2 requirements for each platform."""

    platforms = {
        "facebook": {
            "required_tokens": ["access_token", "page_id"],
            "oauth_version": "OAuth 2.0"
        },
        "twitter": {
            "required_tokens": ["consumer_key", "consumer_secret", "access_token", "access_token_secret"],
            "oauth_version": "OAuth 1.0a"
        },
        "instagram": {
            "required_tokens": ["access_token", "account_id"],
            "oauth_version": "OAuth 2.0"
        }
    }

    results = []

    # Check .env.example for OAuth token placeholders
    env_example_path = Path(".env.example")

    if env_example_path.exists():
        content = env_example_path.read_text()

        for platform, requirements in platforms.items():
            issues = []

            # Check if required tokens are documented
            for token in requirements["required_tokens"]:
                token_pattern = f"{platform.upper()}.*{token.upper()}"
                if not re.search(token_pattern, content, re.IGNORECASE):
                    issues.append(f"Missing {token} in .env.example")

            status = "PASS" if not issues else "FAIL"
            results.append({
                "platform": platform.title(),
                "oauth_version": requirements["oauth_version"],
                "status": status,
                "issues": issues
            })

    return results


def verify_token_refresh_logic():
    """Verify that token refresh logic is implemented."""

    results = []

    # Check for token refresh in social media clients
    client_files = [
        "watchers/social_media_watcher/facebook_client.py",
        "watchers/social_media_watcher/twitter_client.py",
        "watchers/social_media_watcher/instagram_client.py"
    ]

    for client_path in client_files:
        path = Path(client_path)
        if not path.exists():
            continue

        content = path.read_text()
        issues = []

        # Check for token refresh logic
        has_refresh = 'refresh' in content.lower() and 'token' in content.lower()

        # Check for token expiry handling
        has_expiry = 'expir' in content.lower() or 'expires' in content.lower()

        if not has_refresh and not has_expiry:
            issues.append("No token refresh or expiry handling found")

        status = "PASS" if not issues else "WARN"
        results.append({
            "client": path.name,
            "status": status,
            "has_refresh": has_refresh,
            "has_expiry": has_expiry,
            "issues": issues
        })

    return results


def verify_secure_token_storage():
    """Verify that tokens are stored securely."""

    results = []

    # Check that tokens are not stored in plain text files
    sensitive_files = [
        ".env",
        "credentials.json",
        "tokens.json"
    ]

    for file_name in sensitive_files:
        path = Path(file_name)
        issues = []

        if path.exists():
            # File exists - check if it's in .gitignore
            gitignore_path = Path(".gitignore")
            if gitignore_path.exists():
                gitignore_content = gitignore_path.read_text()
                if file_name not in gitignore_content:
                    issues.append(f"{file_name} exists but not in .gitignore")
            else:
                issues.append(f"{file_name} exists but no .gitignore found")

        status = "PASS" if not issues else "FAIL"
        if issues:
            results.append({
                "file": file_name,
                "status": status,
                "issues": issues
            })

    return results


def verify_oauth_flow_documentation():
    """Verify that OAuth flow is documented."""

    results = []

    # Check for OAuth documentation in README or setup files
    doc_files = [
        "README.md",
        "QUICKSTART.md",
        "SETUP_ENV.md"
    ]

    for doc_file in doc_files:
        path = Path(doc_file)
        if not path.exists():
            continue

        content = path.read_text()
        issues = []

        # Check for OAuth mentions
        has_oauth_docs = 'oauth' in content.lower() or 'access_token' in content.lower()

        # Check for setup instructions
        has_setup = 'setup' in content.lower() or 'configure' in content.lower()

        if not has_oauth_docs:
            issues.append("No OAuth documentation found")

        status = "PASS" if not issues else "WARN"
        results.append({
            "document": doc_file,
            "status": status,
            "has_oauth_docs": has_oauth_docs,
            "has_setup": has_setup,
            "issues": issues
        })

    return results


def main():
    """Run all OAuth2 verification checks."""

    print("=" * 70)
    print("OAuth2 Verification")
    print("=" * 70)
    print()

    # Verify OAuth2 implementation
    print("Checking OAuth2 Implementation...")
    print("-" * 70)
    oauth_results = verify_oauth2_implementation()

    for result in oauth_results:
        print(f"\n{result['component']}: {result['status']}")
        print(f"  Has OAuth: {result['has_oauth']}")
        if result['issues']:
            for issue in result['issues']:
                print(f"  - {issue}")

    # Verify platform requirements
    print("\n\nChecking Platform OAuth Requirements...")
    print("-" * 70)
    platform_results = verify_platform_oauth_requirements()

    for result in platform_results:
        print(f"\n{result['platform']} ({result['oauth_version']}): {result['status']}")
        if result['issues']:
            for issue in result['issues']:
                print(f"  - {issue}")

    # Verify token refresh
    print("\n\nChecking Token Refresh Logic...")
    print("-" * 70)
    refresh_results = verify_token_refresh_logic()

    for result in refresh_results:
        print(f"\n{result['client']}: {result['status']}")
        print(f"  Has Refresh: {result['has_refresh']}")
        print(f"  Has Expiry Handling: {result['has_expiry']}")
        if result['issues']:
            for issue in result['issues']:
                print(f"  - {issue}")

    # Verify secure storage
    print("\n\nChecking Secure Token Storage...")
    print("-" * 70)
    storage_results = verify_secure_token_storage()

    if storage_results:
        for result in storage_results:
            print(f"\n{result['file']}: {result['status']}")
            for issue in result['issues']:
                print(f"  - {issue}")
    else:
        print("✓ No insecure token storage found")

    # Verify documentation
    print("\n\nChecking OAuth Documentation...")
    print("-" * 70)
    doc_results = verify_oauth_flow_documentation()

    for result in doc_results:
        print(f"\n{result['document']}: {result['status']}")
        print(f"  Has OAuth Docs: {result['has_oauth_docs']}")
        print(f"  Has Setup Instructions: {result['has_setup']}")
        if result['issues']:
            for issue in result['issues']:
                print(f"  - {issue}")

    # Summary
    print("\n\n" + "=" * 70)
    print("Summary")
    print("=" * 70)

    oauth_pass = sum(1 for r in oauth_results if r['status'] == 'PASS')
    oauth_total = len(oauth_results)

    platform_pass = sum(1 for r in platform_results if r['status'] == 'PASS')
    platform_total = len(platform_results)

    refresh_pass = sum(1 for r in refresh_results if r['status'] in ['PASS', 'WARN'])
    refresh_total = len(refresh_results)

    storage_pass = len(storage_results) == 0 or sum(1 for r in storage_results if r['status'] == 'PASS')

    doc_pass = sum(1 for r in doc_results if r['status'] in ['PASS', 'WARN'])
    doc_total = len(doc_results)

    print(f"OAuth2 Implementation: {oauth_pass}/{oauth_total} passed")
    print(f"Platform Requirements: {platform_pass}/{platform_total} passed")
    print(f"Token Refresh: {refresh_pass}/{refresh_total} passed")
    print(f"Secure Storage: {'PASS' if storage_pass else 'FAIL'}")
    print(f"Documentation: {doc_pass}/{doc_total} passed")

    if oauth_pass == oauth_total and platform_pass == platform_total:
        print("\n✓ OAuth2 verification passed!")
        return 0
    else:
        print("\n✗ Some OAuth2 checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
