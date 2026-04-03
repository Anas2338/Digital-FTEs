"""
Audit Trail System for Digital FTE

Immutable, append-only audit trail for all agent actions.
Provides accountability, compliance, and debugging capabilities.

Based on tasks.md T075 and constitution principles.
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from coordination.logical_clock import LamportClock, LamportTimestamp
from sync.atomic_writer import AtomicWriter


class AuditEventType(Enum):
    """Types of auditable events."""
    DRAFT_GENERATED = "draft_generated"
    DRAFT_APPROVED = "draft_approved"
    DRAFT_REJECTED = "draft_rejected"
    EMAIL_SENT = "email_sent"
    SOCIAL_POST_PUBLISHED = "social_post_published"
    ACCOUNTING_ENTRY_POSTED = "accounting_entry_posted"
    TASK_CLAIMED = "task_claimed"
    TASK_RELEASED = "task_released"
    VAULT_SYNCED = "vault_synced"
    CONFLICT_RESOLVED = "conflict_resolved"
    HEALTH_CHECK_FAILED = "health_check_failed"
    SERVICE_RESTARTED = "service_restarted"
    ALERT_SENT = "alert_sent"
    MANUAL_INTERVENTION = "manual_intervention"
    CREDENTIAL_ROTATED = "credential_rotated"


@dataclass
class AuditEvent:
    """
    Immutable audit event record.

    Attributes:
        event_id: Unique event identifier (hash of content)
        event_type: Type of event
        agent_id: Agent that performed the action
        timestamp: Logical timestamp
        wall_clock_time: Wall clock timestamp
        action: Human-readable action description
        entity_type: Type of entity affected (draft, email, task, etc)
        entity_id: ID of affected entity
        metadata: Additional structured data
        previous_event_hash: Hash of previous event (blockchain-style)
    """
    event_id: str
    event_type: AuditEventType
    agent_id: str
    timestamp: LamportTimestamp
    wall_clock_time: datetime
    action: str
    entity_type: str
    entity_id: str
    metadata: Dict[str, Any]
    previous_event_hash: Optional[str] = None

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.to_dict(),
            "wall_clock_time": self.wall_clock_time.isoformat(),
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "metadata": self.metadata,
            "previous_event_hash": self.previous_event_hash
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "AuditEvent":
        """Deserialize from dictionary."""
        return cls(
            event_id=data["event_id"],
            event_type=AuditEventType(data["event_type"]),
            agent_id=data["agent_id"],
            timestamp=LamportTimestamp(
                agent_id=data["timestamp"]["agent_id"],
                counter=data["timestamp"]["counter"],
                wall_clock_time=datetime.fromisoformat(data["timestamp"]["wall_clock_time"])
            ),
            wall_clock_time=datetime.fromisoformat(data["wall_clock_time"]),
            action=data["action"],
            entity_type=data["entity_type"],
            entity_id=data["entity_id"],
            metadata=data["metadata"],
            previous_event_hash=data.get("previous_event_hash")
        )


class AuditTrail:
    """
    Append-only audit trail with blockchain-style integrity.

    Features:
    - Immutable event records
    - Cryptographic hashing for integrity
    - Logical timestamps for ordering
    - Queryable by entity, agent, time range
    """

    def __init__(self, vault_path: Path, agent_id: str):
        """
        Initialize audit trail.

        Args:
            vault_path: Path to Obsidian vault
            agent_id: Agent identifier
        """
        self.vault_path = Path(vault_path)
        self.agent_id = agent_id
        self.clock = LamportClock(agent_id=agent_id)

        # Audit trail file (append-only JSONL)
        self.audit_file = vault_path / "audit_trail.jsonl"
        self.audit_file.parent.mkdir(parents=True, exist_ok=True)

        # Cache last event hash for blockchain-style linking
        self._last_event_hash: Optional[str] = None
        self._load_last_event_hash()

    def _load_last_event_hash(self) -> None:
        """Load hash of last event from file."""
        if not self.audit_file.exists():
            return

        try:
            # Read last line of file
            with open(self.audit_file, 'rb') as f:
                # Seek to end and read backwards to find last line
                f.seek(0, 2)  # Go to end
                file_size = f.tell()
                if file_size == 0:
                    return

                # Read last 1KB (should contain last event)
                read_size = min(1024, file_size)
                f.seek(file_size - read_size)
                last_chunk = f.read().decode('utf-8')

                # Get last non-empty line
                lines = [l for l in last_chunk.split('\n') if l.strip()]
                if lines:
                    last_event = json.loads(lines[-1])
                    self._last_event_hash = last_event.get("event_id")

        except Exception as e:
            # If we can't load last hash, that's okay - chain will start fresh
            pass

    def _compute_event_hash(self, event_data: Dict) -> str:
        """
        Compute cryptographic hash of event data.

        Args:
            event_data: Event data dict

        Returns:
            SHA-256 hash as hex string
        """
        # Create deterministic string representation
        # Exclude event_id itself from hash computation
        hashable_data = {
            k: v for k, v in event_data.items()
            if k != "event_id"
        }

        data_str = json.dumps(hashable_data, sort_keys=True)
        return hashlib.sha256(data_str.encode('utf-8')).hexdigest()

    def record_event(
        self,
        event_type: AuditEventType,
        action: str,
        entity_type: str,
        entity_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """
        Record an audit event.

        Args:
            event_type: Type of event
            action: Human-readable action description
            entity_type: Type of entity affected
            entity_id: ID of affected entity
            metadata: Additional structured data

        Returns:
            Created audit event
        """
        timestamp = self.clock.tick()

        # Create event (without ID yet)
        event_data = {
            "event_type": event_type.value,
            "agent_id": self.agent_id,
            "timestamp": timestamp.to_dict(),
            "wall_clock_time": datetime.now().isoformat(),
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "metadata": metadata or {},
            "previous_event_hash": self._last_event_hash
        }

        # Compute hash as event ID
        event_id = self._compute_event_hash(event_data)
        event_data["event_id"] = event_id

        # Create event object
        event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            agent_id=self.agent_id,
            timestamp=timestamp,
            wall_clock_time=datetime.now(),
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata=metadata or {},
            previous_event_hash=self._last_event_hash
        )

        # Append to audit file (atomic append)
        self._append_event(event)

        # Update last event hash
        self._last_event_hash = event_id

        return event

    def _append_event(self, event: AuditEvent) -> None:
        """
        Append event to audit file.

        Args:
            event: Event to append
        """
        try:
            # Append to JSONL file (one event per line)
            with open(self.audit_file, 'a') as f:
                f.write(json.dumps(event.to_dict()) + '\n')

        except Exception as e:
            # Critical: audit trail write failure
            # Log to stderr and raise
            import sys
            print(f"CRITICAL: Failed to write audit event: {e}", file=sys.stderr)
            raise

    def query_events(
        self,
        event_type: Optional[AuditEventType] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[AuditEvent]:
        """
        Query audit events with filters.

        Args:
            event_type: Filter by event type
            entity_type: Filter by entity type
            entity_id: Filter by entity ID
            agent_id: Filter by agent ID
            start_time: Filter by start time (inclusive)
            end_time: Filter by end time (inclusive)
            limit: Maximum number of events to return

        Returns:
            List of matching audit events
        """
        if not self.audit_file.exists():
            return []

        events = []

        try:
            with open(self.audit_file, 'r') as f:
                for line in f:
                    try:
                        event_data = json.loads(line.strip())
                        event = AuditEvent.from_dict(event_data)

                        # Apply filters
                        if event_type and event.event_type != event_type:
                            continue
                        if entity_type and event.entity_type != entity_type:
                            continue
                        if entity_id and event.entity_id != entity_id:
                            continue
                        if agent_id and event.agent_id != agent_id:
                            continue
                        if start_time and event.wall_clock_time < start_time:
                            continue
                        if end_time and event.wall_clock_time > end_time:
                            continue

                        events.append(event)

                        # Check limit
                        if limit and len(events) >= limit:
                            break

                    except (json.JSONDecodeError, KeyError):
                        # Skip malformed lines
                        continue

        except Exception as e:
            print(f"Error querying audit trail: {e}")

        return events

    def verify_integrity(self) -> bool:
        """
        Verify audit trail integrity by checking hash chain.

        Returns:
            True if integrity is intact, False if compromised
        """
        if not self.audit_file.exists():
            return True

        try:
            previous_hash = None

            with open(self.audit_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        event_data = json.loads(line.strip())

                        # Verify previous hash matches
                        if event_data.get("previous_event_hash") != previous_hash:
                            print(
                                f"Integrity violation at line {line_num}: "
                                f"previous_event_hash mismatch"
                            )
                            return False

                        # Verify event hash
                        claimed_hash = event_data.get("event_id")
                        computed_hash = self._compute_event_hash(event_data)

                        if claimed_hash != computed_hash:
                            print(
                                f"Integrity violation at line {line_num}: "
                                f"event_id hash mismatch"
                            )
                            return False

                        previous_hash = claimed_hash

                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"Malformed event at line {line_num}: {e}")
                        return False

            return True

        except Exception as e:
            print(f"Error verifying audit trail: {e}")
            return False

    def get_entity_history(
        self,
        entity_type: str,
        entity_id: str
    ) -> List[AuditEvent]:
        """
        Get complete history for an entity.

        Args:
            entity_type: Type of entity
            entity_id: Entity ID

        Returns:
            List of events for this entity, ordered by timestamp
        """
        events = self.query_events(
            entity_type=entity_type,
            entity_id=entity_id
        )

        # Sort by logical timestamp
        events.sort(key=lambda e: (e.timestamp.counter, e.timestamp.wall_clock_time))

        return events

    def export_to_csv(self, output_file: Path) -> None:
        """
        Export audit trail to CSV for analysis.

        Args:
            output_file: Path to output CSV file
        """
        import csv

        if not self.audit_file.exists():
            return

        try:
            with open(self.audit_file, 'r') as f_in, \
                 open(output_file, 'w', newline='') as f_out:

                writer = csv.writer(f_out)

                # Write header
                writer.writerow([
                    "event_id", "event_type", "agent_id",
                    "wall_clock_time", "action", "entity_type",
                    "entity_id", "metadata"
                ])

                # Write events
                for line in f_in:
                    try:
                        event_data = json.loads(line.strip())
                        writer.writerow([
                            event_data.get("event_id"),
                            event_data.get("event_type"),
                            event_data.get("agent_id"),
                            event_data.get("wall_clock_time"),
                            event_data.get("action"),
                            event_data.get("entity_type"),
                            event_data.get("entity_id"),
                            json.dumps(event_data.get("metadata", {}))
                        ])
                    except (json.JSONDecodeError, KeyError):
                        continue

        except Exception as e:
            print(f"Error exporting audit trail: {e}")


# Convenience functions for common audit events

def audit_draft_generated(
    audit_trail: AuditTrail,
    draft_id: str,
    draft_type: str,
    metadata: Optional[Dict] = None
) -> AuditEvent:
    """Record draft generation event."""
    return audit_trail.record_event(
        event_type=AuditEventType.DRAFT_GENERATED,
        action=f"Generated {draft_type} draft",
        entity_type="draft",
        entity_id=draft_id,
        metadata=metadata
    )


def audit_draft_approved(
    audit_trail: AuditTrail,
    draft_id: str,
    approved_by: str,
    metadata: Optional[Dict] = None
) -> AuditEvent:
    """Record draft approval event."""
    return audit_trail.record_event(
        event_type=AuditEventType.DRAFT_APPROVED,
        action=f"Approved draft (by {approved_by})",
        entity_type="draft",
        entity_id=draft_id,
        metadata=metadata
    )


def audit_email_sent(
    audit_trail: AuditTrail,
    email_id: str,
    to_address: str,
    metadata: Optional[Dict] = None
) -> AuditEvent:
    """Record email sent event."""
    return audit_trail.record_event(
        event_type=AuditEventType.EMAIL_SENT,
        action=f"Sent email to {to_address}",
        entity_type="email",
        entity_id=email_id,
        metadata=metadata
    )


def audit_accounting_entry(
    audit_trail: AuditTrail,
    entry_id: str,
    transaction_type: str,
    amount: float,
    metadata: Optional[Dict] = None
) -> AuditEvent:
    """Record accounting entry posted event."""
    return audit_trail.record_event(
        event_type=AuditEventType.ACCOUNTING_ENTRY_POSTED,
        action=f"Posted {transaction_type} entry (amount: {amount})",
        entity_type="accounting_entry",
        entity_id=entry_id,
        metadata=metadata
    )
