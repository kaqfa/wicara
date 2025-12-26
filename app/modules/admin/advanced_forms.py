"""
Advanced Admin Forms - MULTI-05

Forms for managing groups, activity, permissions, and quotas.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, Regexp


class CreateGroupForm(FlaskForm):
    """Form for creating a new site group."""
    group_id = StringField(
        'Group ID',
        validators=[
            DataRequired(),
            Length(3, 50),
            Regexp(r'^[a-z0-9-]+$', message='Only lowercase letters, numbers, and hyphens allowed')
        ]
    )
    name = StringField(
        'Group Name',
        validators=[DataRequired(), Length(1, 100)]
    )
    description = TextAreaField(
        'Description',
        validators=[Optional(), Length(0, 500)]
    )
    parent_group = SelectField(
        'Parent Group (optional)',
        choices=[],
        validators=[Optional()],
        coerce=str
    )
    submit = SubmitField('Create Group')


class EditGroupForm(FlaskForm):
    """Form for editing a site group."""
    name = StringField(
        'Group Name',
        validators=[DataRequired(), Length(1, 100)]
    )
    description = TextAreaField(
        'Description',
        validators=[Optional(), Length(0, 500)]
    )
    submit = SubmitField('Save Changes')


class SetQuotaForm(FlaskForm):
    """Form for setting resource quotas."""
    resource = SelectField(
        'Resource Type',
        choices=[
            ('storage', 'Storage (Bytes)'),
            ('bandwidth', 'Bandwidth (Bytes)'),
            ('api_calls', 'API Calls'),
            ('users', 'Users'),
            ('pages', 'Pages'),
        ],
        validators=[DataRequired()]
    )
    limit = IntegerField(
        'Limit',
        validators=[DataRequired(), NumberRange(min=0)]
    )
    soft_limit = BooleanField(
        'Soft Limit (allow exceeding temporarily)',
        default=False
    )
    submit = SubmitField('Set Quota')


class FilterActivityForm(FlaskForm):
    """Form for filtering activity logs."""
    event_type = SelectField(
        'Event Type',
        choices=[
            ('', '-- All Events --'),
            ('site.created', 'Site Created'),
            ('site.deleted', 'Site Deleted'),
            ('site.enabled', 'Site Enabled'),
            ('site.disabled', 'Site Disabled'),
            ('site.updated', 'Site Updated'),
            ('domain.added', 'Domain Added'),
            ('domain.removed', 'Domain Removed'),
            ('config.saved', 'Config Saved'),
            ('config.restored', 'Config Restored'),
            ('user.added', 'User Added'),
            ('user.removed', 'User Removed'),
            ('permission.changed', 'Permission Changed'),
            ('backup.created', 'Backup Created'),
            ('backup.restored', 'Backup Restored'),
            ('quota.exceeded', 'Quota Exceeded'),
            ('quota.updated', 'Quota Updated'),
            ('group.created', 'Group Created'),
            ('group.deleted', 'Group Deleted'),
        ],
        validators=[Optional()],
        coerce=str
    )
    user = StringField(
        'User (optional)',
        validators=[Optional()]
    )
    days = SelectField(
        'Time Period',
        choices=[
            ('1', 'Last 24 hours'),
            ('7', 'Last 7 days'),
            ('30', 'Last 30 days'),
            ('90', 'Last 90 days'),
        ],
        default='7',
        validators=[Optional()],
        coerce=str
    )
    submit = SubmitField('Filter')


class ExportActivityForm(FlaskForm):
    """Form for exporting activity logs."""
    format_type = SelectField(
        'Export Format',
        choices=[
            ('json', 'JSON'),
            ('csv', 'CSV'),
        ],
        validators=[DataRequired()]
    )
    event_type = SelectField(
        'Event Type Filter',
        choices=[
            ('', '-- All Events --'),
            ('site.created', 'Site Created'),
            ('site.deleted', 'Site Deleted'),
            ('site.enabled', 'Site Enabled'),
            ('site.disabled', 'Site Disabled'),
            ('site.updated', 'Site Updated'),
            ('domain.added', 'Domain Added'),
            ('domain.removed', 'Domain Removed'),
            ('config.saved', 'Config Saved'),
            ('config.restored', 'Config Restored'),
            ('user.added', 'User Added'),
            ('user.removed', 'User Removed'),
            ('permission.changed', 'Permission Changed'),
            ('backup.created', 'Backup Created'),
            ('backup.restored', 'Backup Restored'),
            ('quota.exceeded', 'Quota Exceeded'),
            ('quota.updated', 'Quota Updated'),
            ('group.created', 'Group Created'),
            ('group.deleted', 'Group Deleted'),
        ],
        validators=[Optional()],
        coerce=str
    )
    submit = SubmitField('Export')


class AssignUserForm(FlaskForm):
    """Form for assigning users to sites."""
    username = StringField(
        'Username',
        validators=[DataRequired()]
    )
    email = StringField(
        'Email',
        validators=[DataRequired()]
    )
    role = SelectField(
        'Role',
        choices=[
            ('admin', 'Admin'),
            ('owner', 'Owner'),
            ('developer', 'Developer'),
            ('editor', 'Editor'),
            ('viewer', 'Viewer'),
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField('Assign User')


class ChangeRoleForm(FlaskForm):
    """Form for changing user role."""
    role = SelectField(
        'New Role',
        choices=[
            ('admin', 'Admin'),
            ('owner', 'Owner'),
            ('developer', 'Developer'),
            ('editor', 'Editor'),
            ('viewer', 'Viewer'),
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField('Change Role')
