// گرفتن URLهای لازم از HTML
const configEl = document.getElementById('notification-config');
const markReadUrl = configEl.dataset.markReadUrl;
const markAllUrl = configEl.dataset.markAllUrl;
const deleteUrl = configEl.dataset.deleteUrl;
const getUrl = configEl.dataset.getUrl;

// گرفتن CSRF از کوکی
function getCSRFToken() {
    const name = 'csrftoken';
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + '=')) {
            return cookie.substring(name.length + 1);
        }
    }
    return '';
}

// علامت‌گذاری یک اعلان به‌عنوان خوانده‌شده
function markNotificationRead(notificationId) {
    fetch(markReadUrl.replace('0', notificationId), {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json',
        },
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const item = document.querySelector(`[data-notification-id="${notificationId}"]`);
                if (item) {
                    item.classList.remove('bg-blue-50');
                    const unreadDot = item.querySelector('.bg-blue-500');
                    if (unreadDot) unreadDot.remove();
                    const btn = item.querySelector('button[onclick*="markNotificationRead"]');
                    if (btn) btn.remove();
                }
                updateNotificationCount();
            }
        })
        .catch(err => console.error(err));
}

// علامت‌گذاری همه اعلان‌ها
function markAllNotificationsRead() {
    fetch(markAllUrl, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json',
        },
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                document.querySelectorAll('.notification-item').forEach(item => {
                    item.classList.remove('bg-blue-50');
                    const dot = item.querySelector('.bg-blue-500');
                    if (dot) dot.remove();
                    const btn = item.querySelector('button[onclick*="markNotificationRead"]');
                    if (btn) btn.remove();
                });

                const markAllBtn = document.querySelector('button[onclick="markAllNotificationsRead()"]');
                if (markAllBtn) markAllBtn.style.display = 'none';

                updateNotificationCount();
            }
        })
        .catch(err => console.error(err));
}

// حذف یک اعلان
function deleteNotification(notificationId) {
    if (!confirm('آیا مطمئن هستید که می‌خواهید این اعلان را حذف کنید؟')) return;

    fetch(deleteUrl.replace('0', notificationId), {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json',
        },
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const item = document.querySelector(`[data-notification-id="${notificationId}"]`);
                if (item) item.remove();
                updateNotificationCount();

                if (document.querySelectorAll('.notification-item').length === 0) {
                    document.getElementById('notifications-container').innerHTML = `
                    <div class="text-center py-8 bg-gray-50 rounded-10">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 mx-auto mb-3 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 17h5l-5 5-5-5h5v-5a7.5 7.5 0 01-7.5-7.5"/>
                        </svg>
                        <h3 class="text-lg font-bold text_dr mb-1">اعلان جدیدی ندارید</h3>
                        <p class="text-secondary text-sm">اعلان‌های جدید در اینجا نمایش داده خواهند شد</p>
                    </div>
                `;
                }
            }
        })
        .catch(err => console.error(err));
}

// به‌روزرسانی شمارنده اعلان‌ها در هدر (در صورت نیاز)
function updateNotificationCount() {
    // بسته به ساختار هدر شما قابل شخصی‌سازی است
}

// هر ۳۰ ثانیه بروزرسانی اعلان‌ها
setInterval(() => {
    fetch(getUrl + '?limit=5')
        .then(res => res.json())
        .then(data => {
            const badge = document.querySelector('.notification-count');
            if (badge) {
                badge.textContent = data.unread_count;
                badge.style.display = data.unread_count > 0 ? 'inline' : 'none';
            }
        })
        .catch(err => console.error('Error fetching notifications:', err));
}, 30000);
