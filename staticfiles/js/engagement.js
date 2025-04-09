$(document).ready(function() {
    const articleId = "{{ article.id }}"; // Get the article ID from the template
    let startTime = Date.now();

    $(window).on('beforeunload', function() {
        const timeSpent = (Date.now() - startTime) / 1000; // Time in seconds
        $.ajax({
            url: "{% url 'track_reading' %}",
            type: "POST",
            data: {
                articleId: articleId,
                timeSpent: timeSpent,
            },
            headers: {
                'X-CSRFToken': '{{ csrf_token }}'
            }
        });
    });
}); 