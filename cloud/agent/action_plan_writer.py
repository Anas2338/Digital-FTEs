"""
Action Plan Writer for Cloud Agent

Creates action plans for tasks requiring local execution (banking, WhatsApp).
Cloud agent cannot execute these directly due to credential restrictions.

Based on spec.md FR-011 and User Story 2.
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from cloud.agent.config import CloudAgentConfig
from coordination.logical_clock import LamportClock
from coordination.work_queue import WorkQueueDomain
from sync.atomic_writer import AtomicWriter


class ActionPlanWriter:
    """
    Creates action plans for cloud agent.

    Action plans are written to /Needs_Action/{domain}/ for local agent
    to claim and execute. Used for sensitive operations that require
    full credentials (banking, WhatsApp, payments).
    """

    def __init__(self, config: CloudAgentConfig):
        """
        Initialize action plan writer.

        Args:
            config: Cloud agent configuration
        """
        self.config = config
        self.logger = logging.getLogger("action_plan_writer")
        self.clock = LamportClock(agent_id="cloud")
        self.vault_path = config.vault_path

    def create_banking_action_plan(self, transaction_data: Dict) -> Optional[str]:
        """
        Create action plan for banking transaction.

        Args:
            transaction_data: Transaction details

        Returns:
            Action plan ID if successful
        """
        try:
            plan_id = str(uuid.uuid4())
            timestamp = self.clock.tick()

            plan_content = f"""# Banking Transaction Action Plan

**Plan ID**: {plan_id}
**Created By**: cloud
**Created At**: {timestamp.wall_clock_time.isoformat()}
**Domain**: banking
**Status**: pending

## Transaction Details

- **Type**: {transaction_data.get('type', 'unknown')}
- **Amount**: ${transaction_data.get('amount', 0):.2f}
- **Recipient**: {transaction_data.get('recipient', 'N/A')}
- **Description**: {transaction_data.get('description', 'N/A')}

## Required Actions

1. Verify transaction details
2. Check account balance
3. Execute transaction via banking API
4. Log transaction in Odoo
5. Move to /Done/ when complete

## Security Notes

⚠️ This action requires full banking credentials (local agent only).
Cloud agent cannot execute banking operations per FR-005.

## Metadata

```json
{metadata}
```
"""

            metadata = {
                "plan_id": plan_id,
                "domain": "banking",
                "created_by": "cloud",
                "created_at": timestamp.to_dict(),
                "transaction_data": transaction_data
            }

            plan_file = self.vault_path / "Needs_Action" / "banking" / f"{plan_id}.md"
            plan_file.parent.mkdir(parents=True, exist_ok=True)

            AtomicWriter.write(
                plan_file,
                plan_content.format(metadata=json.dumps(metadata, indent=2))
            )

            self.logger.info(f"Created banking action plan {plan_id}")
            return plan_id

        except Exception as e:
            self.logger.error(f"Failed to create banking action plan: {e}", exc_info=True)
            return None

    def create_whatsapp_action_plan(self, message_data: Dict) -> Optional[str]:
        """
        Create action plan for WhatsApp message.

        Args:
            message_data: Message details

        Returns:
            Action plan ID if successful
        """
        try:
            plan_id = str(uuid.uuid4())
            timestamp = self.clock.tick()

            plan_content = f"""# WhatsApp Message Action Plan

**Plan ID**: {plan_id}
**Created By**: cloud
**Created At**: {timestamp.wall_clock_time.isoformat()}
**Domain**: whatsapp
**Status**: pending

## Message Details

- **Recipient**: {message_data.get('recipient', 'N/A')}
- **Message**: {message_data.get('message', 'N/A')}
- **Priority**: {message_data.get('priority', 'normal')}

## Required Actions

1. Verify recipient contact
2. Send message via WhatsApp session
3. Log message in audit trail
4. Move to /Done/ when complete

## Security Notes

⚠️ This action requires WhatsApp session (local agent only).
Cloud agent cannot access WhatsApp sessions per FR-039.

## Metadata

```json
{metadata}
```
"""

            metadata = {
                "plan_id": plan_id,
                "domain": "whatsapp",
                "created_by": "cloud",
                "created_at": timestamp.to_dict(),
                "message_data": message_data
            }

            plan_file = self.vault_path / "Needs_Action" / "whatsapp" / f"{plan_id}.md"
            plan_file.parent.mkdir(parents=True, exist_ok=True)

            AtomicWriter.write(
                plan_file,
                plan_content.format(metadata=json.dumps(metadata, indent=2))
            )

            self.logger.info(f"Created WhatsApp action plan {plan_id}")
            return plan_id

        except Exception as e:
            self.logger.error(f"Failed to create WhatsApp action plan: {e}", exc_info=True)
            return None

    def create_generic_action_plan(
        self,
        domain: str,
        action_type: str,
        description: str,
        details: Dict
    ) -> Optional[str]:
        """
        Create generic action plan for any domain.

        Args:
            domain: Work domain (banking, whatsapp, etc.)
            action_type: Type of action
            description: Human-readable description
            details: Action details as dict

        Returns:
            Action plan ID if successful
        """
        try:
            plan_id = str(uuid.uuid4())
            timestamp = self.clock.tick()

            plan_content = f"""# Action Plan: {action_type}

**Plan ID**: {plan_id}
**Created By**: cloud
**Created At**: {timestamp.wall_clock_time.isoformat()}
**Domain**: {domain}
**Status**: pending

## Description

{description}

## Details

```json
{json.dumps(details, indent=2)}
```

## Required Actions

(Local agent should determine specific actions based on domain and type)

## Security Notes

⚠️ This action requires local agent execution.

## Metadata

```json
{metadata}
```
"""

            metadata = {
                "plan_id": plan_id,
                "domain": domain,
                "action_type": action_type,
                "created_by": "cloud",
                "created_at": timestamp.to_dict(),
                "details": details
            }

            # Ensure domain directory exists
            domain_dir = self.vault_path / "Needs_Action" / domain
            domain_dir.mkdir(parents=True, exist_ok=True)

            plan_file = domain_dir / f"{plan_id}.md"

            AtomicWriter.write(
                plan_file,
                plan_content.format(metadata=json.dumps(metadata, indent=2))
            )

            self.logger.info(f"Created {domain} action plan {plan_id}")
            return plan_id

        except Exception as e:
            self.logger.error(f"Failed to create action plan: {e}", exc_info=True)
            return None
