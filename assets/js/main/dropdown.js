function toggleDropdown(id, button) {
    let dropdown = document.getElementById(id);
    let arrow = button.querySelector('.arrow');

    if (!dropdown || !arrow) {
        console.error('Dropdown or arrow element not found');
        return;
    }

    if (dropdown.style.maxHeight === "0px" || dropdown.style.maxHeight === "") {
        dropdown.style.display = "block";
        dropdown.style.maxHeight = dropdown.scrollHeight + "px";
        dropdown.style.opacity = "1";
        arrow.style.transform = "rotate(180deg)";
    } else {
        dropdown.style.maxHeight = "0px";
        dropdown.style.opacity = "0";
        setTimeout(() => {
            dropdown.style.display = "none";
        }, 300);
        arrow.style.transform = "rotate(0deg)";
    }
}

function initDropdowns() {
    // باز کردن پیش‌فرض منوهای تخصص و جنسیت
    const sortButton = document.querySelector('button[onclick*="toggleDropdown(\'sort\'"]');
    const genderButton = document.querySelector('button[onclick*="toggleDropdown(\'gender\'"]');

    if (sortButton) {
        toggleDropdown('sort', sortButton);
    }

    if (genderButton) {
        toggleDropdown('gender', genderButton);
    }

    // حذف event listenerهای قدیمی و اضافه کردن جدید
    document.querySelectorAll('button[onclick*="toggleDropdown"]').forEach(button => {
        // حذف attribute onclick قدیمی
        const oldOnclick = button.getAttribute('onclick');
        button.removeAttribute('onclick');

        // اضافه کردن event listener جدید
        button.addEventListener('click', function() {
            // استخراج id از onclick قدیمی
            const match = oldOnclick.match(/toggleDropdown\('([^']+)'/);
            if (match && match[1]) {
                toggleDropdown(match[1], this);
            }
        });
    });
}

// جایگزین window.onload با event listener استاندارد
document.addEventListener('DOMContentLoaded', function() {
    initDropdowns();
});

// برای مواقعی که صفحه از قبل لود شده
if (document.readyState === 'complete') {
    initDropdowns();
}


    function resetFilters() {
            // بازنشانی همه چک‌باکس‌ها
            const checkboxes = document.querySelectorAll('.custom-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = false;
            });

            // بازنشانی همه رادیو باتن‌ها
            const radios = document.querySelectorAll('.custom-radio');
            radios.forEach(radio => {
                radio.checked = false;
            });

            // غیرفعال کردن سوئیچ نوبت پزشکان
            const switchInput = document.querySelector('.switch input');
            if (switchInput) {
                switchInput.checked = false;
            }

            // بسته کردن همه منوهای فیلتر
            const filterDropdowns = document.querySelectorAll('.filter-dropdown');
            filterDropdowns.forEach(dropdown => {
                dropdown.style.maxHeight = "0px";
                dropdown.style.opacity = "0";
                setTimeout(() => {
                    dropdown.style.display = "none";
                }, 300);
            });

            // بازنشانی همه فلش‌های باز/بسته کننده
            const arrows = document.querySelectorAll('.arrow');
            arrows.forEach(arrow => {
                arrow.style.transform = "rotate(0deg)";
            });
        }


        document.addEventListener('DOMContentLoaded', function () {
            // اعمال خودکار فرم با تغییر هر فیلتر
            const autoSubmitElements = document.querySelectorAll('.auto-submit');

            autoSubmitElements.forEach(element => {
                element.addEventListener('change', function () {
                    // برای checkbox‌ها و radioها
                    if (this.type === 'checkbox' || this.type === 'radio') {
                        // اعمال فرم پس از یک تاخیر کوتاه
                        setTimeout(() => {
                            document.getElementById('filter-form').submit();
                        }, 300);
                    }
                });
            });

            // بهبود عملکرد dropdownها
            function toggleDropdown(id, button) {
                const dropdown = document.getElementById(id);
                dropdown.classList.toggle('show');

                // بستن dropdownهای دیگر
                document.querySelectorAll('.filter-dropdown').forEach(item => {
                    if (item.id !== id && item.classList.contains('show')) {
                        item.classList.remove('show');
                    }
                });
            }

            // بستن dropdownها با کلیک خارج از آنها
            window.addEventListener('click', function (event) {
                if (!event.target.matches('.btn-filter')) {
                    document.querySelectorAll('.filter-dropdown').forEach(dropdown => {
                        if (dropdown.classList.contains('show')) {
                            dropdown.classList.remove('show');
                        }
                    });
                }
            });
        });

        function openMobileFilter() {
            document.getElementById('mobileFilterModal').classList.add('active');
            document.body.style.overflow = 'hidden';
        }

        function closeMobileFilter() {
            document.getElementById('mobileFilterModal').classList.remove('active');
            document.body.style.overflow = '';
        }