"""
Advanced Admin Routes - MULTI-05

Routes for managing groups, activity, permissions, and quotas.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from functools import wraps
import logging

from app.multisite import (
    get_group_manager, get_activity_logger,
    get_permission_manager, get_quota_manager
)
from app.multisite.models import EventType, ResourceType, UserRole

from .advanced_forms import (
    CreateGroupForm, EditGroupForm, SetQuotaForm,
    FilterActivityForm, ExportActivityForm, AssignUserForm, ChangeRoleForm
)

logger = logging.getLogger(__name__)

# Create blueprint
advanced_bp = Blueprint('advanced', __name__, url_prefix='/admin/advanced')


def require_auth(f):
    """Decorator to require admin authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # TODO: Implement proper session-based auth check
        # For now, assume authenticated
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# SITE GROUPS MANAGEMENT
# ============================================================================

@advanced_bp.route('/groups/', methods=['GET'])
@require_auth
def groups_dashboard():
    """Display site groups dashboard."""
    group_manager = get_group_manager()
    groups = group_manager.get_all_groups()
    stats = group_manager.get_stats()

    return render_template(
        'admin/advanced/groups.html',
        groups=groups,
        stats=stats
    )


@advanced_bp.route('/groups/create', methods=['GET', 'POST'])
@require_auth
def create_group():
    """Create a new site group."""
    form = CreateGroupForm()
    group_manager = get_group_manager()

    # Populate parent group choices
    all_groups = group_manager.get_all_groups()
    form.parent_group.choices = [('', '-- None --')] + [
        (g_id, g.name) for g_id, g in all_groups.items()
    ]

    if form.validate_on_submit():
        success, error = group_manager.create_group(
            group_id=form.group_id.data,
            name=form.name.data,
            description=form.description.data,
            parent_id=form.parent_group.data or None
        )

        if success:
            flash(f'Group "{form.name.data}" created successfully', 'success')
            return redirect(url_for('advanced.groups_dashboard'))
        else:
            flash(f'Error creating group: {error}', 'danger')

    return render_template('admin/advanced/create_group.html', form=form)


@advanced_bp.route('/groups/<group_id>/edit', methods=['GET', 'POST'])
@require_auth
def edit_group(group_id):
    """Edit a site group."""
    group_manager = get_group_manager()
    group = group_manager.get_group(group_id)

    if not group:
        flash('Group not found', 'danger')
        return redirect(url_for('advanced.groups_dashboard'))

    form = EditGroupForm()

    if form.validate_on_submit():
        # Update group (note: in real implementation, update manager methods)
        group.name = form.name.data
        group.description = form.description.data

        flash('Group updated successfully', 'success')
        return redirect(url_for('advanced.groups_dashboard'))

    elif request.method == 'GET':
        form.name.data = group.name
        form.description.data = group.description

    # Get group sites
    sites = group_manager.get_group_sites(group_id, recursive=False)
    subgroups = group_manager.get_subgroups(group_id)

    return render_template(
        'admin/advanced/edit_group.html',
        form=form,
        group=group,
        sites=sites,
        subgroups=subgroups
    )


@advanced_bp.route('/groups/<group_id>/delete', methods=['POST'])
@require_auth
def delete_group(group_id):
    """Delete a site group."""
    group_manager = get_group_manager()
    force = request.form.get('force') == 'true'

    success, error = group_manager.delete_group(group_id, force=force)

    if success:
        flash('Group deleted successfully', 'success')
    else:
        flash(f'Error deleting group: {error}', 'danger')

    return redirect(url_for('advanced.groups_dashboard'))


# ============================================================================
# ACTIVITY LOGS
# ============================================================================

@advanced_bp.route('/activity/', methods=['GET', 'POST'])
@require_auth
def activity_logs():
    """Display activity logs with filtering."""
    activity_logger = get_activity_logger()
    form = FilterActivityForm()

    events = []
    if form.validate_on_submit() or request.method == 'GET':
        event_type = None
        if form.event_type.data:
            event_type = EventType(form.event_type.data)

        events = activity_logger.search_events(
            event_type=event_type,
            user_id=form.user.data or None,
            limit=500
        )

    stats = activity_logger.get_event_statistics()

    return render_template(
        'admin/advanced/activity.html',
        form=form,
        events=events,
        stats=stats
    )


@advanced_bp.route('/activity/export', methods=['GET', 'POST'])
@require_auth
def export_activity():
    """Export activity logs."""
    form = ExportActivityForm()
    activity_logger = get_activity_logger()

    if form.validate_on_submit():
        event_type = None
        if form.event_type.data:
            event_type = EventType(form.event_type.data)

        # Generate filename
        import time
        timestamp = time.strftime('%Y%m%d_%H%M%S')

        if form.format_type.data == 'json':
            output_path = f'/tmp/activity_export_{timestamp}.json'
            success, error = activity_logger.export_to_json(
                output_path,
                event_type=event_type
            )
            filename = f'activity_export_{timestamp}.json'
        else:  # csv
            output_path = f'/tmp/activity_export_{timestamp}.csv'
            success, error = activity_logger.export_to_csv(
                output_path,
                event_type=event_type
            )
            filename = f'activity_export_{timestamp}.csv'

        if success:
            flash(f'Activity logs exported successfully', 'success')
            return redirect(url_for('advanced.activity_logs'))
        else:
            flash(f'Error exporting: {error}', 'danger')

    return render_template('admin/advanced/export_activity.html', form=form)


# ============================================================================
# QUOTAS MANAGEMENT
# ============================================================================

