class DocPageManager {
    constructor(config) {
        this.config = config || {};
        this.selectedLenses = [];
        this.searchTimeout = null;
        this.init();
    }

    init() {
        this.setupFormActions();
        this.setupSidebar();
        this.setupMediaUpload();
        this.setupLensSearch();
        this.setupPostFiltering();
        this.setupGlobalEvents();

        // Initialize with existing medical lenses if any
        this.initializeExistingLenses();
    }

    // ==================== مدیریت فرم ====================
    setupFormActions() {
        // تعریف تابع setAction برای backward compatibility
        window.setAction = (action) => {
            const actionInput = document.getElementById('action');
            const postForm = document.getElementById('postForm');

            if (actionInput && postForm) {
                actionInput.value = action;
                postForm.submit();
            }
        };
    }

    // ==================== سایدبار موبایل ====================
    setupSidebar() {
        const toggleButton = document.getElementById('sidebarToggle');
        const closeButton = document.getElementById('closeSidebar');
        const sidebar = document.getElementById('sidebar');

        if (toggleButton && closeButton && sidebar) {
            toggleButton.addEventListener('click', () => {
                sidebar.classList.add('active');
                document.body.style.overflow = 'hidden';
            });

            closeButton.addEventListener('click', () => {
                sidebar.classList.remove('active');
                document.body.style.overflow = 'auto';
            });

            // بستن سایدبار با کلیک خارج
            document.addEventListener('click', (e) => {
                if (sidebar.classList.contains('active') &&
                    !sidebar.contains(e.target) &&
                    e.target !== toggleButton) {
                    sidebar.classList.remove('active');
                    document.body.style.overflow = 'auto';
                }
            });
        }

        // مدیریت سایدبار لیست پست‌ها
        const sidebarToggle = document.getElementById('sidebarToggle');
        const closeSidebar = document.getElementById('closeSidebar');
        const postsSidebar = document.getElementById('sidebar');

        if (sidebarToggle && closeSidebar && postsSidebar) {
            sidebarToggle.addEventListener('click', () => {
                postsSidebar.classList.add('active');
                document.body.style.overflow = 'hidden';
            });

            closeSidebar.addEventListener('click', () => {
                postsSidebar.classList.remove('active');
                document.body.style.overflow = 'auto';
            });

            // بستن سایدبار با کلیک خارج
            document.addEventListener('click', (e) => {
                if (postsSidebar.classList.contains('active') &&
                    !postsSidebar.contains(e.target) &&
                    e.target !== sidebarToggle) {
                    postsSidebar.classList.remove('active');
                    document.body.style.overflow = 'auto';
                }
            });
        }
    }

    // ==================== فیلتر کردن پست‌ها ====================
    setupPostFiltering() {
        const showAllBtn = document.getElementById('show-all');
        const showPublishedBtn = document.getElementById('show-published');
        const showDraftsBtn = document.getElementById('show-drafts');
        const posts = document.querySelectorAll('.post-card');

        if (showAllBtn && showPublishedBtn && showDraftsBtn && posts.length > 0) {
            showAllBtn.addEventListener('click', () => {
                this.setActiveFilter(showAllBtn);
                this.showAllPosts(posts);
            });

            showPublishedBtn.addEventListener('click', () => {
                this.setActiveFilter(showPublishedBtn);
                this.showPublishedPosts(posts);
            });

            showDraftsBtn.addEventListener('click', () => {
                this.setActiveFilter(showDraftsBtn);
                this.showDraftPosts(posts);
            });

            // فعال کردن فیلتر پیش‌فرض
            this.setActiveFilter(showAllBtn);
        }
    }

    setActiveFilter(activeBtn) {
        const buttons = document.querySelectorAll('#show-all, #show-published, #show-drafts');
        buttons.forEach(btn => {
            if (btn) {
                btn.classList.remove('text-blue-600', 'border-b-2', 'border-blue-600');
                btn.classList.add('text-gray-500', 'hover:text-gray-700');
            }
        });

        if (activeBtn) {
            activeBtn.classList.remove('text-gray-500', 'hover:text-gray-700');
            activeBtn.classList.add('text-blue-600', 'border-b-2', 'border-blue-600');
        }
    }

