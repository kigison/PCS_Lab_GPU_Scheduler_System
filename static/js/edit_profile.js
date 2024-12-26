document.addEventListener('DOMContentLoaded', async () => {
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
        const minWidth = span.offsetWidth + 10; // 添加額外 padding
        input.style.minWidth = `${minWidth}px`;

        document.body.removeChild(span); // 清理
    }

    const userTable = document.getElementById('userTable');

    // Fetch all users and populate the table
    async function fetchUsers() {
        const response = await fetch('/edit_profile');
        const text = await response.text();

        addEventListeners();
    }

    // Add event listeners to dynamically created elements
    function addEventListeners() {
        const saveButtons = document.querySelectorAll('.save-btn');
        saveButtons.forEach((button) =>
            button.addEventListener('click', async (e) => {
                const userId = button.getAttribute('data-id');
                const username = document.querySelector('.username-input').value;
                const email = document.querySelector('.email-input').value;
                const phone = document.querySelector('.phone-input').value;
                await updateUser(userId, username, email, phone);
            })
        );
    }

    // Update user details
    async function updateUser(userId, username, email, phone) {
        try {
            const response = await fetch('/edit_profile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: userId, username, email, phone }),
            });

            if (response.ok) {
                const data = await response.json();
                alert(data.message);
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
