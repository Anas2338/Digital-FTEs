"""
Credential Rotation Scheduler for Platinum Tier

Monitors credential expiration and schedules automatic rotation.
Alerts 7 days before expiry per FR-042.

Based on spec.md FR-042 and User Story 5.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from sync.atomic_writer import AtomicWriter


class CredentialType(Enum):
    """Types of credentials that require rotation."""
    GMAIL_OAUTH = "gmail_oauth"
    SOCIAL_OAUTH = "social_oauth"
    ODOO_PASSWORD = "odoo_password"
    API_KEY = "api_key"
    SSL_CERTIFICATE = "ssl_certificate"


class CredentialScope(Enum):
    """Credential access scope."""
    READ_ONLY = "read_only"
    FULL = "full"


@dataclass
class Credential:
    """
    Credential entity with expiration tracking.

    Attributes:
        credential_id: Unique identifier
        credential_type: Type of credential
        scope: Access scope (read_only or full)
        service_name: Service this credential is for (e.g., "Gmail", "Odoo")
        agent_id: Which agent uses this credential (cloud or local)
        issued_at: When credential was issued
        expires_at: When credential expires
        rotation_period_days: How often to rotate (default 90 per FR-042)
        last_rotated_at: When credential was last rotated
        rotation_count: Number of times rotated
    """
    credential_id: str
    credential_type: CredentialType
    scope: CredentialScope
    service_name: str
    agent_id: str
    issued_at: datetime
    expires_at: datetime
    rotation_period_days: int = 90
    last_rotated_at: Optional[datetime] = None
    rotation_count: int = 0

    def days_until_expiry(self) -> int:
        """Calculate days until credential expires."""
        delta = self.expires_at - datetime.now()
        return max(0, delta.days)

    def is_expired(self) -> bool:
        """Check if credential has expired."""
        return datetime.now() >= self.expires_at

    def needs_rotation_alert(self, alert_days_before: int = 7) -> bool:
        """
        Check if rotation alert should be sent.

        Args:
            alert_days_before: Days before expiry to alert (default 7 per FR-042)

        Returns:
            True if alert should be sent
        """
        return self.days_until_expiry() <= alert_days_before and not self.is_expired()

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "credential_id": self.credential_id,
            "credential_type": self.credential_type.value,
            "scope": self.scope.value,
            "service_name": self.service_name,
            "agent_id": self.agent_id,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "rotation_period_days": self.rotation_period_days,
            "last_rotated_at": self.last_rotated_at.isoformat() if self.last_rotated_at else None,
            "rotation_count": self.rotation_count
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Credential":
        """Deserialize from dictionary."""
        return cls(
            credential_id=data["credential_id"],
            credential_type=CredentialType(data["credential_type"]),
            scope=CredentialScope(data["scope"]),
            service_name=data["service_name"],
            agent_id=data["agent_id"],
            issued_at=datetime.fromisoformat(data["issued_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            rotation_period_days=data.get("rotation_period_days", 90),
            last_rotated_at=datetime.fromisoformat(data["last_rotated_at"]) if data.get("last_rotated_at") else None,
            rotation_count=data.get("rotation_count", 0)
        )


class CredentialRotationScheduler:
    """
    Manages credential rotation scheduling and alerts.

    Responsibilities:
    - Track credential expiration dates
    - Alert 7 days before expiry (FR-042)
    - Generate rotation reminders
    - Log rotation history
    """

    def __init__(self, vault_path: Path):
        """
        Initialize credential rotation scheduler.

        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_path = Path(vault_path)
        self.logger = logging.getLogger("credential_rotator")
        self.credentials_file = vault_path / "config" / "credentials.json"
        self.credentials_file.parent.mkdir(parents=True, exist_ok=True)

        self.credentials: Dict[str, Credential] = {}
        self._load_credentials()

    def _load_credentials(self) -> None:
        """Load credentials from file."""
        if not self.credentials_file.exists():
            self.logger.info("No credentials file found, starting fresh")
            return

        try:
            import json
            with open(self.credentials_file, 'r') as f:
                data = json.load(f)

            for cred_data in data.get("credentials", []):
                cred = Credential.from_dict(cred_data)
                self.credentials[cred.credential_id] = cred

            self.logger.info(f"Loaded {len(self.credentials)} credentials")

        except Exception as e:
            self.logger.error(f"Error loading credentials: {e}", exc_info=True)

    def _save_credentials(self) -> None:
        """Save credentials to file."""
        try:
            import json
            data = {
                "credentials": [cred.to_dict() for cred in self.credentials.values()],
                "last_updated": datetime.now().isoformat()
            }

            AtomicWriter.write(
                self.credentials_file,
                json.dumps(data, indent=2)
            )

        except Exception as e:
            self.logger.error(f"Error saving credentials: {e}", exc_info=True)

    def register_credential(
        self,
        credential_id: str,
        credential_type: CredentialType,
        scope: CredentialScope,
        service_name: str,
        agent_id: str,
        expires_at: datetime,
        rotation_period_days: int = 90
    ) -> None:
        """
        Register a credential for rotation tracking.

        Args:
            credential_id: Unique identifier
            credential_type: Type of credential
            scope: Access scope
            service_name: Service name
            agent_id: Agent using this credential
            expires_at: Expiration date
            rotation_period_days: Rotation period (default 90 per FR-042)
        """
        credential = Credential(
            credential_id=credential_id,
            credential_type=credential_type,
            scope=scope,
            service_name=service_name,
            agent_id=agent_id,
            issued_at=datetime.now(),
            expires_at=expires_at,
            rotation_period_days=rotation_period_days
        )

        self.credentials[credential_id] = credential
        self._save_credentials()

        self.logger.info(
            f"Registered credential {credential_id} for {service_name} "
            f"(expires {expires_at.date()})"
        )

    def check_expiring_credentials(self, alert_days_before: int = 7) -> List[Credential]:
        """
        Check for credentials expiring soon.

        Args:
            alert_days_before: Days before expiry to alert (default 7 per FR-042)

        Returns:
            List of credentials needing rotation alerts
        """
        expiring = []

        for credential in self.credentials.values():
            if credential.needs_rotation_alert(alert_days_before):
                expiring.append(credential)
                self.logger.warning(
                    f"Credential {credential.credential_id} expires in "
                    f"{credential.days_until_expiry()} days"
                )

        return expiring

    def check_expired_credentials(self) -> List[Credential]:
        """
        Check for expired credentials.

        Returns:
            List of expired credentials
        """
        expired = []

        for credential in self.credentials.values():
            if credential.is_expired():
                expired.append(credential)
                self.logger.error(
                    f"Credential {credential.credential_id} has EXPIRED"
                )

        return expired

    def create_rotation_reminder(self, credential: Credential) -> None:
        """
        Create rotation reminder file in vault.

        Args:
            credential: Credential needing rotation
        """
        reminder_file = (
            self.vault_path / "Credential_Rotations" /
            f"{credential.credential_id}_{datetime.now().strftime('%Y%m%d')}.md"
        )
        reminder_file.parent.mkdir(parents=True, exist_ok=True)

        days_left = credential.days_until_expiry()
        urgency = "🔴 URGENT" if days_left <= 3 else "🟡 ATTENTION REQUIRED"

        content = f"""---
credential_id: {credential.credential_id}
service: {credential.service_name}
agent: {credential.agent_id}
expires_at: {credential.expires_at.isoformat()}
days_until_expiry: {days_left}
urgency: {urgency}
---

# {urgency}: Credential Rotation Required

## Credential Details

- **Service**: {credential.service_name}
- **Type**: {credential.credential_type.value}
- **Scope**: {credential.scope.value}
- **Agent**: {credential.agent_id}
- **Expires**: {credential.expires_at.strftime('%Y-%m-%d %H:%M:%S')}
- **Days Left**: {days_left}

## Rotation Instructions

### For {credential.credential_type.value}

"""

        # Add type-specific instructions
        if credential.credential_type == CredentialType.GMAIL_OAUTH:
            content += """
1. Go to Google Cloud Console: https://console.cloud.google.com/
2. Navigate to APIs & Services > Credentials
3. Find the OAuth 2.0 Client ID for Digital FTE
4. Click "Reset Secret" or create new credentials
5. Update `.env.{agent}` with new credentials:
   - GMAIL_CLIENT_ID
   - GMAIL_CLIENT_SECRET
   - GMAIL_REFRESH_TOKEN (re-authorize)
6. Test: `python -c "from cloud.watchers.gmail_watcher_cloud import GmailWatcherCloud; ..."`
7. Restart agent: `sudo systemctl restart {agent}-agent.service`
"""
        elif credential.credential_type == CredentialType.ODOO_PASSWORD:
            content += """
1. Log into Odoo: https://your-domain.com
2. Go to Settings > Users & Companies > Users
3. Find the agent user account
4. Click "Change Password"
5. Generate strong password (use password manager)
6. Update `.env.{agent}` with new password:
   - ODOO_PASSWORD=new-password
7. Test: `curl -u agent:new-password https://your-domain.com/web/health`
8. Restart agent: `sudo systemctl restart {agent}-agent.service`
"""
        elif credential.credential_type == CredentialType.SSL_CERTIFICATE:
            content += """
1. SSH into cloud VM
2. Run: `sudo certbot renew --force-renewal`
3. Verify: `sudo certbot certificates`
4. Test: `curl https://your-domain.com/web/health`
5. Certificate should auto-renew, but manual renewal may be needed if auto-renewal failed
"""

        content += f"""

## After Rotation

1. Mark this credential as rotated:
   ```python
   from cloud.agent.credential_rotator import CredentialRotationScheduler
   scheduler = CredentialRotationScheduler(vault_path)
   scheduler.mark_rotated("{credential.credential_id}")
   ```

2. Verify service is working:
   - Check agent logs: `sudo journalctl -u {credential.agent_id}-agent.service -n 50`
   - Check health status: `sudo monit status`

3. Delete this reminder file after rotation is complete

## History

- **Issued**: {credential.issued_at.strftime('%Y-%m-%d')}
- **Last Rotated**: {credential.last_rotated_at.strftime('%Y-%m-%d') if credential.last_rotated_at else 'Never'}
- **Rotation Count**: {credential.rotation_count}
- **Rotation Period**: {credential.rotation_period_days} days

---

**Next Rotation Due**: {(credential.expires_at + timedelta(days=credential.rotation_period_days)).strftime('%Y-%m-%d')}
"""

        try:
            with open(reminder_file, 'w') as f:
                f.write(content)

            self.logger.info(f"Created rotation reminder: {reminder_file}")

        except Exception as e:
            self.logger.error(f"Failed to create rotation reminder: {e}")

    def mark_rotated(self, credential_id: str) -> bool:
        """
        Mark a credential as rotated.

        Args:
            credential_id: Credential that was rotated

        Returns:
            True if successful
        """
        if credential_id not in self.credentials:
            self.logger.error(f"Credential {credential_id} not found")
            return False

        credential = self.credentials[credential_id]
        credential.last_rotated_at = datetime.now()
        credential.rotation_count += 1

        # Update expiry date (add rotation period)
        credential.expires_at = datetime.now() + timedelta(days=credential.rotation_period_days)

        self._save_credentials()

        self.logger.info(
            f"Marked credential {credential_id} as rotated "
            f"(next rotation: {credential.expires_at.date()})"
        )

        return True

    def run_rotation_check(self) -> Dict[str, List[Credential]]:
        """
        Run rotation check and create reminders.

        Returns:
            Dict with 'expiring' and 'expired' credential lists
        """
        self.logger.info("Running credential rotation check")

        expiring = self.check_expiring_credentials()
        expired = self.check_expired_credentials()

        # Create reminders for expiring credentials
        for credential in expiring:
            self.create_rotation_reminder(credential)

        # Create urgent reminders for expired credentials
        for credential in expired:
            self.create_rotation_reminder(credential)

        return {
            "expiring": expiring,
            "expired": expired
        }

    def get_rotation_summary(self) -> Dict:
        """
        Get summary of credential rotation status.

        Returns:
            Summary dict with counts and next rotation date
        """
        total = len(self.credentials)
        expiring_7d = len(self.check_expiring_credentials(7))
        expiring_30d = len(self.check_expiring_credentials(30))
        expired = len(self.check_expired_credentials())

        next_rotation = None
        if self.credentials:
            next_rotation = min(
                cred.expires_at for cred in self.credentials.values()
            )

        return {
            "total_credentials": total,
            "expiring_7_days": expiring_7d,
            "expiring_30_days": expiring_30d,
            "expired": expired,
            "next_rotation_date": next_rotation.isoformat() if next_rotation else None
        }
