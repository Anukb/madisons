document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const searchIcon = document.querySelector('.search-icon');
    let searchTimeout;

    // Handle search input
    searchInput.addEventListener('input', function(e) {
        clearTimeout(searchTimeout);
        const query = e.target.value.trim();
        
        searchTimeout = setTimeout(() => {
            if (query.length >= 2) {
                performSearch(query);
            }
        }, 300);
    });

    // Handle search icon click
    searchIcon.addEventListener('click', function() {
        const query = searchInput.value.trim();
        if (query.length >= 2) {
            performSearch(query);
        }
    });

    async function performSearch(query) {
        try {
            const response = await fetch(`/api/search/?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            displaySearchResults(data);
        } catch (error) {
            console.error('Search error:', error);
        }
    }

    function displaySearchResults(results) {
        let resultsContainer = document.querySelector('.search-results');
        if (!resultsContainer) {
            resultsContainer = document.createElement('div');
            resultsContainer.className = 'search-results';
            document.querySelector('.search-wrapper').appendChild(resultsContainer);
        }

        if (results.length === 0) {
            resultsContainer.innerHTML = '<p class="no-results">No articles found</p>';
        } else {
            resultsContainer.innerHTML = results.map(article => `
                <div class="search-result-item">
                    <h3>${article.title}</h3>
                    <p>${article.description.substring(0, 100)}...</p>
                    <a href="/article/${article.id}" class="read-more">Read more</a>
                </div>
            `).join('');
        }

        resultsContainer.classList.add('active');
    }

    // Close search results when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.search-wrapper')) {
            const resultsContainer = document.querySelector('.search-results');
            if (resultsContainer) {
                resultsContainer.classList.remove('active');
            }
        }
    });
}); 