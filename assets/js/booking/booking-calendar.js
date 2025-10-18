// booking-calendar.js

document.addEventListener('DOMContentLoaded', function () {
    // دریافت داده‌های امن از Django
    const daysData = JSON.parse(document.getElementById('days-data').textContent);
    const doctorId = JSON.parse(document.getElementById('doctor-id').textContent);
    const consultationFee = parseFloat(JSON.parse(document.getElementById('consultation-fee').textContent));
    const walletBalance = parseFloat(JSON.parse(document.getElementById('wallet-balance').textContent));

    console.log('Wallet Balance:', walletBalance, 'Type:', typeof walletBalance);
    console.log('Consultation Fee:', consultationFee, 'Type:', typeof consultationFee);
    console.log('Has Insufficient Balance:', walletBalance < consultationFee);

    const persianMonths = [
        'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
        'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
    ];

    const persianDays = ['ش', 'ی', 'د', 'س', 'چ', 'پ', 'ج'];

    const monthDataCache = new Map();
    let pendingRequests = new Set();
    let currentAvailableData = {};
    let currentYear = 1403;
    let currentMonth = 3;
    let selectedDate = null;
    let selectedTime = null;
    let isLoading = false;

    const elements = {
        calendarGrid: document.getElementById('calendar-grid'),
        monthYearElement: document.getElementById('month-year'),
        prevMonthBtn: document.getElementById('prev-month'),
        nextMonthBtn: document.getElementById('next-month'),
        timeSlotsMain: document.getElementById('time-slots-main'),
        timeSlotsGrid: document.getElementById('time-slots-grid'),
        selectedDateText: document.getElementById('selected-date-text'),
        availableSlotsCount: document.getElementById('available-slots-count'),
        selectedDateInput: document.getElementById('selected_date'),
        selectedTimeInput: document.getElementById('selected_time'),
        submitBtn: document.getElementById('submit-btn')
    };

    if (daysData && daysData.length > 0) {
        const firstDate = daysData[0].jalali_date_str;
        if (firstDate) {
            const [year, month] = firstDate.split('/').map(Number);
            currentYear = year;
            currentMonth = month;
        }
    }

    const utils = {
        isLeapYear(year) {
            const mod = year % 33;
            return [1, 5, 9, 13, 17, 22, 26, 30].includes(mod);
        },
        getDaysInMonth(year, month) {
            if (month <= 6) return 31;
            if (month <= 11) return 30;
            return this.isLeapYear(year) ? 30 : 29;
        },
        toGregorian(jy, jm, jd) {
            const g_d_m = [0, 31, (jy % 4 === 3 ? 29 : 28), 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
            let gy = jy + 621;
            let days = (jm <= 7) ? ((jm - 1) * 31) + jd : (6 * 31) + ((jm - 7) * 30) + jd;
            const marchDayDiff = this.isLeapYear(jy) ? 79 : 80;
            const gd = new Date(gy, 2, 21 + days - marchDayDiff);
            return gd;
        },
        getFirstDayOfMonth(year, month) {
            const gregorianDate = this.toGregorian(year, month, 1);
            let dayOfWeek = gregorianDate.getDay();
            return (dayOfWeek + 3) % 7;
        },
        formatDateKey(year, month, day) {
            return `${year}/${month.toString().padStart(2, '0')}/${day.toString().padStart(2, '0')}`;
        },
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
    };

    const dom = {
        setLoading(loading) {
            isLoading = loading;
            elements.prevMonthBtn.disabled = loading;
            elements.nextMonthBtn.disabled = loading;
            elements.calendarGrid.classList.toggle('loading', loading);
        },
        showError(message) {
            const existingError = document.querySelector('.error-message');
            if (existingError) existingError.remove();
            const errorDiv = document.createElement('div');
            errorDiv.className = 'alert alert-danger';
            errorDiv.textContent = message;
            elements.calendarGrid.parentNode.insertBefore(errorDiv, elements.calendarGrid);
            setTimeout(() => errorDiv.remove(), 5000);
        },
        clearErrors() {
            const errors = document.querySelectorAll('.error-message');
            errors.forEach(error => error.remove());
        }
    };

    const api = {
        async loadMonthData(year, month) {
            if (isLoading) return;
            const monthKey = `${year}-${month}`;
            if (monthDataCache.has(monthKey)) {
                Object.assign(currentAvailableData, monthDataCache.get(monthKey));
                calendar.generate();
                return;
            }
            if (pendingRequests.has(monthKey)) return;
            pendingRequests.add(monthKey);
            dom.setLoading(true);
            dom.clearErrors();
            try {
                const response = await fetch(`/reservations/ajax/month-availability/${doctorId}/?year=${year}&month=${month}`, {
                    headers: {'X-Requested-With': 'XMLHttpRequest'}
                });
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                const data = await response.json();
                if (data.success) {
                    monthDataCache.set(monthKey, data.available_days);
                    Object.assign(currentAvailableData, data.available_days);
                    calendar.generate();
                } else {
                    dom.showError(data.error || 'خطا در بارگذاری اطلاعات ماه');
                }
            } catch (error) {
                console.error('Network error:', error);
                dom.showError('خطا در ارتباط با سرور. لطفاً دوباره تلاش کنید.');
            } finally {
                pendingRequests.delete(monthKey);
                dom.setLoading(false);
            }
        },
        async loadDaySlots(dateKey) {
            try {
                const response = await fetch(`/reservations/ajax/day-slots/${doctorId}/?date=${dateKey}`, {
                    headers: {'X-Requested-With': 'XMLHttpRequest'}
                });
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                const data = await response.json();
                if (data.success) {
                    return data.slots;
                } else {
                    console.error('Error loading day slots:', data.error);
                    return [];
                }
            } catch (error) {
                console.error('Network error:', error);
                return [];
            }
        }
    };

    const calendar = {
        generate() {
            const firstDay = utils.getFirstDayOfMonth(currentYear, currentMonth);
            const daysInMonth = utils.getDaysInMonth(currentYear, currentMonth);
            const daysInPrevMonth = currentMonth > 1 ? utils.getDaysInMonth(currentYear, currentMonth - 1) : utils.getDaysInMonth(currentYear - 1, 12);

            elements.monthYearElement.textContent = `${persianMonths[currentMonth - 1]} ${currentYear}`;
            const fragment = document.createDocumentFragment();

            // نمایش روزهای هفته
            persianDays.forEach(day => {
                const header = document.createElement('div');
                header.className = 'col text-center py-2 bg-dark text-white';
                header.textContent = day;
                fragment.appendChild(header);
            });

            // نمایش روزهای ماه قبل (اگر ماه از شنبه شروع نشود)
            for (let i = firstDay; i > 0; i--) {
                const day = daysInPrevMonth - i + 1;
                const dayElement = this.createDayElement(day, 'col text-center py-1 text-muted');
                fragment.appendChild(dayElement);
            }

            // نمایش روزهای ماه جاری
            for (let day = 1; day <= daysInMonth; day++) {
                const dateKey = utils.formatDateKey(currentYear, currentMonth, day);
                const dayData = currentAvailableData[dateKey];
                const isAvailable = dayData && dayData.slots_count > 0;
                let classes = 'col text-center py-1 ';
                if (isAvailable) classes += ' bg text-white';
                if (selectedDate === dateKey) classes += ' border-warning';
                if (!isAvailable) classes += 'bg-light text-muted';
                const dayElement = this.createDayElement(day, classes, dateKey, dayData);
                fragment.appendChild(dayElement);
            }

            // محاسبه سلول‌های باقیمانده
            const totalCells = Math.ceil((firstDay + daysInMonth) / 7) * 7;
            const remainingCells = totalCells - (firstDay + daysInMonth);
            for (let day = 1; day <= remainingCells; day++) {
                const dayElement = this.createDayElement(day, 'col text-center py-1 text-muted');
                fragment.appendChild(dayElement);
            }

            elements.calendarGrid.innerHTML = '';
            elements.calendarGrid.appendChild(fragment);
        },
        createDayElement(day, classes, dateKey = null, dayData = null) {
            const dayElement = document.createElement('div');
            dayElement.className = classes;
            dayElement.textContent = day;

            if (dateKey) {
                dayElement.setAttribute('data-date', dateKey);

                const [year, month, dayNum] = dateKey.split('/').map(Number);
                const gregorianDate = utils.toGregorian(year, month, dayNum);
                const dayOfWeek = gregorianDate.getDay();
                if (dayOfWeek === 3) {
                    dayElement.classList.add('friday');
                }

                if (dayData) {
                    dayElement.style.cursor = 'pointer';
                    dayElement.addEventListener('click', () => this.selectDate(dateKey));

                    const indicator = document.createElement('div');

                    if (dayData.slots_count === 0) {
                        dayElement.classList.add('completed');
                        indicator.textContent = 'تکمیل شده';
                        indicator.classList.add('completed-indicator');
                    } else if (dayData.slots_count > 0) {
                        indicator.textContent = `${dayData.slots_count} نوبت`;
                        indicator.classList.add('small', 'text-dark');
                    } else {
                        indicator.textContent = 'ناموجود';
                        indicator.classList.add('text-muted');
                    }

                    dayElement.appendChild(indicator);
                }
            }

            return dayElement;
        },
        async selectDate(dateKey) {
            const dayData = currentAvailableData[dateKey];
            if (!dayData || dayData.slots_count === 0) return;
            const previousSelected = elements.calendarGrid.querySelector('.border-warning');
            if (previousSelected) {
                previousSelected.classList.remove('border-warning');
            }
            const newSelected = elements.calendarGrid.querySelector(`[data-date="${dateKey}"]`);
            if (newSelected) {
                newSelected.classList.add('border-warning');
            }
            selectedDate = dateKey;
            selectedTime = null;
            elements.selectedDateInput.value = dateKey;
            elements.selectedTimeInput.value = '';
            const [year, month, day] = dateKey.split('/').map(Number);
            const monthName = persianMonths[month - 1];
            elements.selectedDateText.textContent = `${day} ${monthName} ${year}`;
            elements.availableSlotsCount.textContent = `${dayData.slots_count} نوبت خالی `;
            const slots = dayData.slots || await api.loadDaySlots(dateKey);
            timeSlots.display(slots);
            elements.timeSlotsMain.style.display = 'block';
            elements.timeSlotsMain.scrollIntoView({behavior: 'smooth', block: 'center'});
            form.updateSubmitButton();
        }
    };

    const timeSlots = {
        display(slots) {
            if (slots.length === 0) {
                elements.timeSlotsGrid.innerHTML = `
                <div class="col-12 text-center py-4 text-muted">
                    <div class="fs-1">⏰</div>
                    <div>متأسفانه در این تاریخ نوبتی موجود نیست</div>
                </div>
            `;
                return;
            }
            const fragment = document.createDocumentFragment();
            slots.forEach(slot => {
                const slotElement = document.createElement('div');
                slotElement.className = 'col-4 col-md-3 mb-3';
                const btn = document.createElement('button');
                btn.className = 'btn btn-outline-success w-100';
                btn.textContent = slot;
                btn.addEventListener('click', () => this.select(slot, btn));
                slotElement.appendChild(btn);
                fragment.appendChild(slotElement);
            });
            elements.timeSlotsGrid.innerHTML = '';
            elements.timeSlotsGrid.appendChild(fragment);
        },
        select(time, element) {
            const previousSelected = elements.timeSlotsGrid.querySelector('.btn-success');
            if (previousSelected) {
                previousSelected.classList.remove('btn-success');
                previousSelected.classList.add('btn-outline-success');
            }
            element.classList.remove('btn-outline-success');
            element.classList.add('btn-success');
            selectedTime = time;
            elements.selectedTimeInput.value = time;
            form.updateSubmitButton();
        }
    };

    const form = {
        updateSubmitButton() {
            const hasInsufficientBalance = walletBalance < consultationFee;
            const selectedPaymentMethod = document.querySelector('input[name="payment_method"]:checked').value;

            if (selectedDate && selectedTime) {
                if (selectedPaymentMethod === 'wallet' && hasInsufficientBalance) {
                    elements.submitBtn.disabled = false;
                    elements.submitBtn.className = 'btn btn-warning w-100 m-t-10';
                    const neededAmount = consultationFee - walletBalance;
                    elements.submitBtn.textContent = `شارژ کیف پول (${neededAmount.toLocaleString()} تومان کمبود دارید)`;
                } else if (selectedPaymentMethod === 'wallet' && !hasInsufficientBalance) {
                    elements.submitBtn.disabled = false;
                    elements.submitBtn.className = 'btn btn-info dr_bg w-full rounded border-0 m-t-10';
                    elements.submitBtn.textContent = `رزرو و پرداخت خودکار - ${consultationFee.toLocaleString()} تومان`;
                } else if (selectedPaymentMethod === 'direct') {
                    elements.submitBtn.disabled = false;
                    elements.submitBtn.className = 'btn btn-success w-100 m-t-10';
                    elements.submitBtn.textContent = `رزرو و پرداخت مستقیم - ${consultationFee.toLocaleString()} تومان`;
                }
            } else {
                elements.submitBtn.disabled = true;
                elements.submitBtn.className = 'btn btn-secondary w-100 m-t-10';
                elements.submitBtn.textContent = 'لطفاً تاریخ و زمان را انتخاب کنید';
            }
        }
    };

    function validateForm() {
        const name = $('#patient_name').val().trim();
        const last_name = $('#patient_last_name').val().trim();
        const phone = $('#phone').val().trim();
        const national_code = $('#patient_national_id').val().trim();

        $('.text-danger').text('');
        $('.form-control').removeClass('border-danger');

        let isValid = true;
        elements.submitBtn.disabled = false;

        if (name.length < 3) {
            $('#patient_name').addClass('border-danger');
            $('#name_alarm').text('نام باید حداقل ۳ حرف باشد.');
            elements.submitBtn.disabled = true;
            isValid = false;
        }
        if (last_name.length < 3) {
            $('#patient_last_name').addClass('border-danger');
            $('#last_name_alarm').text('نام خانوادگی باید حداقل ۳ حرف باشد.');
            elements.submitBtn.disabled = true;
            isValid = false;
        }

        if (!/^0\d{10}$/.test(phone)) {
            $('#phone').addClass('border-danger');
            $('#phone_alarm').text('شماره تلفن باید با ۰ شروع شود و ۱۱ رقم باشد.');
            elements.submitBtn.disabled = true;
            isValid = false;
        }

        if (!/^\d{10}$/.test(national_code)) {
            $('#patient_national_id').addClass('border-danger');
            $('#code_alarm').text('کد ملی باید ۱۰ رقم باشد.');
            elements.submitBtn.disabled = true;
            isValid = false;
        }

        return isValid;
    }

    // اضافه کردن رویدادهای real-time به فیلدها
    $('#patient_name').on('input', validateForm);
    $('#patient_last_name').on('input', validateForm);
    $('#phone').on('input', validateForm);
    $('#patient_national_id').on('input', validateForm);

    // اضافه کردن رویداد برای تغییر روش پرداخت
    $('input[name="payment_method"]').on('change', function() {
        form.updateSubmitButton();
    });

    // اعتبارسنجی هنگام ارسال فرم
    $('#booking-form').submit(function (e) {
        if (!validateForm()) {
            e.preventDefault();
        }
    });

    const debouncedLoadMonth = utils.debounce(api.loadMonthData, 300);

    elements.prevMonthBtn.addEventListener('click', async () => {
        if (currentMonth === 1) {
            currentMonth = 12;
            currentYear--;
        } else {
            currentMonth--;
        }
        await debouncedLoadMonth(currentYear, currentMonth);
    });

    elements.nextMonthBtn.addEventListener('click', async () => {
        if (currentMonth === 12) {
            currentMonth = 1;
            currentYear++;
        } else {
            currentMonth++;
        }
        await debouncedLoadMonth(currentYear, currentMonth);
    });

    document.getElementById('booking-form').addEventListener('submit', function (e) {
        if (!selectedDate || !selectedTime) {
            e.preventDefault();
            alert('لطفاً ابتدا تاریخ و زمان را انتخاب کنید');
            return;
        }

        const selectedPaymentMethod = document.querySelector('input[name="payment_method"]:checked').value;
        const hasInsufficientBalance = walletBalance < consultationFee;

        if (selectedPaymentMethod === 'wallet' && hasInsufficientBalance) {
            e.preventDefault();
            // محاسبه مقدار کمبود برای شارژ
            const neededAmount = consultationFee - walletBalance;

            // اضافه کردن 10% بیشتر برای اطمینان
            const suggestedAmount = Math.ceil(neededAmount * 1.1);

            // گرد کردن به نزدیکترین 10,000 تومان
            const roundedAmount = Math.ceil(suggestedAmount / 10000) * 10000;

            // حداقل مقدار 10,000 تومان
            const finalAmount = Math.max(10000, roundedAmount);

            // ساخت آدرس بازگشت (آدرس فعلی با پارامترهای انتخاب شده)
            const currentUrl = window.location.href;

            // هدایت به صفحه شارژ کیف پول با مقدار پیشنهادی
            window.location.href = `/wallet/deposit/?amount=${finalAmount}&redirect_to=${encodeURIComponent(currentUrl)}`;
            return;
        }

        let confirmMessage = '';
        if (selectedPaymentMethod === 'wallet') {
            confirmMessage = `آیا از رزرو این نوبت اطمینان دارید؟\n\nتاریخ: ${selectedDate}\nزمان: ${selectedTime}\nهزینه: ${consultationFee.toLocaleString()} تومان\n\nمبلغ به صورت خودکار از کیف پول شما کسر خواهد شد.`;
        } else {
            confirmMessage = `آیا از رزرو این نوبت اطمینان دارید؟\n\nتاریخ: ${selectedDate}\nزمان: ${selectedTime}\nهزینه: ${consultationFee.toLocaleString()} تومان\n\nپس از رزرو به صفحه پرداخت هدایت خواهید شد.`;
        }

        if (!confirm(confirmMessage)) {
            e.preventDefault();
            return;
        }
        elements.submitBtn.classList.add('loading');
        elements.submitBtn.textContent = 'در حال پردازش...';
    });

    // بارگذاری اولیه
    api.loadMonthData(currentYear, currentMonth); // بارگذاری ماه فعلی

    setTimeout(() => {
        const nextMonth = currentMonth === 12 ? 1 : currentMonth + 1;
        const nextYear = currentMonth === 12 ? currentYear + 1 : currentYear;
        api.loadMonthData(nextYear, nextMonth); // پیش‌بارگذاری ماه بعد
    }, 1000);
});

// توابع مربوط به Modal
function showFormModal() {
    document.getElementById("information").classList.remove("hidden");
}

function closeFormModal() {
    document.getElementById("information").classList.add("hidden");
}