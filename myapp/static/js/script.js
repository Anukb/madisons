// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    if (document.querySelector('.error-message')) {
        const errorMessage = document.querySelector('.error-message');
        setTimeout(() => {
            errorMessage.style.display = 'none';
        }, 5000);
    }
});
var registerModal = document.getElementById("registerModal");
var registerLink = document.getElementById("registerLink");
var registerClose = document.getElementById("registerClose");

registerLink.onclick = function() {
    registerModal.style.display = "block";
}

registerClose.onclick = function() {
    registerModal.style.display = "none";
}

window.onclick = function(event) {
    if (event.target == registerModal) {
        registerModal.style.display = "none";
    }
}