document.addEventListener('DOMContentLoaded', async () => {
    const actionButtons = document.querySelectorAll('.remove-btn, .admin-rst-pwd-btn');
    actionButtons.forEach((button) => {
        button.disabled = true; // 預設為禁用
    });

    // 綁定圖示點擊事件
    const actionHeaderIcons = document.querySelectorAll('.action-header-icon');
    actionHeaderIcons.forEach((icon) => {
        icon.addEventListener('click', () => {
            const column = icon.getAttribute('data-column');
            const currentState = icon.getAttribute('data-state');

            if (column === 'actions') {
                const isLocked = currentState === 'locked';

                if (isLocked) {
                    if (!confirm("Are you sure you want to unlock the Delete and Reset Password buttons? This action is risky!")) {
                        return;
                    }
                }

                // 切換按鈕禁用狀態
                actionButtons.forEach((button) => {
                    button.disabled = !isLocked; // 鎖定時禁用，解鎖時啟用
                });

                // 更新圖示狀態和類名
                icon.setAttribute('data-state', isLocked ? 'unlocked' : 'locked');
                icon.className = isLocked ? 'bi bi-unlock-fill action-header-icon' : 'bi bi-lock-fill action-header-icon';
            }
        });
    });

    const inputs = document.querySelectorAll('.table-text-input');
    inputs.forEach((input) => {
        // 初始化最小寬度
        adjustMinWidth(input);

        // 監聽輸入框內容變化，重新調整寬度
        input.addEventListener('input', () => adjustMinWidth(input));
    });

    function adjustMinWidth(input) {
        // 創建隱藏 span 測量內容寬度
        const span = document.createElement('span');
        span.style.visibility = 'hidden';
        span.style.whiteSpace = 'nowrap';
        span.style.position = 'absolute';
        span.style.font = window.getComputedStyle(input).font; // 字體一致
        span.textContent = input.value || input.placeholder;

        document.body.appendChild(span);

        // 根據 span 寬度設置輸入框的最小寬度
        const minWidth = span.offsetWidth + 15; // 添加額外 padding
        input.style.minWidth = `${minWidth}px`;

        document.body.removeChild(span); // 清理
    }

    const userTable = document.getElementById('userTable');

    // Fetch all users and populate the table
    async function fetchUsers() {
        const response = await fetch('/account_manage');
        const text = await response.text();
        addEventListeners();
    }

    // Add event listeners to dynamically created elements
    function addEventListeners() {
        const saveButtons = document.querySelectorAll('.save-btn');
        saveButtons.forEach((button) =>
            button.addEventListener('click', async (e) => {
                const userId = button.getAttribute('data-id');
                const name = document.querySelector(`.name-input[data-id="${userId}"]`).value;
                const email = document.querySelector(`.email-input[data-id="${userId}"]`).value;
                const lab = document.querySelector(`.lab-select[data-id="${userId}"]`).value;
                const priority = document.querySelector(`.priority-select[data-id="${userId}"]`).value;
                const time_multiplier = document.querySelector(`.time_multiplier-number[data-id="${userId}"]`).value;
                const is_admin = document.querySelector(`.admin-switch[data-id="${userId}"]`).checked;

                await updateUser(userId, name, email, lab, priority, time_multiplier, is_admin);
            })
        );
        const removeButtons = document.querySelectorAll('.remove-btn');
        removeButtons.forEach((button) =>
            button.addEventListener('click', async (e) => {
                const userId = button.getAttribute('data-id');
                if (confirm("Are you sure you want to remove this user?")) {
                    if (confirm("This action is irreversible. Are you sure you want to proceed?")) {
                        await removeUser(userId);
                    }
                }
            })
        );
        const rstPwdButtons = document.querySelectorAll('.admin-rst-pwd-btn');
        rstPwdButtons.forEach((button) =>
            button.addEventListener('click', async (e) => {
                const userId = button.getAttribute('data-id');
                if (confirm("Are you sure you want to reset this user's password?")) {
                    if (confirm("A new random password will be generated and emailed to the user. This action is irreversible. Do you want to proceed?")) {
                        await rstUserPwd(userId);
                    }
                }
            })
        );
    }

    // Update user details
    async function updateUser(userId, name, email, lab, priority, time_multiplier, is_admin) {
        try {
            const response = await fetch('/account_manage', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: "update", id: userId, name, email, lab, priority, time_multiplier, is_admin }),
            });

            if (response.ok) {
                const data = await response.json();
                alert(data.message);
                window.location.reload()
            } else {
                const data = await response.json();
                alert(`Error: ${data.error}`);
            }
        } catch (error) {
            console.error('Error:', error);
        }
    }

    async function removeUser(userId) {
        try {
            const response = await fetch('/account_manage', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: "remove", id: userId }),
            });

            if (response.ok) {
                const data = await response.json();
                alert(data.message);
                window.location.reload()
            } else {
                const data = await response.json();
                alert(`Error: ${data.error}`);
            }
        } catch (error) {
            console.error('Error:', error);
        }
    }

    async function rstUserPwd(userId) {
        try {
            const response = await fetch('/reset_password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: "admin_reset_password", id: userId }),
            });

            if (response.ok) {
                const data = await response.json();
                alert(data.message);
                window.location.reload()
            } else {
                const data = await response.json();
                alert(`Error: ${data.error}`);
            }
        } catch (error) {
            console.error('Error:', error);
        }
    }

    // Fetch users on page load
    fetchUsers();
});
