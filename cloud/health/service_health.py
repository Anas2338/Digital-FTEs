"""
Service Health Checker for Platinum Tier

Performs health checks on various services (Odoo, APIs, watchers).
Supports HTTP endpoint checks, process checks, and connectivity tests.

Based on spec.md FR-031, FR-032, FR-034 and User Story 5.
"""

import asyncio
import logging
import subprocess
from datetime import datetime
from typing import Optional, Dict
import aiohttp

from cloud.health.health_status import (
    HealthCheck,
    HealthStatus,
    ServiceType
)


class ServiceHealthChecker:
    """
    Performs health checks on external services and endpoints.

    Supports:
    - HTTP/HTTPS endpoint checks (Odoo /web/health)
    - Process existence checks (systemd services)
    - API connectivity tests (Gmail, social media APIs)
    """

    def __init__(self):
        """Initialize service health checker."""
        self.logger = logging.getLogger("service_health_checker")
        self.timeout_seconds = 10  # Default timeout for checks

    async def check_odoo_health(self, odoo_url: str) -> HealthCheck:
        """
        Check Odoo health via /web/health endpoint.

        Args:
            odoo_url: Base URL of Odoo instance (e.g., https://odoo.example.com)

        Returns:
            HealthCheck result

        Note: Implements FR-028 (Odoo health monitoring requirement)
        """
        service_type = ServiceType.ODOO
        start_time = datetime.now()

        try:
            health_url = f"{odoo_url.rstrip('/')}/web/health"

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    health_url,
                    timeout=aiohttp.ClientTimeout(total=self.timeout_seconds)
                ) as response:
                    response_time = (datetime.now() - start_time).total_seconds()

                    if response.status == 200:
                        data = await response.json()

                        # Odoo health endpoint returns {"status": "pass"}
                        if data.get("status") == "pass":
                            return HealthCheck(
                                service_type=service_type,
                                status=HealthStatus.HEALTHY,
                                checked_at=datetime.now(),
                                response_time_seconds=response_time,
                                metadata={"url": health_url}
                            )
                        else:
                            return HealthCheck(
                                service_type=service_type,
                                status=HealthStatus.DEGRADED,
                                checked_at=datetime.now(),
                                response_time_seconds=response_time,
                                error_message=f"Unexpected status: {data.get('status')}",
                                metadata={"url": health_url, "response": data}
                            )
                    else:
                        return HealthCheck(
                            service_type=service_type,
                            status=HealthStatus.UNHEALTHY,
                            checked_at=datetime.now(),
                            response_time_seconds=response_time,
                            error_message=f"HTTP {response.status}",
                            metadata={"url": health_url}
                        )

        except asyncio.TimeoutError:
            return HealthCheck(
                service_type=service_type,
                status=HealthStatus.UNHEALTHY,
                checked_at=datetime.now(),
                error_message=f"Timeout after {self.timeout_seconds}s",
                metadata={"url": health_url}
            )
        except Exception as e:
            return HealthCheck(
                service_type=service_type,
                status=HealthStatus.UNHEALTHY,
                checked_at=datetime.now(),
                error_message=str(e),
                metadata={"url": health_url}
            )

    async def check_systemd_service(
        self,
        service_name: str,
        service_type: ServiceType
    ) -> HealthCheck:
        """
        Check if a systemd service is running.

        Args:
            service_name: Name of systemd service (e.g., "cloud-agent.service")
            service_type: Type of service for health check

        Returns:
            HealthCheck result
        """
        start_time = datetime.now()

        try:
            # Check service status using systemctl
            result = subprocess.run(
                ["systemctl", "is-active", service_name],
                capture_output=True,
                text=True,
                timeout=5
            )

            response_time = (datetime.now() - start_time).total_seconds()
            is_active = result.stdout.strip() == "active"

            if is_active:
                return HealthCheck(
                    service_type=service_type,
                    status=HealthStatus.HEALTHY,
                    checked_at=datetime.now(),
                    response_time_seconds=response_time,
                    metadata={"service_name": service_name}
                )
            else:
                return HealthCheck(
                    service_type=service_type,
                    status=HealthStatus.UNHEALTHY,
                    checked_at=datetime.now(),
                    response_time_seconds=response_time,
                    error_message=f"Service not active: {result.stdout.strip()}",
                    metadata={"service_name": service_name}
                )

        except subprocess.TimeoutExpired:
            return HealthCheck(
                service_type=service_type,
                status=HealthStatus.UNHEALTHY,
                checked_at=datetime.now(),
                error_message="systemctl command timeout",
                metadata={"service_name": service_name}
            )
        except Exception as e:
            return HealthCheck(
                service_type=service_type,
                status=HealthStatus.UNHEALTHY,
                checked_at=datetime.now(),
                error_message=str(e),
                metadata={"service_name": service_name}
            )

    async def check_api_connectivity(
        self,
        api_url: str,
        service_type: ServiceType,
        headers: Optional[Dict[str, str]] = None
    ) -> HealthCheck:
        """
        Check connectivity to an API endpoint.

        Args:
            api_url: API endpoint URL
            service_type: Type of service for health check
            headers: Optional HTTP headers (e.g., auth tokens)

        Returns:
            HealthCheck result
        """
        start_time = datetime.now()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    api_url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout_seconds)
                ) as response:
                    response_time = (datetime.now() - start_time).total_seconds()

                    # Accept any 2xx or 401 (auth required but endpoint reachable)
                    if 200 <= response.status < 300 or response.status == 401:
                        return HealthCheck(
                            service_type=service_type,
                            status=HealthStatus.HEALTHY,
                            checked_at=datetime.now(),
                            response_time_seconds=response_time,
                            metadata={"url": api_url, "status": response.status}
                        )
                    else:
                        return HealthCheck(
                            service_type=service_type,
                            status=HealthStatus.DEGRADED,
                            checked_at=datetime.now(),
                            response_time_seconds=response_time,
                            error_message=f"HTTP {response.status}",
                            metadata={"url": api_url}
                        )

        except asyncio.TimeoutError:
            return HealthCheck(
                service_type=service_type,
                status=HealthStatus.UNHEALTHY,
                checked_at=datetime.now(),
                error_message=f"Timeout after {self.timeout_seconds}s",
                metadata={"url": api_url}
            )
        except Exception as e:
            return HealthCheck(
                service_type=service_type,
                status=HealthStatus.UNHEALTHY,
                checked_at=datetime.now(),
                error_message=str(e),
                metadata={"url": api_url}
            )

    async def check_gmail_api(self, api_key: Optional[str] = None) -> HealthCheck:
        """
        Check Gmail API connectivity.

        Args:
            api_key: Optional API key for authenticated check

        Returns:
            HealthCheck result
        """
        # Gmail API endpoint for connectivity check
        api_url = "https://www.googleapis.com/gmail/v1/users/me/profile"
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else None

        return await self.check_api_connectivity(
            api_url=api_url,
            service_type=ServiceType.EMAIL_WATCHER,
            headers=headers
        )

    async def check_process_running(
        self,
        process_name: str,
        service_type: ServiceType
    ) -> HealthCheck:
        """
        Check if a process is running by name.

        Args:
            process_name: Name of process to check
            service_type: Type of service for health check

        Returns:
            HealthCheck result
        """
        start_time = datetime.now()

        try:
            # Use pgrep to check if process exists
            result = subprocess.run(
                ["pgrep", "-f", process_name],
                capture_output=True,
                text=True,
                timeout=5
            )

            response_time = (datetime.now() - start_time).total_seconds()
            is_running = result.returncode == 0

            if is_running:
                pid_count = len(result.stdout.strip().split('\n'))
                return HealthCheck(
                    service_type=service_type,
                    status=HealthStatus.HEALTHY,
                    checked_at=datetime.now(),
                    response_time_seconds=response_time,
                    metadata={"process_name": process_name, "pid_count": pid_count}
                )
            else:
                return HealthCheck(
                    service_type=service_type,
                    status=HealthStatus.UNHEALTHY,
                    checked_at=datetime.now(),
                    response_time_seconds=response_time,
                    error_message=f"Process not found: {process_name}",
                    metadata={"process_name": process_name}
                )

        except subprocess.TimeoutExpired:
            return HealthCheck(
                service_type=service_type,
                status=HealthStatus.UNHEALTHY,
                checked_at=datetime.now(),
                error_message="pgrep command timeout",
                metadata={"process_name": process_name}
            )
        except Exception as e:
            return HealthCheck(
                service_type=service_type,
                status=HealthStatus.UNHEALTHY,
                checked_at=datetime.now(),
                error_message=str(e),
                metadata={"process_name": process_name}
            )
