"""
Draft Generator for Cloud Agent

Generates email reply drafts and social post drafts using LLM.
Writes drafts to vault for local agent approval.

Based on spec.md FR-007, FR-009 and User Story 2.
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from cloud.agent.config import CloudAgentConfig
from coordination.logical_clock import LamportClock
from coordination.work_queue import WorkQueueDomain, WorkQueueItemType
from sync.atomic_writer import AtomicWriter


class DraftGenerator:
    """
    Generates drafts for email replies and social media posts.

    Uses LLM (Claude or Gemini per config) to generate contextual drafts.
    Writes drafts to /Pending_Approval/{domain}/ for local agent review.
    """

    def __init__(self, config: CloudAgentConfig):
        """
        Initialize draft generator.

        Args:
            config: Cloud agent configuration
        """
        self.config = config
        self.logger = logging.getLogger("draft_generator")
        self.clock = LamportClock(agent_id="cloud")
        self.vault_path = config.vault_path

    async def generate_draft(self, event: Dict) -> Optional[str]:
        """
        Generate draft for an event.

        Args:
            event: Event dict from watcher (email, social media, accounting, etc)

        Returns:
            Draft ID if successful, None otherwise
        """
        event_type = event.get("type")

        if event_type == "email_received":
            return await self._generate_email_draft(event)
        elif event_type in ["facebook_mention", "instagram_comment", "twitter_mention"]:
            return await self._generate_social_draft(event)
        elif event_type == "transaction_detected":
            return await self._generate_accounting_draft(event)
        else:
            self.logger.warning(f"Unknown event type: {event_type}")
            return None

    async def _generate_email_draft(self, event: Dict) -> Optional[str]:
        """
        Generate email reply draft.

        Args:
            event: Email event from gmail_watcher_cloud

        Returns:
            Draft ID if successful
        """
        try:
            draft_id = str(uuid.uuid4())
            timestamp = self.clock.tick()

            # Generate draft content using LLM (placeholder)
            draft_content = self._call_llm_for_email_draft(event)

            # Create draft metadata
            draft_metadata = {
                "draft_id": draft_id,
                "draft_type": "email_reply",
                "created_by": "cloud",
                "created_at": timestamp.to_dict(),
                "approval_status": "pending",
                "original_email": {
                    "email_id": event.get("email_id"),
                    "from": event.get("from"),
                    "subject": event.get("subject"),
                    "received_at": event.get("received_at")
                }
            }

            # Write draft to vault using atomic write pattern (FR-019a)
            draft_file = self.vault_path / "Pending_Approval" / "email" / f"{draft_id}.md"
            draft_markdown = self._format_email_draft(draft_metadata, draft_content)

            AtomicWriter.write(draft_file, draft_markdown)

            self.logger.info(f"Created email draft {draft_id} for {event.get('from')}")
            return draft_id

        except Exception as e:
            self.logger.error(f"Failed to generate email draft: {e}", exc_info=True)
            return None

    async def _generate_social_draft(self, event: Dict) -> Optional[str]:
        """
        Generate social media post/reply draft.

        Args:
            event: Social media event from social_watcher_cloud

        Returns:
            Draft ID if successful
        """
        try:
            draft_id = str(uuid.uuid4())
            timestamp = self.clock.tick()

            # Generate draft content using LLM (placeholder)
            draft_content = self._call_llm_for_social_draft(event)

            # Create draft metadata
            draft_metadata = {
                "draft_id": draft_id,
                "draft_type": "social_post",
                "created_by": "cloud",
                "created_at": timestamp.to_dict(),
                "approval_status": "pending",
                "platform": event.get("type").split("_")[0],  # facebook, instagram, twitter
                "original_post": {
                    "post_id": event.get("post_id"),
                    "from_user": event.get("from_user"),
                    "message": event.get("message"),
                    "timestamp": event.get("timestamp")
                }
            }

            # Write draft to vault
            draft_file = self.vault_path / "Pending_Approval" / "social" / f"{draft_id}.md"
            draft_markdown = self._format_social_draft(draft_metadata, draft_content)

            AtomicWriter.write(draft_file, draft_markdown)

            self.logger.info(f"Created social draft {draft_id} for {event.get('type')}")
            return draft_id

        except Exception as e:
            self.logger.error(f"Failed to generate social draft: {e}", exc_info=True)
            return None

    async def _generate_accounting_draft(self, event: Dict) -> Optional[str]:
        """
        Generate accounting entry draft for Odoo transaction.

        Args:
            event: Transaction event from odoo_watcher_cloud

        Returns:
            Draft ID if successful
        """
        try:
            draft_id = str(uuid.uuid4())
            timestamp = self.clock.tick()

            # Generate draft accounting entry using LLM (placeholder)
            draft_content = self._call_llm_for_accounting_draft(event)

            # Create draft metadata
            draft_metadata = {
                "draft_id": draft_id,
                "draft_type": "accounting_entry",
                "created_by": "cloud",
                "created_at": timestamp.to_dict(),
                "approval_status": "pending",
                "transaction": {
                    "transaction_id": event.get("transaction_id"),
                    "transaction_type": event.get("transaction_type"),
                    "partner_name": event.get("partner_name"),
                    "amount": event.get("amount"),
                    "currency": event.get("currency"),
                    "date": event.get("date"),
                    "description": event.get("description")
                }
            }

            # Write draft to vault (FR-026: draft-only accounting actions)
            draft_file = self.vault_path / "Pending_Approval" / "accounting" / f"{draft_id}.md"
            draft_markdown = self._format_accounting_draft(draft_metadata, draft_content)

            AtomicWriter.write(draft_file, draft_markdown)

            self.logger.info(f"Created accounting draft {draft_id} for {event.get('transaction_type')} {event.get('transaction_id')}")
            return draft_id

        except Exception as e:
            self.logger.error(f"Failed to generate accounting draft: {e}", exc_info=True)
            return None

    def _call_llm_for_email_draft(self, event: Dict) -> str:
        """
        Call LLM to generate email reply draft.

        Args:
            event: Email event

        Returns:
            Draft reply text

        Note: Placeholder - would use Claude or Gemini API based on config.llm_provider
        """
        # Placeholder: Would call Claude/Gemini API here
        # if self.config.llm_provider == "claude":
        #     # Use Claude API
        # elif self.config.llm_provider == "gemini":
        #     # Use Gemini API

        return f"Draft reply to: {event.get('subject')}\n\n[LLM-generated reply would go here]"

    def _call_llm_for_social_draft(self, event: Dict) -> str:
        """
        Call LLM to generate social media post/reply draft.

        Args:
            event: Social media event

        Returns:
            Draft post/reply text
        """
        # Placeholder: Would call Claude/Gemini API here
        return f"Draft reply to social media post\n\n[LLM-generated reply would go here]"

    def _call_llm_for_accounting_draft(self, event: Dict) -> str:
        """
        Call LLM to generate accounting entry draft.

        Args:
            event: Transaction event

        Returns:
            Draft accounting entry details
        """
        # Placeholder: Would call Claude/Gemini API here
        # LLM would analyze transaction and suggest:
        # - Account codes (debit/credit)
        # - Journal entry lines
        # - Tax implications
        # - Payment terms

        transaction_type = event.get("transaction_type")
        amount = event.get("amount")
        partner = event.get("partner_name")

        return f"""Suggested accounting entry for {transaction_type}:

