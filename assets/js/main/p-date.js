$(document).ready(function () {
    $('#date_display').persianDatepicker({
        format: 'YYYY/MM/DD',
        altField: '#id_requested_date',
        altFormat: 'YYYY-MM-DD',
        observer: true,
        initialValue: !!'{{ id_requested_date }}',
        initialValueType: 'persian',
        autoClose: true
    });
});


$(document).ready(function () {
    $('#birthdate_display').persianDatepicker({
        format: 'YYYY/MM/DD',
        altField: '#birthdate',
        altFormat: 'YYYY-MM-DD',
        observer: true,
        initialValue: !!'{{ birthdate }}',
        initialValueType: 'persian',
        autoClose: true
    });
});

$(document).ready(function () {
    // فیلتر از تاریخ
    $('#from_display').persianDatepicker({
        format: 'YYYY/MM/DD',
        altField: '#from',
        altFormat: 'YYYY-MM-DD',
        observer: true,
        initialValue: !!'{{ from }}',
        initialValueType: 'persian',
        autoClose: true,
        onSelect: function () {
            $('#filterForm').submit();
        }
    });

    // فیلتر تا تاریخ
    $('#to_display').persianDatepicker({
        format: 'YYYY/MM/DD',
        altField: '#to',
        altFormat: 'YYYY-MM-DD',
        observer: true,
        initialValue: !!'{{ to }}',
        initialValueType: 'persian',
        autoClose: true,
        onSelect: function () {
            $('#filterForm').submit();
        }
    });
});


document.addEventListener('DOMContentLoaded', function () {
    const autoInputs = document.querySelectorAll('.auto-submit');
    autoInputs.forEach(input => {
        input.addEventListener('change', function () {
            document.getElementById('filterForm').submit();
        });
    });
});


$(document).ready(function () {
    // گرفتن تاریخ امروز به‌صورت جلالی
    const today = new persianDate().format('YYYY/MM/DD');

    // مقداردهی اولیه به ورودی‌ها در صورت نبود پارامتر URL
    function getUrlParameter(name) {
        name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
        var regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
        var results = regex.exec(location.search);
        return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
    }

    const dateFromParam = getUrlParameter('date_from');
    const dateToParam = getUrlParameter('date_to');

    // مقدار پیش‌فرض امروز برای ورودی‌ها (اگر پارامتر URL نبود)
    if (!dateFromParam) {
        $('#date_from').val(today);
    }
    if (!dateToParam) {
        $('#date_to').val(today);
    }

    // فعال‌سازی تقویم جلالی روی ورودی‌ها
    $('.jalali-datepicker').persianDatepicker({
        format: 'YYYY/MM/DD',
        altFormat: 'YYYY-MM-DD',
        observer: true,
        autoClose: true,
        initialValue: false  // چون ما دستی مقدار رو می‌ذاریم
    });

    // اگر پارامتر URL وجود داشت، مقدار ورودی رو override می‌کنیم
    if (dateFromParam) {
        $('#date_from').val(dateFromParam);
    }
    if (dateToParam) {
        $('#date_to').val(dateToParam);
    }
});




