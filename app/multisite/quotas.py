"""
Quota Manager - MULTI-05

Manages quotas and limits for multi-site system with tracking,
enforcement, and alerting.
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

from .models import ResourceType, QuotaLimit, QuotaUsage

logger = logging.getLogger(__name__)


class QuotaManager:
    """
    Manages quotas and usage limits for sites.

    Features:
    - Define soft/hard quotas per resource
    - Track real-time usage
    - Warning thresholds and alerts
    - Usage reporting
    - Quota enforcement points
    - Reset cycles
    """

    def __init__(self, data_dir: str):
        """
        Initialize quota manager.

        Args:
            data_dir: Directory to store quota data
        """
        self.data_dir = data_dir
        self.quotas_file = os.path.join(data_dir, '.quotas.json')
        self.usage_file = os.path.join(data_dir, '.quota_usage.json')

        self.quotas: Dict[str, Dict[str, QuotaLimit]] = {}  # site_id -> {resource -> limit}
        self.usage: Dict[str, Dict[str, QuotaUsage]] = {}    # site_id -> {resource -> usage}

        self._load_quotas()
        self._load_usage()

    def set_quota(self, site_id: str, resource: ResourceType,
                  limit: int, soft_limit: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Set or update a quota for a site.

        Args:
            site_id: Site ID
            resource: Resource type
            limit: Limit value
            soft_limit: Allow exceeding temporarily

        Returns:
            Tuple of (success, error_message)
        """
        try:
            if site_id not in self.quotas:
                self.quotas[site_id] = {}

            quota = QuotaLimit(
                resource=resource,
                limit=limit,
                soft_limit=soft_limit
            )

            self.quotas[site_id][resource.value] = quota
            self._save_quotas()

            # Initialize usage if not present
            if site_id not in self.usage:
                self.usage[site_id] = {}

            if resource.value not in self.usage[site_id]:
                self.usage[site_id][resource.value] = QuotaUsage(
                    site_id=site_id,
                    resource=resource,
                    used=0,
                    limit=limit
                )

            self._save_usage()
            logger.info(f"Set quota for {site_id}/{resource.value}: {limit}")
            return True, None

        except Exception as e:
            logger.error(f"Error setting quota: {e}")
            return False, str(e)

    def get_quota(self, site_id: str, resource: ResourceType) -> Optional[QuotaLimit]:
        """Get quota limit for a site resource."""
        if site_id not in self.quotas:
            return None
        return self.quotas[site_id].get(resource.value)

    def get_quotas(self, site_id: str) -> Dict[str, QuotaLimit]:
        """Get all quotas for a site."""
        return self.quotas.get(site_id, {}).copy()

    def add_usage(self, site_id: str, resource: ResourceType,
                  amount: int) -> Tuple[bool, Optional[str]]:
        """
        Add usage to a quota.

        Args:
            site_id: Site ID
            resource: Resource type
            amount: Amount to add

        Returns:
            Tuple of (success, error_message)
        """
        try:
            if site_id not in self.usage:
                self.usage[site_id] = {}

            key = resource.value
            if key not in self.usage[site_id]:
                # Initialize usage if not present
                quota = self.get_quota(site_id, resource)
                limit = quota.limit if quota else 0
                self.usage[site_id][key] = QuotaUsage(
                    site_id=site_id,
                    resource=resource,
                    used=amount,
                    limit=limit
                )
            else:
                self.usage[site_id][key].used += amount
                self.usage[site_id][key].last_updated = datetime.now().isoformat()

            self._save_usage()
            logger.debug(f"Added {amount} to {site_id}/{key} (total: {self.usage[site_id][key].used})")
            return True, None

        except Exception as e:
            logger.error(f"Error adding usage: {e}")
            return False, str(e)

    def set_usage(self, site_id: str, resource: ResourceType,
                  amount: int) -> Tuple[bool, Optional[str]]:
        """
        Set usage directly (for recalculation).

        Args:
            site_id: Site ID
            resource: Resource type
            amount: Exact amount

        Returns:
            Tuple of (success, error_message)
        """
        try:
            if site_id not in self.usage:
                self.usage[site_id] = {}

            key = resource.value
            if key not in self.usage[site_id]:
                quota = self.get_quota(site_id, resource)
                limit = quota.limit if quota else 0
                self.usage[site_id][key] = QuotaUsage(
                    site_id=site_id,
                    resource=resource,
                    used=amount,
                    limit=limit
                )
            else:
                self.usage[site_id][key].used = amount
                self.usage[site_id][key].last_updated = datetime.now().isoformat()

            self._save_usage()
            return True, None

        except Exception as e:
            logger.error(f"Error setting usage: {e}")
            return False, str(e)

    def get_usage(self, site_id: str, resource: ResourceType) -> Optional[QuotaUsage]:
        """Get usage info for a resource."""
        if site_id not in self.usage:
            return None
        return self.usage[site_id].get(resource.value)

    def get_all_usage(self, site_id: str) -> Dict[str, QuotaUsage]:
        """Get all usage for a site."""
        return self.usage.get(site_id, {}).copy()

    def check_quota(self, site_id: str, resource: ResourceType,
                    requested_amount: int = 0) -> Tuple[bool, Optional[str]]:
        """
        Check if quota allows operation.

        Args:
            site_id: Site ID
            resource: Resource type
            requested_amount: Amount about to be added

        Returns:
            Tuple of (allowed, warning_message)
        """
        quota = self.get_quota(site_id, resource)
        usage = self.get_usage(site_id, resource)

        if not quota or not usage:
            return True, None

        # Check hard limit
        new_total = usage.used + requested_amount
        if new_total > quota.limit and not quota.soft_limit:
            return False, f"Quota exceeded: {resource.value}"

        # Check soft limit warning
        if new_total > quota.limit and quota.soft_limit:
            return True, f"Quota exceeded but soft limit enabled"

        # Check warning threshold
        if usage.is_warning:
            threshold_pct = int((quota.warning_threshold / quota.limit) * 100)
            return True, f"Usage at {int(usage.percentage)}% of quota"

        return True, None

    def can_perform_action(self, site_id: str, resource: ResourceType,
                          requested_amount: int = 0) -> bool:
        """
        Check if action is allowed based on quotas.

        Args:
            site_id: Site ID
            resource: Resource type
            requested_amount: Amount requested

        Returns:
            True if allowed
        """
        allowed, _ = self.check_quota(site_id, resource, requested_amount)
        return allowed

    def get_quota_status(self, site_id: str) -> Dict:
        """Get comprehensive quota status for a site."""
        quotas = self.get_quotas(site_id)
        usage_data = self.get_all_usage(site_id)

        status = {
            'site_id': site_id,
            'timestamp': datetime.now().isoformat(),
            'resources': {},
            'summary': {
                'total_resources': len(quotas),
                'exceeded': 0,
                'warning': 0,
                'ok': 0
            }
        }

        for resource_key, quota in quotas.items():
            resource = ResourceType(resource_key)
            usage = usage_data.get(resource_key)

            if usage:
                status['resources'][resource_key] = {
                    'quota_limit': quota.limit,
                    'soft_limit': quota.soft_limit,
                    'used': usage.used,
                    'remaining': usage.remaining,
                    'percentage': round(usage.percentage, 2),
                    'is_exceeded': usage.is_exceeded,
                    'is_warning': usage.is_warning,
                    'last_updated': usage.last_updated
                }

                # Update summary
                if usage.is_exceeded:
                    status['summary']['exceeded'] += 1
                elif usage.is_warning:
                    status['summary']['warning'] += 1
                else:
                    status['summary']['ok'] += 1

        return status

    def get_exceeded_quotas(self, site_id: str) -> List[Tuple[ResourceType, QuotaUsage]]:
        """Get resources that exceeded quota."""
        exceeded = []
        usage = self.get_all_usage(site_id)

        for resource_key, use in usage.items():
            if use.is_exceeded:
                exceeded.append((ResourceType(resource_key), use))

        return exceeded

    def get_warning_quotas(self, site_id: str) -> List[Tuple[ResourceType, QuotaUsage]]:
        """Get resources at warning threshold."""
        warnings = []
        usage = self.get_all_usage(site_id)

        for resource_key, use in usage.items():
            if use.is_warning and not use.is_exceeded:
                warnings.append((ResourceType(resource_key), use))

        return warnings

    def reset_quota_usage(self, site_id: str, resource: ResourceType) -> Tuple[bool, Optional[str]]:
        """
        Reset usage for a resource (e.g., monthly reset).

        Args:
            site_id: Site ID
            resource: Resource type

        Returns:
            Tuple of (success, error_message)
        """
        try:
            key = resource.value
            if site_id in self.usage and key in self.usage[site_id]:
                self.usage[site_id][key].used = 0
                self.usage[site_id][key].alerts_sent = []
                self.usage[site_id][key].last_updated = datetime.now().isoformat()
                self._save_usage()
                logger.info(f"Reset usage for {site_id}/{key}")
                return True, None
            return False, "No usage found"

        except Exception as e:
            logger.error(f"Error resetting usage: {e}")
            return False, str(e)

    def export_quota_report(self, output_path: str,
                           site_id: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Export quota status report to JSON.

        Args:
            output_path: Path to write report
            site_id: Optional specific site

        Returns:
            Tuple of (success, error_message)
        """
        try:
            report = {
                'export_date': datetime.now().isoformat(),
                'sites': {}
            }

            sites_to_report = [site_id] if site_id else list(self.quotas.keys())

            for site in sites_to_report:
                report['sites'][site] = self.get_quota_status(site)

            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)

            logger.info(f"Exported quota report to {output_path}")
            return True, None

        except Exception as e:
            logger.error(f"Error exporting quota report: {e}")
            return False, str(e)

    def cleanup_old_usage_records(self, days: int = 90) -> int:
        """
        Clean up old usage records (maintain last_updated tracking).

        Args:
            days: Keep records updated within last N days

        Returns:
            Number of records cleaned
        """
        cutoff = datetime.now() - timedelta(days=days)
        cleaned = 0

        for site_id in list(self.usage.keys()):
            for resource_key in list(self.usage[site_id].keys()):
                usage = self.usage[site_id][resource_key]
                last_update = datetime.fromisoformat(usage.last_updated)
                if last_update < cutoff:
                    # Reset old records
                    usage.used = 0
                    usage.alerts_sent = []
                    cleaned += 1

        if cleaned > 0:
            self._save_usage()
            logger.info(f"Cleaned up {cleaned} old usage records")

        return cleaned

    def _load_quotas(self):
        """Load quotas from file."""
        try:
            if os.path.exists(self.quotas_file):
                with open(self.quotas_file, 'r') as f:
                    data = json.load(f)
                    self.quotas = {
                        site_id: {
                            key: QuotaLimit(
                                resource=ResourceType(key),
                                limit=quota['limit'],
                                warning_threshold=quota.get('warning_threshold'),
                                soft_limit=quota.get('soft_limit', False)
                            )
                            for key, quota in quotas.items()
                        }
                        for site_id, quotas in data.items()
                    }
                logger.debug(f"Loaded quotas for {len(self.quotas)} sites")
            else:
                self.quotas = {}
        except Exception as e:
            logger.error(f"Error loading quotas: {e}")
            self.quotas = {}

    def _save_quotas(self):
        """Save quotas to file."""
        try:
            data = {
                site_id: {
                    key: quota.to_dict()
                    for key, quota in quotas.items()
                }
                for site_id, quotas in self.quotas.items()
            }
            with open(self.quotas_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved quotas for {len(self.quotas)} sites")
        except Exception as e:
            logger.error(f"Error saving quotas: {e}")

    def _load_usage(self):
        """Load usage from file."""
        try:
            if os.path.exists(self.usage_file):
                with open(self.usage_file, 'r') as f:
                    data = json.load(f)
                    self.usage = {
                        site_id: {
                            key: QuotaUsage(
                                site_id=site_id,
                                resource=ResourceType(key),
                                used=usage['used'],
                                limit=usage['limit'],
                                last_updated=usage.get('last_updated', datetime.now().isoformat()),
                                alerts_sent=usage.get('alerts_sent', [])
                            )
                            for key, usage in usages.items()
                        }
                        for site_id, usages in data.items()
                    }
                logger.debug(f"Loaded usage for {len(self.usage)} sites")
            else:
                self.usage = {}
        except Exception as e:
            logger.error(f"Error loading usage: {e}")
            self.usage = {}

    def _save_usage(self):
        """Save usage to file."""
        try:
            data = {
                site_id: {
                    key: usage.to_dict()
                    for key, usage in usages.items()
                }
                for site_id, usages in self.usage.items()
            }
            with open(self.usage_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved usage for {len(self.usage)} sites")
        except Exception as e:
            logger.error(f"Error saving usage: {e}")

    def __repr__(self) -> str:
        return f"<QuotaManager: {len(self.quotas)} sites with quotas>"
