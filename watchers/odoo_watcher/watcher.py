"""
Odoo Watcher

Monitors Odoo Community Edition for new business transactions and
automatically records them in the local database with duplicate detection.

Polling Interval: 5 minutes
Safety Level: Level 0 (Auto-Execute) - Read-only monitoring
"""

import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from watchers.shared.base_watcher import BaseWatcher
from watchers.shared.audit_logger import AuditLogger
from watchers.odoo_watcher.client import OdooClient
from watchers.odoo_watcher.config import OdooConfig
from watchers.odoo_watcher.duplicate_detector import DuplicateDetector
from watchers.odoo_watcher.transaction_processor import TransactionProcessor
from watchers.odoo_watcher.markdown_logger import TransactionMarkdownLogger
from watchers.shared.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


class OdooWatcher(BaseWatcher):
    """
    Watcher for Odoo accounting system integration.

    Polls Odoo every 5 minutes for new transactions, checks for duplicates,
    and automatically records them in the local database.
    """

    def __init__(self):
        """Initialize Odoo watcher."""
        super().__init__(
            watcher_name="odoo_watcher",
            polling_interval=OdooConfig().polling_interval
        )

        # Initialize components
        self.config = OdooConfig()
        self.client = OdooClient()
        self.duplicate_detector = DuplicateDetector(self.db)
        self.transaction_processor = TransactionProcessor(
            db=self.db,
            audit_logger=AuditLogger(self.db)
        )
        self.markdown_logger = TransactionMarkdownLogger()
        self.circuit_breaker = CircuitBreaker(
            integration_name="odoo",
            failure_threshold=0.20,
            domain_context="business"
        )

        # Track last sync time
        self.last_sync_time = None

    def poll(self) -> List[Dict[str, Any]]:
        """
        Poll Odoo for new transactions.

        Returns:
            List of event dictionaries for processing
        """
        events = []

        try:
            # Execute through circuit breaker
            def fetch_and_process():
                return self._fetch_and_process_transactions()

            result = self.circuit_breaker.call(fetch_and_process)
            events = result if result else []

        except Exception as e:
            logger.error(f"Circuit breaker blocked Odoo polling: {e}")
            # Circuit breaker is OPEN, skip this poll cycle
            events = []

        return events

    def _fetch_and_process_transactions(self) -> List[Dict[str, Any]]:
        """
        Fetch transactions from Odoo and process them.

        Returns:
            List of events for the base watcher to process
        """
        events = []

        # Step 1: Connect to Odoo if not connected
        if not self.client.connected:
            logger.info("Connecting to Odoo...")
            if not self.client.connect():
                logger.error("Failed to connect to Odoo")
                return events

        # Step 2: Determine date range for fetching
        if self.last_sync_time:
            # Fetch transactions since last sync
            start_date = self.last_sync_time
        else:
            # First sync: fetch last 7 days
            start_date = datetime.now() - timedelta(days=7)

        end_date = datetime.now()

        # Step 3: Fetch transactions from Odoo
        logger.info(f"Fetching transactions from {start_date} to {end_date}")
        try:
            transactions = self.client.fetch_transactions(
                start_date=start_date,
                end_date=end_date,
                limit=self.config.fetch_limit
            )
            logger.info(f"Fetched {len(transactions)} transactions from Odoo")
        except Exception as e:
            logger.error(f"Failed to fetch transactions: {e}")
            return events

        # Step 4: Process each transaction
        for transaction in transactions:
            # Check if transaction should be processed based on state
            if not self.config.should_process_transaction(transaction.get('state', '')):
                logger.debug(f"Skipping transaction {transaction.get('external_id')} - state: {transaction.get('state')}")
                continue

            # Check for duplicates
            is_duplicate, matching_transaction = self.duplicate_detector.is_duplicate(
                amount=transaction['amount'],
                date=transaction['date'],
                description=transaction['description'],
                external_id=transaction.get('external_id')
            )

            if is_duplicate:
                logger.info(
                    f"Duplicate transaction detected: {transaction.get('external_id')} "
                    f"(matches existing transaction)"
                )
                continue

            # Create event for processing
            event = {
                'event_type': 'new_transaction',
                'source': 'odoo',
                'transaction': transaction,
                'detected_at': datetime.utcnow().isoformat() + 'Z'
            }
            events.append(event)

        # Step 5: Update last sync time
        self.last_sync_time = end_date

        logger.info(f"Processed {len(events)} new transactions")
        return events

    def _process_event(self, event: Dict[str, Any]):
        """
        Process a new transaction event.

        Args:
            event: Event dictionary containing transaction data
        """
        if event['event_type'] != 'new_transaction':
            logger.warning(f"Unknown event type: {event['event_type']}")
            return

        transaction = event['transaction']

        try:
            # Process and store transaction
            result = self.transaction_processor.process_transaction(transaction)

            if result.get('success'):
                logger.info(
                    f"Successfully recorded transaction: {transaction.get('external_id')} "
                    f"- {transaction.get('description')} - ${transaction.get('amount')}"
                )

                # Log to Obsidian vault
                self.markdown_logger.log_transaction(
                    transaction_id=result['transaction_id'],
                    transaction_data=transaction,
                    category=result.get('category', 'Unknown')
                )

                # Log event
                self.event_logger.log_event(
                    event_type='transaction_recorded',
                    source='odoo',
                    data={
                        'transaction_id': result['transaction_id'],
                        'external_id': transaction.get('external_id'),
                        'amount': transaction.get('amount'),
                        'category': result.get('category')
                    }
                )
            else:
                logger.warning(
                    f"Failed to record transaction: {transaction.get('external_id')} "
                    f"- Reason: {result.get('reason')}"
                )

        except Exception as e:
            logger.error(f"Error processing transaction: {e}", exc_info=True)

    def _handle_error(self, error: Exception):
        """
        Handle errors during polling.

        Args:
            error: Exception that occurred
        """
        self.error_count += 1
        logger.error(f"Odoo watcher error (count: {self.error_count}): {error}")

        # If too many errors, disconnect and reconnect
        if self.error_count >= 3:
            logger.warning("Too many errors, reconnecting to Odoo...")
            self.client.disconnect()
            self.error_count = 0

    def stop(self):
        """Stop the watcher and cleanup."""
        super().stop()
        self.client.disconnect()
        logger.info("Odoo watcher stopped and disconnected")

    def get_config(self) -> Dict[str, Any]:
        """
        Get watcher configuration.

        Returns:
            Configuration dict with watcher settings
        """
        return {
            "watcher_name": self.watcher_name,
            "polling_interval": self.polling_interval,
            "fetch_limit": self.config.fetch_limit,
            "only_posted": self.config.only_posted,
            "duplicate_window_hours": self.config.duplicate_window_hours,
            "circuit_breaker_enabled": True
        }


def main():
    """Main entry point for Odoo watcher."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    watcher = OdooWatcher()
    try:
        watcher.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, stopping...")
        watcher.stop()


if __name__ == "__main__":
    main()
