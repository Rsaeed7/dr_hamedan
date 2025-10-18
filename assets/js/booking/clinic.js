// انتقال داده‌های Django به JavaScript
let clinicData = {};

function initializeClinicData() {
    const clinicElement = document.getElementById('clinic-data');
    if (clinicElement) {
        clinicData = {
            id: clinicElement.dataset.clinicId,
            name: clinicElement.dataset.clinicName,
            registerUrl: clinicElement.dataset.registerUrl,
            isAuthenticated: clinicElement.dataset.isAuthenticated === 'true'
        };
    }
}

// مدیریت نمایش لیست دکترها بر اساس تخصص
function initializeTreatmentSelection() {
    $('.treatment-input').change(function() {
        const specialId = $(this).data('special-id');

        // همه لیست‌های دکترها را مخفی کن
        $('.doctor-list').hide();

        // فقط لیست دکترهای مربوط به تخصص انتخاب‌شده را نمایش بده
        $(`.doctor-list[data-special-id="${specialId}"]`).show();
    });
}

// اسکرول به بخش نوبت‌دهی
function initializeScrollButton() {
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
}

// مدیریت modal ثبت نظر
function showFormModal() {
    if (clinicData.isAuthenticated) {
        document.getElementById("formModal").classList.remove("hidden");
    } else {
        const nextUrl = window.location.pathname;
        window.location.href = clinicData.registerUrl + "?next=" + encodeURIComponent(nextUrl);
    }
}

function closeFormModal() {
    document.getElementById("formModal").classList.add("hidden");
}

// مقداردهی اولیه همه قابلیت‌ها
document.addEventListener('DOMContentLoaded', function() {
    initializeClinicData();
    initializeScrollButton();

    // فقط اگر jQuery لود شده باشد
    if (typeof jQuery !== 'undefined') {
        initializeTreatmentSelection();
    } else {
        console.warn('jQuery loaded yet. Treatment selection will not work.');
    }
});