// Main JavaScript File - Utility Functions & Global Handlers

async function fetchAPI(url, options = {}) {
    const defaultHeaders = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    };

    if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
        options.body = JSON.stringify(options.body);
    } else if (options.body instanceof FormData) {
        delete defaultHeaders['Content-Type'];
    }

    options.headers = { ...defaultHeaders, ...options.headers };

    try {
        const response = await fetch(url, options);
        const data = await response.json();
        
        if (!response.ok && response.status === 401) {
            window.location.href = '/login';
            return { success: false, message: 'Unauthorized. Redirecting to login.' };
        }
        
        return data;
    } catch (error) {
        console.error('API Fetch Error:', error);
        return { success: false, message: 'Network or server error occurred.' };
    }
}

function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) return;

    const toastId = 'toast_' + Date.now();
    const bgClass = type === 'success' ? 'bg-success' : type === 'danger' ? 'bg-danger' : type === 'warning' ? 'bg-warning text-dark' : 'bg-primary';

    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0 mb-2" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body font-medium">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;

    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    const toastEl = document.getElementById(toastId);
    const bsToast = new bootstrap.Toast(toastEl, { delay: 4000 });
    bsToast.show();
}

async function loadNotifications() {
    const notifBadge = document.getElementById('notifBadge');
    const notifList = document.getElementById('notifList');
    if (!notifList) return;

    const res = await fetchAPI('/api/notifications');
    if (res.success && res.data) {
        const { notifications, unread_count } = res.data;
        if (notifBadge) {
            if (unread_count > 0) {
                notifBadge.textContent = unread_count;
                notifBadge.classList.remove('d-none');
            } else {
                notifBadge.classList.add('d-none');
            }
        }

        if (notifications.length === 0) {
            notifList.innerHTML = '<li class="dropdown-item text-center text-muted py-3">No notifications</li>';
            return;
        }

        notifList.innerHTML = notifications.map(n => `
            <li class="dropdown-item py-2 px-3 border-bottom ${!n.is_read ? 'bg-light font-weight-bold' : ''}">
                <div class="d-flex justify-content-between align-items-center">
                    <strong class="text-primary font-13">${n.title}</strong>
                    <small class="text-muted" style="font-size: 11px;">${new Date(n.created_at).toLocaleDateString()}</small>
                </div>
                <p class="mb-0 text-dark small text-wrap">${n.message}</p>
            </li>
        `).join('') + `
            <li class="dropdown-item text-center py-2 bg-light">
                <button onclick="markAllNotificationsRead()" class="btn btn-link btn-sm p-0 text-decoration-none">Mark all as read</button>
            </li>
        `;
    }
}

async function markAllNotificationsRead() {
    await fetchAPI('/api/notifications/read-all', { method: 'POST' });
    loadNotifications();
}

document.addEventListener('DOMContentLoaded', () => {
    loadNotifications();
});
