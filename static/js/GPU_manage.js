document.addEventListener('DOMContentLoaded', async () => {
    const actionButtons = document.querySelectorAll('.remove-btn');
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
                    if (!confirm("Are you sure you want to unlock the Delete buttons? This action is risky!")) {
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
        const textarea = input.tagName.toLowerCase() === 'textarea';
        span.style.visibility = 'hidden';
        span.style.whiteSpace = textarea ? 'pre-wrap' : 'nowrap'; // 多行文本適應
        span.style.position = 'absolute';
        span.style.font = window.getComputedStyle(input).font; // 字體一致
        span.style.lineHeight = window.getComputedStyle(input).lineHeight; // 行高一致
        // span.style.wordWrap = 'break-word'; // 確保換行生效
        // span.textContent = input.value || input.placeholder;
        // 為 textarea 的測量添加行尾換行符模擬
        span.textContent = textarea ? input.value + '\n' : input.value || input.placeholder;

        document.body.appendChild(span);

        // 計算寬度和高度
        const minWidth = span.offsetWidth + 10; // 添加額外 padding
        const minHeight = span.offsetHeight + 10; // 自動計算高度

        // 設置最小寬度和高度
        input.style.minWidth = `${minWidth}px`;
        if (textarea) {
            input.style.height = 'auto'; // 先重置高度以便重新計算
            input.style.height = `${minHeight}px`;
        }

        document.body.removeChild(span); // 清理
    }


    // Fetch all GPUs and populate the table
    async function fetchGPUs() {
        const response = await fetch('/GPU_manage');
        const text = await response.text();
        addEventListeners();
    }

    // Add event listeners to dynamically created elements
    function addEventListeners() {
        const saveButtons = document.querySelectorAll('.save-btn');
        saveButtons.forEach((button) =>
            button.addEventListener('click', async (e) => {
                const gpuId = button.getAttribute('data-id');
                const max_hours = document.querySelector(`.max_hours-number[data-id="${gpuId}"]`).value;
                const connection_info = document.querySelector(`.connection_info-input[data-id="${gpuId}"]`).value;
                const status = document.querySelector(`.status-select[data-id="${gpuId}"]`).value === "true";

                await updateGPU(gpuId, max_hours, connection_info, status);
            })
        );
        const removeButtons = document.querySelectorAll('.remove-btn');
        removeButtons.forEach((button) =>
            button.addEventListener('click', async (e) => {
                const gpuId = button.getAttribute('data-id');
                if (confirm("Are you sure you want to remove this GPU?")) {
                    if (confirm("This action is irreversible. Are you sure you want to proceed?")) {
                        await removeGPU(gpuId);
                    }
                }
            })
        );
        const addButtons = document.querySelectorAll('.add-btn');
        addButtons.forEach((button) =>
            button.addEventListener('click', async (e) => {
                const gpuId = "add";
                const model = document.querySelector(`.model-select[data-id="${gpuId}"]`).value;
                const cuda_version = document.querySelector(`.cuda_version-select[data-id="${gpuId}"]`).value;
                const connection_info = document.querySelector(`.connection_info-input[data-id="${gpuId}"]`).value;

                await addGPU(gpuId, model, cuda_version, connection_info);
            })
        );
    }

    // Update GPU details
    async function updateGPU(gpuId, max_hours, connection_info, status) {
        try {
            const response = await fetch('/GPU_manage', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: "update", id: gpuId, max_hours, connection_info, status}),
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

    async function removeGPU(gpuId) {
        try {
            const response = await fetch('/GPU_manage', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: "remove", id: gpuId }),
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

    async function addGPU(gpuId, model, cuda_version, connection_info) {
        try {
            const response = await fetch('/GPU_manage', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: "add", id: gpuId, model, cuda_version, connection_info}),
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

    // Fetch GPUs on page load
    fetchGPUs();
});
