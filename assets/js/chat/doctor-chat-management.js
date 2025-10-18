class DoctorChatManagement {
    constructor(config) {
        this.toggleUrl = config.toggleUrl;
        this.csrfToken = config.csrfToken;
        this.init();
    }

    init() {
        this.setupAvailabilityToggle();
        this.setupRequestHandlers();
    }

    setupAvailabilityToggle() {
        const toggleBtn = document.getElementById('toggle-availability');
        if (!toggleBtn) {
            console.log('Toggle availability button not found');
            return;
        }

        toggleBtn.addEventListener('click', () => {
            fetch(this.toggleUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'Content-Type': 'application/json'
                },
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    this.updateAvailabilityUI(data.is_available);
                } else {
                    throw new Error(data.message || 'Unknown error');
                }
            })
            .catch(error => {
                console.error('Error toggling availability:', error);
                this.showToast('خطا در تغییر وضعیت', 'error');
            });
        });
    }

    updateAvailabilityUI(isAvailable) {
        const statusElement = document.getElementById('availability-status');
        const button = document.getElementById('toggle-availability');

        if (!statusElement || !button) return;

        if (isAvailable) {
            statusElement.innerHTML = '<span class="inline-flex items-center text-green-600"><span class="w-2 h-2 rounded-full bg-green-500 mr-1 m-l-2"></span> آنلاین</span>';
            button.textContent = 'تغییر به آفلاین';
            button.classList.remove('bg-green-50', 'text-green-800', 'hover:bg-green-100');
            button.classList.add('bg-red-50', 'text-red-800', 'hover:bg-red-100');
        } else {
            statusElement.innerHTML = '<span class="inline-flex items-center text-red-600"><span class="w-2 h-2 rounded-full bg-red-500 mr-1 m-l-2"></span> آفلاین</span>';
            button.textContent = 'تغییر به آنلاین';
            button.classList.remove('bg-red-50', 'text-red-800', 'hover:bg-red-100');
            button.classList.add('bg-green-50', 'text-green-800', 'hover:bg-green-100');
        }
    }

    setupRequestHandlers() {
        // اضافه کردن event listener به تمام دکمه‌های مدیریت درخواست
        document.addEventListener('click', (e) => {
            const button = e.target.closest('[data-request-action]');
            if (button) {
                const requestId = button.dataset.requestId;
                const action = button.dataset.requestAction;
                this.handleRequest(requestId, action);
            }
        });
    }

    handleRequest(requestId, action) {
        if (action === 'finished' && !confirm("آیا مطمئن هستید که می‌خواهید مکالمه را پایان دهید؟")) {
            return;
        }

        fetch(`/chat-visit/requests/${requestId}/${action}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.csrfToken,
                'Content-Type': 'application/json'
            },
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'approved') {
                window.location.href = `/chat-visit/room/${data.room_id}/`;
            } else if (data.status === 'rejected' || data.status === 'finished') {
                this.removeRequestElement(requestId);

                const message = action === 'finished' ? 'مکالمه با موفقیت پایان یافت' :
                              action === 'approve' ? 'درخواست با موفقیت تایید شد' :
                              'درخواست با موفقیت رد شد';

                this.showToast(message, 'success');
            }
        })
        .catch(error => {
            console.error("خطا در پردازش درخواست:", error);
            this.showToast('خطا در پردازش درخواست', 'error');
        });
    }

    removeRequestElement(requestId) {
        // پیدا کردن المان درخواست
        const selectors = [
            `[data-request-id="${requestId}"]`,
            `[onclick*="handleRequest(${requestId},"]`,
            `.border:has([onclick*="${requestId}"])`
        ];

        let requestElement = null;

        // روش ۱: جستجو با data attribute
        const elementWithData = document.querySelector(`[data-request-id="${requestId}"]`);
        if (elementWithData) {
            requestElement = elementWithData.closest('.border');
        }

        // روش ۲: جستجو با onclick قدیمی
        if (!requestElement) {
            const elementWithOnclick = document.querySelector(`[onclick*="handleRequest(${requestId},"]`);
            if (elementWithOnclick) {
                requestElement = elementWithOnclick.closest('.border');
            }
        }

        if (requestElement) {
            requestElement.style.opacity = '0';
            requestElement.style.transition = 'opacity 0.3s ease';
            setTimeout(() => {
                if (requestElement.parentNode) {
                    requestElement.remove();
                }
            }, 300);
        }
    }

    showToast(message, type) {
        // حذف toastهای قبلی
        const existingToasts = document.querySelectorAll('[data-toast]');
        existingToasts.forEach(toast => toast.remove());

        const toast = document.createElement('div');
        toast.setAttribute('data-toast', 'true');
        toast.className = `fixed top-4 left-1/2 transform -translate-x-1/2 px-6 py-3 rounded-lg shadow-lg text-white font-medium ${
            type === 'success' ? 'bg-green-500' : 'bg-red-500'
        } z-50 transition-opacity duration-300`;
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.remove();
                }
            }, 300);
        }, 3000);
    }
}

// مقداردهی اولیه
document.addEventListener('DOMContentLoaded', function() {
    if (window.doctorChatConfig) {
        window.doctorChatManager = new DoctorChatManagement(window.doctorChatConfig);
    } else {
        console.error('Doctor chat configuration not found');
    }
});