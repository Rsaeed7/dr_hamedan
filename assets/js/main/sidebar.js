// Toggle sidebar on mobile
document.getElementById('sidebarToggle').addEventListener('click', function () {
    document.getElementById('sidebar').classList.toggle('active');
});

// Close sidebar when clicking outside on mobile
document.addEventListener('click', function (event) {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('sidebarToggle');

    if (window.innerWidth <= 992 &&
        !sidebar.contains(event.target) &&
        !toggleBtn.contains(event.target) &&
        sidebar.classList.contains('active')) {
        sidebar.classList.remove('active');
    }
});

// Prevent closing when clicking inside sidebar
document.getElementById('sidebar').addEventListener('click', function (event) {
    event.stopPropagation();
});


setTimeout(() => {
    const container = document.getElementById('toast-container');
    if (container) {
        container.classList.add('opacity-0', 'transition-opacity');
        setTimeout(() => container.remove(), 500);  // cleanup after fade-out
    }
}, 10000); // 10 seconds