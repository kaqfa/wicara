"""
Site Management Forms - MULTI-03

Forms for creating and managing multiple sites.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, Regexp, ValidationError, Optional
import re


class CreateSiteForm(FlaskForm):
    """Form for creating a new site."""

    site_id = StringField(
        'Site ID',
        validators=[
            DataRequired(message='Site ID is required'),
            Length(min=3, max=50, message='Site ID must be 3-50 characters'),
            Regexp(
                r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$',
                message='Site ID must be lowercase alphanumeric with hyphens only'
            )
        ],
        render_kw={'placeholder': 'e.g., my-site, company-blog', 'class': 'form-control'}
    )

    sitename = StringField(
        'Site Name',
        validators=[
            DataRequired(message='Site name is required'),
            Length(min=1, max=100, message='Site name must be 1-100 characters')
        ],
        render_kw={'placeholder': 'e.g., My Company Website', 'class': 'form-control'}
    )

    description = TextAreaField(
        'Description',
        validators=[Optional(), Length(max=255, message='Description must be 255 characters or less')],
        render_kw={'placeholder': 'Brief description of the site', 'rows': 3, 'class': 'form-control'}
    )

    template_site = SelectField(
        'Clone from Template',
        choices=[],  # Will be populated dynamically
        validators=[DataRequired(message='Please select a template')],
        render_kw={'class': 'form-select'}
    )

    submit = SubmitField('Create Site', render_kw={'class': 'btn btn-primary'})

    def __init__(self, site_manager=None, *args, **kwargs):
        """Initialize form with available template sites."""
        super().__init__(*args, **kwargs)
        self.site_manager = site_manager

        if site_manager:
            # Get all existing sites to use as templates
            sites = site_manager.get_all_sites()
            self.template_site.choices = [
                (site_id, f"{site['name']} ({site_id})")
                for site_id in sites.keys()
            ]

    def validate_site_id(self, field):
        """Validate that site_id is unique."""
        if self.site_manager and self.site_manager.site_exists(field.data):
            raise ValidationError(f"Site '{field.data}' already exists")


class EditSiteForm(FlaskForm):
    """Form for editing site settings."""

    sitename = StringField(
        'Site Name',
        validators=[
            DataRequired(message='Site name is required'),
            Length(min=1, max=100, message='Site name must be 1-100 characters')
        ],
        render_kw={'placeholder': 'Site name', 'class': 'form-control'}
    )

    description = TextAreaField(
        'Description',
        validators=[Optional(), Length(max=255, message='Description must be 255 characters or less')],
        render_kw={'placeholder': 'Site description', 'rows': 3, 'class': 'form-control'}
    )

    keywords = StringField(
        'Keywords',
        validators=[Optional(), Length(max=255, message='Keywords must be 255 characters or less')],
        render_kw={
            'placeholder': 'Comma-separated keywords for SEO',
            'class': 'form-control'
        }
    )

    submit = SubmitField('Save Changes', render_kw={'class': 'btn btn-primary'})


class DomainForm(FlaskForm):
    """Form for adding domain mapping."""

    domain = StringField(
        'Domain Name',
        validators=[
            DataRequired(message='Domain is required'),
            Regexp(
                r'^([a-z0-9]([a-z0-9-]*[a-z0-9])?\.)+[a-z0-9]{2,}$',
                message='Please enter a valid domain (e.g., example.com)'
            )
        ],
        render_kw={
            'placeholder': 'e.g., example.com, subdomain.example.com',
            'class': 'form-control'
        }
    )

    submit = SubmitField('Add Domain', render_kw={'class': 'btn btn-success btn-sm'})

    def __init__(self, site_manager=None, site_id=None, *args, **kwargs):
        """Initialize form."""
        super().__init__(*args, **kwargs)
        self.site_manager = site_manager
        self.site_id = site_id

    def validate_domain(self, field):
        """Validate that domain is not already mapped to another site."""
        if self.site_manager:
            mapped_site = self.site_manager.get_site_by_domain(field.data)
            if mapped_site and mapped_site != self.site_id:
                raise ValidationError(
                    f"Domain '{field.data}' is already mapped to site '{mapped_site}'"
                )


class DeleteSiteForm(FlaskForm):
    """Form for deleting a site (confirmation)."""

    site_id = HiddenField('Site ID', validators=[DataRequired()])

    confirm = StringField(
        'Type site name to confirm deletion',
        validators=[DataRequired(message='Please confirm by typing the site name')],
        render_kw={'placeholder': 'Type site name exactly', 'class': 'form-control'}
    )

    submit = SubmitField('Delete Site', render_kw={'class': 'btn btn-danger'})

    def __init__(self, site_manager=None, site_id=None, *args, **kwargs):
        """Initialize form."""
        super().__init__(*args, **kwargs)
        self.site_manager = site_manager
        self.site_id = site_id
        self.expected_name = None

        if site_manager and site_id:
            site = site_manager.get_site(site_id)
            if site:
                self.expected_name = site['name']

    def validate_confirm(self, field):
        """Validate that user typed the correct site name."""
        if self.expected_name and field.data != self.expected_name:
            raise ValidationError(f"Please type '{self.expected_name}' exactly to confirm")


class BackupSiteForm(FlaskForm):
    """Form for site backup options."""

    backup_mode = SelectField(
        'Backup Type',
        choices=[
            ('full', 'Full Backup (config, templates, uploads)'),
            ('partial', 'Partial Backup (config & templates only)'),
            ('content', 'Content Only (config.json only)')
        ],
        validators=[DataRequired()],
        render_kw={'class': 'form-select'}
    )

    include_images = SelectField(
        'Include Images',
        choices=[
            ('yes', 'Yes, include all uploaded images'),
            ('no', 'No, only config and templates')
        ],
        validators=[DataRequired()],
        render_kw={'class': 'form-select'}
    )

    submit = SubmitField('Create Backup', render_kw={'class': 'btn btn-primary'})
