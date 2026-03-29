"""
Obsidian Vault Initialization Script

Creates the foundational structure for the Digital FTE Obsidian vault including:
- Root vault directory
- Folder structure (/Inbox, /Needs_Action, /Done)
- .obsidian configuration
- Dashboard.md template
- Company_Handbook.md template
"""

import os
import sys
import argparse
import json
from pathlib import Path


def create_vault_directory(vault_path: Path, force: bool = False) -> bool:
    """
    Create the root vault directory.

    Args:
        vault_path: Path to the vault root
        force: If True, reinitialize even if vault exists

    Returns:
        True if directory was created or already exists
    """
    if vault_path.exists():
        if not force:
            print(f"[OK] Vault directory already exists: {vault_path}")
            return True
        else:
            print(f"[WARN] Reinitializing existing vault: {vault_path}")
    else:
        vault_path.mkdir(parents=True, exist_ok=True)
        print(f"[OK] Created vault directory: {vault_path}")

    return True


def create_folder_structure(vault_path: Path) -> bool:
    """
    Create the standard folder structure within the vault.

    Args:
        vault_path: Path to the vault root

    Returns:
        True if all folders were created successfully
    """
    folders = ['Inbox', 'Needs_Action', 'Done']

    for folder in folders:
        folder_path = vault_path / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        print(f"[OK] Created folder: {folder_path}")

    return True


def create_obsidian_config(vault_path: Path) -> bool:
    """
    Create .obsidian configuration directory and workspace.json.

    Args:
        vault_path: Path to the vault root

    Returns:
        True if configuration was created successfully
    """
    config_dir = vault_path / '.obsidian'
    config_dir.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Created .obsidian configuration directory: {config_dir}")

    # Create minimal workspace.json that opens Dashboard.md by default
    workspace_config = {
        "main": {
            "id": "main-workspace",
            "type": "split",
            "children": [
                {
                    "id": "dashboard-leaf",
                    "type": "leaf",
                    "state": {
                        "type": "markdown",
                        "state": {
                            "file": "Dashboard.md",
                            "mode": "source"
                        }
                    }
                }
            ]
        },
        "active": "dashboard-leaf",
        "lastOpenFiles": [
            "Dashboard.md",
            "Company_Handbook.md"
        ]
    }

    workspace_path = config_dir / 'workspace.json'
    with open(workspace_path, 'w', encoding='utf-8') as f:
        json.dump(workspace_config, f, indent=2)

    print(f"[OK] Created workspace configuration: {workspace_path}")
    return True


def create_dashboard_template(vault_path: Path) -> bool:
    """
    Create Dashboard.md template with dynamic sections.

    Args:
        vault_path: Path to the vault root

    Returns:
        True if dashboard was created successfully
    """
    dashboard_content = """# Dashboard

## Last Updated
*This dashboard will be automatically updated by the system*

---

## Folder Status

| Folder | Count | Link |
|--------|-------|------|
| Inbox | 0 | [[Inbox/]] |
| Needs Action | 0 | [[Needs_Action/]] |
| Done | 0 | [[Done/]] |

---

## Recent Activity

*No recent notes yet. The 10 most recent notes will appear here automatically.*

---

## Quick Links

- [[Company_Handbook]] - Business processes and guidelines
- [[Inbox/]] - New items requiring processing
- [[Needs_Action/]] - Tasks requiring attention
- [[Done/]] - Completed items archive

---

*Dashboard automatically updated by Digital FTE system*
"""

    dashboard_path = vault_path / 'Dashboard.md'
    with open(dashboard_path, 'w', encoding='utf-8') as f:
        f.write(dashboard_content)

    print(f"[OK] Created Dashboard template: {dashboard_path}")
    return True


