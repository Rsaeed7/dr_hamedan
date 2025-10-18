document.addEventListener("DOMContentLoaded", function () {
    const mainItemsContainer = document.getElementById("mainItems");
    const extraItemsContainer = document.getElementById("extraItems");
    const showMoreBtn = document.getElementById("showMoreBtn");
    const arrowIcon = document.getElementById("arrowIcon");

    // اگر المان‌ها وجود ندارند، خطا نده
    if (!mainItemsContainer || !extraItemsContainer || !showMoreBtn || !arrowIcon) {
        console.log('Show more items elements not found');
        return;
    }

    function handleItems() {
        const allItems = mainItemsContainer.querySelectorAll(".col-lg-3");
        extraItemsContainer.innerHTML = "";

        let visibleCount;
        if (window.innerWidth >= 992) {
            visibleCount = 8;
        } else if (window.innerWidth >= 768) {
            visibleCount = 4;
        } else {
            visibleCount = 3;
        }

        if (allItems.length > visibleCount) {
            allItems.forEach((item, index) => {
                item.classList.remove('fade-slide', 'show');
                if (index >= visibleCount) {
                    item.classList.add('fade-slide');
                    extraItemsContainer.appendChild(item);
                }
            });
            showMoreBtn.style.display = "inline-block";
        } else {
            showMoreBtn.style.display = "none";
        }

        extraItemsContainer.style.height = "0";
        extraItemsContainer.style.opacity = "0";
        arrowIcon.classList.remove("icon-up-open");
        arrowIcon.classList.add("icon-down-open");
        arrowIcon.style.transform = "rotate(0deg)";
    }

    handleItems();
    window.addEventListener("resize", handleItems);

    showMoreBtn.addEventListener("click", function () {
        const isHidden = extraItemsContainer.style.height === "0px" || extraItemsContainer.style.height === "";

        if (isHidden) {
            let fullHeight = extraItemsContainer.scrollHeight + "px";
            extraItemsContainer.style.height = fullHeight;
            extraItemsContainer.style.opacity = "1";
            arrowIcon.classList.remove("icon-down-open");
            arrowIcon.classList.add("icon-up-open");
            arrowIcon.style.transform = "rotate(180deg)";

            setTimeout(() => {
                extraItemsContainer.style.height = "auto";

                const items = extraItemsContainer.querySelectorAll('.fade-slide');
                items.forEach((item, index) => {
                    setTimeout(() => {
                        item.classList.add('show');
                    }, index * 100);
                });

            }, 600);

        } else {
            extraItemsContainer.style.height = extraItemsContainer.scrollHeight + "px";
            setTimeout(() => {
                extraItemsContainer.style.height = "0";
            }, 10);
            extraItemsContainer.style.opacity = "0";
            arrowIcon.classList.remove("icon-up-open");
            arrowIcon.classList.add("icon-down-open");
            arrowIcon.style.transform = "rotate(0deg)";
        }
    });
});



    // اسکریپت مدیریت آلرت‌ها (اضافه شده)
    document.addEventListener('DOMContentLoaded', function () {
        const alerts = document.querySelectorAll('.floating-alert');

        alerts.forEach(alert => {
            setTimeout(() => {
                alert.classList.add('fade-out');
                setTimeout(() => alert.remove(), 500);
            }, 3000);
        });
    });