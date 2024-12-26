document.addEventListener('DOMContentLoaded', () => {
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
