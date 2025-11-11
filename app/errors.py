"""
Error handlers for WICARA CMS.
Defines error pages and exception handling strategies.
"""

from flask import render_template, request, redirect, url_for, flash


def register_error_handlers(app):
    """
    Register error handlers with the Flask application.

    Args:
        app: Flask application instance
    """

    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 Not Found errors."""
        app.logger.warning(f'404 error: {request.path}')
        if request.path.startswith('/admin'):
            return render_template('admin/404.html'), 404
        else:
            return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors."""
        app.logger.error(f'500 error: {str(error)}')
        if request.path.startswith('/admin'):
            return render_template('admin/500.html'), 500
        else:
            return render_template('500.html'), 500

    @app.errorhandler(413)
    def too_large(error):
        """Handle 413 Payload Too Large errors."""
        app.logger.warning(f'413 error - file too large: {request.path}')
        flash('File too large. Maximum size is 5MB.', 'error')
        return redirect(request.referrer or url_for('public.index'))

    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 Forbidden errors."""
        app.logger.warning(f'403 error: {request.path}')
        if request.path.startswith('/admin'):
            return render_template('admin/404.html'), 403
        else:
            return render_template('404.html'), 403

    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle 405 Method Not Allowed errors."""
        app.logger.warning(f'405 error: {request.method} {request.path}')
        if request.path.startswith('/admin'):
            return render_template('admin/404.html'), 405
        else:
            return render_template('404.html'), 405
