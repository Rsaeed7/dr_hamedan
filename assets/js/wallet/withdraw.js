document.addEventListener('DOMContentLoaded', function() {
    const withdrawForm = document.getElementById('withdraw-form');
    const amountInput = document.getElementById('id_amount');
    const accountNumberInput = document.getElementById('account_number');
    const routingNumberInput = document.getElementById('routing_number');
    const walletBalance = parseFloat(document.querySelector('.card-body h4').textContent.replace(/[^\d.]/g, '')) || 0;

    // Set amount when buttons are clicked
    document.querySelectorAll('.amount-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const amount = this.getAttribute('data-amount');
            amountInput.value = amount;

            // Remove active class from all buttons and add to clicked one
            document.querySelectorAll('.amount-btn').forEach(b => {
                b.classList.remove('active');
            });
            this.classList.add('active');
        });
    });

    // Form validation
    if (withdrawForm) {
        withdrawForm.addEventListener('submit', function(e) {
            const amount = parseFloat(amountInput.value);
            const termsChecked = document.getElementById('terms').checked;

            if (!termsChecked) {
                e.preventDefault();
                alert('لطفاً تأییدیه شرایط برداشت را انتخاب کنید');
                return;
            }

            if (amount < 10000) {
                e.preventDefault();
                alert('حداقل مبلغ برداشت 10,000 تومان می‌باشد');
                amountInput.focus();
            } else if (amount > walletBalance) {
                e.preventDefault();
                alert('مبلغ درخواستی بیشتر از موجودی کیف پول شماست');
                amountInput.focus();
            }
        });
    }

    // Format account number (only digits)
    if (accountNumberInput) {
        accountNumberInput.addEventListener('input', function() {
            this.value = this.value.replace(/\D/g, '');
        });
    }

    // Format Sheba number (IR + digits)
    if (routingNumberInput) {
        routingNumberInput.addEventListener('input', function() {
            let value = this.value.toUpperCase().replace(/[^IR0-9]/g, '');

            // Auto-add IR prefix if not present
            if (!value.startsWith('IR') && value.length > 0) {
                value = 'IR' + value;
            }

            this.value = value;
        });
    }

    // Real-time validation for amount input
    if (amountInput) {
        amountInput.addEventListener('input', function() {
            const amount = parseFloat(this.value);

            if (amount > walletBalance) {
                this.classList.add('is-invalid');
            } else {
                this.classList.remove('is-invalid');
            }
        });
    }
});