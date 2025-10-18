class ExploreGrid {
    constructor(config) {
        this.config = config || {};
        this.currentPage = config.currentPage || 1;
        this.hasNextPage = config.hasNextPage || false;
        this.isLoading = false;
        this.searchTimeout = null;
        this.currentFilter = 'all';
        this.currentSpecialty = '';
        this.scrollHandler = this.handleScroll.bind(this);

        this.init();
    }

    init() {
        this.setupSearch();
        this.setupFilters();
        this.setupInfiniteScroll();
        this.setupModal();
        this.setupGlobalEvents();

        console.log('ExploreGrid initialized', {
            currentPage: this.currentPage,
            hasNextPage: this.hasNextPage
        });
    }

    // ==================== جستجو ====================
    setupSearch() {
        const searchInput = document.getElementById('searchInput');
        const mobileSearchInput = document.getElementById('mobileSearchInput');

        [searchInput, mobileSearchInput].forEach(input => {
            if (input) {
                input.addEventListener('input', () => {
                    clearTimeout(this.searchTimeout);
                    this.searchTimeout = setTimeout(() => {
                        this.performSearch();
                    }, 500);
                });
            }
        });
    }

    // ==================== فیلترها ====================
    setupFilters() {
        const filterPills = document.querySelectorAll('.filter-pill');

        filterPills.forEach(pill => {
            pill.addEventListener('click', () => {
                // Remove active from all pills
                filterPills.forEach(p => p.classList.remove('active'));
                pill.classList.add('active');

                // Get filter type
                const filter = pill.dataset.filter;
                const specialty = pill.dataset.specialty;

                if (filter) {
                    this.currentFilter = filter;
                    this.currentSpecialty = '';
                } else if (specialty) {
                    this.currentFilter = 'all';
                    this.currentSpecialty = specialty;
                }

                this.performSearch();
            });
        });
    }

    // ==================== Infinite Scroll ====================
    setupInfiniteScroll() {
        // Remove existing scroll listener
        window.removeEventListener('scroll', this.scrollHandler);
        // Add new scroll listener
        window.addEventListener('scroll', this.scrollHandler);

        console.log('Infinite scroll activated');
    }

    handleScroll() {
        // اگر در حال لود هستیم یا صفحه بعدی وجود ندارد، return
        if (this.isLoading || !this.hasNextPage) return;

        // محاسبه موقعیت اسکرول
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const windowHeight = window.innerHeight;
        const documentHeight = document.documentElement.scrollHeight;

        // اگر کاربر به 300px مانده به انتهای صفحه رسید
        if (scrollTop + windowHeight >= documentHeight - 300) {
            this.loadMorePosts();
        }
    }

    // ==================== مودال ====================
    setupModal() {
        this.postModal = document.getElementById('postModal');
        this.modalContent = document.getElementById('modalContent');

        // Global modal close with backdrop click
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-backdrop')) {
                this.closeModal();
            }
        });
    }

    // ==================== ایونت‌های سراسری ====================
    setupGlobalEvents() {
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });

        // Hover preview on desktop
        if (window.innerWidth > 768) {
            const postsGrid = document.getElementById('postsGrid');
            if (postsGrid) {
                // استفاده از event delegation برای کارایی بهتر
                postsGrid.addEventListener('mouseover', (e) => {
                    const gridItem = e.target.closest('.grid-item');
                    if (gridItem) {
                        const video = gridItem.querySelector('video');
                        if (video) {
                            video.play().catch(e => console.log('Video autoplay prevented'));
                        }
                    }
                });

                postsGrid.addEventListener('mouseout', (e) => {
                    const gridItem = e.target.closest('.grid-item');
                    if (gridItem) {
                        const video = gridItem.querySelector('video');
                        if (video) {
                            video.pause();
                            video.currentTime = 0;
                        }
                    }
                });

                // کلیک روی پست‌ها
                postsGrid.addEventListener('click', (e) => {
                    const gridItem = e.target.closest('.grid-item');
                    if (gridItem && !e.target.closest('a')) {
                        e.preventDefault();
                        const postId = gridItem.dataset.postId;
                        if (postId) {
                            this.openPost(postId);
                        }
                    }
                });
            }
        }
    }

    // ==================== عملیات اصلی ====================
    performSearch() {
        if (this.isLoading) return;

        const searchQuery = this.getSearchQuery();

        // Reset pagination
        this.currentPage = 1;

        // Update URL
        this.updateURL(searchQuery);

        this.loadPosts(true);
    }

    loadMorePosts() {
        if (this.isLoading || !this.hasNextPage) return;

        this.currentPage++;
        this.loadPosts(false);
    }

    loadPosts(resetGrid = false) {
        if (this.isLoading) return;

        this.isLoading = true;
        this.showLoading();

        const searchQuery = this.getSearchQuery();
        const postsGrid = document.getElementById('postsGrid');

        const params = new URLSearchParams({
            search: searchQuery,
            media_type: this.currentFilter,
            specialty: this.currentSpecialty,
            page: this.currentPage
        });

        console.log('Loading posts with params:', params.toString());

        fetch(`${this.config.exploreUrl}?${params}`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Received data:', data);

            if (data.success) {
                if (resetGrid && postsGrid) {
                    postsGrid.innerHTML = data.posts_html;
                } else if (postsGrid && data.posts_html) {
                    // Create temporary container to parse HTML
                    const temp = document.createElement('div');
                    temp.innerHTML = data.posts_html;

                    // Append each grid item
                    const newItems = temp.querySelectorAll('.grid-item');
                    newItems.forEach(item => {
                        postsGrid.appendChild(item);
                    });

                    console.log(`Added ${newItems.length} new items`);
                }

                this.hasNextPage = data.has_next;
                this.updateLoadMoreButton();

                // اگر صفحه بعدی وجود دارد و ما در حالت infinite scroll هستیم، دکمه "موارد بیشتر" رو پنهان کن
                if (this.hasNextPage) {
                    this.hideLoadMoreButton();
                }
            } else {
                console.error('API returned success: false', data);
            }
        })
        .catch(error => {
            console.error('Error loading posts:', error);
            // نمایش خطا به کاربر
            this.showError('خطا در بارگذاری پست‌ها');
        })
        .finally(() => {
            this.isLoading = false;
            this.hideLoading();
        });
    }

    // ==================== مدیریت مودال پست ====================
    openPost(postId) {
        console.log('Opening post:', postId);

        // مستقیماً به صفحه جزئیات پست بروید (برای عملکرد بهتر)
        window.location.href = `/docpages/posts/${postId}/`;

        // اگر می‌خواهید از مودال استفاده کنید، کد زیر را فعال کنید:
        /*
        fetch(`/api/posts/${postId}/`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                this.showPostModal(data);
            })
            .catch(error => {
                console.error('Error loading post:', error);
                // Fallback: redirect to post detail page
                window.location.href = `/docpages/posts/${postId}/`;
            });
        */
    }

    showPostModal(post) {
        const modalHTML = `
            <div class="flex flex-col md:flex-row h-full">
                <!-- Media Section -->
                <div class="md:w-3/5 bg-black flex items-center justify-center">
                    ${post.video ?
                        `<video src="${post.video}" controls class="max-w-full max-h-full"></video>` :
                        post.image ?
                            `<img src="${post.image}" alt="${post.title}" class="max-w-full max-h-full object-contain">` :
                            `<div class="p-8 text-center">
                                <h2 class="text-2xl font-bold mb-4">${post.title}</h2>
                                <p class="text-gray-300">${post.content}</p>
                            </div>`
                    }
                </div>

                <!-- Details Section -->
                <div class="md:w-2/5 bg-gray-900 flex flex-col">
                    <!-- Header -->
                    <div class="p-4 border-b border-gray-800 flex items-center justify-between">
                        <div class="flex items-center gap-3">
                            <div class="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full"></div>
                            <div>
                                <h3 class="font-medium">${post.doctor_name}</h3>
                                <p class="text-sm text-gray-400">${post.specialty}</p>
                            </div>
                        </div>
                        <button onclick="exploreGrid.closeModal()" class="text-gray-400 hover:text-white">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                            </svg>
                        </button>
                    </div>

                    <!-- Content -->
                    <div class="flex-1 overflow-y-auto p-4">
                        <h2 class="text-xl font-bold mb-2">${post.title}</h2>
                        <p class="text-gray-300 whitespace-pre-wrap">${post.content}</p>
                    </div>

                    <!-- Actions -->
                    <div class="p-4 border-t border-gray-800">
                        <div class="flex items-center gap-4 mb-4">
                            <button class="hover:text-red-500 transition-colors">
                                <svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
                                </svg>
                            </button>
                            <button class="hover:text-blue-400 transition-colors">
                                <svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
                                </svg>
                            </button>
                        </div>
                        <p class="text-sm text-gray-400">${post.likes || 0} پسند</p>
                        <p class="text-xs text-gray-500 mt-1">${post.created_at}</p>
                    </div>
                </div>
            </div>
        `;

        if (this.modalContent) {
            this.modalContent.innerHTML = modalHTML;
        }

        if (this.postModal) {
            this.postModal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        }
    }

    closeModal() {
        if (this.postModal) {
            this.postModal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        }

        if (this.modalContent) {
            this.modalContent.innerHTML = '';
        }
    }

    // ==================== متدهای کمکی ====================
    getSearchQuery() {
        const searchInput = document.getElementById('searchInput');
        const mobileSearchInput = document.getElementById('mobileSearchInput');
        return (searchInput?.value || mobileSearchInput?.value || '').trim();
    }

    updateURL(searchQuery) {
        const url = new URL(window.location);
        url.searchParams.set('search', searchQuery);
        url.searchParams.set('media_type', this.currentFilter);
        url.searchParams.set('specialty', this.currentSpecialty);
        url.searchParams.delete('page');
        window.history.pushState({}, '', url);
    }

    showLoading() {
        const loadingSkeleton = document.getElementById('loadingSkeleton');
        const loadMoreBtn = document.getElementById('loadMoreBtn');

        if (loadingSkeleton) {
            loadingSkeleton.classList.remove('hidden');
        }

        if (loadMoreBtn) {
            loadMoreBtn.disabled = true;
            loadMoreBtn.textContent = 'در حال بارگیری...';
        }
    }

    hideLoading() {
        const loadingSkeleton = document.getElementById('loadingSkeleton');
        if (loadingSkeleton) {
            loadingSkeleton.classList.add('hidden');
        }
    }

    hideLoadMoreButton() {
        const loadMoreBtn = document.getElementById('loadMoreBtn');
        if (loadMoreBtn) {
            loadMoreBtn.style.display = 'none';
        }
    }

    updateLoadMoreButton() {
        const loadMoreBtn = document.getElementById('loadMoreBtn');

        if (!loadMoreBtn) return;

        if (this.hasNextPage) {
            loadMoreBtn.parentElement.classList.remove('hidden');
            loadMoreBtn.disabled = false;
            loadMoreBtn.textContent = 'موارد بیشتر';
            loadMoreBtn.setAttribute('data-next-page', this.currentPage + 1);
        } else {
            loadMoreBtn.parentElement.classList.add('hidden');
        }

        console.log('Load more button updated:', {
            hasNextPage: this.hasNextPage,
            currentPage: this.currentPage
        });
    }

    showError(message) {
        // ایجاد یک toast برای نمایش خطا
        const toast = document.createElement('div');
        toast.className = 'fixed top-4 left-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    // برای توقف infinite scroll وقتی لازم نیست
    destroy() {
        window.removeEventListener('scroll', this.scrollHandler);
    }
}

// ==================== مقداردهی اولیه ====================
document.addEventListener('DOMContentLoaded', function() {
    window.exploreGrid = new ExploreGrid({
        exploreUrl: "{% url 'doctors:explore' %}",
        currentPage: {{ posts.number }},
        hasNextPage: {{ posts.has_next|yesno:"true,false" }}
    });

    // تعریف فانکشن‌های سراسری برای backward compatibility با HTML
    window.openPost = (postId) => window.exploreGrid.openPost(postId);
    window.closeModal = () => window.exploreGrid.closeModal();
    window.performSearch = () => window.exploreGrid.performSearch();
    window.loadMorePosts = () => window.exploreGrid.loadMorePosts();
});

// برای مواقعی که صفحه از قبل لود شده
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(() => {
        if (!window.exploreGrid) {
            window.exploreGrid = new ExploreGrid({
                exploreUrl: "{% url 'doctors:explore' %}",
                currentPage: {{ posts.number }},
                hasNextPage: {{ posts.has_next|yesno:"true,false" }}
            });
        }
    }, 100);
}