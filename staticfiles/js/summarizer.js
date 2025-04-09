function showSummary(element) {
    const popup = document.getElementById("summaryPopup");
    const summaryText = document.getElementById("summaryText");
    const loading = document.querySelector(".loading");
    
    // Show popup with loading state
    popup.style.display = "block";
    summaryText.style.display = "none";
    loading.style.display = "block";
    
    // Get the article text
    const articleText = document.querySelector('.article-content').innerText;
    
    // Request summary from server
    fetch('/generate-summary', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ text: articleText })
    })
    .then(response => response.json())
    .then(data => {
        loading.style.display = "none";
        summaryText.style.display = "block";
        if (data.error) {
            summaryText.innerHTML = `<p class="error-message">${data.error}</p>`;
        } else {
            summaryText.innerHTML = `<p class="summary-content">${data.summary}</p>`;
        }
    })
    .catch(error => {
        loading.style.display = "none";
        summaryText.style.display = "block";
        summaryText.innerHTML = '<p class="error-message">Failed to generate summary. Please try again.</p>';
    });
}

function closePopup() {
    const popup = document.getElementById("summaryPopup");
    popup.classList.add('fade-out');
    setTimeout(() => {
        popup.style.display = "none";
        popup.classList.remove('fade-out');
    }, 300);
}

// Helper function to get CSRF token
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
