// image-preview.js
document.addEventListener("DOMContentLoaded", function () {
    let bgInput = document.querySelector("input[name='background_image']");
    let previewBg = document.getElementById("preview-background");
    let previewContainer = document.getElementById("preview-container");
    let previewTitle = document.getElementById("preview-title");

    bgInput?.addEventListener("change", function (event) {
        let file = event.target.files[0];
        if (file) {
            let reader = new FileReader();
            reader.onload = function (e) {
                previewBg.style.backgroundImage = "url(" + e.target.result + ")";
                previewContainer.classList.remove("hidden");
                previewTitle.classList.remove("hidden");
            };
            reader.readAsDataURL(file);
        } else {
            previewContainer.classList.add("hidden");
            previewTitle.classList.add("hidden");
        }
    });
});


// مدیریت نقاشی دستی
let signaturePad;

document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('sketchpad');
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    signaturePad = new SignaturePad(canvas, {
        backgroundColor: 'rgb(255, 255, 255)',
        penColor: 'rgb(0, 0, 0)',
        minWidth: 1,
        maxWidth: 3,
        throttle: 16
    });
});

function clearCanvas() {
    signaturePad.clear();
    document.getElementById('sketchpadInput').value = '';
}

function saveCanvas() {
    const input = document.getElementById('sketchpadInput');
    if (!signaturePad.isEmpty()) {
        input.value = signaturePad.toDataURL('image/jpeg', 0.8);
        alert('دست نوشته ذخیره شد!');
    } else {
        input.value = '';
    }
}

// نمایش/مخفی کردن جزئیات ویزیت
function toggleVisitDetails(id) {
    const el = document.getElementById(id);
    el.classList.toggle('hidden');
}

// جلوگیری از اسکرول هنگام نقاشی روی موبایل
document.getElementById('sketchpad').addEventListener('touchmove', (e) => {
    e.preventDefault();
}, {passive: false});

// توابع جدید برای مدیریت modal عکس
function openImageModal(imageUrl) {
    const modal = document.getElementById('imageModal');
    const modalImage = document.getElementById('modalImage');

    modalImage.src = imageUrl;
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden'; // جلوگیری از اسکرول صفحه پس زمینه
}

function closeImageModal() {
    const modal = document.getElementById('imageModal');
    modal.classList.add('hidden');
    document.body.style.overflow = 'auto'; // فعال کردن مجدد اسکرول صفحه
}

// بستن modal با کلیک روی پس زمینه
document.getElementById('imageModal').addEventListener('click', function (e) {
    if (e.target === this) {
        closeImageModal();
    }
});


