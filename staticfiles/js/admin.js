// Initialize GSAP
gsap.registerPlugin(ScrollTrigger);

// DOM Elements
const sidebar = document.querySelector('.admin-sidebar');
const mainContent = document.querySelector('.admin-main');
const sidebarToggle = document.querySelector('.sidebar-toggle');
const searchInput = document.querySelector('.search-bar input');
const notificationBtn = document.querySelector('.notification-btn');
const userProfile = document.querySelector('.user-profile');
const statsCards = document.querySelectorAll('.stats-card');
const meshGradient = document.querySelector('.mesh-gradient');

// Sidebar Toggle
function toggleSidebar() {
    sidebar.classList.toggle('active');
    mainContent.style.marginLeft = sidebar.classList.contains('active') ? '280px' : '0';
}

// Notification Animation
function animateNotification() {
    gsap.to(notificationBtn, {
        scale: 1.2,
        duration: 0.2,
        yoyo: true,
        repeat: 1
    });
}

// Stats Cards Animation
function animateStatsCards() {
    statsCards.forEach((card, index) => {
        gsap.from(card, {
            scrollTrigger: {
                trigger: card,
                start: 'top bottom-=100',
                toggleActions: 'play none none reverse'
            },
            y: 50,
            opacity: 0,
            duration: 0.8,
            delay: index * 0.2
        });
    });
}

// Mesh Gradient Animation
function animateMeshGradient() {
    gsap.to(meshGradient, {
        backgroundPosition: '200% 200%',
        duration: 20,
        repeat: -1,
        ease: 'none'
    });
}

// Search Input Animation
function initSearchAnimation() {
    searchInput.addEventListener('focus', () => {
        gsap.to(searchInput, {
            width: '+=50',
            duration: 0.3,
            ease: 'power2.out'
        });
    });

    searchInput.addEventListener('blur', () => {
        gsap.to(searchInput, {
            width: '-=50',
            duration: 0.3,
            ease: 'power2.in'
        });
    });
}

// Particle System
function initParticleSystem() {
    particlesJS('particles-js', {
        particles: {
            number: {
                value: 80,
                density: {
                    enable: true,
                    value_area: 800
                }
            },
            color: {
                value: '#6c63ff'
            },
            shape: {
                type: 'circle'
            },
            opacity: {
                value: 0.5,
                random: false
            },
            size: {
                value: 3,
                random: true
            },
            line_linked: {
                enable: true,
                distance: 150,
                color: '#6c63ff',
                opacity: 0.2,
                width: 1
            },
            move: {
                enable: true,
                speed: 2,
                direction: 'none',
                random: false,
                straight: false,
                out_mode: 'out',
                bounce: false
            }
        },
        interactivity: {
            detect_on: 'canvas',
            events: {
                onhover: {
                    enable: true,
                    mode: 'grab'
                },
                resize: true
            },
            modes: {
                grab: {
                    distance: 140,
                    line_linked: {
                        opacity: 0.5
                    }
                }
            }
        },
        retina_detect: true
    });
}

// Chart Animations
function initCharts() {
    // Activity Overview Chart
    const ctx = document.getElementById('activityChart').getContext('2d');
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(108, 99, 255, 0.2)');
    gradient.addColorStop(1, 'rgba(108, 99, 255, 0)');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [{
                label: 'User Activity',
                data: [65, 59, 80, 81, 56, 85],
                fill: true,
                backgroundColor: gradient,
                borderColor: '#6c63ff',
                tension: 0.4,
                pointBackgroundColor: '#6c63ff',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: '#6c63ff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#a0a0a0'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#a0a0a0'
                    }
                }
            }
        }
    });
}

// Hover Effects
function initHoverEffects() {
    const cards = document.querySelectorAll('.stats-card');
    
    cards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            gsap.to(card, {
                y: -10,
                duration: 0.3,
                ease: 'power2.out'
            });
        });
        
        card.addEventListener('mouseleave', () => {
            gsap.to(card, {
                y: 0,
                duration: 0.3,
                ease: 'power2.out'
            });
        });
    });
}

// Initialize everything
document.addEventListener('DOMContentLoaded', () => {
    // Initialize animations and effects
    animateStatsCards();
    animateMeshGradient();
    initSearchAnimation();
    initParticleSystem();
    initCharts();
    initHoverEffects();

    // Event listeners
    sidebarToggle?.addEventListener('click', toggleSidebar);
    notificationBtn?.addEventListener('click', animateNotification);

    // Initialize tooltips
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(tooltip => {
        tippy(tooltip, {
            content: tooltip.dataset.tooltip,
            placement: 'top',
            animation: 'scale',
            theme: 'cyber'
        });
    });
});

