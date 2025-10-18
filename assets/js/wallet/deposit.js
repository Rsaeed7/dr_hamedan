        // دکمه‌های انتخاب مبلغ
        document.querySelectorAll('.amount-btn').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                const amount = this.getAttribute('data-amount');
                document.getElementById('amount').value = amount;
            });
        });

        // نمایش جزئیات درگاه پرداخت بر اساس انتخاب
        document.querySelectorAll('input[name="gateway_type"]').forEach(radio => {
            radio.addEventListener('change', function () {
                // مخفی کردن تمام جزئیات
                document.querySelectorAll('[id$="-details"]').forEach(detail => {
                    detail.classList.add('d-none');
                });

                // نمایش جزئیات درگاه انتخاب شده
                const selectedDetails = document.getElementById(this.value + '-details');
                if (selectedDetails) {
                    selectedDetails.classList.remove('d-none');
                }
            });
        });

        // مقداردهی اولیه به فیلد amount در صورت وجود suggested_amount
        document.addEventListener('DOMContentLoaded', function() {
            const suggestedAmount = '{{ suggested_amount }}';
            const amountInput = document.getElementById('amount');

            if (suggestedAmount && amountInput) {
                amountInput.value = suggestedAmount;
            }
        });