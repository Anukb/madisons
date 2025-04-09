$(document).ready(function() {
    $('#comment-form').on('submit', function(e) {
        e.preventDefault(); // Prevent the default form submission
        $.ajax({
            type: 'POST',
            url: $(this).attr('action'),
            data: $(this).serialize(),
            success: function(response) {
                // Append the new comment to the comments section
                $('.comments-section').append(`
                    <div class="comment-card">
                        <p><strong>${response.username}</strong> - ${response.created_at}</p>
                        <p>${response.body}</p>
                    </div>
                `);
                $('#comment-form')[0].reset(); // Reset the form
            },
            error: function(xhr, status, error) {
                console.error("Error posting comment:", error);
            }
        });
    });
});
