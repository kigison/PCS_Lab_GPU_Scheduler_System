document.addEventListener('DOMContentLoaded', () => {
    const rstpwdForm = document.getElementById('rstpwdForm');
    const newPasswordInput = document.getElementById('new_password');
    const confirmNewPasswordInput = document.getElementById('confirmPassword');
    const submitButton = rstpwdForm.querySelector('button[type="submit"]');

    // 初始禁用提交按鈕
    submitButton.disabled = true;
    submitButton.classList.add('disabled');

    // 驗證密碼一致性
    confirmNewPasswordInput.addEventListener('input', () => {
        // 清除樣式僅針對 confirmPasswordInput
        confirmNewPasswordInput.classList.remove('valid', 'invalid');

        // 若一致且 newPasswordInput 有值
        if (confirmNewPasswordInput.value === newPasswordInput.value && newPasswordInput.value.trim() !== "") {
            confirmNewPasswordInput.classList.add('valid');
            submitButton.disabled = false; // 啟用提交按鈕
            submitButton.classList.remove('disabled'); // 移除禁用樣式
        } else {
            confirmNewPasswordInput.classList.add('invalid');
            submitButton.disabled = true; // 禁用提交按鈕
            submitButton.classList.add('disabled'); // 增加禁用樣式
        }
    });

    // Handle registration
    if (rstpwdForm) {
        rstpwdForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const old_password = document.getElementById('old_password').value;
            const new_password = document.getElementById('new_password').value;

            try {
                const response = await fetch('/reset_password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: "user_reset_password", old_password, new_password }),
                });

                const data = await response.json();
                if (response.ok) {
                    alert(data.message);
                    window.location.href = "/logout";
                } else {
                    alert(`Error: ${data.error}`);
                }
            } catch (error) {
                console.error('Error:', error);
            }
        });
    }
});
