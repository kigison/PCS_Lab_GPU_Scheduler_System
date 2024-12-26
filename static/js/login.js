document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');

    // Handle login
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password }),
                });

                const data = await response.json();
                if (response.ok) {
                    alert(data.message);
                    window.location.href = '/';  // Redirect to dashboard
                } else {
                    alert(data.error);
                }
            } catch (error) {
                console.error('Error:', error);
            }
        });
    }

    // Redirect to the register page
    if (redirectButton) {
        redirectButton.addEventListener('click', () => {
            window.location.href = '/register';
        });
    }
});

const showHidePassword = document.getElementById('show-hide');
let passwordInput = document.getElementById('password');

showHidePassword.addEventListener('click', function () {
    showHidePassword.classList.toggle('show');

    if (showHidePassword.classList.contains('show')) {
        showHidePassword.classList.remove('fa-eye-slash');
        showHidePassword.classList.add('fa-eye');
        passwordInput.setAttribute('type', 'text');
    }
    else {
        showHidePassword.classList.add('fa-eye-slash');
        showHidePassword.classList.remove('fa-eye');
        passwordInput.setAttribute('type', 'password');
    }
});

function isMobileDevice() {
    let mobileDevices = ['Android','iPhone', 'iPad']
    for (var i = 0; i < mobileDevices.length; i++) {
        if (navigator.userAgent.match(mobileDevices[i])) {
            //console.log("isMobileDevice: match " + mobileDevices[i]);
            return true;
        }
    }
    return false
}

if (isMobileDevice()) {
    console.log("is mobile device");
} else {
    console.log("not mobile device");
}

if (window.PublicKeyCredential) {  //確認瀏覽器支援 WebAuthn
    console.log("support q-login");
    console.log(PublicKeyCredential.isConditionalMediationAvailable)
    // do your webauthn stuff
} else {
    // wah-wah, back to passwords for you
    console.log("not support q-login");
}

