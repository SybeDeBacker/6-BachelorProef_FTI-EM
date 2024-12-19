const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const axios = require('axios');

let mainWindow;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            preload: path.join(__dirname, 'renderer.js'),
            nodeIntegration: true,
            contextIsolation: false,
        },
    });

    mainWindow.loadFile('index.html');
}

app.whenReady().then(() => {
    createWindow();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
});

ipcMain.handle('send-message', async (event, { message, endpoint, serverUrl }) => {
    try {
        const url = `${serverUrl}/${endpoint}`;
        const response = endpoint === 'request'
            ? await axios.get(url)
            : await axios.post(url, JSON.parse(message));
        return { status: response.status, data: response.data };
    } catch (error) {
        return { error: error.message };
    }
});
