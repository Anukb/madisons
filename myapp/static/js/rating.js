$(document).ready(function() {
    $('#rating-form').on('submit', function(event) {
        event.preventDefault(); // Prevent the default form submission

        $.ajax({
            url: $(this).attr('action'), // Use the form's action URL
            type: 'POST',
            data: $(this).serialize(), // Serialize the form data
            success: function(response) {
                if (response.status === 'success') {
                    // Append the new review to the reviews container
                    $('#reviews-container').prepend(`
                        <div class="review-card">
                            <strong>${response.new_review.username}</strong> rated this article <strong>${response.new_review.score}</strong>
                            <p>${response.new_review.review}</p>
                        </div>
                    `);
                    // Update the average rating displayed
                    $('#average-rating').text(response.average_rating.toFixed(1));
                    
                    // Show a success message
                    $('<div class="notification">✅ Review submitted successfully!</div>').appendTo('body').fadeIn().delay(2000).fadeOut();
                }
            },
            error: function(xhr) {
                // Handle errors
                const errorMessage = xhr.responseJSON ? xhr.responseJSON.message : 'An error occurred. Please try again.';
                $('<div class="notification error">').text(errorMessage).appendTo('body').fadeIn().delay(2000).fadeOut();
            }
        });
    });
}); 