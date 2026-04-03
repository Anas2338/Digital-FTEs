"""
Cloud Agent Configuration Manager for Platinum Tier

Loads and validates agent configuration from agent-config.json.
Ensures cloud agent has read-only credential scope.

Based on contracts/agent-config.schema.json and spec.md FR-004, FR-005.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class SyncConfig:
    """Vault synchronization configuration."""
    enabled: bool
    method: str  # "git" only per research.md
    remote_url: Optional[str]
    sync_interval_seconds: int
    ssh_key_path: Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> 'SyncConfig':
        return cls(
            enabled=data["enabled"],
            method=data["method"],
            remote_url=data.get("remote_url"),
            sync_interval_seconds=data["sync_interval_seconds"],
            ssh_key_path=data.get("ssh_key_path")
        )


@dataclass
class HealthConfig:
    """Health monitoring configuration."""
    check_interval_seconds: int
    alert_channels: List[str]
    alert_threshold_failures: int

    @classmethod
    def from_dict(cls, data: dict) -> 'HealthConfig':
        return cls(
            check_interval_seconds=data["check_interval_seconds"],
            alert_channels=data["alert_channels"],
            alert_threshold_failures=data["alert_threshold_failures"]
        )


@dataclass
class WorkZones:
    """Work-zone specialization configuration."""
    can_draft: bool
    can_approve: bool
    can_execute: bool
    domains: List[str]

    @classmethod
    def from_dict(cls, data: dict) -> 'WorkZones':
        return cls(
            can_draft=data["can_draft"],
            can_approve=data["can_approve"],
            can_execute=data["can_execute"],
            domains=data["domains"]
        )


class CloudAgentConfig:
    """
    Cloud agent configuration.

    Validates that cloud agent has correct permissions:
    - credential_scope MUST be "read_only" (FR-005)
    - can_draft MUST be True (cloud generates drafts)
    - can_approve MUST be False (only local approves)
    - can_execute MUST be False (only local executes)
    """

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        llm_provider: str,
        credential_scope: str,
        vault_path: Path,
        sync_config: SyncConfig,
        health_config: HealthConfig,
        work_zones: WorkZones
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.llm_provider = llm_provider
        self.credential_scope = credential_scope
        self.vault_path = Path(vault_path)
        self.sync_config = sync_config
        self.health_config = health_config
        self.work_zones = work_zones

        self._validate()

    def _validate(self) -> None:
        """
        Validate cloud agent configuration.

        Raises:
            ValueError: If configuration violates cloud agent constraints
        """
        if self.agent_id != "cloud":
            raise ValueError(f"Cloud agent must have agent_id='cloud', got '{self.agent_id}'")

        if self.agent_type != "cloud":
            raise ValueError(f"Cloud agent must have agent_type='cloud', got '{self.agent_type}'")

        # FR-005: Cloud agent MUST NOT have write credentials
        if self.credential_scope != "read_only":
            raise ValueError(
                f"Cloud agent MUST have credential_scope='read_only', got '{self.credential_scope}'"
            )

        # Work-zone validation (FR-007, FR-008)
        if not self.work_zones.can_draft:
            raise ValueError("Cloud agent MUST have can_draft=True")

        if self.work_zones.can_approve:
            raise ValueError("Cloud agent MUST have can_approve=False")

        if self.work_zones.can_execute:
            raise ValueError("Cloud agent MUST have can_execute=False")

        # Sync validation
        if self.sync_config.method != "git":
            raise ValueError(f"Only 'git' sync method supported, got '{self.sync_config.method}'")

    @classmethod
    def load(cls, config_path: Path) -> 'CloudAgentConfig':
        """
        Load configuration from JSON file.

        Args:
            config_path: Path to agent-config.json

        Returns:
            CloudAgentConfig instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If configuration is invalid
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, 'r') as f:
            data = json.load(f)

        return cls(
            agent_id=data["agent_id"],
            agent_type=data["agent_type"],
            llm_provider=data["llm_provider"],
            credential_scope=data["credential_scope"],
            vault_path=Path(data["vault_path"]),
            sync_config=SyncConfig.from_dict(data["sync_config"]),
            health_config=HealthConfig.from_dict(data["health_config"]),
            work_zones=WorkZones.from_dict(data["work_zones"])
        )
