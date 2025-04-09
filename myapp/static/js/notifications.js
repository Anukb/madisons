document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const notificationButton = document.getElementById('notificationIcon');
    const notificationDropdown = document.getElementById('notificationDropdown');
    const notificationBadge = document.getElementById('notificationBadge');
    const notificationList = document.getElementById('notificationList');

    // Initialize notification state
    let isDropdownVisible = false;

    // Toggle notification dropdown
    function toggleDropdown(event) {
        event.stopPropagation();
        isDropdownVisible = !isDropdownVisible;
        notificationDropdown.classList.toggle('show', isDropdownVisible);
    }

    // Close dropdown when clicking outside
    document.addEventListener('click', function(event) {
        if (isDropdownVisible && !event.target.closest('.notification-wrapper')) {
            isDropdownVisible = false;
            notificationDropdown.classList.remove('show');
        }
    });

    // Prevent dropdown from closing when clicking inside
    notificationDropdown?.addEventListener('click', function(event) {
        event.stopPropagation();
    });

    // Add click event to notification button
    if (notificationButton) {
        notificationButton.addEventListener('click', toggleDropdown);
    }

    // Format time function
    function formatTime(date) {
        const now = new Date();
        const diff = Math.floor((now - new Date(date)) / 1000);

        if (diff < 60) return 'Just now';
        if (diff < 3600) return Math.floor(diff / 60) + ' minutes ago';
        if (diff < 86400) return Math.floor(diff / 3600) + ' hours ago';
        return new Date(date).toLocaleDateString();
    }

    // Update notifications
    function updateNotifications() {
        if (!notificationList) return;

        fetch('/api/notifications/')
            .then(response => response.json())
            .then(data => {
                let notifications = data.notifications || [];
                
                // Add default welcome notification if no notifications exist
                if (notifications.length === 0) {
                    notifications = [{
                        id: 'default',
                        title: '🔔 Welcome to Madison!',
                        message: 'Thank you for joining our community.',
                        created_at: new Date().toISOString(),
                        is_read: false
                    }];
                }

                // Update badge
                const unreadCount = notifications.filter(n => !n.is_read).length;
                notificationBadge.textContent = unreadCount;
                notificationBadge.style.display = unreadCount > 0 ? 'flex' : 'none';

                // Update notification list
                notificationList.innerHTML = notifications.map(notification => `
                    <div class="notification-item ${notification.is_read ? '' : 'unread'}">
                        <div class="notification-content">
                            <h4>${notification.title || 'Notification'}</h4>
                            <p>${notification.message}</p>
                            <span class="notification-time">${formatTime(notification.created_at)}</span>
                        </div>
                    </div>
                `).join('');
            })
            .catch(error => {
                console.error('Error fetching notifications:', error);
                // Show default notification on error
                notificationList.innerHTML = `
                    <div class="notification-item">
                        <div class="notification-content">
                            <h4>🔔 Welcome to Madison!</h4>
                            <p>Thank you for joining our community.</p>
                            <span class="notification-time">Just now</span>
                        </div>
                    </div>
                `;
            });
    }

    // Initial update
    updateNotifications();

    // Update notifications every 30 seconds
    setInterval(updateNotifications, 30000);
}); 

// Notification handling
const notificationDropdown = document.getElementById('notification-dropdown');
const notificationIcon = document.getElementById('notification-icon');
const notificationBadge = document.getElementById('notification-badge');
const notificationList = document.getElementById('notification-list');

// Toggle notification dropdown
notificationIcon.addEventListener('click', (e) => {
    e.preventDefault();
    notificationDropdown.classList.toggle('show');
    fetchNotifications();
});

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
    if (!notificationIcon.contains(e.target) && !notificationDropdown.contains(e.target)) {
        notificationDropdown.classList.remove('show');
    }
});

// Fetch notifications from API
async function fetchNotifications() {
    try {
        const response = await fetch('/api/notifications/');
        const data = await response.json();
        
        if (data.success) {
            updateNotificationBadge(data.unread_count);
            renderNotifications(data.notifications);
        }
    } catch (error) {
        console.error('Error fetching notifications:', error);
    }
}

// Render notifications in dropdown
function renderNotifications(notifications) {
    notificationList.innerHTML = '';
    
    if (notifications.length === 0) {
        notificationList.innerHTML = '<div class="no-notifications">No notifications</div>';
        return;
    }
    
    notifications.forEach(notification => {
        const notificationItem = document.createElement('div');
        notificationItem.className = `notification-item ${notification.read ? '' : 'unread'}`;
        notificationItem.innerHTML = `
            <div class="notification-content">
                <div class="notification-title">${notification.title}</div>
                <div class="notification-message">${notification.message}</div>
                <div class="notification-time">${formatTime(notification.created_at)}</div>
            </div>
        `;
        
        if (!notification.read) {
            notificationItem.addEventListener('click', () => markAsRead(notification.id));
        }
        
        notificationList.appendChild(notificationItem);
    });
    
    // Add "Mark All as Read" button if there are unread notifications
    if (notifications.some(n => !n.read)) {
        const markAllButton = document.createElement('button');
        markAllButton.className = 'mark-all-read';
        markAllButton.textContent = 'Mark All as Read';
        markAllButton.addEventListener('click', markAllAsRead);
        notificationList.appendChild(markAllButton);
    }
}

// Mark single notification as read
async function markAsRead(notificationId) {
    try {
        const response = await fetch(`/api/notifications/${notificationId}/read/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
            }
        });
        const data = await response.json();
        
        if (data.success) {
            updateNotificationBadge(data.unread_count);
            fetchNotifications();
        }
    } catch (error) {
        console.error('Error marking notification as read:', error);
    }
}

// Mark all notifications as read
async function markAllAsRead() {
    try {
        const response = await fetch('/api/notifications/mark-all-read/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
            }
        });
        const data = await response.json();
        
        if (data.success) {
            updateNotificationBadge(0);
            fetchNotifications();
        }
    } catch (error) {
        console.error('Error marking all notifications as read:', error);
    }
}

// Update notification badge count
function updateNotificationBadge(count) {
    notificationBadge.textContent = count;
    notificationBadge.style.display = count > 0 ? 'block' : 'none';
}

// Format time for notifications
function formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);
    
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
    
    return date.toLocaleDateString();
}

// Get CSRF token from cookies
function getCsrfToken() {
    const name = 'csrftoken';
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

// Initial fetch of notifications
document.addEventListener('DOMContentLoaded', () => {
    fetchNotifications();
});