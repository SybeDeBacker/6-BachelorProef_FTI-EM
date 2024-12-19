const { ipcRenderer } = require('electron');

document.addEventListener('DOMContentLoaded', () => {
    const serverUrl = 'http://10.0.1.250'; // Server URL
    const statusLabel = document.getElementById('statusLabel');
    const messageArea = document.getElementById('messageArea');

    async function sendMessage(message, endpoint) {
        try {
            const result = await ipcRenderer.invoke('send-message', { message, endpoint, serverUrl });
            if (result.error) {
                appendMessage(`Error: ${result.error}`);
            } else {
                appendMessage(`Server: ${result.data.message || JSON.stringify(result.data)}`);
            }
        } catch (err) {
            appendMessage(`Unexpected Error: ${err.message}`);
        }
    }

    function appendMessage(msg) {
        messageArea.value += `${msg}\n`;
        messageArea.scrollTop = messageArea.scrollHeight;
    }

    document.getElementById('moveButton').addEventListener('click', () => {
        const x = document.getElementById('x').value || 0;
        const y = document.getElementById('y').value || 0;
        const z = document.getElementById('z').value || 0;
        const coordSystem = document.getElementById('coordSystem').value;

        const message = JSON.stringify({
            type: 'move',
            coordinate_system: coordSystem,
            data: { x, y, z },
        });
        sendMessage(message, 'move');
    });

    document.getElementById('pipetButton').addEventListener('click', () => {
        const pipetLevel = document.getElementById('pipetLevel').value || 0;

        const message = JSON.stringify({
            type: 'pipet_control',
            data: { pipet_level: pipetLevel },
        });
        sendMessage(message, 'pipet_control');
    });

    document.getElementById('requestButton').addEventListener('click', () => {
        sendMessage(JSON.stringify({ type: 'request', subject: 'current_pos' }), 'request');
    });

    appendMessage("Connecting...");
});
