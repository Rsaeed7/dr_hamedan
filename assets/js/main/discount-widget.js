class DiscountWidget {
    constructor(config) {
        this.config = config || {};
        this.reservationId = null;
        this.currentDiscount = null;
        this.init();
    }

    init() {
        this.reservationId = this.config.reservationId ||
                           document.querySelector('[data-reservation-id]')?.dataset.reservationId;

        if (this.reservationId) {
            this.bindEvents();
            this.loadAvailableDiscounts();
        } else {
            console.warn('DiscountWidget: Reservation ID not found');
        }
    }

    bindEvents() {
        // Apply coupon code
        const applyBtn = document.getElementById('apply-coupon-btn');
        if (applyBtn) {
            applyBtn.addEventListener('click', () => {
                this.applyCouponCode();
            });
        }

        // Check automatic discounts
        const checkAutoBtn = document.getElementById('check-automatic-btn');
        if (checkAutoBtn) {
            checkAutoBtn.addEventListener('click', () => {
                this.checkAutomaticDiscounts();
            });
        }

        // Remove discount
        const removeBtn = document.getElementById('remove-discount-btn');
        if (removeBtn) {
            removeBtn.addEventListener('click', () => {
                this.removeDiscount();
            });
        }

        // Enter key on coupon input
        const couponInput = document.getElementById('coupon-code');
        if (couponInput) {
            couponInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.applyCouponCode();
                }
            });
        }
    }

    applyCouponCode() {
        const couponCode = document.getElementById('coupon-code')?.value.trim();
        if (!couponCode) {
            this.showMessage('coupon-message', 'کد تخفیف را وارد کنید', 'error');
            return;
        }

        this.setLoading('apply-coupon-btn', true);

        fetch(this.config.applyCouponUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({
                coupon_code: couponCode,
                reservation_id: this.reservationId
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                this.showCurrentDiscount({
                    title: 'کد تخفیف اعمال شد',
                    description: data.message,
                    original_amount: data.original_amount,
                    discount_amount: data.discount_amount,
                    final_amount: data.final_amount
                });
                this.showMessage('coupon-message', data.message, 'success');
                document.getElementById('coupon-code').value = '';
                this.hideDiscountSections();
            } else {
                this.showMessage('coupon-message', data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Error applying coupon:', error);
            this.showMessage('coupon-message', 'خطا در اعمال کد تخفیف', 'error');
        })
        .finally(() => {
            this.setLoading('apply-coupon-btn', false);
        });
    }

    checkAutomaticDiscounts() {
        this.setLoading('check-automatic-btn', true);

        fetch(this.config.checkAutomaticUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({
                reservation_id: this.reservationId
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                this.showCurrentDiscount({
                    title: data.discount_title,
                    description: data.message,
                    original_amount: data.original_amount,
                    discount_amount: data.discount_amount,
                    final_amount: data.final_amount
                });
                this.showMessage('automatic-message', data.message, 'success');
                this.hideDiscountSections();
            } else {
                this.showMessage('automatic-message', data.message, 'info');
            }
        })
        .catch(error => {
            console.error('Error checking automatic discounts:', error);
            this.showMessage('automatic-message', 'خطا در بررسی تخفیفات خودکار', 'error');
        })
        .finally(() => {
            this.setLoading('check-automatic-btn', false);
        });
    }

    removeDiscount() {
        fetch(this.config.removeDiscountUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({
                reservation_id: this.reservationId
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                this.hideCurrentDiscount();
                this.showDiscountSections();
                this.showMessage('coupon-message', data.message, 'success');
                // Update amount display if exists
                this.updateAmountDisplay(data.original_amount);
            }
        })
        .catch(error => {
            console.error('Error removing discount:', error);
            this.showMessage('coupon-message', 'خطا در حذف تخفیف', 'error');
        });
    }

    loadAvailableDiscounts() {
        fetch(`${this.config.getAvailableUrl}?reservation_id=${this.reservationId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.discounts.length > 0) {
                this.displayAvailableDiscounts(data.discounts);
            }
        })
        .catch(error => {
            console.error('Error loading available discounts:', error);
        });
    }

    displayAvailableDiscounts(discounts) {
        const container = document.getElementById('discounts-list');
        const section = document.getElementById('available-discounts');

        if (!container || !section) return;

        container.innerHTML = '';

        discounts.forEach(discount => {
            const discountEl = document.createElement('div');
            discountEl.className = 'p-3 border border-gray-200 rounded-md hover:bg-gray-50 cursor-pointer';
            discountEl.innerHTML = `
                <div class="flex justify-between items-center">
                    <div>
                        <h5 class="text-sm font-medium text-gray-900">${discount.title}</h5>
                        <p class="text-xs text-gray-600">${discount.description}</p>
                        <p class="text-xs text-green-600 mt-1">تخفیف: ${this.formatAmount(discount.discount_amount)} تومان</p>
                    </div>
                    <span class="text-xs text-gray-500">${discount.discount_type}</span>
                </div>
            `;

            container.appendChild(discountEl);
        });

        section.classList.remove('hidden');
    }

    showCurrentDiscount(discount) {
        const currentDiscountEl = document.getElementById('current-discount');
        if (!currentDiscountEl) return;

        document.getElementById('discount-title').textContent = discount.title;
        document.getElementById('discount-description').textContent = discount.description;
        document.getElementById('original-amount').textContent = this.formatAmount(discount.original_amount) + ' تومان';
        document.getElementById('discount-amount').textContent = this.formatAmount(discount.discount_amount) + ' تومان';
        document.getElementById('final-amount').textContent = this.formatAmount(discount.final_amount) + ' تومان';

        currentDiscountEl.classList.remove('hidden');
        this.currentDiscount = discount;

        // Update amount display if exists
        this.updateAmountDisplay(discount.final_amount);
    }

    hideCurrentDiscount() {
        const currentDiscountEl = document.getElementById('current-discount');
        if (currentDiscountEl) {
            currentDiscountEl.classList.add('hidden');
        }
        this.currentDiscount = null;
    }

    hideDiscountSections() {
        this.toggleSection('coupon-section', true);
        this.toggleSection('check-automatic-btn', true, 'parentElement');
        this.toggleSection('available-discounts', true);
    }

    showDiscountSections() {
        this.toggleSection('coupon-section', false);
        this.toggleSection('check-automatic-btn', false, 'parentElement');
        this.toggleSection('available-discounts', false);
    }

    toggleSection(elementId, hide, target = 'self') {
        const element = document.getElementById(elementId);
        if (!element) return;

        let targetElement = element;
        if (target === 'parentElement' && element.parentElement) {
            targetElement = element.parentElement;
        }

        if (hide) {
            targetElement.classList.add('hidden');
        } else {
            targetElement.classList.remove('hidden');
        }
    }

    updateAmountDisplay(amount) {
        // Update any amount display elements on the page
        const amountElements = document.querySelectorAll('[data-amount-display]');
        amountElements.forEach(el => {
            el.textContent = this.formatAmount(amount) + ' تومان';
        });
    }

    showMessage(elementId, message, type) {
        const element = document.getElementById(elementId);
        if (!element) return;

        element.textContent = message;
        element.className = `mt-2 text-sm ${this.getMessageClass(type)}`;
        element.classList.remove('hidden');

        // Auto hide after 5 seconds
        setTimeout(() => {
            element.classList.add('hidden');
        }, 5000);
    }

    getMessageClass(type) {
        switch(type) {
            case 'success': return 'text-green-600';
            case 'error': return 'text-red-600';
            case 'info': return 'text-blue-600';
            default: return 'text-gray-600';
        }
    }

    setLoading(buttonId, loading) {
        const button = document.getElementById(buttonId);
        if (!button) return;

        const text = button.querySelector('.btn-text');
        const spinner = button.querySelector('.btn-loading');

        if (loading) {
            if (text) text.classList.add('hidden');
            if (spinner) spinner.classList.remove('hidden');
            button.disabled = true;
        } else {
            if (text) text.classList.remove('hidden');
            if (spinner) spinner.classList.add('hidden');
            button.disabled = false;
        }
    }

    formatAmount(amount) {
        return parseInt(amount).toLocaleString('fa-IR');
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
               this.config.csrfToken;
    }

    // متدهای عمومی برای استفاده خارجی
    applyDiscount(couponCode) {
        if (couponCode) {
            document.getElementById('coupon-code').value = couponCode;
        }
        this.applyCouponCode();
    }

    reset() {
        this.hideCurrentDiscount();
        this.showDiscountSections();
        const couponInput = document.getElementById('coupon-code');
        if (couponInput) couponInput.value = '';
        this.showMessage('coupon-message', '', 'success');
        this.showMessage('automatic-message', '', 'success');
    }

    getCurrentDiscount() {
        return this.currentDiscount;
    }
}

// مقداردهی اولیه وقتی DOM آماده شد
document.addEventListener('DOMContentLoaded', function() {
    window.discountWidget = new DiscountWidget({
        reservationId: document.querySelector('[data-reservation-id]')?.dataset.reservationId,
        applyCouponUrl: "{% url 'discounts:apply_coupon_code' %}",
        checkAutomaticUrl: "{% url 'discounts:check_automatic_discounts' %}",
        removeDiscountUrl: "{% url 'discounts:remove_discount' %}",
        getAvailableUrl: "{% url 'discounts:get_available_discounts' %}",
        csrfToken: "{{ csrf_token }}"
    });
});

// برای backward compatibility با کد قدیمی
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(() => {
        if (!window.discountWidget) {
            window.discountWidget = new DiscountWidget({
                reservationId: document.querySelector('[data-reservation-id]')?.dataset.reservationId,
                applyCouponUrl: "{% url 'discounts:apply_coupon_code' %}",
                checkAutomaticUrl: "{% url 'discounts:check_automatic_discounts' %}",
                removeDiscountUrl: "{% url 'discounts:remove_discount' %}",
                getAvailableUrl: "{% url 'discounts:get_available_discounts' %}",
                csrfToken: "{{ csrf_token }}"
            });
        }
    }, 100);
}