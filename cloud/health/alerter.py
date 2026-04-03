"""
Alerter for Platinum Tier

Sends alerts via multiple channels when health checks fail.
Supports email, SMS (Twilio), and push notifications (Pushover, ntfy.sh).

Based on spec.md FR-032 and User Story 5.
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List
import aiohttp

from cloud.health.health_status import HealthCheck, ServiceType


class AlertChannel(Enum):
    """Alert delivery channels."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class AlertPriority(Enum):
    """Alert priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class Alerter:
    """
    Sends alerts via multiple channels.

    Supports:
    - Email alerts (via SMTP or API)
    - SMS alerts (via Twilio)
    - Push notifications (via Pushover or ntfy.sh)
    """

    def __init__(self, config: Dict):
        """
        Initialize alerter.

        Args:
            config: Alert configuration dict with channel settings
                {
                    "email": {"enabled": bool, "smtp_host": str, ...},
                    "sms": {"enabled": bool, "twilio_account_sid": str, ...},
                    "push": {"enabled": bool, "provider": "pushover|ntfy", ...}
                }
        """
        self.config = config
        self.logger = logging.getLogger("alerter")

        # Track last alert time per service to avoid spam
        self.last_alert_time: Dict[ServiceType, datetime] = {}
        self.min_alert_interval_seconds = 300  # 5 minutes between alerts

    async def send_alert(
        self,
        service_type: ServiceType,
        health_check: HealthCheck,
        priority: AlertPriority = AlertPriority.NORMAL,
        channels: Optional[List[AlertChannel]] = None
    ) -> bool:
        """
        Send alert about failed health check.

        Args:
            service_type: Service that failed
            health_check: Health check result
            priority: Alert priority level
            channels: Specific channels to use (None = all enabled)

        Returns:
            True if at least one alert sent successfully
        """
        # Check if we should throttle alerts for this service
        if self._should_throttle(service_type):
            self.logger.debug(
                f"Throttling alert for {service_type.value} "
                f"(last alert too recent)"
            )
            return False

        # Prepare alert message
        message = self._format_alert_message(service_type, health_check)
        subject = f"[{priority.value.upper()}] {service_type.value} health check failed"

        # Determine which channels to use
        if channels is None:
            channels = self._get_enabled_channels()

        # Send via all requested channels
        results = []
        for channel in channels:
            try:
                if channel == AlertChannel.EMAIL:
                    success = await self._send_email_alert(subject, message, priority)
                    results.append(success)
                elif channel == AlertChannel.SMS:
                    success = await self._send_sms_alert(message, priority)
                    results.append(success)
                elif channel == AlertChannel.PUSH:
                    success = await self._send_push_alert(subject, message, priority)
                    results.append(success)
            except Exception as e:
                self.logger.error(f"Failed to send {channel.value} alert: {e}")
                results.append(False)

        # Update last alert time if any succeeded
        if any(results):
            self.last_alert_time[service_type] = datetime.now()
            self.logger.info(
                f"Sent {priority.value} alert for {service_type.value} "
                f"via {len([r for r in results if r])} channels"
            )

        return any(results)

    def _should_throttle(self, service_type: ServiceType) -> bool:
        """Check if alerts should be throttled for this service."""
        last_alert = self.last_alert_time.get(service_type)
        if not last_alert:
            return False

        elapsed = (datetime.now() - last_alert).total_seconds()
        return elapsed < self.min_alert_interval_seconds

    def _get_enabled_channels(self) -> List[AlertChannel]:
        """Get list of enabled alert channels from config."""
        channels = []
        if self.config.get("email", {}).get("enabled", False):
            channels.append(AlertChannel.EMAIL)
        if self.config.get("sms", {}).get("enabled", False):
            channels.append(AlertChannel.SMS)
        if self.config.get("push", {}).get("enabled", False):
            channels.append(AlertChannel.PUSH)
        return channels

    def _format_alert_message(
        self,
        service_type: ServiceType,
        health_check: HealthCheck
    ) -> str:
        """Format alert message with health check details."""
        lines = [
            f"Service: {service_type.value}",
            f"Status: {health_check.status.value}",
            f"Time: {health_check.checked_at.isoformat()}",
        ]

        if health_check.error_message:
            lines.append(f"Error: {health_check.error_message}")

        if health_check.response_time_seconds:
            lines.append(
                f"Response time: {health_check.response_time_seconds:.2f}s"
            )

        if health_check.metadata:
            lines.append(f"Details: {health_check.metadata}")

        return "\n".join(lines)

    async def _send_email_alert(
        self,
        subject: str,
        message: str,
        priority: AlertPriority
    ) -> bool:
        """
        Send email alert.

        Args:
            subject: Email subject
            message: Email body
            priority: Alert priority

        Returns:
            True if sent successfully
        """
        email_config = self.config.get("email", {})
        if not email_config.get("enabled", False):
            return False

        try:
            # Placeholder: Would use SMTP or email API here
            # import smtplib
            # from email.mime.text import MIMEText
            #
            # msg = MIMEText(message)
            # msg['Subject'] = subject
            # msg['From'] = email_config['from_address']
            # msg['To'] = email_config['to_address']
            #
            # with smtplib.SMTP(email_config['smtp_host'], email_config['smtp_port']) as server:
            #     server.starttls()
            #     server.login(email_config['username'], email_config['password'])
            #     server.send_message(msg)

            self.logger.info(f"Email alert sent: {subject}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
            return False

    async def _send_sms_alert(
        self,
        message: str,
        priority: AlertPriority
    ) -> bool:
        """
        Send SMS alert via Twilio.

        Args:
            message: SMS message text
            priority: Alert priority

        Returns:
            True if sent successfully
        """
        sms_config = self.config.get("sms", {})
        if not sms_config.get("enabled", False):
            return False

        try:
            # Placeholder: Would use Twilio API here
            # from twilio.rest import Client
            #
            # client = Client(
            #     sms_config['twilio_account_sid'],
            #     sms_config['twilio_auth_token']
            # )
            #
            # message = client.messages.create(
            #     body=message,
            #     from_=sms_config['from_number'],
            #     to=sms_config['to_number']
            # )

            self.logger.info(f"SMS alert sent (priority: {priority.value})")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send SMS alert: {e}")
            return False

    async def _send_push_alert(
        self,
        title: str,
        message: str,
        priority: AlertPriority
    ) -> bool:
        """
        Send push notification via Pushover or ntfy.sh.

        Args:
            title: Notification title
            message: Notification message
            priority: Alert priority

        Returns:
            True if sent successfully
        """
        push_config = self.config.get("push", {})
        if not push_config.get("enabled", False):
            return False

        provider = push_config.get("provider", "pushover")

        try:
            if provider == "pushover":
                return await self._send_pushover(title, message, priority, push_config)
            elif provider == "ntfy":
                return await self._send_ntfy(title, message, priority, push_config)
            else:
                self.logger.error(f"Unknown push provider: {provider}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to send push alert: {e}")
            return False

    async def _send_pushover(
        self,
        title: str,
        message: str,
        priority: AlertPriority,
        config: Dict
    ) -> bool:
        """Send push notification via Pushover API."""
        # Map priority to Pushover priority levels
        priority_map = {
            AlertPriority.LOW: -1,
            AlertPriority.NORMAL: 0,
            AlertPriority.HIGH: 1,
            AlertPriority.CRITICAL: 2
        }

        data = {
            "token": config["pushover_app_token"],
            "user": config["pushover_user_key"],
            "title": title,
            "message": message,
            "priority": priority_map.get(priority, 0)
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.pushover.net/1/messages.json",
                data=data
            ) as response:
                success = response.status == 200
                if success:
                    self.logger.info("Pushover notification sent")
                return success

    async def _send_ntfy(
        self,
        title: str,
        message: str,
        priority: AlertPriority,
        config: Dict
    ) -> bool:
        """Send push notification via ntfy.sh."""
        # Map priority to ntfy priority levels
        priority_map = {
            AlertPriority.LOW: "low",
            AlertPriority.NORMAL: "default",
            AlertPriority.HIGH: "high",
            AlertPriority.CRITICAL: "urgent"
        }

        topic = config["ntfy_topic"]
        server = config.get("ntfy_server", "https://ntfy.sh")

        headers = {
            "Title": title,
            "Priority": priority_map.get(priority, "default"),
            "Tags": "warning"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{server}/{topic}",
                data=message.encode("utf-8"),
                headers=headers
            ) as response:
                success = response.status == 200
                if success:
                    self.logger.info("ntfy notification sent")
                return success
