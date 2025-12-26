"""
Permission Manager - MULTI-05

Manages role-based access control (RBAC) for multi-site system
with fine-grained permissions.
"""

import json
import os
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
import logging

from .models import UserRole, Permission, Role, SiteUser

logger = logging.getLogger(__name__)


# Define all available permissions in the system
PERMISSION_CATEGORIES = {
    'admin': [
        'manage.sites',
        'manage.users',
        'manage.roles',
        'manage.quotas',
        'view.activity',
        'system.settings',
    ],
    'content': [
        'create.page',
        'edit.page',
        'delete.page',
        'publish.page',
        'upload.images',
        'delete.images',
    ],
    'settings': [
        'edit.siteinfo',
        'edit.metadata',
        'manage.domains',
        'edit.theme',
        'manage.templates',
    ],
    'users': [
        'add.user',
        'remove.user',
        'change.role',
        'change.permissions',
    ],
    'quotas': [
        'view.quotas',
        'edit.quotas',
        'view.usage',
    ],
    'backup': [
        'create.backup',
        'restore.backup',
        'export.site',
        'import.site',
    ],
}

# Predefined permission sets for each role
ROLE_PERMISSIONS = {
    UserRole.ADMIN: {
        'admin': PERMISSION_CATEGORIES['admin'],
        'content': PERMISSION_CATEGORIES['content'],
        'settings': PERMISSION_CATEGORIES['settings'],
        'users': PERMISSION_CATEGORIES['users'],
        'quotas': PERMISSION_CATEGORIES['quotas'],
        'backup': PERMISSION_CATEGORIES['backup'],
    },
    UserRole.OWNER: {
        'admin': ['manage.sites', 'manage.users'],
        'content': PERMISSION_CATEGORIES['content'],
        'settings': PERMISSION_CATEGORIES['settings'],
        'users': PERMISSION_CATEGORIES['users'],
        'quotas': ['view.quotas'],
        'backup': PERMISSION_CATEGORIES['backup'],
    },
    UserRole.DEVELOPER: {
        'content': PERMISSION_CATEGORIES['content'],
        'settings': ['manage.templates', 'manage.domains', 'edit.metadata'],
        'quotas': ['view.quotas', 'view.usage'],
        'backup': ['create.backup', 'export.site'],
    },
    UserRole.EDITOR: {
        'content': PERMISSION_CATEGORIES['content'],
        'quotas': ['view.usage'],
    },
    UserRole.VIEWER: {
        'content': ['view.page'],  # Implicit read-only
        'quotas': ['view.usage'],
    },
}


