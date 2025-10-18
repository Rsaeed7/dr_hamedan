const config = document.getElementById('notification-config');
const csrfToken = config.dataset.csrfToken;
const markReadUrl = config.dataset.markReadUrl;
const markAllUrl = config.dataset.markAllUrl;
const deleteUrl = config.dataset.deleteUrl;

function markNotificationRead(id) {
    fetch(markReadUrl.replace('0', id), {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json',
        },
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            const el = document.querySelector(`[data-notification-id="${id}"]`);
            if (el) {
                el.classList.remove('notification-unread', 'bg-blue-50');
                el.classList.add('notification-read', 'bg-white');
                const badge = el.querySelector('.bg-blue-100');
                if (badge) badge.remove();
                const btn = el.querySelector('button[onclick*="markNotificationRead"]');
                if (btn) btn.remove();
            }
        }
    })
    .catch(console.error);
}

function markAllNotificationsRead() {
    fetch(markAllUrl, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json',
        },
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            document.querySelectorAll('.notification-item').forEach(el => {
                el.classList.remove('notification-unread', 'bg-blue-50');
                el.classList.add('notification-read', 'bg-white');
                const badge = el.querySelector('.bg-blue-100');
                if (badge) badge.remove();
                const btn = el.querySelector('button[onclick*="markNotificationRead"]');
                if (btn) btn.remove();
            });
            const markAllBtn = document.querySelector('button[onclick="markAllNotificationsRead()"]');
            if (markAllBtn) markAllBtn.style.display = 'none';
        }
    })
    .catch(console.error);
}

function deleteNotification(id) {
    if (!confirm('آیا مطمئن هستید؟')) return;
    fetch(deleteUrl.replace('0', id), {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json',
        },
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            const el = document.querySelector(`[data-notification-id="${id}"]`);
            if (el) {
                el.style.opacity = '0';
                setTimeout(() => el.remove(), 300);
            }
        }
    })
    .catch(console.error);
}
