document.addEventListener('DOMContentLoaded', function () {
    const chatMessages = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatToggle = document.getElementById('chat-toggle');
    const chatContent = document.getElementById('chat-content');
    const chatIcon = document.getElementById('chat-icon');
    const chatHeader = document.getElementById('chat-header');

    let chatSocket = null;

    // ابتدا چت مخفی است
    chatContent.style.display = 'none';

    // تابع اضافه کردن پیام به چت
function appendMessage(data) {
    const messageEl = document.createElement('div');
    messageEl.classList.add('p-2', 'rounded', 'mb-2');
    if (data.sender_is_admin) {
        messageEl.classList.add('bg-light-green', 'text-end');
        messageEl.innerHTML = `<strong>ادمین:</strong> ${data.message || data.content}`;
    } else {
        messageEl.classList.add('bg-light-blue', 'text-start');
        messageEl.innerHTML = `<strong>شما:</strong> ${data.message || data.content}`;
    }

    if (data.is_welcome) {
        // 👈 پیام خوشامد همیشه بالای لیست
        chatMessages.insertBefore(messageEl, chatMessages.firstChild);
    } else {
        chatMessages.appendChild(messageEl);
    }

    chatMessages.scrollTop = chatMessages.scrollHeight;
}


    // باز کردن چت با کلیک روی آیکون
    chatToggle.addEventListener('click', function () {
        chatContent.style.display = 'block';
        setTimeout(() => {
            chatContent.classList.add('show');
        }, 10);
        chatIcon.style.display = 'none';

        // اگر وب‌سوکت ساخته نشده، بساز و پیام‌ها رو بارگذاری کن
        if (!chatSocket) {
            fetch('/api/chat/messages/')
                .then(response => response.json())
                .then(data => {
                    chatMessages.innerHTML = '';  // پاک کردن پیام‌های قبلی
                    data.messages.forEach(msg => {
                        appendMessage(msg);
                    });
                })
                .catch(error => {
                    console.error('خطا در دریافت پیام‌ها:', error);
                });

            const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
            chatSocket = new WebSocket(protocol + '://' + window.location.host + '/ws/chat/support/');

            chatSocket.onmessage = function (e) {
                const data = JSON.parse(e.data);
                appendMessage(data);
            };

            chatSocket.onclose = function (e) {
                console.error('WebSocket قطع شد:', e);
            };

            chatSocket.onerror = function (e) {
                console.error('WebSocket خطا:', e);
            };
        }
    });

    // بستن چت با کلیک روی هدر
    chatHeader.addEventListener('click', function () {
        chatContent.classList.remove('show');
        setTimeout(() => {
            chatContent.style.display = 'none';
            chatIcon.style.display = 'flex';
        }, 300); // مطابق با مدت زمان transition
    });

    // ارسال پیام
    chatForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const message = chatInput.value.trim();
        if (!message || !chatSocket || chatSocket.readyState !== WebSocket.OPEN) return;

        chatSocket.send(JSON.stringify({'message': message}));
        chatInput.value = '';
    });
});