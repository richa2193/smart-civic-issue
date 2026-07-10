document.addEventListener("DOMContentLoaded", function() {
    
    // Auto-hide Django messages after 5 seconds using Bootstrap Toast logic if adapted, 
    // or just plain JS fade out for standard alerts.
    const alerts = document.querySelectorAll('.alert');
    if(alerts.length > 0) {
        setTimeout(() => {
            alerts.forEach(alert => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            });
        }, 5000);
    }

    // Loading Buttons
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.classList.add('btn-loading');
            }
        });
    });

    // Image Preview Feature for File Inputs
    const fileInputs = document.querySelectorAll('input[type="file"][accept="image/*"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                let previewContainer = this.nextElementSibling;
                
                // Create preview container if not exists
                if (!previewContainer || !previewContainer.classList.contains('image-preview-container')) {
                    previewContainer = document.createElement('div');
                    previewContainer.className = 'image-preview-container mt-2 mb-2 text-center';
                    this.parentNode.insertBefore(previewContainer, this.nextSibling);
                }
                
                reader.onload = function(e) {
                    previewContainer.innerHTML = `<img src="${e.target.result}" class="img-thumbnail shadow-sm" style="max-height: 200px; border-radius: 8px;">`;
                }
                
                reader.readAsDataURL(this.files[0]);
            }
        });
    });

    // Theme Toggle Logic
    const themeToggleBtn = document.getElementById('theme-toggle');
    const htmlElement = document.documentElement;
    
    // Check local storage for theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        htmlElement.setAttribute('data-bs-theme', savedTheme);
        updateThemeIcon(savedTheme);
    } else {
        // Default to light theme if no preference saved
        htmlElement.setAttribute('data-bs-theme', 'light');
    }

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const currentTheme = htmlElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            htmlElement.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);
        });
    }

    function updateThemeIcon(theme) {
        if (!themeToggleBtn) return;
        const icon = themeToggleBtn.querySelector('i');
        if (theme === 'dark') {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
        } else {
            icon.classList.remove('fa-sun');
            icon.classList.add('fa-moon');
        }
    }

});
