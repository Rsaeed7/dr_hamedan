function toggleBlockDayModal() {
    const modal = document.getElementById('blockDayModal');
    if (modal.classList.contains('active')) {
        modal.classList.remove('active');
    } else {
        modal.classList.add('active');
        // Reset form
        document.getElementById('blockDayForm').reset();
        document.getElementById('block_date_hidden').value = '';
    }
}

// Initialize Persian DatePicker
document.addEventListener('DOMContentLoaded', function () {
    $("#block_date").persianDatepicker({
        format: 'YYYY/MM/DD',
        autoClose: true,
        initialValueType: 'persian',
        onlySelectOnDate: true,
        minDate: new Date(),
        calendar: {
            persian: {
                locale: 'fa'
            }
        },
        onSelect: function (unix) {
            const today = new Date();
            today.setHours(0, 0, 0, 0);

            if (new Date(unix) <= today) {
                alert('فقط می‌توانید روزهای آینده را مسدود کنید.');
                $("#block_date").val('');
                $("#block_date_hidden").val('');
                return false;
            }

            const selectedDate = new Date(unix);
            const year = selectedDate.getFullYear();
            const month = String(selectedDate.getMonth() + 1).padStart(2, '0');
            const day = String(selectedDate.getDate()).padStart(2, '0');
            const formattedDate = `${year}-${month}-${day}`;

            $("#block_date_hidden").val(formattedDate);
        }
    });

    // Close modal when clicking outside
    document.getElementById('blockDayModal').addEventListener('click', function (e) {
        if (e.target === this) {
            toggleBlockDayModal();
        }
    });

    // Close modal with Escape key
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            const modal = document.getElementById('blockDayModal');
            if (modal.classList.contains('active')) {
                toggleBlockDayModal();
            }
        }
    });
});