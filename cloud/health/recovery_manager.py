"""
Automatic Recovery Manager for Platinum Tier

Implements automatic recovery actions when health checks fail.
Restarts services, triggers vault sync, and escalates to manual intervention.

Based on spec.md FR-033 and User Story 5.
"""

import asyncio
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

from cloud.health.health_status import ServiceType, HealthCheck
from cloud.health.health_monitor import HealthMonitor
from cloud.health.health_check_db import HealthCheckDatabase


class RecoveryAction:
    """Types of recovery actions."""
    RESTART_SERVICE = "restart_service"
    TRIGGER_SYNC = "trigger_sync"
    RESTART_WATCHER = "restart_watcher"
    CLEAR_CACHE = "clear_cache"
    MANUAL_INTERVENTION = "manual_intervention"


class AutomaticRecoveryManager:
    """
    Manages automatic recovery actions for failed services.

    Responsibilities:
    - Restart cloud-agent.service after failures (FR-033)
    - Restart odoo.service after failures (FR-033)
    - Trigger vault sync after sync failures
    - Track recovery attempts and escalate to manual intervention
    - Log all recovery actions to database
    """

    def __init__(
        self,
        health_monitor: HealthMonitor,
        health_db: HealthCheckDatabase,
        vault_path: Path
    ):
        """
        Initialize recovery manager.

        Args:
            health_monitor: Health monitor instance
            health_db: Health check database
            vault_path: Path to Obsidian vault
        """
        self.health_monitor = health_monitor
        self.health_db = health_db
        self.vault_path = Path(vault_path)
        self.logger = logging.getLogger("recovery_manager")

    async def handle_failed_check(
        self,
        service_type: ServiceType,
        health_check: HealthCheck
    ) -> bool:
        """
        Handle a failed health check with automatic recovery.

        Args:
            service_type: Service that failed
            health_check: Failed health check result

        Returns:
            True if recovery attempted, False if manual intervention required
        """
        self.logger.warning(
            f"Handling failed check for {service_type.value}: "
            f"{health_check.error_message}"
        )

        # Check if manual intervention required (FR-033: after 3 restart attempts)
        if self.health_monitor.requires_manual_intervention(service_type):
            self.logger.error(
                f"{service_type.value} requires manual intervention "
                f"(restart limit exceeded)"
            )
            await self._escalate_to_manual_intervention(service_type, health_check)
            return False

        # Check if restart threshold reached
        if self.health_monitor.should_restart(service_type):
            success = await self._attempt_recovery(service_type, health_check)
            return success

        return False

    async def _attempt_recovery(
        self,
        service_type: ServiceType,
        health_check: HealthCheck
    ) -> bool:
        """
        Attempt automatic recovery for a service.

        Args:
            service_type: Service to recover
            health_check: Failed health check

        Returns:
            True if recovery succeeded
        """
        recovery_action = self._determine_recovery_action(service_type)

        self.logger.info(
            f"Attempting recovery for {service_type.value}: {recovery_action}"
        )

        success = False
        error_message = None

        try:
            if recovery_action == RecoveryAction.RESTART_SERVICE:
                success = await self._restart_systemd_service(service_type)
            elif recovery_action == RecoveryAction.TRIGGER_SYNC:
                success = await self._trigger_vault_sync()
            elif recovery_action == RecoveryAction.RESTART_WATCHER:
                success = await self._restart_watcher(service_type)
            else:
                self.logger.warning(f"Unknown recovery action: {recovery_action}")

            if success:
                self.health_monitor.record_restart(service_type)
                self.logger.info(f"Recovery succeeded for {service_type.value}")
            else:
                error_message = "Recovery action failed"
                self.logger.error(f"Recovery failed for {service_type.value}")

        except Exception as e:
            success = False
            error_message = str(e)
            self.logger.error(
                f"Recovery exception for {service_type.value}: {e}",
                exc_info=True
            )

        # Log recovery action to database
        self.health_db.record_recovery_action(
            service_type=service_type,
            action_type=recovery_action,
            success=success,
            triggered_by="automatic_recovery",
            error_message=error_message
        )

        return success

    def _determine_recovery_action(self, service_type: ServiceType) -> str:
        """
        Determine appropriate recovery action for a service.

        Args:
            service_type: Service that failed

        Returns:
            Recovery action type
        """
        if service_type == ServiceType.CLOUD_AGENT:
            return RecoveryAction.RESTART_SERVICE
        elif service_type == ServiceType.ODOO:
            return RecoveryAction.RESTART_SERVICE
        elif service_type == ServiceType.VAULT_SYNC:
            return RecoveryAction.TRIGGER_SYNC
        elif service_type in [
            ServiceType.EMAIL_WATCHER,
            ServiceType.SOCIAL_WATCHER,
            ServiceType.ODOO_WATCHER
        ]:
            return RecoveryAction.RESTART_WATCHER
        else:
            return RecoveryAction.MANUAL_INTERVENTION

    async def _restart_systemd_service(self, service_type: ServiceType) -> bool:
        """
        Restart a systemd service.

        Args:
            service_type: Service to restart

        Returns:
            True if restart succeeded
        """
        # Map service type to systemd service name
        service_map = {
            ServiceType.CLOUD_AGENT: "cloud-agent.service",
            ServiceType.ODOO: "odoo.service",
            ServiceType.VAULT_SYNC: "vault-sync.timer"
        }

        service_name = service_map.get(service_type)
        if not service_name:
            self.logger.error(f"No systemd service mapped for {service_type.value}")
            return False

        try:
            self.logger.info(f"Restarting systemd service: {service_name}")

            # Restart service using systemctl
            result = subprocess.run(
                ["systemctl", "restart", service_name],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                self.logger.info(f"Successfully restarted {service_name}")
                return True
            else:
                self.logger.error(
                    f"Failed to restart {service_name}: {result.stderr}"
                )
                return False

        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout restarting {service_name}")
            return False
        except Exception as e:
            self.logger.error(f"Error restarting {service_name}: {e}")
            return False

    async def _trigger_vault_sync(self) -> bool:
        """
        Trigger vault synchronization.

        Returns:
            True if sync triggered successfully
        """
        try:
            self.logger.info("Triggering vault sync")

            # Run sync script
            sync_script = Path("/opt/digital-fte/sync-vault.sh")
            if not sync_script.exists():
                self.logger.error(f"Sync script not found: {sync_script}")
                return False

            result = subprocess.run(
                [str(sync_script)],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                self.logger.info("Vault sync triggered successfully")
                return True
            else:
                self.logger.error(f"Vault sync failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error("Vault sync timeout")
            return False
        except Exception as e:
            self.logger.error(f"Error triggering vault sync: {e}")
            return False

    async def _restart_watcher(self, service_type: ServiceType) -> bool:
        """
        Restart a watcher component.

        Args:
            service_type: Watcher to restart

        Returns:
            True if restart succeeded

        Note: Watchers run as part of cloud agent, so we restart the agent
        """
        self.logger.info(f"Restarting watcher: {service_type.value}")
        return await self._restart_systemd_service(ServiceType.CLOUD_AGENT)

    async def _escalate_to_manual_intervention(
        self,
        service_type: ServiceType,
        health_check: HealthCheck
    ) -> None:
        """
        Escalate to manual intervention after automatic recovery fails.

        Args:
            service_type: Service requiring intervention
            health_check: Failed health check
        """
        self.logger.critical(
            f"MANUAL INTERVENTION REQUIRED for {service_type.value}"
        )

        # Create intervention file in vault for visibility
        intervention_file = (
            self.vault_path / "Manual_Interventions" /
            f"{service_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )
        intervention_file.parent.mkdir(parents=True, exist_ok=True)

        intervention_content = f"""---
service: {service_type.value}
status: requires_manual_intervention
created_at: {datetime.now().isoformat()}
---

# Manual Intervention Required: {service_type.value}

## Issue
Service has failed health checks and automatic recovery has been exhausted.

**Error**: {health_check.error_message}

**Status**: {health_check.status.value}

**Time**: {health_check.checked_at.isoformat()}

## Recovery Attempts
Automatic recovery has been attempted {self.health_monitor.restart_counts.get(service_type, 0)} times.

Maximum restart attempts (3) exceeded per FR-033.

## Required Actions
1. Investigate root cause of failure
2. Review service logs: `journalctl -u {service_type.value} -n 100`
3. Check system resources: `top`, `df -h`
4. Manually restart service if appropriate
5. Document resolution in this file
6. Reset restart counter after resolution

## Metadata
{health_check.metadata}

## Resolution Notes
[Add resolution notes here after fixing the issue]
"""

        try:
            with open(intervention_file, 'w') as f:
                f.write(intervention_content)

            self.logger.info(
                f"Created manual intervention file: {intervention_file}"
            )

        except Exception as e:
            self.logger.error(f"Failed to create intervention file: {e}")

    def reset_service_after_manual_intervention(
        self,
        service_type: ServiceType,
        performed_by: str,
        resolution_notes: str
    ) -> None:
        """
        Reset service state after manual intervention.

        Args:
            service_type: Service that was fixed
            performed_by: Who performed the intervention
            resolution_notes: Notes about the resolution
        """
        # Reset restart counter
        self.health_monitor.reset_restart_count(service_type)

        # Record manual intervention in database
        self.health_db.record_manual_intervention(
            service_type=service_type,
            intervention_type="manual_restart",
            reason="Automatic recovery exhausted",
            performed_by=performed_by,
            resolution_notes=resolution_notes
        )

        self.logger.info(
            f"Reset {service_type.value} after manual intervention by {performed_by}"
        )
