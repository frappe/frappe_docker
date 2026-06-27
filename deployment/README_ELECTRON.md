# CosmOS ERP Electron Desktop App

This package contains the source code to build a native desktop application for CosmOS ERP using Electron.

## 🚀 Building the Application

1. **Prerequisites:**
   - Ensure you have [Node.js](https://nodejs.org/) and [npm](https://www.npmjs.com/) installed.

2. **Install Dependencies:**
   Navigate to the `electron_app` directory and run:
   ```bash
   cd electron_app
   npm install
   ```

3. **Run in Development Mode:**
   ```bash
   npm start
   ```

4. **Build the Installer (Windows/Mac/Linux):**
   To create a distributable installer (e.g., `.exe`, `.dmg`, `.deb`), run:
   ```bash
   npm run build
   ```

## ⚙️ Configuration

The app points to `http://cosmos.local:8081` by default. 
If you need to change the target server, edit `main.js` in the `electron_app` directory:

```javascript
const serverUrl = 'http://<YOUR_SERVER_IP>:8081';
```

## 🛠 Architecture
- **Shell:** Electron (Chromium + Node.js)
- **Backend:** Dockerized Frappe/CosmOS ERP
- **Communication:** Standard HTTPS/Websockets