**Transaction Details:**
- Partner: {partner}
- Amount: {amount} {event.get("currency")}
- Date: {event.get("date")}

**Suggested Journal Entry:**
[LLM would generate appropriate debit/credit entries here]

**Notes:**
[LLM would add context-specific notes about tax, payment terms, etc.]
"""

    def _format_email_draft(self, metadata: Dict, content: str) -> str:
        """
        Format email draft as markdown with metadata.

        Args:
            metadata: Draft metadata
            content: Draft content

        Returns:
            Formatted markdown
        """
        return f"""---
draft_id: {metadata['draft_id']}
draft_type: {metadata['draft_type']}
created_by: {metadata['created_by']}
created_at: {metadata['created_at']['wall_clock_time']}
approval_status: {metadata['approval_status']}
---

# Email Reply Draft

**Original Email:**
- From: {metadata['original_email']['from']}
- Subject: {metadata['original_email']['subject']}
- Received: {metadata['original_email']['received_at']}

**Draft Reply:**

{content}

---

**Actions:**
- [ ] Approve and send
- [ ] Reject
- [ ] Edit and approve
"""

    def _format_social_draft(self, metadata: Dict, content: str) -> str:
        """
        Format social media draft as markdown with metadata.

        Args:
            metadata: Draft metadata
            content: Draft content

        Returns:
            Formatted markdown
        """
        return f"""---
draft_id: {metadata['draft_id']}
draft_type: {metadata['draft_type']}
created_by: {metadata['created_by']}
created_at: {metadata['created_at']['wall_clock_time']}
approval_status: {metadata['approval_status']}
platform: {metadata['platform']}
---

# Social Media Reply Draft

**Original Post:**
- Platform: {metadata['platform']}
- From: {metadata['original_post']['from_user']}
- Message: {metadata['original_post']['message']}

**Draft Reply:**

{content}

---

**Actions:**
- [ ] Approve and post
- [ ] Reject
- [ ] Edit and approve
"""

    def _format_accounting_draft(self, metadata: Dict, content: str) -> str:
        """
        Format accounting entry draft as markdown with metadata.

        Args:
            metadata: Draft metadata
            content: Draft content

        Returns:
            Formatted markdown
        """
        txn = metadata['transaction']
        return f"""---
draft_id: {metadata['draft_id']}
draft_type: {metadata['draft_type']}
created_by: {metadata['created_by']}
created_at: {metadata['created_at']['wall_clock_time']}
approval_status: {metadata['approval_status']}
---

# Accounting Entry Draft

**Transaction:**
- ID: {txn['transaction_id']}
- Type: {txn['transaction_type']}
- Partner: {txn['partner_name']}
- Amount: {txn['amount']} {txn['currency']}
- Date: {txn['date']}
- Description: {txn['description']}

**Draft Accounting Entry:**

{content}

---

**Actions:**
- [ ] Approve and post to Odoo
- [ ] Reject
- [ ] Edit and approve

**Security Note:** This action requires local agent approval (FR-026).
Cloud agent cannot post accounting entries directly.
"""
