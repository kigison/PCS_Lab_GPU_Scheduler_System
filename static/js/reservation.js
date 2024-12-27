document.addEventListener('DOMContentLoaded', () => {
    // 計算並更新倒數時間
    function updateCountdown(id, startTime, duration) {
        const countdownElement = document.getElementById(`countdown-${id}`);
        const startTimeDate = new Date(startTime); // 把 datetime 字符串轉換成 Date 物件
        const endTime = startTimeDate.getTime() + (duration * 60 * 60 * 1000); // Convert duration to milliseconds
        setInterval(function() {
            const now = new Date().getTime();
            const timeLeft = endTime - now;

            if (timeLeft <= 0) {
                countdownElement.innerHTML = "Time is up!";
            } else {
                const hours = Math.floor(timeLeft / (1000 * 60 * 60));
                const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
                countdownElement.innerHTML = `${hours}hours ${String(minutes).padStart(2, '0')}minutes.`; // 顯示 [小時:分鐘]
            }
        }, 1000);
    }

    // 當頁面加載完成後，對每個GPU進行倒數計時更新
    document.querySelectorAll('.remaining_time').forEach((element) => {
        const gpuId = element.getAttribute('data-id');
        const startTime = element.getAttribute('start_time');
        const duration = element.getAttribute('duration');
        
        if (gpuId && startTime && duration) {
            updateCountdown(gpuId, startTime, duration);
        }
    });

    function addEventListeners() {
        const terminateButtons = document.querySelectorAll('.terminate-btn');
        terminateButtons.forEach((button) =>
            button.addEventListener('click', async (e) => {
                const gpuId = button.getAttribute('data-id');
                
                await terminateRsv(gpuId);
            })
        );
        const startButtons = document.querySelectorAll('.start-btn');
        startButtons.forEach((button) =>
            button.addEventListener('click', async (e) => {
                const gpuId = button.getAttribute('data-id');
                
                await startRsv(gpuId);
            })
        );
        const cancelButtons = document.querySelectorAll('.cancel-btn');
        cancelButtons.forEach((button) =>
            button.addEventListener('click', async (e) => {
                const gpuId = button.getAttribute('data-id');
                
                await cancelRsv(gpuId);
            })
        );
        const reserveButtons = document.querySelectorAll('.reserve-btn');
        reserveButtons.forEach((button) =>
            button.addEventListener('click', async (e) => {
                const gpuId = button.getAttribute('data-id');
                const duration = document.querySelector(`.duration[data-id="${gpuId}"]`).value;
                
                await reserveRsv(gpuId, duration);
            })
        );
    }

    async function terminateRsv(gpuId) {
        try {
            const response = await fetch('/reservation', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'terminate', gpu: gpuId }),
            });

            if (response.ok) {
                const data = await response.json();
                alert(data.message);
                window.location.reload()
            } else {
                const data = await response.json();
                alert(data.error);
            }
        } catch (error) {
            console.error('Error:', error);
        }
    }

    async function startRsv(gpuId) {
        try {
            const response = await fetch('/reservation', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'start', gpu: gpuId }),
            });

            if (response.ok) {
                const data = await response.json();
                alert(data.message);
                window.location.reload()
            } else {
                const data = await response.json();
                alert(data.error);
            }
        } catch (error) {
            console.error('Error:', error);
        }
    }

    async function cancelRsv(gpuId) {
        try {
            const response = await fetch('/reservation', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'cancel', gpu: gpuId }),
            });

            if (response.ok) {
                const data = await response.json();
                alert(data.message);
                window.location.reload()
            } else {
                const data = await response.json();
                alert(data.error);
            }
        } catch (error) {
            console.error('Error:', error);
        }
    }

    async function reserveRsv(gpuId, duration) {
        try {
            const response = await fetch('/reservation', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'reserve', gpu: gpuId, duration: duration }),
            });

            if (response.ok) {
                const data = await response.json();
                alert(data.message);
                window.location.reload()
            } else {
                const data = await response.json();
                alert(data.error);
            }
        } catch (error) {
            console.error('Error:', error);
        }
    }

    addEventListeners();
});
