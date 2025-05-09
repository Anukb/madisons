document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initNavigation();
    initCharts();
    initCalendar();
    initEventHandlers();
    init3DEffects();
    initSparkleEffects();
    initDynamicBackground();
    initFormValidations();
    
    // Show dashboard by default
    document.querySelector('.nav-link[href="#dashboard"]').click();
});

function initNavigation() {
    const navLinks = document.querySelectorAll('.admin-sidebar .nav-link');
    const contentSections = document.querySelectorAll('.content-section');
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    
    // Handle sidebar toggle for mobile
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            document.querySelector('.admin-sidebar').classList.toggle('show');
            addSparkleEffect(sidebarToggle);
        });
    }
    
    // Handle navigation clicks
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Remove active class from all links and sections
            navLinks.forEach(l => l.classList.remove('active'));
            contentSections.forEach(s => s.classList.remove('active'));
            
            // Add active class to clicked link
            link.classList.add('active');
            
            // Show corresponding section with animation
            const targetId = link.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);
            targetSection.classList.add('active');
            
            // Add sparkle effect to the clicked nav item
            addSparkleEffect(link);
            
            // Close sidebar on mobile after selection
            if (window.innerWidth < 992) {
                document.querySelector('.admin-sidebar').classList.remove('show');
            }
        });
    });
}

function initCharts() {
    // User Growth Chart (Line Chart)
    const userCtx = document.getElementById('userGrowthChart');
    if (userCtx) {
        new Chart(userCtx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
                datasets: [{
                    label: 'New Users',
                    data: [120, 190, 170, 220, 300, 280, 400],
                    borderColor: '#ff2d75',
                    borderWidth: 3,
                    backgroundColor: 'rgba(255, 45, 117, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#ffffff',
                    pointBorderColor: '#ff2d75',
                    pointRadius: 5,
                    pointHoverRadius: 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#ffffff',
                            font: {
                                size: 14
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(255,255,255,0.1)'
                        },
                        ticks: {
                            color: '#d8b4fe'
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(255,255,255,0.1)'
                        },
                        ticks: {
                            color: '#d8b4fe'
                        },
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // Content Distribution Chart (Doughnut)
    const contentCtx = document.getElementById('contentDistributionChart');
    if (contentCtx) {
        new Chart(contentCtx, {
            type: 'doughnut',
            data: {
                labels: ['Products', 'Blog Posts', 'Reviews', 'Comments'],
                datasets: [{
                    data: [35, 25, 20, 20],
                    backgroundColor: [
                        '#ff2d75',
                        '#9d00ff',
                        '#ff6b6b',
                        '#51cf66'
                    ],
                    borderWidth: 0,
                    hoverOffset: 20
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: '#ffffff',
                            font: {
                                size: 12
                            },
                            padding: 20
                        }
                    }
                }
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
            themeSystem: 'bootstrap5',
            events: [
                {
                    title: 'Team Meeting',
                    start: new Date(),
                    backgroundColor: '#ff2d75',
                    borderColor: '#ff2d75'
                },
                {
                    title: 'Product Launch',
                    start: new Date(new Date().setDate(new Date().getDate() + 5)),
                    backgroundColor: '#9d00ff',
                    borderColor: '#9d00ff'
                }
            ],
            editable: true,
            selectable: true,
            select: function(info) {
                $('#eventTitle').val('');
                $('#eventStart').val(info.startStr);
                $('#eventEnd').val(info.endStr);
                $('#addEventModal').modal('show');
            },
            eventClick: function(info) {
                $('#eventTitle').val(info.event.title);
                $('#eventStart').val(info.event.startStr);
                $('#eventEnd').val(info.event.end ? info.event.endStr : info.event.startStr);
                $('#eventId').val(info.event.id);
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
                // Simulate API call
                await new Promise(resolve => setTimeout(resolve, 1000));
                
                showNotification('Event saved successfully!', 'success');
                $('#addEventModal').modal('hide');
                
                // In a real app, you would refresh the calendar here
                // document.getElementById('adminCalendar').fullCalendar('refetchEvents');
            } catch (error) {
                showNotification('Failed to save event', 'error');
            }
        });
    }

    // Add sparkle effect to all buttons
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            addSparkleEffect(this);
        });
    });

    // Add hover effects to cards
    document.querySelectorAll('.card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            addSparkleEffect(this);
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = '';
        });
    });
}

