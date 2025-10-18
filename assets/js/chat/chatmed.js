class MedicalChat {
    constructor(config) {
        this.roomId = config.roomId;
        this.currentUserId = config.currentUserId;
        this.uploadFileUrl = config.uploadFileUrl;
        this.isDoctor = config.isDoctor;
        this.csrfToken = config.csrfToken;
        
        this.currentFile = null;
        this.isUploading = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.audioBlob = null;
        
        this.elements = {};
        
        this.init();
    }

    init() {
        this.cacheElements();
        this.setupWebSocket();
        this.setupEventListeners();
        this.scrollToBottom();
        
        // اضافه کردن event listener برای تصاویر موجود
        document.querySelectorAll('img.message-image').forEach(img => {
            img.addEventListener('click', () => this.openImageModal(img.src));
        });
    }

    cacheElements() {
        this.elements = {
            fileInput: document.getElementById('file-input'),
            filePreviewContainer: document.getElementById('file-preview-container'),
            previewSendBtn: document.getElementById('preview-send-btn'),
            previewCancelBtn: document.getElementById('preview-cancel-btn'),
            previewMedia: document.getElementById('preview-media'),
            uploadProgressBar: document.getElementById('upload-progress-bar'),
            uploadStatus: document.getElementById('upload-status'),
            sendButton: document.getElementById('send-button'),
            sendIcon: document.getElementById('send-icon'),
            sendSpinner: document.getElementById('send-spinner'),
            textInput: document.getElementById('text-input'),
            attachmentButton: document.getElementById('attachment-button'),
            voiceButton: document.getElementById('voice-button'),
            voiceIcon: document.getElementById('voice-icon'),
            messageForm: document.getElementById('message-form'),
            chatMessages: document.getElementById('chat-messages'),
            imageModal: document.getElementById('imageModal'),
            modalImage: document.getElementById('modalImage'),
            sidebar: document.getElementById('sidebar'),
            sidebarToggle: document.getElementById('sidebar-toggle'),
            closeSidebar: document.getElementById('close-sidebar')
        };
    }

    setupWebSocket() {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        const wsPath = `${wsProtocol}${window.location.host}/ws/medical-chat/${this.roomId}/`;
        this.chatSocket = new WebSocket(wsPath);

        this.chatSocket.onmessage = (e) => this.handleMessage(e);
        this.chatSocket.onclose = (e) => this.handleClose(e);
        this.chatSocket.onerror = (e) => this.handleError(e);
    }

    setupEventListeners() {
        // فرم ارسال پیام
        this.elements.messageForm.addEventListener('submit', (e) => this.handleSubmit(e));
        
        // فایل
        this.elements.attachmentButton.addEventListener('click', () => this.elements.fileInput.click());
        this.elements.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        
        // پیش‌نمایش فایل
        this.elements.previewSendBtn.addEventListener('click', () => this.handlePreviewSend());
        this.elements.previewCancelBtn.addEventListener('click', () => this.cancelFileUpload());
        
        // ضبط صوت
        this.elements.voiceButton.addEventListener('click', () => this.toggleRecording());
        
        // ورودی متن
        this.elements.textInput.addEventListener('input', () => this.updateSendButtonState());
        
        // مدیریت سایدبار
        this.elements.sidebarToggle.addEventListener('click', () => this.toggleSidebar());
        this.elements.closeSidebar.addEventListener('click', () => this.closeSidebar());
        document.addEventListener('click', (e) => this.handleOutsideClick(e));
        
        // مدیریت modal
        this.elements.imageModal.addEventListener('click', (e) => this.handleModalClick(e));
        document.addEventListener('keydown', (e) => this.handleKeydown(e));
        
        // قبل از بسته شدن صفحه
        window.addEventListener('beforeunload', () => this.cleanup());
    }

    // ==================== مدیریت پیام‌ها ====================
    handleMessage(e) {
        const data = JSON.parse(e.data);
        this.appendMessage(data);
    }

    appendMessage(data) {
        const isSentByMe = data.sender_id === this.currentUserId;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isSentByMe ? 'sent' : 'received'}`;

        let messageContentHtml = '';
        if (data.message_type === 'text') {
            messageContentHtml = data.message.replace(/\n/g, '<br />');
        } else if (data.message_type === 'image' && data.file_url) {
            messageContentHtml = `<img src="${data.file_url}" class="message-image" />`;
        } else if (data.message_type === 'audio' && data.file_url) {
            messageContentHtml = `<audio controls><source src="${data.file_url}" type="audio/mpeg" />مرورگر شما از پخش صوت پشتیبانی نمی‌کند.</audio>`;
        } else if (data.message_type === 'file' && data.file_url) {
            messageContentHtml = `<a href="${data.file_url}" target="_blank" class="file-link">دانلود فایل <i class="icon-download-1"></i></a>`;
        } else {
            messageContentHtml = '<em>پیام نامشخص</em>';
        }

        messageDiv.innerHTML = `
            <div class="message-content">${messageContentHtml}</div>
            <div class="message-time">
                ${new Date(data.timestamp).toLocaleTimeString('fa-IR', { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                })}
                ${isSentByMe ? '<i class="icon-ok text-success ms-2" style="font-size: 8px;"></i>' : ''}
            </div>
        `;

        this.elements.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();

        // اضافه کردن event listener برای تصاویر جدید
        setTimeout(() => {
            const newImages = messageDiv.querySelectorAll('img.message-image');
            newImages.forEach(img => {
                img.addEventListener('click', () => this.openImageModal(img.src));
            });
        }, 100);
    }

    handleClose(e) {
        console.error('اتصال چت بسته شد', e);
    }

    handleError(e) {
        console.error('خطا در اتصال WebSocket', e);
    }

    // ==================== مدیریت فرم و ارسال ====================
    async handleSubmit(e) {
        e.preventDefault();
        const messageText = this.elements.textInput.value.trim();
        
        if (this.currentFile) {
            await this.uploadAndSendFile(this.currentFile, messageText);
        } else if (messageText) {
            this.sendTextMessage(messageText);
        }
    }

    async handlePreviewSend() {
        if (this.currentFile) {
            await this.uploadAndSendFile(this.currentFile, this.elements.textInput.value.trim());
        }
    }

    sendTextMessage(message) {
        if (this.chatSocket.readyState === WebSocket.OPEN) {
            this.chatSocket.send(JSON.stringify({
                message_type: 'text',
                message: message
            }));
            this.resetForm();
        } else {
            console.error('WebSocket connection is not open');
        }
    }

    // ==================== مدیریت فایل‌ها ====================
    handleFileSelect(e) {
        if (e.target.files.length > 0) {
            const file = e.target.files[0];
            this.currentFile = file;
            this.showFilePreview(file);
        }
    }

    showFilePreview(file) {
        this.elements.previewMedia.innerHTML = '';

        if (file.type.startsWith('image/')) {
            const img = document.createElement('img');
            img.className = 'message-image';
            img.alt = 'پیش‌نمایش تصویر';
            img.src = URL.createObjectURL(file);
            img.addEventListener('click', () => this.openImageModal(img.src));
            this.elements.previewMedia.appendChild(img);
        } else if (file.type.startsWith('audio/')) {
            const audio = document.createElement('audio');
            audio.controls = true;
            audio.src = URL.createObjectURL(file);
            this.elements.previewMedia.appendChild(audio);
        } else {
            const p = document.createElement('p');
            p.textContent = `فایل: ${file.name}`;
            this.elements.previewMedia.appendChild(p);
        }

        this.elements.filePreviewContainer.style.display = 'block';
        this.elements.uploadProgressBar.style.width = '0%';
        this.elements.uploadStatus.textContent = 'آماده برای ارسال';
        this.updateSendButtonState();
    }

    cancelFileUpload() {
        this.currentFile = null;
        this.elements.fileInput.value = '';
        this.elements.previewMedia.innerHTML = '';
        this.elements.filePreviewContainer.style.display = 'none';
        this.isUploading = false;
        this.elements.uploadProgressBar.style.width = '0%';
        this.elements.uploadStatus.textContent = 'آماده برای ارسال';
        this.updateSendButtonState();
    }

    // ==================== آپلود فایل ====================
    async uploadAndSendFile(file, caption = '') {
        if (this.isUploading) return;
        
        this.isUploading = true;
        this.updateSendButtonState();
        this.elements.uploadStatus.textContent = 'در حال آپلود...';

        try {
            const formData = new FormData();
            formData.append('file', file, file.name);
            formData.append('csrfmiddlewaretoken', this.csrfToken);

            this.simulateUploadProgress();

            const response = await fetch(this.uploadFileUrl, {
                method: 'POST',
                body: formData,
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.file_url) {
                this.elements.uploadProgressBar.style.width = '100%';
                this.elements.uploadStatus.textContent = 'در حال ارسال پیام...';

                if (this.chatSocket.readyState === WebSocket.OPEN) {
                    this.chatSocket.send(JSON.stringify({
                        message_type: this.getMessageTypeFromFile(file),
                        file_url: data.file_url,
                        message: caption
                    }));

                    this.resetForm();
                    this.elements.uploadStatus.textContent = 'ارسال شد!';

                    setTimeout(() => {
                        this.elements.filePreviewContainer.style.display = 'none';
                        this.elements.previewMedia.innerHTML = '';
                    }, 1000);
                } else {
                    throw new Error('اتصال چت برقرار نیست');
                }
            } else {
                throw new Error('خطا در آپلود فایل: آدرس فایل دریافت نشد');
            }
        } catch (error) {
            console.error('Error uploading file:', error);
            this.elements.uploadStatus.textContent = 'خطا در آپلود فایل';
            this.elements.uploadProgressBar.style.backgroundColor = '#f44336';
            alert('خطا در آپلود فایل: ' + (error.message || error));
        } finally {
            this.isUploading = false;
            this.updateSendButtonState();
        }
    }

    simulateUploadProgress() {
        this.elements.uploadProgressBar.style.backgroundColor = '#4caf50';
        let progress = 0;
        const interval = setInterval(() => {
            if (!this.isUploading) {
                clearInterval(interval);
                return;
            }
            if (progress >= 90) {
                clearInterval(interval);
                return;
            }
            progress += Math.random() * 15;
            if (progress > 90) progress = 90;
            this.elements.uploadProgressBar.style.width = progress + '%';
        }, 200);
    }

    getMessageTypeFromFile(file) {
        if (!file) return 'text';
        const type = file.type || '';
        if (type.startsWith('image/')) return 'image';
        if (type.startsWith('audio/')) return 'audio';
        if (type.startsWith('video/')) return 'video';
        return 'file';
    }

    // ==================== ضبط صوت ====================
    async toggleRecording() {
        if (!this.isRecording) {
            await this.startRecording();
        } else {
            this.stopRecording();
        }
    }

    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];
            
            this.mediaRecorder.ondataavailable = (ev) => this.audioChunks.push(ev.data);
            this.mediaRecorder.onstop = () => {
                this.audioBlob = new Blob(this.audioChunks, { type: 'audio/mpeg' });
                const audioFile = new File([this.audioBlob], `voice_${Date.now()}.mp3`, { type: 'audio/mpeg' });
                
                this.currentFile = audioFile;
                this.showFilePreview(this.currentFile);

                try {
                    stream.getTracks().forEach(track => track.stop());
                } catch (e) {
                    console.error('Error stopping tracks:', e);
                }
                
                this.elements.voiceButton.classList.remove('recording');
                this.isRecording = false;
            };

            this.mediaRecorder.start();
            this.isRecording = true;
            this.elements.voiceButton.classList.add('recording');
            this.elements.uploadStatus.textContent = 'در حال ضبط...';
        } catch (err) {
            console.error('خطا در دسترسی به میکروفن', err);
            alert('برای ضبط صدا باید دسترسی میکروفن را فعال کنید.');
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
        }
        this.elements.voiceButton.classList.remove('recording');
        this.elements.uploadStatus.textContent = 'پایان ضبط — پیش‌نمایش آماده است';
    }

    // ==================== مدیریت وضعیت دکمه‌ها ====================
    updateSendButtonState() {
        const hasText = this.elements.textInput.value.trim() !== '';
        const hasFile = this.currentFile !== null;

        if (this.isUploading) {
            this.elements.sendButton.disabled = true;
            this.elements.sendButton.classList.add('send-button-loading');
            this.elements.sendIcon.style.display = 'none';
            this.elements.sendSpinner.style.display = 'block';
        } else {
            this.elements.sendButton.disabled = !hasText && !hasFile;
            this.elements.sendButton.classList.remove('send-button-loading');
            this.elements.sendIcon.style.display = 'block';
            this.elements.sendSpinner.style.display = 'none';
        }
    }

    resetForm() {
        this.elements.textInput.value = '';
        this.currentFile = null;
        this.elements.fileInput.value = '';
        this.elements.previewMedia.innerHTML = '';
        this.elements.filePreviewContainer.style.display = 'none';
        this.elements.uploadProgressBar.style.width = '0%';
        this.elements.uploadStatus.textContent = 'آماده برای ارسال';
        this.updateSendButtonState();
    }

    // ==================== مدیریت Modal تصویر ====================
    openImageModal(imageUrl) {
        this.elements.modalImage.src = imageUrl;
        this.elements.imageModal.style.display = 'block';
        document.body.style.overflow = 'hidden';
        this.isZoomed = false;
        this.elements.imageModal.classList.remove('zoomed');
    }

    closeImageModal() {
        this.elements.imageModal.style.display = 'none';
        document.body.style.overflow = 'auto';
        this.isZoomed = false;
        this.elements.imageModal.classList.remove('zoomed');
    }

    toggleZoom() {
        this.isZoomed = !this.isZoomed;
        if (this.isZoomed) {
            this.elements.imageModal.classList.add('zoomed');
        } else {
            this.elements.imageModal.classList.remove('zoomed');
        }
    }

    handleModalClick(e) {
        if (e.target === this.elements.imageModal) {
            this.closeImageModal();
        }
    }

    handleKeydown(e) {
        if (e.key === 'Escape') {
            this.closeImageModal();
        }
    }

    // ==================== مدیریت سایدبار ====================
    toggleSidebar() {
        this.elements.sidebar.classList.toggle('active');
    }

    closeSidebar() {
        this.elements.sidebar.classList.remove('active');
    }

    handleOutsideClick(e) {
        if (!this.elements.sidebar.contains(e.target) && 
            e.target !== this.elements.sidebarToggle && 
            !this.elements.sidebarToggle.contains(e.target)) {
            this.elements.sidebar.classList.remove('active');
        }
    }

    // ==================== Utility Functions ====================
    scrollToBottom() {
        if (this.elements.chatMessages) {
            this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
        }
    }

    cleanup() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            try {
                this.mediaRecorder.stop();
            } catch (e) {
                console.error('Error stopping recorder:', e);
            }
        }
        
        if (this.chatSocket && this.chatSocket.readyState === WebSocket.OPEN) {
            this.chatSocket.close();
        }
    }
}

// مقداردهی زمانی که DOM لود شد
document.addEventListener('DOMContentLoaded', function() {
    if (window.chatConfig) {
        window.medicalChat = new MedicalChat(window.chatConfig);
    } else {
        console.error('Chat configuration not found');
    }
});

// توابع عمومی برای فراخوانی از HTML
function openImageModal(imageUrl) {
    if (window.medicalChat) {
        window.medicalChat.openImageModal(imageUrl);
    }
}

function closeImageModal() {
    if (window.medicalChat) {
        window.medicalChat.closeImageModal();
    }
}

function toggleZoom() {
    if (window.medicalChat) {
        window.medicalChat.toggleZoom();
    }
}