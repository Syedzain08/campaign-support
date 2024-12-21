document.addEventListener("DOMContentLoaded", function() {
    var showPassword = document.getElementById('showPassword');
    var showConfirmPassword = document.getElementById('showConfirmPassword');
    
    if (showPassword) {
        showPassword.addEventListener('change', function() {
            var passwordField = document.getElementById('password');
            if (this.checked) {
                passwordField.type = 'text';
            } else {
                passwordField.type = 'password';
            }
        });
    }

    if (showConfirmPassword) {
        showConfirmPassword.addEventListener('change', function() {
            var passwordField = document.getElementById('Confirm-password');
            if (this.checked) {
                passwordField.type = 'text';
            } else {
                passwordField.type = 'password';
            }
        });
    }
});