class PermissionManager:
    """
    Manages permissions and roles for multi-site access control.

    Features:
    - Predefined roles with permission sets
    - Custom role creation
    - Fine-grained permission checking
    - User-role assignment
    - Site-level user management
    - Audit logging of permission changes
    """

    def __init__(self, data_dir: str):
        """
        Initialize permission manager.

        Args:
            data_dir: Directory to store permission data
        """
        self.data_dir = data_dir
        self.roles_file = os.path.join(data_dir, '.roles.json')
        self.users_file = os.path.join(data_dir, '.site_users.json')

        self.roles: Dict[str, Role] = {}
        self.site_users: Dict[str, List[SiteUser]] = {}  # site_id -> [SiteUser]

        self._load_roles()
        self._load_users()
        self._initialize_default_roles()

    def create_role(self, role_name: str, description: str = "",
                    permissions: Optional[List[str]] = None) -> Tuple[bool, Optional[str]]:
        """
        Create a custom role.

        Args:
            role_name: Unique role name
            description: Role description
            permissions: List of permission names

        Returns:
            Tuple of (success, error_message)
        """
        # Check if role already exists
        if role_name in self.roles:
            return False, f"Role '{role_name}' already exists"

        # Validate permissions
        if permissions:
            for perm in permissions:
                if not self._is_valid_permission(perm):
                    return False, f"Invalid permission: {perm}"

        try:
            role = Role(
                name=role_name,
                description=description,
                permissions=permissions or [],
                is_custom=True
            )

            self.roles[role_name] = role
            self._save_roles()

            logger.info(f"Created custom role: {role_name}")
            return True, None

        except Exception as e:
            logger.error(f"Error creating role: {e}")
            return False, str(e)

    def delete_role(self, role_name: str) -> Tuple[bool, Optional[str]]:
        """
        Delete a custom role.

        Args:
            role_name: Role to delete

        Returns:
            Tuple of (success, error_message)
        """
        # Prevent deletion of built-in roles
        try:
            UserRole[role_name.upper()]
            return False, "Cannot delete built-in roles"
        except KeyError:
            pass

        if role_name not in self.roles:
            return False, f"Role '{role_name}' not found"

        if not self.roles[role_name].is_custom:
            return False, "Cannot delete built-in roles"

        try:
            del self.roles[role_name]
            self._save_roles()
            logger.info(f"Deleted role: {role_name}")
            return True, None

        except Exception as e:
            logger.error(f"Error deleting role: {e}")
            return False, str(e)

    def add_user_to_site(self, site_id: str, user_id: str, username: str,
                         email: str, role: UserRole,
                         permissions: Optional[List[str]] = None) -> Tuple[bool, Optional[str]]:
        """
        Add a user to a site with a specific role.

        Args:
            site_id: Site ID
            user_id: User ID
            username: Username
            email: User email
            role: User role
            permissions: Additional custom permissions (optional)

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Initialize site users list if needed
            if site_id not in self.site_users:
                self.site_users[site_id] = []

            # Check if user already exists
            existing = [u for u in self.site_users[site_id] if u.user_id == user_id]
            if existing:
                return False, f"User already added to this site"

            # Get role permissions
            role_perms = self._get_role_permissions(role)
            user_perms = list(set(role_perms + (permissions or [])))

            user = SiteUser(
                user_id=user_id,
                username=username,
                email=email,
                role=role,
                permissions=user_perms
            )

            self.site_users[site_id].append(user)
            self._save_users()

            logger.info(f"Added user {username} to site {site_id} with role {role.value}")
            return True, None

        except Exception as e:
            logger.error(f"Error adding user to site: {e}")
            return False, str(e)

    def remove_user_from_site(self, site_id: str, user_id: str) -> Tuple[bool, Optional[str]]:
        """
        Remove a user from a site.

        Args:
            site_id: Site ID
            user_id: User ID to remove

        Returns:
            Tuple of (success, error_message)
        """
        try:
            if site_id not in self.site_users:
                return False, f"Site '{site_id}' has no users"

            initial_count = len(self.site_users[site_id])
            self.site_users[site_id] = [
                u for u in self.site_users[site_id] if u.user_id != user_id
            ]

            if len(self.site_users[site_id]) == initial_count:
                return False, f"User not found in site"

            self._save_users()
            logger.info(f"Removed user {user_id} from site {site_id}")
            return True, None

        except Exception as e:
            logger.error(f"Error removing user from site: {e}")
            return False, str(e)

    def change_user_role(self, site_id: str, user_id: str,
                         new_role: UserRole) -> Tuple[bool, Optional[str]]:
        """
        Change a user's role for a site.

        Args:
            site_id: Site ID
            user_id: User ID
            new_role: New role to assign

        Returns:
            Tuple of (success, error_message)
        """
        try:
            if site_id not in self.site_users:
                return False, f"Site '{site_id}' not found"

            # Find user
            user = None
            for u in self.site_users[site_id]:
                if u.user_id == user_id:
                    user = u
                    break

            if not user:
                return False, f"User '{user_id}' not found in site"

            # Update role and permissions
            old_role = user.role
            user.role = new_role
            user.permissions = self._get_role_permissions(new_role)

            self._save_users()
            logger.info(f"Changed role for user {user_id}: {old_role.value} -> {new_role.value}")
            return True, None

        except Exception as e:
            logger.error(f"Error changing user role: {e}")
            return False, str(e)

    def check_permission(self, site_id: str, user_id: str,
                        permission: str) -> bool:
        """
        Check if a user has a specific permission on a site.

        Args:
            site_id: Site ID
            user_id: User ID
            permission: Permission name

        Returns:
            True if user has permission
        """
        if site_id not in self.site_users:
            return False

        for user in self.site_users[site_id]:
            if user.user_id == user_id:
                return permission in user.permissions

        return False

    def check_permissions(self, site_id: str, user_id: str,
                         permissions: List[str]) -> bool:
        """
        Check if user has ALL specified permissions.

        Args:
            site_id: Site ID
            user_id: User ID
            permissions: List of permission names

        Returns:
            True if user has all permissions
        """
        for perm in permissions:
            if not self.check_permission(site_id, user_id, perm):
                return False
        return True

    def check_any_permission(self, site_id: str, user_id: str,
                            permissions: List[str]) -> bool:
        """
        Check if user has ANY of the specified permissions.

        Args:
            site_id: Site ID
            user_id: User ID
            permissions: List of permission names

        Returns:
            True if user has any permission
        """
        for perm in permissions:
            if self.check_permission(site_id, user_id, perm):
                return True
        return False

    def get_user_role(self, site_id: str, user_id: str) -> Optional[UserRole]:
        """Get user's role for a site."""
        if site_id not in self.site_users:
            return None

        for user in self.site_users[site_id]:
            if user.user_id == user_id:
                return user.role

        return None

    def get_user_permissions(self, site_id: str, user_id: str) -> List[str]:
        """Get user's permissions for a site."""
        if site_id not in self.site_users:
            return []

        for user in self.site_users[site_id]:
            if user.user_id == user_id:
                return user.permissions.copy()

        return []

    def get_site_users(self, site_id: str) -> List[SiteUser]:
        """Get all users for a site."""
        return self.site_users.get(site_id, []).copy()

    def get_user_sites(self, user_id: str) -> List[str]:
        """Get all sites a user has access to."""
        sites = []
        for site_id, users in self.site_users.items():
            for user in users:
                if user.user_id == user_id:
                    sites.append(site_id)
                    break
        return sites

    def get_role_permissions(self, role: UserRole) -> List[str]:
        """Get all permissions for a role."""
        return self._get_role_permissions(role)

    def export_permissions_report(self, output_path: str) -> Tuple[bool, Optional[str]]:
        """
        Export permissions report to JSON.

        Args:
            output_path: Path to write report

        Returns:
            Tuple of (success, error_message)
        """
        try:
            report = {
                'export_date': datetime.now().isoformat(),
                'roles': {
                    name: {
                        'description': role.description,
                        'is_custom': role.is_custom,
                        'permissions': role.permissions
                    }
                    for name, role in self.roles.items()
                },
                'site_users': {
                    site_id: [
                        {
                            'user_id': user.user_id,
                            'username': user.username,
                            'email': user.email,
                            'role': user.role.value,
                            'permissions': user.permissions,
                            'created_at': user.created_at
                        }
                        for user in users
                    ]
                    for site_id, users in self.site_users.items()
                }
            }

            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)

            logger.info(f"Exported permissions report to {output_path}")
            return True, None

        except Exception as e:
            logger.error(f"Error exporting permissions: {e}")
            return False, str(e)

    def _get_role_permissions(self, role: UserRole) -> List[str]:
        """Get flat list of permissions for a role."""
        perms = []
        role_perms = ROLE_PERMISSIONS.get(role)

        if role_perms:
            for category_perms in role_perms.values():
                perms.extend(category_perms)

        return list(set(perms))

    def _is_valid_permission(self, permission: str) -> bool:
        """Check if permission string is valid."""
        for category_perms in PERMISSION_CATEGORIES.values():
            if permission in category_perms:
                return True
        return False

    def _initialize_default_roles(self):
        """Initialize built-in roles if not present."""
        for role_enum in UserRole:
            if role_enum.name not in self.roles:
                perms = self._get_role_permissions(role_enum)
                self.roles[role_enum.name] = Role(
                    name=role_enum.name,
                    description=f"Built-in {role_enum.name.lower()} role",
                    permissions=perms,
                    is_custom=False
                )
        self._save_roles()

    def _load_roles(self):
        """Load roles from file."""
        try:
            if os.path.exists(self.roles_file):
                with open(self.roles_file, 'r') as f:
                    data = json.load(f)
                    self.roles = {
                        name: Role(**role_data)
                        for name, role_data in data.items()
                    }
                logger.debug(f"Loaded {len(self.roles)} roles")
            else:
                self.roles = {}
        except Exception as e:
            logger.error(f"Error loading roles: {e}")
            self.roles = {}

    def _save_roles(self):
        """Save roles to file."""
        try:
            data = {name: role.to_dict() for name, role in self.roles.items()}
            with open(self.roles_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved {len(self.roles)} roles")
        except Exception as e:
            logger.error(f"Error saving roles: {e}")

    def _load_users(self):
        """Load site users from file."""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r') as f:
                    data = json.load(f)
                    self.site_users = {
                        site_id: [
                            SiteUser(
                                user_id=u['user_id'],
                                username=u['username'],
                                email=u['email'],
                                role=UserRole(u['role']),
                                permissions=u['permissions'],
                                created_at=u['created_at'],
                                last_accessed=u.get('last_accessed')
                            )
                            for u in users
                        ]
                        for site_id, users in data.items()
                    }
                logger.debug(f"Loaded site users for {len(self.site_users)} sites")
            else:
                self.site_users = {}
        except Exception as e:
            logger.error(f"Error loading site users: {e}")
            self.site_users = {}

    def _save_users(self):
        """Save site users to file."""
        try:
            data = {
                site_id: [u.to_dict() for u in users]
                for site_id, users in self.site_users.items()
            }
            with open(self.users_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved users for {len(self.site_users)} sites")
        except Exception as e:
            logger.error(f"Error saving site users: {e}")

    def __repr__(self) -> str:
        total_users = sum(len(users) for users in self.site_users.values())
        return f"<PermissionManager: {len(self.roles)} roles, {total_users} site users>"
