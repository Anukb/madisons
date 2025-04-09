$(document).ready(function() {
    $('#profile-pic').change(function(event) {
        const reader = new FileReader();
        reader.onload = function() {
            $('#preview').attr('src', reader.result);
            const fileName = event.target.files[0].name;
            $('#file-label').text(fileName);
            $('#set-dp').show();
        }
        reader.readAsDataURL(event.target.files[0]);
    });

    $('#set-dp').click(function() {
        const fileInput = $('#profile-pic')[0];
        if (fileInput.files.length > 0) {
            $('#profile-form').submit();
        } else {
            alert('Please select a profile picture to upload.');
        }
    });
}); 