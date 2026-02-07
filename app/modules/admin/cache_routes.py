"""Cache management routes for admin panel.

Provides endpoints for viewing and managing cache statistics,
clearing caches, and cache warming.
"""

from flask import Blueprint, render_template, jsonify, request, redirect, url_for
import logging

cache_bp = Blueprint('cache', __name__, url_prefix='/admin/cache')
logger = logging.getLogger(__name__)

# Global cache service (will be injected by app factory)
_cache_service = None


def set_cache_service(cache_service):
    """Set the cache service instance.

    Args:
        cache_service: CacheService instance from app
    """
    global _cache_service
    _cache_service = cache_service


def require_cache_service(f):
    """Decorator to ensure cache service is available."""
    def decorated_function(*args, **kwargs):
        if _cache_service is None:
            return (
                jsonify(
                    {
                        'error': 'Cache service not configured',
                        'message': 'Cache management is not available',
                    }
                ),
                503,
            )
        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function


@cache_bp.route('/')
@cache_bp.route('/dashboard')
@require_cache_service
def cache_dashboard():
    """Display cache dashboard with statistics.

    Returns:
        Rendered cache dashboard template
    """
    try:
        stats = _cache_service.get_comprehensive_stats()
        return render_template('admin/cache_dashboard.html', stats=stats)
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        return (
            render_template(
                'admin/error.html',
                error='Failed to load cache dashboard',
                message=str(e),
            ),
            500,
        )


@cache_bp.route('/api/stats')
@require_cache_service
def get_stats():
    """Get cache statistics as JSON.

    Returns:
        JSON response with cache statistics
    """
    try:
        stats = _cache_service.get_comprehensive_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        return jsonify({'error': str(e)}), 500


@cache_bp.route('/clear', methods=['POST'])
@require_cache_service
def clear_cache():
    """Clear all caches.

    Returns:
        Redirect to dashboard or JSON response
    """
    try:
        cache_type = request.form.get('type', 'all')

        # Execute before_cache_clear hook
        try:
            from app.plugins import get_plugin_manager
            manager = get_plugin_manager()
            if manager:
                result = manager.hooks.execute('before_cache_clear', cache_type)
                # If hook returns a modified cache_type, use it
                if result is not None and isinstance(result, str):
                    cache_type = result
        except Exception as e:
            logger.debug(f'Plugin hook before_cache_clear error: {e}')

        if cache_type == 'all':
            success = _cache_service.clear_all()
            message = 'All caches cleared'
        elif cache_type == 'template':
            success = _cache_service.clear_template_cache()
            message = 'Template cache cleared'
        elif cache_type == 'response':
            success = _cache_service.clear_response_cache()
            message = 'Response cache cleared'
        elif cache_type == 'config':
            success = _cache_service.clear_config_cache()
            message = 'Config cache cleared'
        else:
            return jsonify({'error': 'Invalid cache type'}), 400

        # Execute after_cache_clear hook
        try:
            from app.plugins import get_plugin_manager
            manager = get_plugin_manager()
            if manager:
                manager.hooks.execute('after_cache_clear', cache_type)
        except Exception as e:
            logger.debug(f'Plugin hook after_cache_clear error: {e}')

        if success:
            logger.info(f"Cache cleared: {cache_type}")
            return redirect(url_for('cache.cache_dashboard'))
        else:
            return jsonify({'error': 'Failed to clear cache'}), 500
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return jsonify({'error': str(e)}), 500


@cache_bp.route('/api/clear', methods=['POST'])
@require_cache_service
def api_clear_cache():
    """Clear cache via API.

    Returns:
        JSON response with result
    """
    try:
        data = request.get_json() or {}
        cache_type = data.get('type', 'all')

        # Execute before_cache_clear hook
        try:
            from app.plugins import get_plugin_manager
            manager = get_plugin_manager()
            if manager:
                result = manager.hooks.execute('before_cache_clear', cache_type)
                # If hook returns a modified cache_type, use it
                if result is not None and isinstance(result, str):
                    cache_type = result
        except Exception as e:
            logger.debug(f'Plugin hook before_cache_clear error: {e}')

        if cache_type == 'all':
            success = _cache_service.clear_all()
            message = 'All caches cleared'
        elif cache_type == 'template':
            success = _cache_service.clear_template_cache()
            message = 'Template cache cleared'
        elif cache_type == 'response':
            success = _cache_service.clear_response_cache()
            message = 'Response cache cleared'
        elif cache_type == 'config':
            success = _cache_service.clear_config_cache()
            message = 'Config cache cleared'
        else:
            return jsonify({'error': 'Invalid cache type'}), 400

        # Execute after_cache_clear hook
        try:
            from app.plugins import get_plugin_manager
            manager = get_plugin_manager()
            if manager:
                manager.hooks.execute('after_cache_clear', cache_type)
        except Exception as e:
            logger.debug(f'Plugin hook after_cache_clear error: {e}')

        if success:
            logger.info(f"Cache cleared via API: {cache_type}")
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'error': 'Failed to clear cache'}), 500
    except Exception as e:
        logger.error(f"Error clearing cache via API: {str(e)}")
        return jsonify({'error': str(e)}), 500


@cache_bp.route('/warm', methods=['POST'])
@require_cache_service
def warm_cache():
    """Warm the cache.

    Returns:
        JSON response with warming results
    """
    try:
        if _cache_service.template_cache is None:
            return jsonify({'error': 'Template cache not enabled'}), 400

        results = _cache_service.template_cache.warm_cache()
        logger.info(f"Cache warmed: {results['successful']}/{results['total']} successful")
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error warming cache: {str(e)}")
        return jsonify({'error': str(e)}), 500


@cache_bp.route('/reset-stats', methods=['POST'])
@require_cache_service
def reset_stats():
    """Reset cache statistics.

    Returns:
        JSON response confirming reset
    """
    try:
        _cache_service.manager.reset_stats()
        logger.info("Cache statistics reset")
        return jsonify({'success': True, 'message': 'Statistics reset'})
    except Exception as e:
        logger.error(f"Error resetting stats: {str(e)}")
        return jsonify({'error': str(e)}), 500
