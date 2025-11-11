"""
Admin forms validation for WICARA CMS.
Handles validation of admin panel forms.
"""


class SettingsForm:
    """Settings form validator."""

    @staticmethod
    def validate(data):
        """
        Validate settings form data.

        Args:
            data: Dictionary with form data

        Returns:
            Tuple of (is_valid, errors_list, validated_data)
        """
        errors = []
        validated_data = {}

        # Validate sitename
        sitename = data.get('sitename', '').strip()
        if not sitename:
            errors.append("Site name is required")
        elif len(sitename) > 100:
            errors.append("Site name must be 100 characters or less")
        else:
            validated_data['sitename'] = sitename

        # Validate description
        description = data.get('description', '').strip()
        if description and len(description) > 255:
            errors.append("Description must be 255 characters or less")
        else:
            validated_data['description'] = description

        # Validate keywords
        keywords_input = data.get('keywords', '').strip()
        if keywords_input:
            keywords = [kw.strip() for kw in keywords_input.split(',') if kw.strip()]
            validated_data['keywords'] = keywords
        else:
            validated_data['keywords'] = []

        # Validate footer content
        footer_lines = data.get('footer_content', [])
        footer_lines = [line.strip() for line in footer_lines if line.strip()]
        validated_data['footer'] = {'content': footer_lines}

        return len(errors) == 0, errors, validated_data


class PasswordChangeForm:
    """Password change form validator."""

    @staticmethod
    def validate(current_password_hash, new_password, confirm_password):
        """
        Validate password change form data.

        Args:
            current_password_hash: Hashed current password from config
            new_password: New password to set
            confirm_password: Confirmation of new password

        Returns:
            Tuple of (is_valid, errors_list)
        """
        errors = []

        # Validate new password
        if not new_password:
            errors.append('New password is required')
        elif len(new_password) < 8:
            errors.append('New password must be at least 8 characters long')
        elif not any(c.isupper() for c in new_password):
            errors.append('New password must contain at least one uppercase letter')
        elif not any(c.islower() for c in new_password):
            errors.append('New password must contain at least one lowercase letter')
        elif not any(c.isdigit() for c in new_password):
            errors.append('New password must contain at least one number')

        # Validate password confirmation
        if new_password != confirm_password:
            errors.append('Password confirmation does not match')

        return len(errors) == 0, errors
