"""
Site Groups Manager - MULTI-05

Manages site groups, hierarchy, and group operations.
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

from .models import SiteGroup

logger = logging.getLogger(__name__)


class SiteGroupManager:
    """
    Manages site groups and organization.

    Features:
    - Create/delete groups
    - Nested group hierarchy
    - Assign sites to groups
    - Group-level operations
    - Bulk operations
    """

    def __init__(self, data_dir: str):
        """
        Initialize group manager.

        Args:
            data_dir: Directory to store group data
        """
        self.data_dir = data_dir
        self.groups_file = os.path.join(data_dir, '.groups.json')
        self.groups: Dict[str, SiteGroup] = {}
        self._load_groups()

    def create_group(self, group_id: str, name: str,
                    description: str = "",
                    parent_id: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Create a new site group.

        Args:
            group_id: Unique group identifier
            name: Group display name
            description: Optional description
            parent_id: Parent group for hierarchy (optional)

        Returns:
            Tuple of (success, error_message)
        """
        # Validate
        if group_id in self.groups:
            return False, f"Group '{group_id}' already exists"

        if parent_id and parent_id not in self.groups:
            return False, f"Parent group '{parent_id}' not found"

        # Create group
        try:
            group = SiteGroup(
                id=group_id,
                name=name,
                description=description,
                parent_id=parent_id
            )

            self.groups[group_id] = group
            self._save_groups()

            logger.info(f"Created group: {group_id}")
            return True, None

        except Exception as e:
            logger.error(f"Error creating group: {e}")
            return False, str(e)

    def delete_group(self, group_id: str, force: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Delete a group.

        Args:
            group_id: Group to delete
            force: Delete even if has sites/subgroups

        Returns:
            Tuple of (success, error_message)
        """
        if group_id not in self.groups:
            return False, f"Group '{group_id}' not found"

        group = self.groups[group_id]

        # Check for subgroups
        subgroups = [g for g in self.groups.values() if g.parent_id == group_id]
        if subgroups and not force:
            return False, f"Group has {len(subgroups)} subgroups. Use force=True to delete"

        # Check for sites
        if group.sites and not force:
            return False, f"Group has {len(group.sites)} sites. Move them first or use force=True"

        try:
            del self.groups[group_id]
            self._save_groups()

            logger.info(f"Deleted group: {group_id}")
            return True, None

        except Exception as e:
            logger.error(f"Error deleting group: {e}")
            return False, str(e)

    def add_site(self, group_id: str, site_id: str) -> bool:
        """Add site to group."""
        if group_id not in self.groups:
            return False

        group = self.groups[group_id]
        if site_id not in group.sites:
            group.sites.append(site_id)
            group.updated_at = datetime.now().isoformat()
            self._save_groups()

        return True

    def remove_site(self, group_id: str, site_id: str) -> bool:
        """Remove site from group."""
        if group_id not in self.groups:
            return False

        group = self.groups[group_id]
        if site_id in group.sites:
            group.sites.remove(site_id)
            group.updated_at = datetime.now().isoformat()
            self._save_groups()

        return True

    def get_group(self, group_id: str) -> Optional[SiteGroup]:
        """Get group by ID."""
        return self.groups.get(group_id)

    def get_all_groups(self) -> Dict[str, SiteGroup]:
        """Get all groups."""
        return self.groups.copy()

    def get_group_sites(self, group_id: str, recursive: bool = False) -> List[str]:
        """
        Get sites in group.

        Args:
            group_id: Group to get sites from
            recursive: Include sites from subgroups

        Returns:
            List of site IDs
        """
        group = self.get_group(group_id)
        if not group:
            return []

        sites = group.sites.copy()

        if recursive:
            # Add sites from subgroups
            for other_id, other_group in self.groups.items():
                if other_group.parent_id == group_id:
                    sites.extend(self.get_group_sites(other_id, recursive=True))

        return sites

    def get_site_group(self, site_id: str) -> Optional[str]:
        """Get group that contains site."""
        for group_id, group in self.groups.items():
            if site_id in group.sites:
                return group_id

        return None

    def get_subgroups(self, group_id: str) -> List[str]:
        """Get all subgroups of a group."""
        return [
            g_id for g_id, g in self.groups.items()
            if g.parent_id == group_id
        ]

    def get_group_hierarchy(self, group_id: str) -> Dict[str, any]:
        """Get group hierarchy tree."""
        group = self.get_group(group_id)
        if not group:
            return {}

        subgroups = self.get_subgroups(group_id)

        return {
            'id': group.id,
            'name': group.name,
            'sites': group.sites,
            'subgroups': [self.get_group_hierarchy(sg) for sg in subgroups]
        }

    def move_site(self, site_id: str, from_group: str, to_group: str) -> bool:
        """Move site between groups."""
        if not self.remove_site(from_group, site_id):
            return False

        return self.add_site(to_group, site_id)

    def bulk_create_groups(self, groups_data: List[Dict]) -> Tuple[int, List[str]]:
        """
        Create multiple groups at once.

        Args:
            groups_data: List of group data dicts

        Returns:
            Tuple of (created_count, errors)
        """
        created = 0
        errors = []

        for data in groups_data:
            try:
                success, error = self.create_group(
                    data['id'],
                    data['name'],
                    data.get('description', ''),
                    data.get('parent_id')
                )

                if success:
                    created += 1
                else:
                    errors.append(f"{data['id']}: {error}")

            except Exception as e:
                errors.append(f"{data['id']}: {str(e)}")

        logger.info(f"Bulk created {created} groups, {len(errors)} errors")
        return created, errors

    def get_stats(self) -> Dict[str, any]:
        """Get group statistics."""
        total_sites = sum(len(g.sites) for g in self.groups.values())
        max_depth = self._get_max_hierarchy_depth()

        return {
            'total_groups': len(self.groups),
            'total_sites': total_sites,
            'root_groups': len([g for g in self.groups.values() if g.parent_id is None]),
            'max_hierarchy_depth': max_depth
        }

    def _get_max_hierarchy_depth(self, group_id: str = None, current_depth: int = 0) -> int:
        """Get maximum hierarchy depth."""
        if group_id is None:
            # Start from root groups
            depths = []
            for g_id, g in self.groups.items():
                if g.parent_id is None:
                    depths.append(self._get_max_hierarchy_depth(g_id))
            return max(depths) if depths else 0

        # Recursively get depth
        subgroups = self.get_subgroups(group_id)
        if not subgroups:
            return current_depth

        return max(self._get_max_hierarchy_depth(sg, current_depth + 1) for sg in subgroups)

    def _load_groups(self):
        """Load groups from file."""
        try:
            if os.path.exists(self.groups_file):
                with open(self.groups_file, 'r') as f:
                    data = json.load(f)
                    self.groups = {
                        g_id: SiteGroup(**g_data)
                        for g_id, g_data in data.items()
                    }
                logger.debug(f"Loaded {len(self.groups)} groups")
            else:
                self.groups = {}
        except Exception as e:
            logger.error(f"Error loading groups: {e}")
            self.groups = {}

    def _save_groups(self):
        """Save groups to file."""
        try:
            data = {g_id: g.to_dict() for g_id, g in self.groups.items()}
            with open(self.groups_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved {len(self.groups)} groups")
        except Exception as e:
            logger.error(f"Error saving groups: {e}")

    def __repr__(self) -> str:
        return f"<SiteGroupManager: {len(self.groups)} groups>"
