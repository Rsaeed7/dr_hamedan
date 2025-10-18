// متغیرهای گلوبال برای ذخیره داده‌های Django
let doctorData = {};
let tipsData = [];

// تابع برای دریافت داده‌ها از HTML
function initializeDoctorData() {
    const doctorElement = document.getElementById('doctor-data');
    if (doctorElement) {
        doctorData = {
            id: doctorElement.dataset.doctorId,
            name: doctorElement.dataset.doctorName,
            onlineFee: doctorElement.dataset.onlineFee,
            chatUrl: doctorElement.dataset.chatUrl,
            registerUrl: doctorElement.dataset.registerUrl,
            isAuthenticated: doctorElement.dataset.isAuthenticated === 'true'
        };
    }

    // دریافت داده‌های tips
    const tipsElement = document.getElementById('tips-data');
    if (tipsElement) {
        tipsData = JSON.parse(tipsElement.textContent);
    }
}

// اسکرول به بخش نوبت‌دهی
document.addEventListener('DOMContentLoaded', function() {
    initializeDoctorData();

    const scrollButton = document.getElementById('scrollButton');
    if (scrollButton) {
        scrollButton.addEventListener('click', function () {
            const asideElement = document.getElementById('aside');
            if (asideElement) {
                const offsetTop = asideElement.getBoundingClientRect().top + window.scrollY - 150;
                window.scrollTo({top: offsetTop, behavior: 'smooth'});
            }
        });
    }
});

// مدیریت modal ثبت نظر
function showFormModal() {
    if (doctorData.isAuthenticated) {
        document.getElementById("formModal").classList.remove("hidden");
    } else {
        const nextUrl = window.location.pathname;
        window.location.href = doctorData.registerUrl + "?next=" + encodeURIComponent(nextUrl);
    }
}

function closeFormModal() {
    document.getElementById("formModal").classList.add("hidden");
}

// مدیریت modal مشاوره آنلاین
function showFormChat() {
    document.getElementById("information").classList.remove("hidden");
}

function closeFormChat() {
    document.getElementById("information").classList.add("hidden");
}

// اعتبارسنجی فرم مشاوره آنلاین
function validateForm() {
    const name = document.getElementById('patient_name')?.value.trim() || '';
    const last_name = document.getElementById('patient_last_name')?.value.trim() || '';
    const phone = document.getElementById('phone')?.value.trim() || '';
    const national_code = document.getElementById('patient_national_id')?.value.trim() || '';

    // Reset errors
    const nameAlarm = document.getElementById('name_alarm');
    const lastNameAlarm = document.getElementById('last_name_alarm');
    const phoneAlarm = document.getElementById('phone_alarm');
    const nationalIdAlarm = document.getElementById('national_id_alarm');

    if (nameAlarm) nameAlarm.textContent = '';
    if (lastNameAlarm) lastNameAlarm.textContent = '';
    if (phoneAlarm) phoneAlarm.textContent = '';
    if (nationalIdAlarm) nationalIdAlarm.textContent = '';

    const nameInput = document.getElementById('patient_name');
    const lastNameInput = document.getElementById('patient_last_name');
    const phoneInput = document.getElementById('phone');
    const nationalIdInput = document.getElementById('patient_national_id');

    if (nameInput) nameInput.classList.remove('border-danger');
    if (lastNameInput) lastNameInput.classList.remove('border-danger');
    if (phoneInput) phoneInput.classList.remove('border-danger');
    if (nationalIdInput) nationalIdInput.classList.remove('border-danger');

    let isValid = true;

    // Validate name
    if (name.length < 3) {
        if (nameInput) nameInput.classList.add('border-danger');
        if (nameAlarm) nameAlarm.textContent = 'نام باید حداقل ۳ حرف باشد.';
        isValid = false;
    }

    // Validate last name
    if (last_name.length < 3) {
        if (lastNameInput) lastNameInput.classList.add('border-danger');
        if (lastNameAlarm) lastNameAlarm.textContent = 'نام خانوادگی باید حداقل ۳ حرف باشد.';
        isValid = false;
    }

    // Validate phone
    if (phone && !phone.match(/^0\d{10}$/) && phoneInput && !phoneInput.disabled) {
        phoneInput.classList.add('border-danger');
        if (phoneAlarm) phoneAlarm.textContent = 'شماره تلفن باید با ۰ شروع شود و ۱۱ رقم باشد.';
        isValid = false;
    }

    // Validate national code
    if (national_code && !national_code.match(/^\d{10}$/)) {
        if (nationalIdInput) nationalIdInput.classList.add('border-danger');
        if (nationalIdAlarm) nationalIdAlarm.textContent = 'کد ملی باید ۱۰ رقم باشد.';
        isValid = false;
    }

    return isValid;
}

// مدیریت باز شدن اتوماتیک فرم رزرو
function handleAutoOpenBooking() {
    const params = new URLSearchParams(window.location.search);
    if (!params.has('open_booking')) return;

    const fee = params.get('fee');

    try {
        if (typeof showDynamicForm === 'function' && doctorData.id) {
            showDynamicForm(doctorData.id, fee || doctorData.onlineFee, doctorData.chatUrl, doctorData.name);
            return;
        }

        if (typeof showFormChat === 'function') {
            showFormChat();
            if (fee) {
                const feeEl = document.getElementById('visit-fee') || document.querySelector('#visit-fee');
                if (feeEl) feeEl.textContent = fee;
            }
            return;
        }
    } catch (e) {
        console.warn('خطا هنگام تلاش برای استفاده از فانکشن‌های بازکننده:', e);
    }

    // fallback
    const possibleIds = ['information-modal', 'information', 'formModal', 'booking-form-modal', 'modal-booking'];
    for (let id of possibleIds) {
        const el = document.getElementById(id);
        if (el) {
            el.classList.remove('hidden');
            el.style.display = (el.style.display === 'none' || window.getComputedStyle(el).display === 'none') ? 'block' : el.style.display;
            el.scrollIntoView({behavior: 'smooth', block: 'center'});
            break;
        }
    }

    if (fee) {
        const feeEl = document.getElementById('visit-fee') || document.querySelector('#visit-fee');
        if (feeEl) feeEl.textContent = fee;
    }
}

// مقداردهی اولیه و اضافه کردن event listeners
document.addEventListener('DOMContentLoaded', function() {
    initializeDoctorData();
    handleAutoOpenBooking();

    // اضافه کردن رویدادهای اعتبارسنجی
    const patientName = document.getElementById('patient_name');
    const patientLastName = document.getElementById('patient_last_name');
    const phone = document.getElementById('phone');
    const nationalId = document.getElementById('patient_national_id');
    const bookingForm = document.getElementById('booking-form');

    if (patientName) patientName.addEventListener('input', validateForm);
    if (patientLastName) patientLastName.addEventListener('input', validateForm);
    if (phone) phone.addEventListener('input', validateForm);
    if (nationalId) nationalId.addEventListener('input', validateForm);

    if (bookingForm) {
        bookingForm.addEventListener('submit', function (e) {
            if (!validateForm()) {
                e.preventDefault();
                const firstError = document.querySelector('.border-danger');
                if (firstError) {
                    firstError.scrollIntoView({behavior: 'smooth', block: 'center'});
                }
            }
        });
    }
});