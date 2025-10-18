    document.addEventListener('DOMContentLoaded', function () {
        const showAll = document.getElementById('show-all');
        const showApproved = document.getElementById('show-approved');
        const showPending = document.getElementById('show-pending');
        const commentCards = document.querySelectorAll('.comment-card');

        function setActiveTab(tab) {
            [showAll, showApproved, showPending].forEach(t => {
                t.classList.remove('text-blue-600', 'border-blue-600', 'border-b-2');
                t.classList.add('text-gray-500');
            });
            tab.classList.remove('text-gray-500');
            tab.classList.add('text-blue-600', 'border-blue-600', 'border-b-2');
        }

        showAll?.addEventListener('click', () => {
            setActiveTab(showAll);
            commentCards.forEach(card => card.style.display = 'block');
        });

        showApproved?.addEventListener('click', () => {
            setActiveTab(showApproved);
            commentCards.forEach(card => card.style.display = card.dataset.approved === 'true' ? 'block' : 'none');
        });

        showPending?.addEventListener('click', () => {
            setActiveTab(showPending);
            commentCards.forEach(card => card.style.display = card.dataset.approved === 'false' ? 'block' : 'none');
        });
    });