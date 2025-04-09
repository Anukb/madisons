document.addEventListener('DOMContentLoaded', function() {
    // Initialize navigation
    initNavigation();
    
    // Initialize charts
    initCharts();
    
    // Initialize calendar
    initCalendar();
    
    // Initialize event handlers
    initEventHandlers();
});

function initNavigation() {
    const navLinks = document.querySelectorAll('.admin-sidebar .nav-link');
    const contentSections = document.querySelectorAll('.content-section');
    
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Remove active class from all links and sections
            navLinks.forEach(l => l.classList.remove('active'));
            contentSections.forEach(s => s.classList.remove('active'));
            
            // Add active class to clicked link
            link.classList.add('active');
            
            // Show corresponding section
            const targetId = link.getAttribute('href').substring(1);
            document.getElementById(targetId).classList.add('active');
        });
    });
}

function initCharts() {
    // User Growth Chart
    const userCtx = document.getElementById('userGrowthChart');
    if (userCtx) {
        new Chart(userCtx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'User Growth',
                    data: [0, 10, 25, 45, 70, 100],
                    borderColor: '#4f5bd5',
                    tension: 0.4,
                    fill: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // Content Distribution Chart
    const contentCtx = document.getElementById('contentDistributionChart');
    if (contentCtx) {
        new Chart(contentCtx, {
            type: 'doughnut',
            data: {
                labels: ['Articles', 'Comments', 'Reviews'],
                datasets: [{
                    data: [60, 25, 15],
                    backgroundColor: ['#4f5bd5', '#ff6b6b', '#51cf66']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }
}

function initCalendar() {
    const calendarEl = document.getElementById('adminCalendar');
    if (calendarEl) {
        const calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            events: [], // Will be populated from backend
            editable: true,
            selectable: true,
            select: function(info) {
                // Show event creation modal
                $('#addEventModal').modal('show');
            }
        });
        calendar.render();
    }
}

function initEventHandlers() {
    // Event form submission
    const eventForm = document.getElementById('addEventForm');
    if (eventForm) {
        eventForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(eventForm);
            try {
                const response = await fetch('/admin/add-event/', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                });
                
                if (response.ok) {
                    $('#addEventModal').modal('hide');
                    showNotification('Event added successfully', 'success');
                    // Refresh calendar
                    document.getElementById('adminCalendar').fullCalendar('refetchEvents');
                } else {
                    throw new Error('Failed to add event');
                }
            } catch (error) {
                showNotification('Failed to add event', 'error');
            }
        });
    }
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.role = 'alert';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    document.querySelector('.admin-main').insertAdjacentElement('afterbegin', notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Utility function to get CSRF token
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