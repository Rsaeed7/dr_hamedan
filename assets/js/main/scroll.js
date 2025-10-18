document.addEventListener('DOMContentLoaded', function () {
    // ==================== اسکرول نرم ====================
    const internalLinks = document.querySelectorAll('a[href^="#"]');

    internalLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href');

            // اگر لینک برای آکاردئون است، از پیش‌فرض جلوگیری نکن
            if (targetId.includes('_detail')) return;

            // اگر لینک برای تب‌های بوت استرپ است، جلوگیری نکن
            if (this.getAttribute('data-bs-toggle') === 'tab') return;

            e.preventDefault();
            const targetElement = document.querySelector(targetId);

            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });

                // فقط برای هدرهای اصلی URL را آپدیت کن
                const mainSections = ['#pay', '#lenz', '#text', '#report', '#file',
                                    '#management', '#support', '#prescription'];

                if (mainSections.includes(targetId)) {
                    history.pushState(null, null, targetId);
                }
            }
        });
    });

    // ==================== مدیریت آکاردئون‌ها ====================
    function initAccordions() {
        const collapses = document.querySelectorAll('.accordion .collapse');

        collapses.forEach(collapse => {
            collapse.addEventListener('show.bs.collapse', function () {
                const parent = this.closest('.accordion-item');
                const icon = parent.querySelector('.pe-7s-more, .pe-7s-less');
                if (icon) {
                    icon.classList.remove('pe-7s-more');
                    icon.classList.add('pe-7s-less');
                }
            });

            collapse.addEventListener('hide.bs.collapse', function () {
                const parent = this.closest('.accordion-item');
                const icon = parent.querySelector('.pe-7s-more, .pe-7s-less');
                if (icon) {
                    icon.classList.remove('pe-7s-less');
                    icon.classList.add('pe-7s-more');
                }
            });
        });
    }

    initAccordions();
});


// service-selection.js
document.addEventListener('DOMContentLoaded', function () {
    console.log('Service selection JS loaded');

    const citySelect = document.getElementById('city');
    console.log('City select found:', citySelect);

    // وقتی شهر انتخاب شد، اسکرول کن به بخش دسته‌بندی‌ها
    if (citySelect) {
        citySelect.addEventListener('change', function () {
            console.log('City changed, scrolling...');
            // صبر کن تا صفحه با انتخاب شهر دوباره بارگذاری بشه
            setTimeout(() => {
                const categorySection = document.querySelector('.list_home');
                console.log('Category section:', categorySection);
                if (categorySection) {
                    categorySection.scrollIntoView({behavior: 'smooth', block: 'start'});
                }
            }, 500);
        });
    }

    // بررسی اینکه آیا دسته‌بندی انتخاب شده (با استفاده از data attribute)
    const hasSelectedCategory = document.body.getAttribute('data-category-selected') === 'true';
    console.log('Has selected category:', hasSelectedCategory);

    if (hasSelectedCategory) {
        console.log('Scrolling to services...');
        // اسکرول به بخش خدمات بعد از لود
        setTimeout(() => {
            const servicesSection = document.querySelector('.row.g-3');
            console.log('Services section:', servicesSection);
            if (servicesSection) {
                servicesSection.scrollIntoView({behavior: 'smooth', block: 'start'});
            }
        }, 500);
    }
});