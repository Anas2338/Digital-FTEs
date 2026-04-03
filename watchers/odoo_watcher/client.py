"""
Odoo API Client

Handles communication with Odoo Community Edition 19+ via XML-RPC.
Implements authentication, transaction fetching, and error handling.
"""

import odoorpc
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from urllib.parse import urlparse

from watchers.odoo_watcher.config import OdooConfig, TransactionState
from watchers.shared.env_loader import get_loader


logger = logging.getLogger(__name__)


class OdooClient:
    """
    Client for Odoo Community Edition 19+ API.

    Uses XML-RPC protocol for communication.
    """

    def __init__(self):
        """Initialize Odoo client with credentials from .env or keychain."""
        self.odoo: Optional[odoorpc.ODOO] = None
        self.uid: Optional[int] = None
        self.connected = False

    def connect(self) -> bool:
        """
        Connect to Odoo instance using credentials from .env or keychain.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Retrieve credentials from .env or keychain
            loader = get_loader()
            credentials = loader.get_odoo_credentials()

            # Parse URL to get host, port, and protocol
            url = credentials["url"]
            parsed = urlparse(url)
            host = parsed.hostname or url
            database = credentials["database"]
            username = credentials["username"]
            password = credentials["password"]

            if not all([host, database, username, password]):
                logger.error("Missing Odoo credentials")
                return False

            # Determine protocol and port based on URL scheme
            if parsed.scheme == 'https':
                protocol = 'jsonrpc+ssl'
                port = parsed.port or 443
            else:
                protocol = 'jsonrpc'
                port = parsed.port or 8069

            # Connect to Odoo
            logger.info(f"Connecting to Odoo at {host}:{port} using {protocol}...")
            self.odoo = odoorpc.ODOO(host, protocol=protocol, port=int(port))
            self.uid = self.odoo.login(database, username, password)
            self.connected = True

            logger.info(f"Connected to Odoo at {host}:{port} as {username}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Odoo: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """Disconnect from Odoo instance."""
        if self.odoo:
            self.odoo = None
            self.uid = None
            self.connected = False
            logger.info("Disconnected from Odoo")

    def fetch_transactions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch account moves (transactions) from Odoo.

        Args:
            start_date: Start date for filtering (default: 30 days ago)
            end_date: End date for filtering (default: now)
            limit: Maximum number of transactions to fetch

        Returns:
            List of transaction dictionaries

        Raises:
            ConnectionError: If not connected to Odoo
        """
        if not self.connected or not self.odoo:
            raise ConnectionError("Not connected to Odoo. Call connect() first.")

        # Default date range: last 30 days
        if not start_date:
            start_date = datetime.now() - timedelta(days=OdooConfig.INITIAL_SYNC_DAYS)
        if not end_date:
            end_date = datetime.now()

        try:
            # Search for account moves in date range
            # Filter for posted moves only (state='posted')
            move_ids = self.odoo.env['account.move'].search([
                ('date', '>=', start_date.strftime('%Y-%m-%d')),
                ('date', '<=', end_date.strftime('%Y-%m-%d')),
                ('state', '=', 'posted')
            ], limit=limit)

            if not move_ids:
                logger.info("No transactions found in date range")
                return []

            # Read transaction details
            moves = self.odoo.env['account.move'].read(
                move_ids,
                ['id', 'name', 'date', 'amount_total', 'currency_id',
                 'partner_id', 'move_type', 'state', 'line_ids']
            )

            transactions = []
            for move in moves:
                # Get line items for account codes
                line_ids = move.get('line_ids', [])
                if line_ids:
                    lines = self.odoo.env['account.move.line'].read(
                        line_ids,
                        ['account_id', 'name', 'debit', 'credit']
                    )
                else:
                    lines = []

                # Extract account code from first line
                account_code = None
                description = move.get('name', '')
                if lines:
                    account_id = lines[0].get('account_id')
                    if account_id:
                        account = self.odoo.env['account.account'].read(
                            [account_id[0]],
                            ['code']
                        )
                        if account:
                            account_code = account[0].get('code', '')
                    # Use line description if available
                    if lines[0].get('name'):
                        description = lines[0]['name']

                # Extract partner name
                partner_name = None
                partner_id = None
                if move.get('partner_id'):
                    partner_id = str(move['partner_id'][0])
                    partner_name = move['partner_id'][1]

                # Extract currency
                currency = OdooConfig.DEFAULT_CURRENCY
                if move.get('currency_id'):
                    currency = move['currency_id'][1]

                # Build transaction dict
                transaction = {
                    'external_id': str(move['id']),
                    'amount': abs(move.get('amount_total', 0.0)),
                    'currency': currency,
                    'date': move.get('date', ''),
                    'description': description,
                    'partner_name': partner_name,
                    'partner_id': partner_id,
                    'account_code': account_code or '000',
                    'move_type': move.get('move_type', 'entry'),
                    'state': move.get('state', 'draft')
                }

                transactions.append(transaction)

            logger.info(f"Fetched {len(transactions)} transactions from Odoo")
            return transactions

        except Exception as e:
            logger.error(f"Failed to fetch transactions from Odoo: {e}")
            raise

    def test_connection(self) -> Dict[str, Any]:
        """
        Test Odoo connection and return server info.

        Returns:
            Dictionary with connection status and server info
        """
        if not self.connected or not self.odoo:
            return {
                'connected': False,
                'error': 'Not connected'
            }

        try:
            # Get server version
            version = self.odoo.version

            # Get user info - handle potential errors
            user = None
            try:
                if self.uid:
                    user_data = self.odoo.env['res.users'].browse([self.uid])
                    if user_data:
                        user = {
                            'name': user_data[0].name if hasattr(user_data[0], 'name') else 'Unknown',
                            'login': user_data[0].login if hasattr(user_data[0], 'login') else 'Unknown'
                        }
            except Exception as user_error:
                logger.warning(f"Could not fetch user details: {user_error}")
                user = {'name': 'Connected User', 'login': 'N/A'}

            return {
                'connected': True,
                'version': version,
                'user': user,
                'database': self.odoo.env.db
            }

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                'connected': False,
                'error': str(e)
            }
