document.addEventListener("DOMContentLoaded", function () {
    // ==================== اسکرول با دکمه ====================
    document.querySelectorAll(".scroll-wrapper-box").forEach(function (wrapper) {
        const container = wrapper.querySelector(".scroll-container");
        const btnLeft = wrapper.querySelector(".scroll-left");
        const btnRight = wrapper.querySelector(".scroll-right");

        if (!container || !btnLeft || !btnRight) return;

        const isRTL = getComputedStyle(container).direction === "rtl";

        btnLeft.addEventListener("click", function () {
            container.scrollBy({ left: isRTL ? 800 : -800, behavior: "smooth" });
        });

        btnRight.addEventListener("click", function () {
            container.scrollBy({ left: isRTL ? -800 : 800, behavior: "smooth" });
        });
    });

    // ==================== اسکرول با درگ موس ====================
    document.querySelectorAll('.scroll-wrapper').forEach(scrollWrapper => {
        let isDragging = false;
        let startX;
        let scrollLeft;

        scrollWrapper.addEventListener('mousedown', (e) => {
            isDragging = true;
            startX = e.pageX - scrollWrapper.offsetLeft;
            scrollLeft = scrollWrapper.scrollLeft;
            scrollWrapper.style.cursor = 'grabbing';
        });

        scrollWrapper.addEventListener('mouseleave', () => {
            isDragging = false;
            scrollWrapper.style.cursor = 'grab';
        });

        scrollWrapper.addEventListener('mouseup', () => {
            isDragging = false;
            scrollWrapper.style.cursor = 'grab';
        });

        scrollWrapper.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            e.preventDefault();
            const x = e.pageX - scrollWrapper.offsetLeft;
            const walk = (x - startX) * 2;
            scrollWrapper.scrollLeft = scrollLeft - walk;
        });

        // برای تاچ دیوایس‌ها
        scrollWrapper.addEventListener('touchstart', (e) => {
            isDragging = true;
            startX = e.touches[0].pageX - scrollWrapper.offsetLeft;
            scrollLeft = scrollWrapper.scrollLeft;
        });

        scrollWrapper.addEventListener('touchmove', (e) => {
            if (!isDragging) return;
            const x = e.touches[0].pageX - scrollWrapper.offsetLeft;
            const walk = (x - startX) * 2;
            scrollWrapper.scrollLeft = scrollLeft - walk;
        });

        scrollWrapper.addEventListener('touchend', () => {
            isDragging = false;
        });
    });
});



    window.addEventListener("scroll", function () {
        var bottomNav = document.getElementById("bottom-nav");
        var scrollPosition = window.scrollY + window.innerHeight; // موقعیت کنونی اسکرول

        // بررسی که آیا به انتهای صفحه نزدیک شده‌ایم
        if (document.documentElement.scrollHeight - scrollPosition <= 20) {
            bottomNav.style.bottom = "270px"; // وقتی به انتها رسیدیم 20 پیکسل بالاتر از پایین قرار بگیرد
            bottomNav.className = 'bottom-nav r'

        } else {
            bottomNav.style.bottom = "0"; // وقتی پایین صفحه نیستیم، در پایین باقی بماند
            bottomNav.className = 'bottom-nav'
        }
    });



      window.addEventListener("scroll", function () {
        var bottomNav = document.getElementById("bottom-nav");
        var scrollPosition = window.scrollY + window.innerHeight;

        if (document.documentElement.scrollHeight - scrollPosition <= 20) {
            bottomNav.style.bottom = "270px";
            bottomNav.className = 'bottom-nav r'
        } else {
            bottomNav.style.bottom = "0";
            bottomNav.className = 'bottom-nav'
        }
    });

