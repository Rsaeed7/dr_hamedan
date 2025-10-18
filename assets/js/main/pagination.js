function createPagination(totalPages, currentPage) {
    var paginationContainer = document.getElementById('pagination');
    
    // اگر المان pagination وجود نداشت، خطا نده
    if (!paginationContainer) {
        console.log('Pagination container not found');
        return;
    }
    
    paginationContainer.innerHTML = '';

    if (totalPages <= 1) return;

    var maxVisiblePages = 5;
    var startPage, endPage;

    if (totalPages <= maxVisiblePages) {
        startPage = 1;
        endPage = totalPages;
    } else {
        var maxPagesBeforeCurrentPage = Math.floor(maxVisiblePages / 2);
        var maxPagesAfterCurrentPage = Math.ceil(maxVisiblePages / 2) - 1;

        if (currentPage <= maxPagesBeforeCurrentPage) {
            startPage = 1;
            endPage = maxVisiblePages;
        } else if (currentPage + maxPagesAfterCurrentPage >= totalPages) {
            startPage = totalPages - maxVisiblePages + 1;
            endPage = totalPages;
        } else {
            startPage = currentPage - maxPagesBeforeCurrentPage;
            endPage = currentPage + maxPagesAfterCurrentPage;
        }
    }

    // ایجاد دکمه اولین صفحه
    if (startPage > 1) {
        var firstPage = document.createElement('li');
        firstPage.innerHTML = '<a class="page-link border-0 down-3" href="#" data-page="1"><i class="icon-right-open-3"></i></a>';
        paginationContainer.appendChild(firstPage);

        if (startPage > 2) {
            var dots = document.createElement('li');
            dots.innerHTML = '<span class="page-link border-0 down-2">...</span>';
            paginationContainer.appendChild(dots);
        }
    }

    // ایجاد صفحات
    for (var page = startPage; page <= endPage; page++) {
        var pageItem = document.createElement('li');
        pageItem.classList.add('page-iter');
        if (page === currentPage) {
            pageItem.classList.add('active');
        }
        pageItem.innerHTML = `<a class="page-link" href="#" data-page="${page}">${page}</a>`;
        paginationContainer.appendChild(pageItem);
    }

    // ایجاد دکمه آخرین صفحه
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            var dots = document.createElement('li');
            dots.innerHTML = '<span class="page-link border-0 down-2">...</span>';
            paginationContainer.appendChild(dots);
        }

        var lastPage = document.createElement('li');
        lastPage.innerHTML = `<a class="page-link border-0 down-3" href="#" data-page="${totalPages}"><i class="icon-left-open-3"></i></a>`;
        paginationContainer.appendChild(lastPage);
    }
}

function initPagination() {
    // بررسی وجود کانفیگ
    if (!window.paginationConfig) {
        console.error('Pagination config not found');
        return;
    }
    
    var currentPage = window.paginationConfig.currentPage;
    var totalPages = window.paginationConfig.totalPages;

    console.log('Initializing pagination - Current Page:', currentPage, 'Total Pages:', totalPages);

    createPagination(totalPages, currentPage);

    var paginationElement = document.getElementById('pagination');
    if (paginationElement) {
        paginationElement.addEventListener('click', function (event) {
            if (event.target.tagName === 'A' || event.target.tagName === 'I') {
                event.preventDefault();
                var pageParam = event.target.getAttribute('data-page') || 
                              event.target.parentElement.getAttribute('data-page');
                
                console.log('Page clicked:', pageParam);
                
                var urlParams = new URLSearchParams(window.location.search);
                urlParams.set('page', pageParam);
                window.location.search = urlParams.toString();
            }
        });
    }
}

// راه اندازی وقتی DOM آماده شد
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing pagination...');
    initPagination();
});

// اگر DOM از قبل لود شده باشه
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(initPagination, 1);
}