function manageComment(type, id, action) {
    const button = event.target;
    const originalText = button.innerHTML;

    button.innerHTML = '...';
    button.disabled = true;

    fetch("/admin/comments/ajax/", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            type: type,
            id: id,
            action: action
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (action === 'delete') {
                document.getElementById(`${type}-comment-${id}`).remove();
            } else if (action === 'approve') {
                const statusElement = document.getElementById(`status-${type}-${id}`);
                statusElement.textContent = 'تایید شده';
                statusElement.className = 'text-green-600';
                button.style.display = 'none';
            }
        } else {
            alert('خطا: ' + data.error);
            button.innerHTML = originalText;
            button.disabled = false;
        }
    })
    .catch(error => {
        alert('خطا در ارتباط با سرور');
        button.innerHTML = originalText;
        button.disabled = false;
    });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}