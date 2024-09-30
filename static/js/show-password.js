document.addEventListener("DOMContentLoaded", function() {
document.getElementById('showPassword').addEventListener('change', function() {
    var passwordField = document.getElementById('password');
    if (this.checked) {
        passwordField.type = 'text';
    } else {
        passwordField.type = 'password';
    }
});

document.getElementById('showConfirmPassword').addEventListener('change', function() {
    var passwordField = document.getElementById('Confirm-password');
    if (this.checked) {
        passwordField.type = 'text';
    } else {
        passwordField.type = 'password';
    }
});
});