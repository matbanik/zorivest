"use strict";
const electron = require("electron");
let __baseUrl = "http://127.0.0.1:8000";
let __token = "";
electron.contextBridge.exposeInMainWorld("api", {
  get baseUrl() {
    return __baseUrl;
  },
  get token() {
    return __token;
  },
  /** Initialize the bridge by fetching backend URL and token from main process */
  async init() {
    __baseUrl = await electron.ipcRenderer.invoke("get-backend-url");
    __token = await electron.ipcRenderer.invoke("get-auth-token");
  }
});
electron.contextBridge.exposeInMainWorld("electronStore", {
  get(key) {
    return electron.ipcRenderer.invoke("electron-store-get", key);
  },
  set(key, value) {
    electron.ipcRenderer.invoke("electron-store-set", key, value);
  }
});
electron.contextBridge.exposeInMainWorld("startupMetrics", {
  async getMetrics() {
    return electron.ipcRenderer.invoke("get-startup-metrics");
  },
  logRendererReady() {
    electron.ipcRenderer.invoke("log-renderer-ready", Date.now());
  }
});