function init3DEffects() {
    // Apply tilt.js to all cards
    VanillaTilt.init(document.querySelectorAll(".stat-card, .card, .profile-card"), {
        max: 10,
        speed: 300,
        glare: true,
        "max-glare": 0.1,
        scale: 1.02,
    });

    // Entrance animations for dashboard elements
    anime({
        targets: '.stat-card',
        translateY: [20, 0],
        opacity: [0, 1],
        delay: anime.stagger(100),
        duration: 800,
        easing: 'easeOutExpo'
    });

    // Floating animation for stats cards
    document.querySelectorAll('.stat-card').forEach((card, index) => {
        anime({
            targets: card,
            translateY: [0, -10],
            duration: 2000 + (index * 200),
            direction: 'alternate',
            loop: true,
            easing: 'easeInOutSine',
            delay: index * 100
        });
    });
}

function initSparkleEffects() {
    // Add sparkle effect to all navigation links on hover
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('mouseenter', function() {
            addSparkleEffect(this);
        });
    });

    // Add sparkle effect to table rows on hover
    document.querySelectorAll('.table tr').forEach(row => {
        row.addEventListener('mouseenter', function() {
            addSparkleEffect(this);
        });
    });
}

function initDynamicBackground() {
    // Create dynamic cyber particles in the background
    const particlesContainer = document.createElement('div');
    particlesContainer.className = 'cyber-particles';
    document.body.appendChild(particlesContainer);
    
    for (let i = 0; i < 50; i++) {
        const particle = document.createElement('div');
        particle.className = 'cyber-particle';
        
        // Random properties
        const size = Math.random() * 4 + 1;
        const posX = Math.random() * 100;
        const posY = Math.random() * 100;
        const delay = Math.random() * 5;
        const duration = Math.random() * 15 + 10;
        const color = Math.random() > 0.5 ? 'var(--neon-pink)' : 'var(--neon-purple)';
        
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        particle.style.left = `${posX}%`;
        particle.style.top = `${posY}%`;
        particle.style.animationDelay = `${delay}s`;
        particle.style.animationDuration = `${duration}s`;
        particle.style.backgroundColor = color;
        
        particlesContainer.appendChild(particle);
    }
}

function initFormValidations() {
    // Example form validation
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Add sparkle effect to invalid fields
                form.querySelectorAll(':invalid').forEach(field => {
                    addSparkleEffect(field, 'error');
                });
            }
            
            form.classList.add('was-validated');
        }, false);
    });
    
    // Add validation styling to all form controls
    document.querySelectorAll('.form-control').forEach(control => {
        control.addEventListener('input', function() {
            if (this.checkValidity()) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            } else {
                this.classList.remove('is-valid');
                this.classList.add('is-invalid');
            }
        });
    });
}

function addSparkleEffect(element, type = 'default') {
    const sparkle = document.createElement('div');
    sparkle.className = 'sparkle';
    
    // Position the sparkle randomly within the element
    const rect = element.getBoundingClientRect();
    const x = Math.random() * rect.width;
    const y = Math.random() * rect.height;
    
    sparkle.style.left = `${x}px`;
    sparkle.style.top = `${y}px`;
    
    if (type === 'error') {
        sparkle.style.backgroundColor = 'var(--neon-pink)';
    }
    
    element.appendChild(sparkle);
    
    // Remove sparkle after animation completes
    setTimeout(() => {
        sparkle.remove();
    }, 1000);
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show floating`;
    notification.role = 'alert';
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    const notificationsContainer = document.querySelector('.notifications-container') || createNotificationsContainer();
    notificationsContainer.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 5000);
}

function createNotificationsContainer() {
    const container = document.createElement('div');
    container.className = 'notifications-container';
    document.body.appendChild(container);
    return container;
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

// Example of including CSRF token in an AJAX request
fetch('/your-url/', {
    method: 'POST',
    headers: {
        'X-CSRFToken': getCookie('csrftoken'),
        'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
});