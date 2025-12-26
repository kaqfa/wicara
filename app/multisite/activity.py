"""
Activity Logger - MULTI-05

Tracks all activities/events in the multi-site system for audit trails,
analytics, and compliance.
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from enum import Enum

from .models import ActivityEvent, EventType

logger = logging.getLogger(__name__)


class ActivityFilterType(Enum):
    """Filter types for activity queries."""
    BY_SITE = "site_id"
    BY_USER = "user_id"
    BY_EVENT = "event_type"
    BY_DATE_RANGE = "date_range"
    BY_RESOURCE = "resource_id"


class ActivityLogger:
    """
    Logs and manages activity events for audit trails.

    Features:
    - Event logging with user attribution
    - Search and filtering by multiple criteria
    - Export to CSV/JSON
    - Retention policies and cleanup
    - Statistics and analytics
    - Real-time event streaming capability
    """

    def __init__(self, data_dir: str):
        """
        Initialize activity logger.

        Args:
            data_dir: Directory to store activity logs
        """
        self.data_dir = data_dir
        self.activity_file = os.path.join(data_dir, '.activity.json')
        self.events: List[ActivityEvent] = []
        self.max_events = 10000  # Prevent unbounded growth
        self._load_events()

    def log_event(self, event_type: EventType, site_id: str,
                  user_id: Optional[str] = None,
                  resource_id: Optional[str] = None,
                  details: Optional[Dict] = None) -> bool:
        """
        Log an activity event.

        Args:
            event_type: Type of event
            site_id: Site where event occurred
            user_id: User who triggered event (optional)
            resource_id: Resource affected (optional)
            details: Additional event details (optional)

        Returns:
            Success status
        """
        try:
            event = ActivityEvent(
                event_type=event_type,
                site_id=site_id,
                user_id=user_id,
                resource_id=resource_id,
                details=details or {},
                timestamp=datetime.now().isoformat()
            )

            self.events.append(event)

            # Maintain size limit
            if len(self.events) > self.max_events:
                self.events = self.events[-self.max_events:]

            self._save_events()
            logger.debug(f"Logged event: {event_type.value} on {site_id}")
            return True

        except Exception as e:
            logger.error(f"Error logging event: {e}")
            return False

    def search_events(self, site_id: Optional[str] = None,
                      user_id: Optional[str] = None,
                      event_type: Optional[EventType] = None,
                      resource_id: Optional[str] = None,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None,
                      limit: int = 100) -> List[ActivityEvent]:
        """
        Search activity events with multiple filters.

        Args:
            site_id: Filter by site
            user_id: Filter by user
            event_type: Filter by event type
            resource_id: Filter by resource
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)
            limit: Maximum results to return

        Returns:
            List of matching events
        """
        results = self.events.copy()

        # Apply filters
        if site_id:
            results = [e for e in results if e.site_id == site_id]

        if user_id:
            results = [e for e in results if e.user_id == user_id]

        if event_type:
            results = [e for e in results if e.event_type == event_type]

        if resource_id:
            results = [e for e in results if e.resource_id == resource_id]

        # Date range filter
        if start_date:
            start = datetime.fromisoformat(start_date)
            results = [
                e for e in results
                if datetime.fromisoformat(e.timestamp) >= start
            ]

        if end_date:
            end = datetime.fromisoformat(end_date)
            results = [
                e for e in results
                if datetime.fromisoformat(e.timestamp) <= end
            ]

        # Sort by timestamp descending (newest first)
        results.sort(key=lambda e: e.timestamp, reverse=True)

        return results[:limit]

    def get_events_by_site(self, site_id: str, limit: int = 100) -> List[ActivityEvent]:
        """Get recent events for a site."""
        return self.search_events(site_id=site_id, limit=limit)

    def get_events_by_user(self, user_id: str, limit: int = 100) -> List[ActivityEvent]:
        """Get events triggered by a user."""
        return self.search_events(user_id=user_id, limit=limit)

    def get_events_by_type(self, event_type: EventType, limit: int = 100) -> List[ActivityEvent]:
        """Get events of a specific type."""
        return self.search_events(event_type=event_type, limit=limit)

    def get_site_timeline(self, site_id: str, days: int = 7) -> List[ActivityEvent]:
        """Get site activity timeline for the last N days."""
        end_date = datetime.now().isoformat()
        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        return self.search_events(
            site_id=site_id,
            start_date=start_date,
            end_date=end_date,
            limit=1000
        )

    def export_to_json(self, output_path: str,
                       site_id: Optional[str] = None,
                       user_id: Optional[str] = None,
                       event_type: Optional[EventType] = None) -> Tuple[bool, Optional[str]]:
        """
        Export activity events to JSON.

        Args:
            output_path: Path to write JSON file
            site_id: Optional site filter
            user_id: Optional user filter
            event_type: Optional event type filter

        Returns:
            Tuple of (success, error_message)
        """
        try:
            events = self.search_events(
                site_id=site_id,
                user_id=user_id,
                event_type=event_type,
                limit=10000
            )

            data = {
                'export_date': datetime.now().isoformat(),
                'filter': {
                    'site_id': site_id,
                    'user_id': user_id,
                    'event_type': event_type.value if event_type else None
                },
                'total_events': len(events),
                'events': [e.to_dict() for e in events]
            }

            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Exported {len(events)} events to {output_path}")
            return True, None

        except Exception as e:
            logger.error(f"Error exporting events: {e}")
            return False, str(e)

    def export_to_csv(self, output_path: str,
                      site_id: Optional[str] = None,
                      user_id: Optional[str] = None,
                      event_type: Optional[EventType] = None) -> Tuple[bool, Optional[str]]:
        """
        Export activity events to CSV.

        Args:
            output_path: Path to write CSV file
            site_id: Optional site filter
            user_id: Optional user filter
            event_type: Optional event type filter

        Returns:
            Tuple of (success, error_message)
        """
        try:
            events = self.search_events(
                site_id=site_id,
                user_id=user_id,
                event_type=event_type,
                limit=10000
            )

            # Write CSV header and data
            with open(output_path, 'w') as f:
                f.write("timestamp,site_id,user_id,event_type,resource_id,details\n")

                for event in events:
                    details = json.dumps(event.details).replace('"', '""')
                    line = f'"{event.timestamp}","{event.site_id}","{event.user_id or ""}","{event.event_type.value}","{event.resource_id or ""}","{details}"\n'
                    f.write(line)

            logger.info(f"Exported {len(events)} events to CSV: {output_path}")
            return True, None

        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False, str(e)

    def get_event_statistics(self, site_id: Optional[str] = None) -> Dict:
        """Get statistics about logged events."""
        events = self.events
        if site_id:
            events = [e for e in events if e.site_id == site_id]

        if not events:
            return {
                'total_events': 0,
                'unique_sites': 0,
                'unique_users': 0,
                'event_types': {},
                'date_range': None
            }

        # Count by event type
        event_type_counts = {}
        for event in events:
            key = event.event_type.value
            event_type_counts[key] = event_type_counts.get(key, 0) + 1

        # Collect unique sites and users
        unique_sites = len(set(e.site_id for e in events))
        unique_users = len(set(e.user_id for e in events if e.user_id))

        # Date range
        timestamps = [datetime.fromisoformat(e.timestamp) for e in events]
        date_range = {
            'oldest': min(timestamps).isoformat(),
            'newest': max(timestamps).isoformat()
        } if timestamps else None

        return {
            'total_events': len(events),
            'unique_sites': unique_sites,
            'unique_users': unique_users,
            'event_types': event_type_counts,
            'date_range': date_range
        }

    def cleanup_old_events(self, days: int = 90) -> int:
        """
        Delete events older than specified days.

        Args:
            days: Number of days to keep

        Returns:
            Number of events deleted
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        initial_count = len(self.events)

        self.events = [
            e for e in self.events
            if datetime.fromisoformat(e.timestamp) > cutoff_date
        ]

        deleted = initial_count - len(self.events)
        if deleted > 0:
            self._save_events()
            logger.info(f"Cleaned up {deleted} events older than {days} days")

        return deleted

    def clear_site_events(self, site_id: str) -> int:
        """
        Delete all events for a site (e.g., when site is deleted).

        Args:
            site_id: Site to clear events for

        Returns:
            Number of events deleted
        """
        initial_count = len(self.events)
        self.events = [e for e in self.events if e.site_id != site_id]
        deleted = initial_count - len(self.events)

        if deleted > 0:
            self._save_events()
            logger.info(f"Cleared {deleted} events for site: {site_id}")

        return deleted

    def _load_events(self):
        """Load events from file."""
        try:
            if os.path.exists(self.activity_file):
                with open(self.activity_file, 'r') as f:
                    data = json.load(f)
                    self.events = [
                        ActivityEvent(**event_data)
                        for event_data in data
                    ]
                logger.debug(f"Loaded {len(self.events)} activity events")
            else:
                self.events = []
        except Exception as e:
            logger.error(f"Error loading activity events: {e}")
            self.events = []

    def _save_events(self):
        """Save events to file."""
        try:
            data = [e.to_dict() for e in self.events]
            with open(self.activity_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved {len(self.events)} activity events")
        except Exception as e:
            logger.error(f"Error saving activity events: {e}")

    def __repr__(self) -> str:
        return f"<ActivityLogger: {len(self.events)} events>"
