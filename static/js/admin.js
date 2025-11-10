document.addEventListener('DOMContentLoaded', function() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    const textInputs = document.querySelectorAll('input[type="text"]');
    const textareas = document.querySelectorAll('textarea');
    
    // File validation
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const fileSize = file.size / 1024 / 1024;
                if (fileSize > 5) {
                    alert('File size must be less than 5MB');
                    e.target.value = '';
                    return;
                }
                
                const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
                if (!allowedTypes.includes(file.type)) {
                    alert('Only image files (JPG, PNG, GIF, WebP) are allowed');
                    e.target.value = '';
                    return;
                }
            }
        });
    });
    
    // Text input validation
    textInputs.forEach(function(input) {
        input.addEventListener('input', function(e) {
            const value = e.target.value;
            const countElement = document.getElementById(input.id + '_count');
            const maxLength = 255;
            
            if (value.length > maxLength) {
                e.target.setCustomValidity(`Text must be ${maxLength} characters or less`);
                if (countElement) {
                    countElement.textContent = value.length + '/' + maxLength;
                    countElement.classList.add('warning');
                }
            } else {
                e.target.setCustomValidity('');
                if (countElement) {
                    countElement.textContent = value.length + '/' + maxLength;
                    countElement.classList.remove('warning');
                }
            }
        });
    });
    
    // Textarea validation
    textareas.forEach(function(textarea) {
        textarea.addEventListener('input', function(e) {
            const value = e.target.value;
            const countElement = document.getElementById(textarea.id + '_count');
            const maxLength = 5000;
            
            if (value.length > maxLength) {
                e.target.setCustomValidity(`Text must be ${maxLength} characters or less`);
                if (countElement) {
                    countElement.textContent = value.length + '/' + maxLength;
                    countElement.classList.add('warning');
                }
            } else {
                e.target.setCustomValidity('');
                if (countElement) {
                    countElement.textContent = value.length + '/' + maxLength;
                    countElement.classList.remove('warning');
                }
            }
        });
    });
    
    // Form submission validation
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            let isValid = true;
            const errorMessages = [];
            
            // Check required fields
            const requiredFields = form.querySelectorAll('[required]');
            requiredFields.forEach(function(field) {
                if (!field.value.trim()) {
                    isValid = false;
                    const label = field.previousElementSibling ? field.previousElementSibling.textContent : field.name;
                    errorMessages.push(`${label} is required`);
                }
            });
            
            // Check text length limits
            textInputs.forEach(function(input) {
                if (input.value.length > 255) {
                    isValid = false;
                    errorMessages.push('Text fields must be 255 characters or less');
                }
            });
            
            textareas.forEach(function(textarea) {
                if (textarea.value.length > 5000) {
                    isValid = false;
                    errorMessages.push('Text areas must be 5000 characters or less');
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                alert('Please fix the following errors:\n' + errorMessages.join('\n'));
            }
        });
    });
});