// chat-room.js

class ChatRoom {
    constructor() {
        this.roomId = null;
        this.chatSocket = null;
        this.init();
    }

    init() {
        this.loadRoomId();
        this.initializeWebSocket();
        this.setupEventListeners();
    }

    loadRoomId() {
        try {
            const roomIdElement = document.getElementById('room-id');
            if (!roomIdElement) {
                throw new Error('Room ID element not found');
            }

            this.roomId = JSON.parse(roomIdElement.textContent);

            if (!this.roomId) {
                console.error("Room ID is missing!");
                return false;
            }

            return true;
        } catch (error) {
            console.error('Error loading room ID:', error);
            return false;
        }
    }

    initializeWebSocket() {
        if (!this.roomId) return;

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        const wsUrl = `${protocol}//${host}/ws/chat/${this.roomId}/`;

        console.log('Connecting to WebSocket:', wsUrl);

        this.chatSocket = new WebSocket(wsUrl);

        this.chatSocket.onopen = () => {
            console.log("✅ WebSocket connection established.");
            this.updateConnectionStatus('متصل', 'success');
        };

        this.chatSocket.onclose = (e) => {
            console.error("WebSocket closed:", e);
            this.handleConnectionClose(e);
        };

        this.chatSocket.onerror = (error) => {
            console.error("WebSocket error:", error);
            this.updateConnectionStatus('خطا', 'error');
        };

        this.chatSocket.onmessage = (e) => {
            this.handleNewMessage(e);
        };
    }

    updateConnectionStatus(text, type) {
        const statusElement = document.getElementById('connection-status');
        if (!statusElement) return;

        statusElement.textContent = text;

        if (type === 'success') {
            statusElement.classList.add('text-green-500');
            statusElement.classList.remove('text-red-500');
        } else {
            statusElement.classList.add('text-red-500');
            statusElement.classList.remove('text-green-500');
        }
    }

    handleConnectionClose(e) {
        if (e.code !== 1000) {  // Not a normal closure
            setTimeout(() => {
                console.log("Attempting to reconnect...");
                location.reload();
            }, 5000);
        }
        this.updateConnectionStatus('متصل نیست', 'error');
    }

    handleNewMessage(e) {
        try {
            const data = JSON.parse(e.data);
            const chatMessages = document.getElementById('chat-messages');

            if (!chatMessages) {
                console.error('Chat messages container not found');
                return;
            }

            const messageElement = this.createMessageElement(data);
            chatMessages.appendChild(messageElement);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        } catch (error) {
            console.error('Error handling new message:', error);
        }
    }

    createMessageElement(data) {
        const wrapper = document.createElement('div');
        wrapper.className = `flex ${data.sender_is_admin ? 'justify-end' : 'justify-start'}`;

        const bubble = document.createElement('div');
        bubble.className = `max-w-md rounded-xl p-3 shadow ${
            data.sender_is_admin ? 'bg-green-100 text-right' : 'bg-blue-100 text-left'
        }`;

        const name = document.createElement('div');
        name.className = `font-semibold text-sm ${
            data.sender_is_admin ? 'text-green-800' : 'text-blue-800'
        }`;
        name.textContent = data.sender;

        const text = document.createElement('p');
        text.className = 'mt-1 text-gray-800 break-words';
        text.textContent = data.message;

        const time = document.createElement('div');
        time.className = 'text-xs mt-1 text-gray-400';
        time.textContent = data.timestamp;

        bubble.appendChild(name);
        bubble.appendChild(text);
        bubble.appendChild(time);
        wrapper.appendChild(bubble);

        return wrapper;
    }

    setupEventListeners() {
        const messageForm = document.getElementById('message-form');
        if (messageForm) {
            messageForm.addEventListener('submit', (e) => this.handleMessageSubmit(e));
        }
    }

    handleMessageSubmit(e) {
        e.preventDefault();

        const input = e.target.querySelector('input[name="content"]');
        if (!input) return;

        const content = input.value.trim();
        if (!content) return;

        if (!this.chatSocket || this.chatSocket.readyState !== WebSocket.OPEN) {
            alert('اتصال برقرار نیست. لطفاً دوباره تلاش کنید.');
            return;
        }

        try {
            this.chatSocket.send(JSON.stringify({ message: content }));
            input.value = '';
            input.focus();
        } catch (error) {
            console.error('Error sending message:', error);
            alert('خطا در ارسال پیام');
        }
    }

    // متد برای بستن اتصال
    disconnect() {
        if (this.chatSocket) {
            this.chatSocket.close(1000, 'User initiated disconnect');
        }
    }
}

// مقداردهی اولیه هنگامی که DOM آماده است
document.addEventListener('DOMContentLoaded', function() {
    window.chatRoom = new ChatRoom();
});

// مدیریت زمانی که کاربر صفحه را ترک می‌کند
window.addEventListener('beforeunload', function() {
    if (window.chatRoom) {
        window.chatRoom.disconnect();
    }
});