    showAllPosts(posts) {
        posts.forEach(post => {
            post.style.display = 'block';
            post.style.opacity = '0';
            setTimeout(() => {
                post.style.opacity = '1';
                post.style.transition = 'opacity 0.3s ease';
            }, 10);
        });
    }

    showPublishedPosts(posts) {
        posts.forEach(post => {
            if (post.dataset.status === 'published') {
                post.style.display = 'block';
                post.style.opacity = '0';
                setTimeout(() => {
                    post.style.opacity = '1';
                    post.style.transition = 'opacity 0.3s ease';
                }, 10);
            } else {
                post.style.display = 'none';
            }
        });
    }

    showDraftPosts(posts) {
        posts.forEach(post => {
            if (post.dataset.status === 'draft') {
                post.style.display = 'block';
                post.style.opacity = '0';
                setTimeout(() => {
                    post.style.opacity = '1';
                    post.style.transition = 'opacity 0.3s ease';
                }, 10);
            } else {
                post.style.display = 'none';
            }
        });
    }

    // ==================== آپلود مدیا ====================
    setupMediaUpload() {
        const imageInput = document.getElementById('image');
        const videoInput = document.getElementById('video');

        if (imageInput) {
            imageInput.addEventListener('change', (e) => this.handleImageUpload(e));
        }

        if (videoInput) {
            videoInput.addEventListener('change', (e) => this.handleVideoUpload(e));
        }

        // تعریف توابع remove برای backward compatibility
        window.removeImage = () => this.removeImage();
        window.removeVideo = () => this.removeVideo();
    }

    handleImageUpload(e) {
        if (e.target.files && e.target.files[0]) {
            const videoInput = document.getElementById('video');
            const videoPreview = document.getElementById('video-preview');
            const videoSection = document.getElementById('video-upload-section');
            const imagePreview = document.getElementById('image-preview');
            const imageSection = document.getElementById('image-upload-section');

            // Clear video if image is selected
            if (videoInput) videoInput.value = '';
            if (videoPreview) videoPreview.classList.add('hidden');
            if (videoSection) {
                videoSection.classList.remove('has-file');
                videoSection.classList.add('disabled');
            }

            const file = e.target.files[0];
            const reader = new FileReader();

            reader.onload = function(e) {
                const previewImg = document.getElementById('image-preview-img');
                if (previewImg) previewImg.src = e.target.result;
                if (imagePreview) imagePreview.classList.remove('hidden');
                if (imageSection) {
                    imageSection.classList.add('has-file');
                }
            };

            reader.readAsDataURL(file);
        }
    }

    handleVideoUpload(e) {
        if (e.target.files && e.target.files[0]) {
            const imageInput = document.getElementById('image');
            const imagePreview = document.getElementById('image-preview');
            const imageSection = document.getElementById('image-upload-section');
            const videoPreview = document.getElementById('video-preview');
            const videoSection = document.getElementById('video-upload-section');

            // Clear image if video is selected
            if (imageInput) imageInput.value = '';
            if (imagePreview) imagePreview.classList.add('hidden');
            if (imageSection) {
                imageSection.classList.remove('has-file');
                imageSection.classList.add('disabled');
            }

            const file = e.target.files[0];
            const url = URL.createObjectURL(file);

            const videoSource = document.getElementById('video-source');
            const videoPreviewVideo = document.getElementById('video-preview-video');

            if (videoSource) videoSource.src = url;
            if (videoPreviewVideo) videoPreviewVideo.load();
            if (videoPreview) videoPreview.classList.remove('hidden');
            if (videoSection) {
                videoSection.classList.add('has-file');
            }
        }
    }

    removeImage() {
        const imageInput = document.getElementById('image');
        const imagePreview = document.getElementById('image-preview');
        const imageSection = document.getElementById('image-upload-section');
        const videoSection = document.getElementById('video-upload-section');

        if (imageInput) imageInput.value = '';
        if (imagePreview) imagePreview.classList.add('hidden');
        if (imageSection) imageSection.classList.remove('has-file');
        if (videoSection) videoSection.classList.remove('disabled');
    }

