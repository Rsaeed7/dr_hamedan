// otp-auth.js

// تایمر OTP
const initialTime = 180; // 3 دقیقه
const phoneNumber = "{{ phone }}"; // شماره تلفن از context
const storageKey = `otpStartTime_${phoneNumber}`;

// شروع تایمر وقتی صفحه لود می‌شود
window.onload = function() {
    const startTime = localStorage.getItem(storageKey);
    const currentTime = Date.now();

    // اگر زمان ذخیره شده وجود ندارد یا زمان سپری شده بیشتر از initialTime است
    if (!startTime || (currentTime - parseInt(startTime)) / 1000 > initialTime) {
        localStorage.setItem(storageKey, currentTime);
    }

    updateTimer();
};

function updateTimer() {
    const startTime = parseInt(localStorage.getItem(storageKey));
    const elapsedTime = Math.floor((Date.now() - startTime) / 1000);
    const remainingTime = Math.max(initialTime - elapsedTime, 0);

    // نمایش زمان
    document.getElementById('minutes').value = Math.floor(remainingTime / 60).toString().padStart(2, '0');
    document.getElementById('seconds').value = (remainingTime % 60).toString().padStart(2, '0');

    // تغییر رنگ وقتی کمتر از 1 دقیقه باقی مانده
    if (remainingTime < 60) {
        document.getElementById('minutes').style.color = "red";
        document.getElementById('seconds').style.color = "red";
    }

    // ادامه تایمر اگر زمان تمام نشده
    if (remainingTime > 0) {
        setTimeout(updateTimer, 1000);
    } else {
        document.getElementById('minutes').value = "00";
        document.getElementById('seconds').value = "00";
    }
}

// اعتبارسنجی کد OTP
function validateCode() {
    const codeInput = document.getElementById('id_code');
    const codeError = document.getElementById('code_error');
    const submitBtn = document.getElementById('submit_btn');
    const value = codeInput.value.trim();

    if (value.length !== 4 || !/^\d+$/.test(value)) {
        codeInput.classList.add('text-alert');
        codeInput.classList.remove('input100');
        codeError.textContent = value.length > 0 ? '!!کد تایید باید 4 رقم باشد' : '';
        submitBtn.disabled = true;
        return false;
    } else {
        codeInput.classList.remove('text-alert');
        codeInput.classList.add('input100');
        codeError.textContent = '';
        submitBtn.disabled = false;
        return true;
    }
}

// ارسال فرم کد
function submitForm() {
    if (validateCode()) {
        localStorage.removeItem(storageKey);
        document.getElementById('code_form').submit();
    }
}

// وقتی کاربر فرم را ارسال می‌کند
document.getElementById('code_form')?.addEventListener('submit', function(e) {
    if (validateCode()) {
        localStorage.removeItem(storageKey);
    } else {
        e.preventDefault();
    }
});

// اعتبارسنجی شماره تلفن
document.addEventListener('DOMContentLoaded', function() {
    const phoneInput = document.getElementById('id_phone');
    const submitBtn = document.getElementById('submit_btn');
    const phoneError = document.getElementById('phone_error');

    if (phoneInput) {
        // Initially disable the submit button
        submitBtn.disabled = true;

        // Validate phone number on input change
        phoneInput.addEventListener('input', function() {
            validatePhoneNumber();
        });

        function validatePhoneNumber() {
            const value = phoneInput.value.trim();

            // Check if phone number is valid (11 digits and starts with 0)
            const isValid = value.length === 11 && value.startsWith('0');

            if (isValid) {
                phoneInput.classList.remove('text-alert');
                phoneInput.classList.add('input100');
                phoneError.textContent = '';
                submitBtn.disabled = false;
            } else {
                phoneInput.classList.add('text-alert');
                phoneInput.classList.remove('input100');
                phoneError.textContent = value.length > 0 ? 'شماره تلفن صحیح وارد کنید!' : '';
                submitBtn.disabled = true;
            }
        }

        // Form submission handler
        document.getElementById('phone_form')?.addEventListener('submit', function(e) {
            const value = phoneInput.value.trim();

            if (value.length !== 11 || !value.startsWith('0')) {
                e.preventDefault();
                phoneInput.classList.add('text-alert');
                phoneError.textContent = '!!شماره تلفن صحیح وارد کنید';
            }
        });
    }
});