// Handle page transitions
document.addEventListener('turbolinks:load', () => {
    // Reinitialize animations and effects when navigating between pages
    animateStatsCards();
    initCharts();
    initHoverEffects();
});

// Notification Badge Animation
const notificationBadge = document.querySelector('.badge');
if (notificationBadge) {
    gsap.to(notificationBadge, {
        scale: 1.2,
        duration: 0.5,
        repeat: -1,
        yoyo: true,
        ease: 'power1.inOut'
    });
}

// Search Bar Animation
const searchBar = document.querySelector('.search-bar input');
searchBar.addEventListener('focus', () => {
    gsap.to(searchBar, {
        scale: 1.02,
        duration: 0.3,
        ease: 'power2.out'
    });
});

searchBar.addEventListener('blur', () => {
    gsap.to(searchBar, {
        scale: 1,
        duration: 0.3,
        ease: 'power2.out'
    });
});

// Activity Items Animation
const activityItems = document.querySelectorAll('.activity-item');
activityItems.forEach((item, index) => {
    gsap.from(item, {
        opacity: 0,
        y: 20,
        duration: 0.5,
        delay: index * 0.1,
        ease: 'power2.out',
        scrollTrigger: {
            trigger: item,
            start: 'top bottom-=100',
            toggleActions: 'play none none reverse'
        }
    });
});

// Tooltip Implementation
const tooltips = document.querySelectorAll('[data-tooltip]');
tooltips.forEach(element => {
    tippy(element, {
        content: element.getAttribute('data-tooltip'),
        placement: 'top',
        arrow: true,
        theme: 'custom-dark'
    });
});

// Dark Mode Toggle
const darkModeToggle = document.querySelector('.dark-mode-toggle');
if (darkModeToggle) {
    darkModeToggle.addEventListener('click', () => {
        document.body.classList.toggle('light-mode');
        const isDarkMode = !document.body.classList.contains('light-mode');
        localStorage.setItem('darkMode', isDarkMode);
    });
}

// Check for saved dark mode preference
const savedDarkMode = localStorage.getItem('darkMode');
if (savedDarkMode === 'false') {
    document.body.classList.add('light-mode');
}

// Responsive Navigation
const menuItems = document.querySelectorAll('.nav-link');
menuItems.forEach(item => {
    item.addEventListener('click', () => {
        if (window.innerWidth <= 768) {
            sidebar.classList.remove('active');
        }
    });
});

// Window Resize Handler
let resizeTimeout;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        if (window.innerWidth > 768) {
            sidebar.classList.remove('active');
            mainContent.classList.remove('expanded');
        }
    }, 250);
});

// Initialize Custom Scrollbar
document.querySelectorAll('.custom-scroll').forEach(element => {
    new PerfectScrollbar(element, {
        wheelSpeed: 2,
        wheelPropagation: true,
        minScrollbarLength: 20
    });
});

// Stats Counter Animation
const statsNumbers = document.querySelectorAll('.stats-number');
statsNumbers.forEach(number => {
    const targetNumber = parseInt(number.textContent);
    gsap.to(number, {
        textContent: targetNumber,
        duration: 2,
        ease: 'power1.out',
        snap: { textContent: 1 },
        scrollTrigger: {
            trigger: number,
            start: 'top bottom-=100',
            toggleActions: 'play none none reverse'
        }
    });
});

// Add loading animation
const showLoading = () => {
    const loader = document.createElement('div');
    loader.className = 'loader';
    document.body.appendChild(loader);
    return loader;
};

const hideLoading = (loader) => {
    loader.remove();
};

// API calls with loading state
const fetchData = async (url) => {
    const loader = showLoading();
    try {
        const response = await fetch(url);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching data:', error);
        throw error;
    } finally {
        hideLoading(loader);
    }
};

// Error handling
const showError = (message) => {
    const errorToast = document.createElement('div');
    errorToast.className = 'error-toast';
    errorToast.textContent = message;
    document.body.appendChild(errorToast);

    gsap.to(errorToast, {
        opacity: 1,
        y: 20,
        duration: 0.3,
        ease: 'power2.out'
    });

    setTimeout(() => {
        gsap.to(errorToast, {
            opacity: 0,
            y: 0,
            duration: 0.3,
            ease: 'power2.in',
            onComplete: () => errorToast.remove()
        });
    }, 3000);
};

// Handle form submissions
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const loader = showLoading();

        try {
            const formData = new FormData(form);
            const response = await fetch(form.action, {
                method: form.method,
                body: formData
            });

            if (!response.ok) {
                throw new Error('Form submission failed');
            }

            // Handle success
            form.reset();
        } catch (error) {
            showError(error.message);
        } finally {
            hideLoading(loader);
        }
    });
});