class MessageForm {
    constructor(config) {
        this.config = config || {};
        this.init();
    }

    init() {
        this.setupDoctorSearch();
        this.setupTemplateSelect();
        this.setupFormStyling();
        this.setupGlobalEvents();
    }

    // ==================== جستجوی پزشک ====================
    setupDoctorSearch() {
        const searchInput = document.getElementById('doctor-search');
        const doctorOptions = document.querySelectorAll('.doctor-option');
        const recipientInput = document.getElementById('id_recipient');
        const selectedDoctorDiv = document.getElementById('selected-doctor');

        if (!searchInput || !recipientInput) {
            console.log('Doctor search elements not found');
            return;
        }

        // فیلتر کردن لیست پزشکان بر اساس جستجو
        searchInput.addEventListener('input', () => {
            const searchTerm = searchInput.value.toLowerCase();

            doctorOptions.forEach(option => {
                const doctorName = option.dataset.name.toLowerCase();
                const doctorSpec = option.dataset.specialization.toLowerCase();

                if (doctorName.includes(searchTerm) || doctorSpec.includes(searchTerm)) {
                    option.style.display = 'flex';
                } else {
                    option.style.display = 'none';
                }
            });
        });

        // انتخاب پزشک از لیست
        doctorOptions.forEach(option => {
            option.addEventListener('click', () => {
                const doctorId = option.dataset.id;
                const doctorName = option.dataset.name;
                const doctorSpec = option.dataset.specialization;
                const doctorImage = option.dataset.image || '';

                // ذخیره انتخاب
                recipientInput.value = doctorId;

                // نمایش پزشک انتخاب شده
                const selectedName = document.getElementById('selected-doctor-name');
                const selectedSpec = document.getElementById('selected-doctor-spec');
                const selectedImage = document.getElementById('selected-doctor-image');

                if (selectedName) selectedName.textContent = doctorName;
                if (selectedSpec) selectedSpec.textContent = doctorSpec;

                if (doctorImage && selectedImage) {
                    selectedImage.src = doctorImage;
                } else if (selectedImage) {
                    selectedImage.src = this.config.defaultDoctorImage || "{% static 'img/logo.png' %}";
                }

                if (selectedDoctorDiv) {
                    selectedDoctorDiv.classList.remove('hidden');
                }

                // پنهان کردن لیست جستجو بعد از انتخاب
                const searchResults = document.querySelector('.doctor-search-results');
                if (searchResults) {
                    searchResults.classList.add('hidden');
                }

                console.log('Doctor selected:', { id: doctorId, name: doctorName });
            });
        });

        // نمایش/پنهان کردن لیست جستجو
        searchInput.addEventListener('focus', () => {
            const searchResults = document.querySelector('.doctor-search-results');
            if (searchResults) {
                searchResults.classList.remove('hidden');
            }
        });

        // پنهان کردن لیست جستجو وقتی خارج می‌شویم
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.doctor-search-container')) {
                const searchResults = document.querySelector('.doctor-search-results');
                if (searchResults) {
                    searchResults.classList.add('hidden');
                }
            }
        });
    }

    // ==================== انتخاب تمپلیت ====================
    setupTemplateSelect() {
        const templateSelect = document.getElementById('templateSelect');

        if (!templateSelect) {
            console.log('Template select not found');
            return;
        }

        templateSelect.addEventListener('change', () => {
            const option = templateSelect.options[templateSelect.selectedIndex];
            const subjectInput = document.getElementById('id_subject');
            const bodyInput = document.getElementById('id_body');

            if (subjectInput && option.dataset.subject) {
                subjectInput.value = option.dataset.subject;
            }

            if (bodyInput && option.dataset.body) {
                bodyInput.value = option.dataset.body;
            }

            console.log('Template selected:', templateSelect.value);
        });
    }

    // ==================== استایل‌دهی فرم ====================
    setupFormStyling() {
        // اعمال استایل به فیلدهای فرم
        document.querySelectorAll('input, textarea, select').forEach(el => {
            if (!el.classList.contains('btn') && !el.type === 'checkbox' && !el.type === 'radio') {
                el.classList.add(
                    'w-full',
                    'px-3',
                    'py-2',
                    'border',
                    'border-gray-300',
                    'rounded-lg',
                    'focus:outline-none',
                    'focus:ring-2',
                    'focus:ring-blue-500',
                    'transition-colors',
                    'duration-200'
                );
            }
        });

        // استایل مخصوص textarea
        const textarea = document.querySelector('textarea');
        if (textarea) {
            textarea.classList.add('min-h-[200px]', 'resize-vertical');
        }

        // استایل مخصوص select
        const selects = document.querySelectorAll('select');
        selects.forEach(select => {
            select.classList.add('bg-white', 'cursor-pointer');
        });
    }

    // ==================== ایونت‌های سراسری ====================
    setupGlobalEvents() {
        // اعتبارسنجی فرم قبل از ارسال
        const form = document.querySelector('form');
        if (form) {
            form.addEventListener('submit', (e) => {
                if (!this.validateForm()) {
                    e.preventDefault();
                    this.showError('لطفاً تمام فیلدهای ضروری را پر کنید');
                }
            });
        }

        // کلیدهای میانبر
        document.addEventListener('keydown', (e) => {
            // Ctrl + Enter برای ارسال فرم
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                const submitBtn = form?.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.click();
                }
            }

            // Escape برای پاک کردن فرم
            if (e.key === 'Escape') {
                this.clearForm();
            }
        });
    }

    // ==================== متدهای کمکی ====================
    validateForm() {
        const recipient = document.getElementById('id_recipient')?.value;
        const subject = document.getElementById('id_subject')?.value;
        const body = document.getElementById('id_body')?.value;

        if (!recipient || !subject || !body) {
            return false;
        }

        return true;
    }

    clearForm() {
        const recipient = document.getElementById('id_recipient');
        const subject = document.getElementById('id_subject');
        const body = document.getElementById('id_body');
        const selectedDoctorDiv = document.getElementById('selected-doctor');

        if (recipient) recipient.value = '';
        if (subject) subject.value = '';
        if (body) body.value = '';
        if (selectedDoctorDiv) selectedDoctorDiv.classList.add('hidden');

        // بازنشانی انتخاب پزشک
        const searchInput = document.getElementById('doctor-search');
        if (searchInput) searchInput.value = '';

        // نمایش مجدد تمام پزشکان
        const doctorOptions = document.querySelectorAll('.doctor-option');
        doctorOptions.forEach(option => {
            option.style.display = 'flex';
        });

        console.log('Form cleared');
    }

    showError(message) {
        // ایجاد پیام خطا
        const errorDiv = document.createElement('div');
        errorDiv.className = 'fixed top-4 left-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg z-50 animate-fade-in';
        errorDiv.textContent = message;
        document.body.appendChild(errorDiv);

        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }

    showSuccess(message) {
        // ایجاد پیام موفقیت
        const successDiv = document.createElement('div');
        successDiv.className = 'fixed top-4 left-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg z-50 animate-fade-in';
        successDiv.textContent = message;
        document.body.appendChild(successDiv);

        setTimeout(() => {
            successDiv.remove();
        }, 5000);
    }

    // ==================== متدهای عمومی ====================
    selectDoctor(doctorId) {
        const doctorOption = document.querySelector(`.doctor-option[data-id="${doctorId}"]`);
        if (doctorOption) {
            doctorOption.click();
        }
    }

    loadTemplate(templateId) {
        const templateSelect = document.getElementById('templateSelect');
        if (templateSelect) {
            templateSelect.value = templateId;
            templateSelect.dispatchEvent(new Event('change'));
        }
    }

    getSelectedDoctor() {
        const recipient = document.getElementById('id_recipient')?.value;
        const selectedName = document.getElementById('selected-doctor-name')?.textContent;
        const selectedSpec = document.getElementById('selected-doctor-spec')?.textContent;

        return {
            id: recipient,
            name: selectedName,
            specialization: selectedSpec
        };
    }
}

// ==================== مقداردهی اولیه ====================
document.addEventListener('DOMContentLoaded', function() {
    window.messageForm = new MessageForm({
        defaultDoctorImage: "{% static 'img/logo.png' %}"
    });
});

// برای مواقعی که صفحه از قبل لود شده
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(() => {
        if (!window.messageForm) {
            window.messageForm = new MessageForm({
                defaultDoctorImage: "{% static 'img/logo.png' %}"
            });
        }
    }, 100);
}