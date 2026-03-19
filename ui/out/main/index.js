"use strict";
const electron = require("electron");
const path = require("path");
const Store = require("electron-store");
const child_process = require("child_process");
const net = require("net");
const crypto = require("crypto");
class PythonManager {
  process = null;
  port = 0;
  token = "";
  externalUrl = null;
  /** Generate ephemeral Bearer token (64 hex chars = 32 random bytes) */
  generateToken() {
    this.token = crypto.randomBytes(32).toString("hex");
    return this.token;
  }
  /** Allocate a free port dynamically via net.createServer */
  async allocatePort() {
    return new Promise((resolve) => {
      const srv = net.createServer();
      srv.listen(0, () => {
        this.port = srv.address().port;
        srv.close(() => resolve(this.port));
      });
    });
  }
  /** Spawn Python subprocess with token and port */
  async start() {
    const pythonPath = electron.app.isPackaged ? path.join(process.resourcesPath, "python", "zorivest.exe") : "uv";
    const args = electron.app.isPackaged ? ["--port", String(this.port), "--token", this.token] : [
      "run",
      "uvicorn",
      "zorivest.api.app:create_app",
      "--factory",
      "--port",
      String(this.port),
      "--host",
      "127.0.0.1"
    ];
    const env = {
      ...process.env,
      ZORIVEST_AUTH_TOKEN: this.token
    };
    this.process = child_process.spawn(pythonPath, args, {
      stdio: electron.app.isPackaged ? "ignore" : "pipe",
      env
    });
    this.process.on("error", (err) => {
      console.error("[PythonManager] spawn error:", err.message);
    });
  }
  /** Health check with exponential backoff (100ms → 5s cap) */
  async waitForReady(maxWaitMs = 3e4) {
    const startTime = Date.now();
    let delay = 100;
    while (Date.now() - startTime < maxWaitMs) {
      try {
        const res = await fetch(`http://127.0.0.1:${this.port}/health`, {
          headers: { Authorization: `Bearer ${this.token}` }
        });
        if (res.ok) return true;
      } catch {
      }
      await new Promise((r) => setTimeout(r, delay));
      delay = Math.min(delay * 2, 5e3);
    }
    return false;
  }
  /** Graceful shutdown: POST /shutdown then wait up to 5s */
  async stop() {
    if (!this.process) return;
    try {
      await fetch(`http://127.0.0.1:${this.port}/shutdown`, {
        method: "POST",
        headers: { Authorization: `Bearer ${this.token}` }
      });
      await new Promise((resolve) => {
        const timer = setTimeout(() => {
          this.process?.kill();
          resolve();
        }, 5e3);
        this.process?.on("exit", () => {
          clearTimeout(timer);
          resolve();
        });
      });
    } catch {
      this.process?.kill();
    }
    this.process = null;
  }
  /** Override base URL for external backend (dev mode / E2E). */
  setExternalUrl(url) {
    this.externalUrl = url;
  }
  get baseUrl() {
    return this.externalUrl ?? `http://127.0.0.1:${this.port}`;
  }
  get authToken() {
    return this.token;
  }
}
const DEFAULT_BOUNDS = {
  width: 1280,
  height: 800
};
let _store = null;
function getStore() {
  if (!_store) {
    _store = new Store({
      name: "zorivest-window-state",
      defaults: {
        windowBounds: DEFAULT_BOUNDS
      }
    });
  }
  return _store;
}
function getStoredBounds() {
  return getStore().get("windowBounds") ?? DEFAULT_BOUNDS;
}
function saveWindowBounds(bounds) {
  getStore().set("windowBounds", bounds);
}
if (typeof electron.app === "undefined") {
  console.error(
    "\n[FATAL] This script must be run with the Electron binary, not Node.js.\n  Correct:   npx electron ./out/main/index.js\n  Incorrect: node ./out/main/index.js\n\nIf npx electron also fails, ensure the electron npm package is properly\ninstalled and has a valid binary at node_modules/electron/dist/electron.exe.\n"
  );
  process.exit(1);
}
function createAppMenu() {
  const template = [
    { role: "fileMenu" },
    { role: "editMenu" },
    { role: "viewMenu" },
    { role: "windowMenu" },
    {
      role: "help",
      submenu: [
        {
          label: "Zorivest on GitHub",
          click: () => electron.shell.openExternal("https://github.com/matbanik/zorivest")
        },
        {
          label: "Report an Issue",
          click: () => electron.shell.openExternal("https://github.com/matbanik/zorivest/issues")
        },
        {
          label: "Discord Community",
          click: () => electron.shell.openExternal("https://discord.gg/aW5RS8g6D7")
        }
      ]
    }
  ];
  electron.Menu.setApplicationMenu(electron.Menu.buildFromTemplate(template));
}
const pythonManager = new PythonManager();
let mainWindow = null;
let splashWindow = null;
function createSplashWindow() {
  const splash = new electron.BrowserWindow({
    width: 400,
    height: 300,
    frame: false,
    transparent: false,
    resizable: false,
    show: true,
    icon: path.join(__dirname, "../../build/icon.ico"),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  });
  splash.loadFile(path.join(__dirname, "splash.html"));
  return splash;
}
function createMainWindow() {
  const storedBounds = getStoredBounds();
  const win = new electron.BrowserWindow({
    width: storedBounds.width,
    height: storedBounds.height,
    ...storedBounds.x !== void 0 && { x: storedBounds.x },
    ...storedBounds.y !== void 0 && { y: storedBounds.y },
    minWidth: 1024,
    minHeight: 600,
    show: false,
    backgroundColor: "#282a36",
    icon: path.join(__dirname, "../../build/icon.ico"),
    webPreferences: {
      preload: path.join(__dirname, "../preload/index.js"),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      webSecurity: true
    }
  });
  let boundsTimer = null;
  const debouncedSaveBounds = () => {
    if (boundsTimer) clearTimeout(boundsTimer);
    boundsTimer = setTimeout(() => {
      if (!win.isDestroyed()) {
        const bounds = win.getBounds();
        saveWindowBounds(bounds);
      }
    }, 500);
  };
  win.on("resize", debouncedSaveBounds);
  win.on("move", debouncedSaveBounds);
  win.webContents.on("will-navigate", (event, url) => {
    if (!url.startsWith("file://")) {
      event.preventDefault();
    }
  });
  win.webContents.setWindowOpenHandler(() => ({ action: "deny" }));
  return win;
}
function registerIpcHandlers() {
  electron.ipcMain.handle("get-startup-metrics", () => ({
    processStart: process.hrtime.bigint().toString(),
    electronReady: Date.now()
  }));
  electron.ipcMain.handle("get-backend-url", () => pythonManager.baseUrl);
  electron.ipcMain.handle("get-auth-token", () => pythonManager.authToken);
  const rendererStore = new Store({ name: "zorivest-renderer" });
  electron.ipcMain.handle("electron-store-get", (_event, key) => rendererStore.get(key));
  electron.ipcMain.handle("electron-store-set", (_event, key, value) => {
    rendererStore.set(key, value);
  });
  electron.ipcMain.handle("log-renderer-ready", (_event, timestamp) => {
    console.log(`[startup] renderer ready at ${timestamp}ms`);
  });
}
electron.app.whenReady().then(async () => {
  registerIpcHandlers();
  createAppMenu();
  const isDev = !!process.env.ELECTRON_RENDERER_URL;
  splashWindow = createSplashWindow();
  mainWindow = createMainWindow();
  let ready;
  if (process.env.ZORIVEST_BACKEND_URL) {
    pythonManager.setExternalUrl(process.env.ZORIVEST_BACKEND_URL);
    await new Promise((r) => setTimeout(r, 500));
    ready = true;
  } else if (isDev) {
    console.warn(
      '[startup] Dev mode: no ZORIVEST_BACKEND_URL set. Backend will be unreachable. Use "npm run dev" to start both processes.'
    );
    await new Promise((r) => setTimeout(r, 1e3));
    ready = true;
  } else {
    pythonManager.generateToken();
    await pythonManager.allocatePort();
    await pythonManager.start();
    ready = await pythonManager.waitForReady(3e4);
  }
  if (ready) {
    if (process.env.ELECTRON_RENDERER_URL) {
      mainWindow.loadURL(process.env.ELECTRON_RENDERER_URL);
    } else {
      mainWindow.loadFile(path.join(__dirname, "../renderer/index.html"));
    }
    mainWindow.once("ready-to-show", () => {
      splashWindow?.close();
      splashWindow = null;
      mainWindow?.show();
    });
  } else {
    splashWindow?.webContents.executeJavaScript(`
      document.getElementById('loading').style.display = 'none';
      document.getElementById('status').style.display = 'none';
      document.getElementById('error-container').style.display = 'flex';
    `);
  }
});
electron.app.on("window-all-closed", () => {
  pythonManager.stop();
  electron.app.quit();
});
electron.app.on("before-quit", async () => {
  await pythonManager.stop();
});
