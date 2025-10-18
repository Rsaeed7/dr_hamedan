document.addEventListener('DOMContentLoaded', function() {
    // File upload handling
    const fileInputs = document.querySelectorAll('input[type="file"]');

    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            const uploadArea = e.target.closest('.file-upload-area');
            const textElement = uploadArea.querySelector('p');

            if (file) {
                textElement.textContent = file.name;
                uploadArea.style.borderColor = '#10b981';
                uploadArea.style.backgroundColor = '#f0fdf4';
            } else {
                textElement.textContent = textElement.getAttribute('data-original-text') || 'فایل انتخاب کنید';
                uploadArea.style.borderColor = '#d1d5db';
                uploadArea.style.backgroundColor = 'transparent';
            }
        });

        // Store original text
        const uploadArea = input.closest('.file-upload-area');
        const textElement = uploadArea.querySelector('p');
        textElement.setAttribute('data-original-text', textElement.textContent);
    });
});