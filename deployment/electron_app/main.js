const { app, BrowserWindow, shell } = require('electron');
const path = require('path');
const isDev = require('electron-is-dev');

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    title: "CosmOS ERP",
    icon: path.join(__dirname, 'icons/cosmos-icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      spellcheck: true
    },
    // Remove menu bar for a clean "native" feel
    autoHideMenuBar: true 
  });

  // Point to the server address
  const serverUrl = 'http://cosmos.local:8081';
  
  // Load the CosmOS ERP interface
  win.loadURL(serverUrl);

  // Open external links in the system browser instead of inside the app
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith(serverUrl)) {
      return { action: 'allow' };
    }
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
