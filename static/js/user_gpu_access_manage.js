document.addEventListener('DOMContentLoaded', async () => {
    const actionButtons = document.querySelectorAll('.save-btn');
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
                    if (!confirm("Are you sure you want to unlock the Update buttons? This action is risky!")) {
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

    // Fetch all users and populate the table
    async function fetchUserGpuAccess() {
        const response = await fetch('/user_gpu_access_manage');
        const text = await response.text();
        addEventListeners();
    }

    // Add event listeners to dynamically created elements
    function addEventListeners() {
        const saveButtons = document.querySelectorAll('.save-btn');
        saveButtons.forEach((button) =>
            button.addEventListener('click', async (e) => {
                const userId = button.getAttribute('data-user-id');
                const selectedGpuIds = [];
                // 搜集所有勾選的 GPU ID
                const checkboxes = document.querySelectorAll(`.gpu-checkbox[data-user-id="${userId}"]:checked`);
                checkboxes.forEach((checkbox) => {
                    selectedGpuIds.push(checkbox.getAttribute('data-gpu-id'));
                });

                await updateUserGpuAccess(userId, selectedGpuIds);
            })
        );
    }

    // Update user details
    async function updateUserGpuAccess(userId, selectedGpuIds) {
        try {
            const response = await fetch('/user_gpu_access_manage', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({id: userId, selectedGpuIds}),
            });
            
            if (response.ok) {
                const data = await response.json();
                alert(data.message);
                window.location.reload()
            } else if (response.status === 304) {
                alert("Nothing changed!");
                window.location.reload()
            } else {
                const data = await response.json();
                alert("Error:", data.message);
            }
        } catch (error) {
            console.error('Error:', error);
        }
    }

    // Fetch users on page load
    fetchUserGpuAccess();
});
