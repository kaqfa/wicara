"""
Error handlers for WICARA CMS.
Defines error pages and exception handling strategies.
"""

from flask import current_app, render_template, request, redirect, url_for, flash
from jinja2 import TemplateNotFound


def register_error_handlers(app):
    """
    Register error handlers with the Flask application.

    Args:
        app: Flask application instance
    """

    def render_error_template(status_code, template_candidates):
        for template_name in template_candidates:
            try:
                current_app.jinja_env.get_or_select_template(template_name)
                return render_template(template_name), status_code
            except TemplateNotFound:
                continue

        app.logger.error(
            "No error template found for status %s (tried: %s)",
            status_code,
            ", ".join(template_candidates),
        )
        return f"{status_code} Error", status_code

    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 Not Found errors."""
        app.logger.warning(f"404 error: {request.path}")
        if request.path.startswith("/admin"):
            return render_error_template(404, ["admin/404.html", "404.html"])
        else:
            return render_error_template(404, ["404.html"])

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors."""
        app.logger.error(f"500 error: {str(error)}")
        if request.path.startswith("/admin"):
            return render_error_template(500, ["admin/500.html", "500.html"])
        else:
            return render_error_template(500, ["500.html"])

    @app.errorhandler(413)
    def too_large(error):
        """Handle 413 Payload Too Large errors."""
        app.logger.warning(f"413 error - file too large: {request.path}")
        flash("File too large. Maximum size is 5MB.", "error")
        return redirect(request.referrer or url_for("public.index"))

    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 Forbidden errors."""
        app.logger.warning(f"403 error: {request.path}")
        if request.path.startswith("/admin"):
            return render_error_template(403, ["admin/404.html", "404.html"])
        else:
            return render_error_template(403, ["404.html"])

    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle 405 Method Not Allowed errors."""
        app.logger.warning(f"405 error: {request.method} {request.path}")
        if request.path.startswith("/admin"):
            return render_error_template(405, ["admin/404.html", "404.html"])
        else:
            return render_error_template(405, ["404.html"])
