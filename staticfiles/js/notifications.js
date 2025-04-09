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