class FilterForm {
    constructor() {
        this.filterForm = document.querySelector('form[method="get"]');
        this.searchInput = document.getElementById('search');
        this.doctorSelect = document.getElementById('doctor_id');
        this.statusSelect = document.getElementById('status');
        this.dateFromInput = document.getElementById('date_from');
        this.dateToInput = document.getElementById('date_to');

        this.init();
    }

    init() {
        if (!this.filterForm) {
            console.log('Filter form not found');
            return;
        }

        this.setupEventListeners();
        this.enhanceUI();
        this.setupKeyboardShortcuts();
        this.autoHideMessages();

        // اضافه کردن دکمه export اگر جدول وجود دارد
        if (document.querySelector('table')) {
            this.addExportButton();
        }
    }

    setupEventListeners() {
        // جستجو با debounce
        if (this.searchInput) {
            this.searchInput.addEventListener('input', this.debounce(() => {
                this.showLoading();
                this.filterForm.submit();
            }, 800));

            // پاک کردن جستجو با کلید Escape
            this.searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    this.searchInput.value = '';
                    this.showLoading();
                    this.filterForm.submit();
                }
            });

            this.searchInput.classList.add('search-input');
        }

        // تغییرات selectها (submit فوری)
        if (this.doctorSelect) {
            this.doctorSelect.addEventListener('change', () => this.immediateSubmit());
        }

        if (this.statusSelect) {
            this.statusSelect.addEventListener('change', () => this.immediateSubmit());
        }

        // اعتبارسنجی تاریخ‌ها
        if (this.dateFromInput) {
            this.dateFromInput.addEventListener('change', () => this.validateDateRange());
        }

        if (this.dateToInput) {
            this.dateToInput.addEventListener('change', () => this.validateDateRange());
        }
    }

    validateDateRange() {
        if (this.dateFromInput.value && this.dateToInput.value) {
            if (this.dateFromInput.value > this.dateToInput.value) {
                alert('تاریخ شروع نمی‌تواند از تاریخ پایان بزرگ‌تر باشد');
                this.dateFromInput.value = '';
                return false;
            }
        }
        this.immediateSubmit();
        return true;
    }

    immediateSubmit() {
        this.showLoading();
        this.filterForm.submit();
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    showLoading() {
        const submitBtn = this.filterForm.querySelector('button[type="submit"]');
        if (submitBtn) {
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mx-auto"></div>';
            submitBtn.disabled = true;

            // بازیابی دکمه بعد از 5 ثانیه (fallback)
            setTimeout(() => {
                if (submitBtn.disabled) {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }
            }, 5000);
        }

        this.filterForm.classList.add('loading');
    }

    enhanceUI() {
        // اضافه کردن کلاس به فرم
        this.filterForm.classList.add('filter-form');

        // اضافه کردن افکت hover به badgeها
        document.querySelectorAll('.px-2.inline-flex, .status-badge').forEach(badge => {
            badge.classList.add('enhanced-badge');
        });

        // بهبود responsiveness جدول
        const table = document.querySelector('table');
        if (table) {
            table.classList.add('table-responsive');

            // بهینه‌سازی برای موبایل
            if (window.innerWidth <= 768) {
                const cells = table.querySelectorAll('td, th');
                cells.forEach(cell => {
                    if (cell.textContent.length > 20) {
                        cell.title = cell.textContent;
                        cell.classList.add('truncate-mobile');
                    }
                });
            }
        }

        // اضافه کردن کلاس به grid آمار
        const statsGrid = document.querySelector('.grid.grid-cols-1.md\\:grid-cols-5, .stats-grid');
        if (statsGrid) {
            statsGrid.classList.add('enhanced-stats-grid');
        }
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + F برای فوکوس روی جستجو
            if ((e.ctrlKey || e.metaKey) && e.key === 'f' && this.searchInput) {
                e.preventDefault();
                this.searchInput.focus();
                this.searchInput.select();
            }

            // Escape برای پاک کردن جستجو
            if (e.key === 'Escape' && this.searchInput && document.activeElement === this.searchInput) {
                this.searchInput.value = '';
                this.showLoading();
                this.filterForm.submit();
            }
        });
    }

    autoHideMessages() {
        const messages = document.querySelectorAll('.bg-red-50, .bg-green-50, .bg-blue-50, .bg-yellow-50, .alert-message');
        messages.forEach(message => {
            setTimeout(() => {
                message.style.transition = 'opacity 0.5s ease';
                message.style.opacity = '0';
                setTimeout(() => {
                    if (message.parentNode) {
                        message.remove();
                    }
                }, 500);
            }, 5000);
        });
    }

    addExportButton() {
        const filterHeader = document.querySelector('.bg-white.rounded-lg.shadow-md .flex.items-center.justify-between, .filter-header');
        if (filterHeader && window.location.search) {
            // اگر دکمه export از قبل وجود دارد، اضافه نکن
            if (filterHeader.querySelector('.export-btn')) return;

            const exportBtn = document.createElement('a');
            exportBtn.className = 'export-btn inline-flex items-center px-3 py-1 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 transition-colors';
            exportBtn.href = window.location.pathname + window.location.search + '&export=csv';
            exportBtn.innerHTML = `
                <svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                </svg>
                خروجی اکسل
            `;
            filterHeader.appendChild(exportBtn);
        }
    }

    // متد برای reset فرم
    resetForm() {
        if (this.searchInput) this.searchInput.value = '';
        if (this.doctorSelect) this.doctorSelect.selectedIndex = 0;
        if (this.statusSelect) this.statusSelect.selectedIndex = 0;
        if (this.dateFromInput) this.dateFromInput.value = '';
        if (this.dateToInput) this.dateToInput.value = '';

        this.showLoading();
        this.filterForm.submit();
    }
}

// مقداردهی اولیه وقتی DOM آماده شد
document.addEventListener('DOMContentLoaded', function() {
    window.filterForm = new FilterForm();
});

// همچنین برای مواقعی که صفحه از قبل لود شده
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(() => {
        window.filterForm = new FilterForm();
    }, 100);
}