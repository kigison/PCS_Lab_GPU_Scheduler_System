document.addEventListener('DOMContentLoaded', () => {
    const registerForm = document.getElementById('registerForm');

    // Handle registration
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const name = document.getElementById('name').value;
            const email = document.getElementById('email').value;
            const phone = document.getElementById('phone').value;
            const password = document.getElementById('password').value;

            try {
                const response = await fetch('/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, username, email, phone, password }),
                });

                if (response.ok) {
                    const data = await response.json();
                    alert(data.message);
                    // Display or process the Login page.
                    window.location.href = "/login";
                } else {
                    alert("Redirect to Login page failed."); // Display error message.
                }
            } catch (error) {
                console.error('Error:', error);
            }
        });
    }
});