    removeVideo() {
        const videoInput = document.getElementById('video');
        const videoPreview = document.getElementById('video-preview');
        const videoSection = document.getElementById('video-upload-section');
        const imageSection = document.getElementById('image-upload-section');

        if (videoInput) videoInput.value = '';
        if (videoPreview) videoPreview.classList.add('hidden');
        if (videoSection) videoSection.classList.remove('has-file');
        if (imageSection) imageSection.classList.remove('disabled');
    }

    // ==================== جستجوی لنزهای پزشکی ====================
    setupLensSearch() {
        const lensSearch = document.getElementById('lens-search');
        if (lensSearch) {
            lensSearch.addEventListener('input', (e) => this.handleLensSearch(e));
        }

        // تعریف تابع removeLens برای backward compatibility
        window.removeLens = (lensId) => this.removeLens(lensId);
    }

    handleLensSearch(e) {
        const query = e.target.value.trim();
        const lensSuggestions = document.getElementById('lens-suggestions');

        clearTimeout(this.searchTimeout);

        if (query.length < 2) {
            if (lensSuggestions) lensSuggestions.style.display = 'none';
            return;
        }

        this.searchTimeout = setTimeout(() => {
            this.searchMedicalLenses(query);
        }, 300);
    }

    searchMedicalLenses(query) {
        const searchUrl = this.config.lensSearchUrl || '/docpages/ajax/search-medical-lenses/';

        fetch(`${searchUrl}?q=${encodeURIComponent(query)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    this.displayLensSuggestions(data.lenses);
                }
            })
            .catch(error => {
                console.error('Error searching medical lenses:', error);
            });
    }

    displayLensSuggestions(lenses) {
        const lensSuggestions = document.getElementById('lens-suggestions');
        if (!lensSuggestions) return;

        lensSuggestions.innerHTML = '';

        if (lenses.length === 0) {
            lensSuggestions.style.display = 'none';
            return;
        }

        const filteredLenses = lenses.filter(lens =>
            !this.selectedLenses.find(selected => selected.id === lens.id)
        );

        if (filteredLenses.length === 0) {
            lensSuggestions.style.display = 'none';
            return;
        }

        filteredLenses.forEach(lens => {
            const suggestion = document.createElement('div');
            suggestion.className = 'medical-lens-suggestion cursor-pointer p-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0';
            suggestion.innerHTML = `
                <div class="flex items-center space-x-3 space-x-reverse">
                    <div class="medical-lens-color w-4 h-4 rounded-full" style="background-color: ${lens.color};"></div>
                    <div class="flex-1">
                        <div class="font-medium text-sm text-gray-800">${lens.name}</div>
                        <div class="text-xs text-gray-500 mt-1">${lens.description}</div>
                    </div>
                </div>
            `;

            suggestion.addEventListener('click', () => {
                this.selectLens(lens);
                const lensSearch = document.getElementById('lens-search');
                if (lensSearch) lensSearch.value = '';
                lensSuggestions.style.display = 'none';
            });

            lensSuggestions.appendChild(suggestion);
        });

        lensSuggestions.style.display = 'block';
    }

    selectLens(lens) {
        if (this.selectedLenses.find(selected => selected.id === lens.id)) {
            return;
        }

        this.selectedLenses.push(lens);
        this.updateSelectedLensesDisplay();
    }

    removeLens(lensId) {
        this.selectedLenses = this.selectedLenses.filter(lens => lens.id !== lensId);
        this.updateSelectedLensesDisplay();
    }

    updateSelectedLensesDisplay() {
        const selectedLensesContainer = document.getElementById('selected-lenses');
        const lensInputsContainer = document.getElementById('lens-inputs');

        // Update visual display
        if (selectedLensesContainer) {
            selectedLensesContainer.innerHTML = '';

            this.selectedLenses.forEach(lens => {
                const lensElement = document.createElement('div');
                lensElement.className = 'selected-lens inline-flex items-center px-3 py-1 rounded-full text-white text-sm font-medium mr-2 mb-2';
                lensElement.style.backgroundColor = lens.color;
                lensElement.innerHTML = `
                    ${lens.name}
                    <span class="remove-lens mr-2 cursor-pointer hover:opacity-75" onclick="docPageManager.removeLens(${lens.id})">&times;</span>
                `;
                selectedLensesContainer.appendChild(lensElement);
            });
        }

        // Update hidden inputs
        if (lensInputsContainer) {
            lensInputsContainer.innerHTML = '';

            this.selectedLenses.forEach(lens => {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'medical_lenses';
                input.value = lens.id;
                lensInputsContainer.appendChild(input);
            });
        }
    }

    // ==================== لنزهای موجود ====================
    initializeExistingLenses() {
        // این بخش برای صفحه ویرایش استفاده می‌شود
        if (this.config.existingLenses && this.config.existingLenses.length > 0) {
            this.selectedLenses = this.config.existingLenses;
            this.updateSelectedLensesDisplay();
        }
    }

    // ==================== ایونت‌های سراسری ====================
    setupGlobalEvents() {
        // Hide lens suggestions when clicking outside
        document.addEventListener('click', (e) => {
            const lensSuggestions = document.getElementById('lens-suggestions');
            if (lensSuggestions && !e.target.closest('.medical-lens-input')) {
                lensSuggestions.style.display = 'none';
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Escape to clear search
            if (e.key === 'Escape') {
                const lensSearch = document.getElementById('lens-search');
                const lensSuggestions = document.getElementById('lens-suggestions');
                if (lensSearch && document.activeElement === lensSearch) {
                    lensSearch.value = '';
                    if (lensSuggestions) lensSuggestions.style.display = 'none';
                }
            }

            // Ctrl/Cmd + F for search focus
            if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
                e.preventDefault();
                const searchInput = document.getElementById('lens-search') || document.querySelector('input[type="search"]');
                if (searchInput) {
                    searchInput.focus();
                    searchInput.select();
                }
            }
        });
    }

    // ==================== متدهای کمکی ====================
    resetForm() {
        this.removeImage();
        this.removeVideo();
        this.selectedLenses = [];
        this.updateSelectedLensesDisplay();

        const lensSearch = document.getElementById('lens-search');
        if (lensSearch) lensSearch.value = '';

        const lensSuggestions = document.getElementById('lens-suggestions');
        if (lensSuggestions) lensSuggestions.style.display = 'none';
    }

    getSelectedLenses() {
        return this.selectedLenses;
    }

    setSelectedLenses(lenses) {
        this.selectedLenses = lenses;
        this.updateSelectedLensesDisplay();
    }

    // فیلتر کردن پست‌ها بر اساس جستجو
    searchPosts(query) {
        const posts = document.querySelectorAll('.post-card');
        const searchTerm = query.toLowerCase();

        posts.forEach(post => {
            const title = post.querySelector('.post-title')?.textContent.toLowerCase() || '';
            const content = post.querySelector('.post-content')?.textContent.toLowerCase() || '';

            if (title.includes(searchTerm) || content.includes(searchTerm)) {
                post.style.display = 'block';
                post.style.opacity = '0';
                setTimeout(() => {
                    post.style.opacity = '1';
                    post.style.transition = 'opacity 0.3s ease';
                }, 10);
            } else {
                post.style.display = 'none';
            }
        });
    }
}

// ==================== مقداردهی اولیه ====================
document.addEventListener('DOMContentLoaded', function() {
    window.docPageManager = new DocPageManager({
        lensSearchUrl: '/docpages/ajax/search-medical-lenses/',
        existingLenses: window.existingLenses || []
    });
});

// برای مواقعی که صفحه از قبل لود شده
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(() => {
        if (!window.docPageManager) {
            window.docPageManager = new DocPageManager({
                lensSearchUrl: '/docpages/ajax/search-medical-lenses/',
                existingLenses: window.existingLenses || []
            });
        }
    }, 100);
}