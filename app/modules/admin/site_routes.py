"""
Site Management Routes - MULTI-03

Admin interface for managing multiple sites.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, g
from app.modules.auth.utils import login_required
# TODO: Uncomment when multisite is integrated
# from app.multisite import get_site_manager
from .site_forms import CreateSiteForm, EditSiteForm, DomainForm, DeleteSiteForm, BackupSiteForm
import logging

logger = logging.getLogger(__name__)

# Create blueprint
site_bp = Blueprint('sites', __name__, url_prefix='/admin/sites')


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_site_manager():
    """Get site manager instance."""
    try:
        return get_site_manager()
    except Exception as e:
        logger.error(f"Failed to get site manager: {e}")
        return None


def _require_site_exists(site_id):
    """Decorator to check if site exists."""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            manager = _get_site_manager()
            if not manager or not manager.site_exists(site_id):
                flash(f"Site '{site_id}' not found", 'error')
                return redirect(url_for('sites.dashboard'))
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator


# ============================================================================
# DASHBOARD
# ============================================================================

@site_bp.route('/', methods=['GET'])
@require_auth
def dashboard():
    """Site management dashboard."""
    manager = _get_site_manager()

    if not manager:
        flash("Multi-site system not initialized", 'error')
        return redirect(url_for('admin.dashboard'))

    sites = manager.get_all_sites()
    stats = manager.get_stats()

    return render_template(
        'admin/sites/sites.html',
        sites=sites,
        stats=stats,
        total_sites=len(sites)
    )


# ============================================================================
# CREATE SITE
# ============================================================================

@site_bp.route('/create', methods=['GET', 'POST'])
@require_auth
def create():
    """Create new site."""
    manager = _get_site_manager()

    if not manager:
        flash("Multi-site system not initialized", 'error')
        return redirect(url_for('admin.dashboard'))

    form = CreateSiteForm(site_manager=manager)

    if form.validate_on_submit():
        try:
            # Create site
            success = manager.create_site(
                form.site_id.data,
                template_site=form.template_site.data
            )

            if success:
                # Update sitename in config
                from app.multisite.context import SiteContext
                context = SiteContext(manager)
                config = context.get_config(form.site_id.data)
                if config:
                    config['sitename'] = form.sitename.data
                    if form.description.data:
                        config['description'] = form.description.data
                    context.save_config(config, form.site_id.data)

                flash(f"Site '{form.site_id.data}' created successfully", 'success')
                return redirect(url_for('sites.edit', site_id=form.site_id.data))
            else:
                flash(f"Failed to create site '{form.site_id.data}'", 'error')

        except Exception as e:
            logger.error(f"Error creating site: {e}")
            flash(f"Error creating site: {str(e)}", 'error')

    return render_template('admin/sites/create.html', form=form)


# ============================================================================
# EDIT SITE
# ============================================================================

@site_bp.route('/<site_id>/edit', methods=['GET', 'POST'])
@require_auth
def edit(site_id):
    """Edit site settings."""
    manager = _get_site_manager()

    if not manager or not manager.site_exists(site_id):
        flash(f"Site '{site_id}' not found", 'error')
        return redirect(url_for('sites.dashboard'))

    from app.multisite.context import SiteContext
    context = SiteContext(manager)
    config = context.get_config(site_id)

    if not config:
        flash(f"Failed to load configuration for site '{site_id}'", 'error')
        return redirect(url_for('sites.dashboard'))

    form = EditSiteForm()

    if form.validate_on_submit():
        try:
            config['sitename'] = form.sitename.data
            config['description'] = form.description.data

            # Parse keywords
            if form.keywords.data:
                config['keywords'] = [k.strip() for k in form.keywords.data.split(',')]
            else:
                config['keywords'] = []

            context.save_config(config, site_id)
            flash('Site settings updated successfully', 'success')
            return redirect(url_for('sites.edit', site_id=site_id))

        except Exception as e:
            logger.error(f"Error saving site config: {e}")
            flash(f"Error saving settings: {str(e)}", 'error')

    elif request.method == 'GET':
        # Populate form with current values
        form.sitename.data = config.get('sitename', '')
        form.description.data = config.get('description', '')
        keywords = config.get('keywords', [])
        form.keywords.data = ', '.join(keywords) if keywords else ''

    site = manager.get_site(site_id)

    return render_template(
        'admin/sites/edit.html',
        form=form,
        site_id=site_id,
        site=site,
        config=config
    )


# ============================================================================
# DOMAIN MANAGEMENT
# ============================================================================

@site_bp.route('/<site_id>/domains', methods=['GET', 'POST'])
@require_auth
def domains(site_id):
    """Manage domain mappings."""
    manager = _get_site_manager()

    if not manager or not manager.site_exists(site_id):
        flash(f"Site '{site_id}' not found", 'error')
        return redirect(url_for('sites.dashboard'))

    site = manager.get_site(site_id)
    form = DomainForm(site_manager=manager, site_id=site_id)

    if form.validate_on_submit():
        try:
            manager.add_domain(site_id, form.domain.data.lower())
            flash(f"Domain '{form.domain.data}' added successfully", 'success')
            return redirect(url_for('sites.domains', site_id=site_id))
        except Exception as e:
            logger.error(f"Error adding domain: {e}")
            flash(f"Error adding domain: {str(e)}", 'error')

    return render_template(
        'admin/sites/domains.html',
        site_id=site_id,
        site=site,
        form=form
    )


@site_bp.route('/<site_id>/domains/<domain>', methods=['POST'])
@require_auth
def remove_domain(site_id, domain):
    """Remove domain mapping."""
    manager = _get_site_manager()

    if not manager or not manager.site_exists(site_id):
        return jsonify({'error': 'Site not found'}), 404

    try:
        manager.remove_domain(site_id, domain)
        flash(f"Domain '{domain}' removed successfully", 'success')
    except Exception as e:
        logger.error(f"Error removing domain: {e}")
        flash(f"Error removing domain: {str(e)}", 'error')

    return redirect(url_for('sites.domains', site_id=site_id))


# ============================================================================
# ENABLE/DISABLE SITE
# ============================================================================

@site_bp.route('/<site_id>/enable', methods=['POST'])
@require_auth
def enable_site(site_id):
    """Enable a site."""
    manager = _get_site_manager()

    if not manager or not manager.site_exists(site_id):
        return jsonify({'error': 'Site not found'}), 404

    try:
        manager.enable_site(site_id)
        flash(f"Site '{site_id}' enabled", 'success')
    except Exception as e:
        logger.error(f"Error enabling site: {e}")
        flash(f"Error enabling site: {str(e)}", 'error')

    return redirect(request.referrer or url_for('sites.dashboard'))


@site_bp.route('/<site_id>/disable', methods=['POST'])
@require_auth
def disable_site(site_id):
    """Disable a site."""
    manager = _get_site_manager()

    if not manager or not manager.site_exists(site_id):
        return jsonify({'error': 'Site not found'}), 404

    if site_id == 'default':
        flash("Cannot disable default site", 'error')
        return redirect(request.referrer or url_for('sites.dashboard'))

    try:
        manager.disable_site(site_id)
        flash(f"Site '{site_id}' disabled", 'success')
    except Exception as e:
        logger.error(f"Error disabling site: {e}")
        flash(f"Error disabling site: {str(e)}", 'error')

    return redirect(request.referrer or url_for('sites.dashboard'))


# ============================================================================
# DELETE SITE
# ============================================================================

@site_bp.route('/<site_id>/delete', methods=['GET', 'POST'])
@require_auth
def delete(site_id):
    """Delete a site."""
    manager = _get_site_manager()

    if not manager or not manager.site_exists(site_id):
        flash(f"Site '{site_id}' not found", 'error')
        return redirect(url_for('sites.dashboard'))

    if site_id == 'default':
        flash("Cannot delete default site", 'error')
        return redirect(url_for('sites.dashboard'))

    site = manager.get_site(site_id)
    form = DeleteSiteForm(site_manager=manager, site_id=site_id)

    if form.validate_on_submit():
        try:
            manager.delete_site(site_id)
            flash(f"Site '{site_id}' deleted successfully", 'success')
            return redirect(url_for('sites.dashboard'))
        except Exception as e:
            logger.error(f"Error deleting site: {e}")
            flash(f"Error deleting site: {str(e)}", 'error')

    return render_template(
        'admin/sites/delete.html',
        form=form,
        site_id=site_id,
        site=site
    )


# ============================================================================
# API ENDPOINTS (JSON)
# ============================================================================

@site_bp.route('/api/', methods=['GET'])
@require_auth
def api_sites():
    """Get all sites as JSON."""
    manager = _get_site_manager()

    if not manager:
        return jsonify({'error': 'Multi-site system not initialized'}), 500

    sites = manager.get_all_sites()
    stats = manager.get_stats()

    return jsonify({
        'success': True,
        'sites': sites,
        'stats': stats
    })


@site_bp.route('/api/<site_id>/', methods=['GET'])
@require_auth
def api_site(site_id):
    """Get specific site as JSON."""
    manager = _get_site_manager()

    if not manager or not manager.site_exists(site_id):
        return jsonify({'error': 'Site not found'}), 404

    site = manager.get_site(site_id)

    from app.multisite.context import SiteContext
    context = SiteContext(manager)
    config = context.get_config(site_id)

    return jsonify({
        'success': True,
        'site': site,
        'config': config
    })


@site_bp.route('/api/<site_id>/enable', methods=['POST'])
@require_auth
def api_enable(site_id):
    """API endpoint to enable site."""
    manager = _get_site_manager()

    if not manager or not manager.site_exists(site_id):
        return jsonify({'error': 'Site not found'}), 404

    try:
        manager.enable_site(site_id)
        return jsonify({'success': True, 'message': 'Site enabled'})
    except Exception as e:
        logger.error(f"Error enabling site: {e}")
        return jsonify({'error': str(e)}), 500


@site_bp.route('/api/<site_id>/disable', methods=['POST'])
@require_auth
def api_disable(site_id):
    """API endpoint to disable site."""
    manager = _get_site_manager()

    if not manager or not manager.site_exists(site_id):
        return jsonify({'error': 'Site not found'}), 404

    if site_id == 'default':
        return jsonify({'error': 'Cannot disable default site'}), 400

    try:
        manager.disable_site(site_id)
        return jsonify({'success': True, 'message': 'Site disabled'})
    except Exception as e:
        logger.error(f"Error disabling site: {e}")
        return jsonify({'error': str(e)}), 500


@site_bp.route('/api/validate-id', methods=['POST'])
@require_auth
def api_validate_id():
    """Validate unique site_id."""
    manager = _get_site_manager()
    site_id = request.get_json().get('site_id', '')

    if not manager:
        return jsonify({'valid': False, 'message': 'System not initialized'})

    exists = manager.site_exists(site_id)
    return jsonify({
        'valid': not exists,
        'message': f"Site '{site_id}' already exists" if exists else 'Site ID is available'
    })


# ============================================================================
# REGISTRATION
# ============================================================================

def register_site_routes(app):
    """Register site management blueprint with app."""
    app.register_blueprint(site_bp)
    logger.info("Site management routes registered")
