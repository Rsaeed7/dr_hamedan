document.addEventListener('DOMContentLoaded', function () {
    // Time validation
    const startTime = document.getElementById('start_time');
    const endTime = document.getElementById('end_time');

    if (startTime) {
        startTime.addEventListener('change', function () {
            if (endTime.value && this.value >= endTime.value) {
                endTime.value = '';
            }
        });
    }

    if (endTime) {
        endTime.addEventListener('change', function () {
            if (startTime.value && this.value <= startTime.value) {
                alert('ساعت پایان باید بعد از ساعت شروع باشد.');
                this.value = '';
            }
        });
    }

    // Initialize Persian DatePicker for block_date input
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
            // Additional validation to ensure future dates only
            const today = new Date();
            today.setHours(0, 0, 0, 0);

            if (new Date(unix) <= today) {
                alert('فقط می‌توانید روزهای آینده را مسدود کنید.');
                $("#block_date").val('');
                $("#block_date_hidden").val('');

                return false;
            }


            // Convert to Gregorian date format for backend (YYYY-MM-DD)
            const selectedDate = new Date(unix);
            const year = selectedDate.getFullYear();
            const month = String(selectedDate.getMonth() + 1).padStart(2, '0');
            const day = String(selectedDate.getDate()).padStart(2, '0');
            const formattedDate = `${year}-${month}-${day}`;

            // Set hidden input value with the formatted Gregorian date
            $("#block_date_hidden").val(formattedDate);

            console.log('Selected date for display:', $("#block_date").val());
            console.log('Selected date for backend:', formattedDate);
        }
    });

    // Add calendar icon for better UX
    if ($("#block_date").parent().css('position') !== 'relative') {
        $("#block_date").parent().css('position', 'relative');
        $("#block_date").after('<i class="icon-calendar text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2"></i>');
    }
});

// Block Day Modal Functions
function toggleBlockDayModal() {
    const modal = document.getElementById('blockDayModal');
    if (modal.classList.contains('hidden')) {
        modal.classList.remove('hidden');
        // Reset form and prepare input
        const blockDateInput = document.getElementById('block_date');
        if (blockDateInput) {
            blockDateInput.value = '';
            setTimeout(() => blockDateInput.focus(), 300);
        }
    } else {
        modal.classList.add('hidden');
        // Reset form
        const form = modal.querySelector('form');
        if (form) {
            form.reset();
        }
    }
}

// Close modal when clicking outside
document.addEventListener('DOMContentLoaded', function () {
    const modal = document.getElementById('blockDayModal');
    if (modal) {
        modal.addEventListener('click', function (e) {
            if (e.target === this) {
                toggleBlockDayModal();
            }
        });
    }
});

// Close modal with Escape key
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        const modal = document.getElementById('blockDayModal');
        if (!modal.classList.contains('hidden')) {
            toggleBlockDayModal();
        }
    }
});

// Form validation to ensure date is properly set
function validateBlockDayForm() {
    const dateHidden = document.getElementById('block_date_hidden');
    if (!dateHidden.value) {
        alert('لطفا یک تاریخ معتبر انتخاب کنید.');
        return false;
    }
    return true;
}