def create_company_handbook_template(vault_path: Path) -> bool:
    """
    Create Company_Handbook.md template.

    Args:
        vault_path: Path to the vault root

    Returns:
        True if handbook was created successfully
    """
    handbook_content = """# Company Handbook

## Business Information

**Company Name:** [Your Company Name]
**Industry:** [Your Industry]
**Founded:** [Year]
**Mission:** [Your Mission Statement]

---

## Key Contacts

| Role | Name | Email | Phone |
|------|------|-------|-------|
| CEO | [Name] | [email] | [phone] |
| Operations Manager | [Name] | [email] | [phone] |
| Technical Lead | [Name] | [email] | [phone] |
| Customer Support | [Name] | [email] | [phone] |

---

## Business Processes

### Email Management
- All emails labeled "ToVault" are automatically captured
- New items appear in [[Inbox/]]
- Review inbox daily and move items to [[Needs_Action/]] or [[Done/]]

### Task Workflow
1. **Inbox** - New items requiring initial review
2. **Needs Action** - Tasks requiring attention or follow-up
3. **Done** - Completed items for reference

### Communication Guidelines
- Response time expectations: [Define SLAs]
- Escalation procedures: [Define process]
- After-hours protocol: [Define policy]

---

## Guidelines

### Decision Making
- [Your decision-making framework]
- [Approval authorities]
- [Budget thresholds]

### Quality Standards
- [Your quality criteria]
- [Review processes]
- [Compliance requirements]

---

## Resources

### Internal Systems
- [System 1]: [URL/Access info]
- [System 2]: [URL/Access info]

### External Tools
- [Tool 1]: [URL/Purpose]
- [Tool 2]: [URL/Purpose]

### Documentation
- [Doc 1]: [Link]
- [Doc 2]: [Link]

---

*Last Updated: [Date]*
*Maintained by: [Owner]*
"""

    handbook_path = vault_path / 'Company_Handbook.md'
    with open(handbook_path, 'w', encoding='utf-8') as f:
        f.write(handbook_content)

    print(f"[OK] Created Company Handbook template: {handbook_path}")
    return True


def verify_vault_structure(vault_path: Path) -> bool:
    """
    Verify that all required vault components exist.

    Args:
        vault_path: Path to the vault root

    Returns:
        True if all components exist, False otherwise
    """
    print("\n" + "="*60)
    print("VAULT STRUCTURE VERIFICATION")
    print("="*60)

    required_items = [
        ('Root directory', vault_path),
        ('Inbox folder', vault_path / 'Inbox'),
        ('Needs_Action folder', vault_path / 'Needs_Action'),
        ('Done folder', vault_path / 'Done'),
        ('.obsidian config', vault_path / '.obsidian'),
        ('workspace.json', vault_path / '.obsidian' / 'workspace.json'),
        ('Dashboard.md', vault_path / 'Dashboard.md'),
        ('Company_Handbook.md', vault_path / 'Company_Handbook.md'),
    ]

    all_exist = True
    for name, path in required_items:
        exists = path.exists()
        status = "[OK]" if exists else "[FAIL]"
        print(f"{status} {name}: {path}")
        if not exists:
            all_exist = False

    print("="*60)

    if all_exist:
        print("\n[SUCCESS] Vault initialization complete! All components verified.")
        print(f"\nVault location: {vault_path.absolute()}")
        print("\nNext steps:")
        print("   1. Open the vault in Obsidian")
        print("   2. Customize Company_Handbook.md with your business information")
        print("   3. Configure Gmail watcher to start capturing emails")
    else:
        print("\n[ERROR] Vault initialization incomplete. Some components are missing.")
        return False

    return True


def main():
    """Main entry point for vault initialization."""
    parser = argparse.ArgumentParser(
        description='Initialize Obsidian vault structure for Digital FTE system'
    )
    parser.add_argument(
        '--vault-path',
        type=str,
        default='obsidian-vault',
        help='Path to vault directory (default: obsidian-vault)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Reinitialize existing vault (overwrites templates)'
    )

    args = parser.parse_args()

    # Convert to absolute path
    vault_path = Path(args.vault_path).resolve()

    print("="*60)
    print("OBSIDIAN VAULT INITIALIZATION")
    print("="*60)
    print(f"Vault path: {vault_path}")
    print(f"Force mode: {args.force}")
    print("="*60 + "\n")

    try:
        # Create vault structure
        if not create_vault_directory(vault_path, args.force):
            sys.exit(1)

        if not create_folder_structure(vault_path):
            sys.exit(1)

        if not create_obsidian_config(vault_path):
            sys.exit(1)

        if not create_dashboard_template(vault_path):
            sys.exit(1)

        if not create_company_handbook_template(vault_path):
            sys.exit(1)

        # Verify everything was created
        if not verify_vault_structure(vault_path):
            sys.exit(1)

    except Exception as e:
        print(f"\n[ERROR] Error during vault initialization: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