@advanced_bp.route('/quotas/', methods=['GET'])
@require_auth
def quotas_dashboard():
    """Display quotas dashboard for all sites."""
    quota_manager = get_quota_manager()
    from app.multisite import get_site_manager
    site_manager = get_site_manager()

    sites = site_manager.get_all_sites()
    quota_status = {}

    for site_id in sites:
        quota_status[site_id] = quota_manager.get_quota_status(site_id)

    return render_template(
        'admin/advanced/quotas.html',
        sites=sites,
        quota_status=quota_status
    )


@advanced_bp.route('/quotas/<site_id>', methods=['GET', 'POST'])
@require_auth
def manage_quotas(site_id):
    """Manage quotas for a specific site."""
    quota_manager = get_quota_manager()
    form = SetQuotaForm()

    if form.validate_on_submit():
        resource = ResourceType(form.resource.data)
        success, error = quota_manager.set_quota(
            site_id=site_id,
            resource=resource,
            limit=form.limit.data,
            soft_limit=form.soft_limit.data
        )

        if success:
            flash(f'Quota for {resource.value} set successfully', 'success')
        else:
            flash(f'Error setting quota: {error}', 'danger')

    quotas = quota_manager.get_quotas(site_id)
    usage = quota_manager.get_all_usage(site_id)
    status = quota_manager.get_quota_status(site_id)

    return render_template(
        'admin/advanced/manage_quotas.html',
        site_id=site_id,
        form=form,
        quotas=quotas,
        usage=usage,
        status=status
    )


@advanced_bp.route('/quotas/<site_id>/reset', methods=['POST'])
@require_auth
def reset_quota(site_id):
    """Reset quota usage for a site."""
    quota_manager = get_quota_manager()
    resource_value = request.form.get('resource')

    if not resource_value:
        flash('No resource specified', 'danger')
        return redirect(url_for('advanced.manage_quotas', site_id=site_id))

    resource = ResourceType(resource_value)
    success, error = quota_manager.reset_quota_usage(site_id, resource)

    if success:
        flash(f'Quota for {resource.value} reset successfully', 'success')
    else:
        flash(f'Error resetting quota: {error}', 'danger')

    return redirect(url_for('advanced.manage_quotas', site_id=site_id))


# ============================================================================
# PERMISSIONS & USERS
# ============================================================================

@advanced_bp.route('/permissions/<site_id>', methods=['GET', 'POST'])
@require_auth
def manage_permissions(site_id):
    """Manage users and permissions for a site."""
    permission_manager = get_permission_manager()
    form = AssignUserForm()

    if form.validate_on_submit():
        role = UserRole[form.role.data.upper()]
        success, error = permission_manager.add_user_to_site(
            site_id=site_id,
            user_id=form.username.data,  # In real app, would be numeric ID
            username=form.username.data,
            email=form.email.data,
            role=role
        )

        if success:
            flash(f'User {form.username.data} assigned successfully', 'success')
        else:
            flash(f'Error assigning user: {error}', 'danger')

    users = permission_manager.get_site_users(site_id)

    return render_template(
        'admin/advanced/permissions.html',
        site_id=site_id,
        form=form,
        users=users
    )


@advanced_bp.route('/permissions/<site_id>/users/<user_id>/role', methods=['POST'])
@require_auth
def change_user_role(site_id, user_id):
    """Change user role for a site."""
    form = ChangeRoleForm()
    permission_manager = get_permission_manager()

    if form.validate_on_submit():
        role = UserRole[form.role.data.upper()]
        success, error = permission_manager.change_user_role(site_id, user_id, role)

        if success:
            flash('User role updated successfully', 'success')
        else:
            flash(f'Error changing role: {error}', 'danger')

    return redirect(url_for('advanced.manage_permissions', site_id=site_id))


@advanced_bp.route('/permissions/<site_id>/users/<user_id>/remove', methods=['POST'])
@require_auth
def remove_user(site_id, user_id):
    """Remove user from a site."""
    permission_manager = get_permission_manager()
    success, error = permission_manager.remove_user_from_site(site_id, user_id)

    if success:
        flash('User removed successfully', 'success')
    else:
        flash(f'Error removing user: {error}', 'danger')

    return redirect(url_for('advanced.manage_permissions', site_id=site_id))


# ============================================================================
# JSON APIs
# ============================================================================

@advanced_bp.route('/api/groups', methods=['GET'])
def api_groups():
    """JSON API for groups."""
    group_manager = get_group_manager()
    groups = {g_id: g.to_dict() for g_id, g in group_manager.get_all_groups().items()}
    return jsonify(groups)


@advanced_bp.route('/api/activity', methods=['GET'])
def api_activity():
    """JSON API for activity logs."""
    activity_logger = get_activity_logger()
    site_id = request.args.get('site_id')
    limit = int(request.args.get('limit', 100))

    events = activity_logger.search_events(site_id=site_id, limit=limit)
    return jsonify([e.to_dict() for e in events])


@advanced_bp.route('/api/quotas/<site_id>', methods=['GET'])
def api_quotas(site_id):
    """JSON API for quotas."""
    quota_manager = get_quota_manager()
    status = quota_manager.get_quota_status(site_id)
    return jsonify(status)


@advanced_bp.route('/api/permissions/<site_id>', methods=['GET'])
def api_permissions(site_id):
    """JSON API for site users and permissions."""
    permission_manager = get_permission_manager()
    users = permission_manager.get_site_users(site_id)

    return jsonify({
        'site_id': site_id,
        'users': [
            {
                'user_id': u.user_id,
                'username': u.username,
                'email': u.email,
                'role': u.role.value,
                'created_at': u.created_at
            }
            for u in users
        ]
    })


def init_advanced_routes(app):
    """Register advanced routes blueprint with app."""
    app.register_blueprint(advanced_bp)
