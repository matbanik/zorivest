# Phase 10: Service Daemon — Cross-Platform Background Service

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) | Prerequisites: [Phase 4](04-rest-api.md), [Phase 7](07-distribution.md), [Phase 9](09-scheduling.md) | Consumed by: [Phase 6 GUI](06-gui.md) (Settings panel), [Phase 5 MCP](05-mcp-server.md) (service tools)

---

## Goal

Enable the Python backend (FastAPI + APScheduler + SQLCipher) to run as a **native OS background service/daemon** that auto-starts at user login, auto-restarts on crash, and runs independently of the Electron GUI. On Windows, the service runs at the system level and survives logout/reboot. On macOS and Linux, the service runs at the user session level — it starts at login and stops at logout. Provide GUI and MCP control surfaces for service lifecycle management, health monitoring, and log access.

---

## Design Decisions

### Why Custom Native Wrappers (Not npm Packages)

| Alternative | Why Not |
|---|---|
| `node-windows`/`node-mac`/`node-linux` | Adds Node.js runtime dependency just to wrap a PyInstaller binary — unnecessary indirection |
| `nsm` (Node Service Manager) | Thin wrapper over above; same runtime concern, less maintained |
| `os-service` (C++ addon) | Requires `node-gyp` compilation, no macOS support |
| `serviceman` (Go binary) | CLI-only, no programmatic API for GUI integration |
| PM2 | Process manager (not a true OS service); wraps in another Node.js process |
| `pywin32` `win32service` | Windows-only Python dependency; WinSW is simpler and language-agnostic |

**Chosen approach:** Platform-native service config files (WinSW XML + launchd plist + systemd unit) managed by a TypeScript `ServiceManager` class in the Electron main process. The backend binary is the managed process — no additional runtime required.

### Dual-Layer Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  Layer 1: OS Service Wrapper (per-platform, zero dependencies)   │
│  ┌───────────────────┐  ┌─────────────────┐  ┌────────────────┐ │
│  │  WinSW            │  │  launchd        │  │  systemd       │ │
│  │  (Windows Service) │  │  (LaunchAgent)  │  │  (user unit)   │ │
│  └────────┬──────────┘  └────────┬────────┘  └───────┬────────┘ │
│           └──────────────────────┴───────────────────┘           │
│                               │ manages                          │
│  ┌────────────────────────────▼──────────────────────────────┐   │
│  │  Layer 2: Python Backend (zorivest-api binary)            │   │
│  │  ┌──────────┐  ┌──────────────┐  ┌───────────────┐       │   │
│  │  │ FastAPI   │  │ APScheduler  │  │ SQLCipher DB  │       │   │
│  │  │ :8765     │  │ (cron jobs)  │  │               │       │   │
│  │  └──────────┘  └──────────────┘  └───────────────┘       │   │
│  └───────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  Consumers (connect to backend over localhost:8765)               │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐    │
│  │ Electron GUI │  │ MCP Server   │  │ IDE Clients         │    │
│  │ (React)      │  │ (TypeScript) │  │ (Cursor, Claude,..) │    │
│  └──────────────┘  └──────────────┘  └─────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

**Key properties:**

1. **The Python backend IS the service** — it already contains FastAPI + APScheduler + SQLCipher. The wrapper just ensures it stays running.
2. **No additional runtime** — the PyInstaller binary is self-contained. No Node.js needed on the user's system for the service itself.
3. **GUI is optional** — the backend runs independently; the Electron GUI connects when opened.
4. **MCP server is independent** — connects to the backend over REST; can run in IDE or as a second service.
5. **Existing REST API is the control plane** — `GET /health`, `GET /version`, `zorivest_diagnose` already provide diagnostics.

### Platform Service Scope

| Platform | Service Level | Admin Required | Auto-Start Mechanism | Persistence |
|---|---|---|---|---|
| **Windows** | System-level service (user account) | ✅ UAC prompt at install + start/stop | Windows SCM `AUTO_START` | Survives logout + reboot |
| **macOS** | User-level LaunchAgent | ❌ No admin needed | `RunAtLoad` key in plist | Starts at login, stops at logout |
| **Linux** | User-level systemd | ❌ No admin needed | `systemctl --user enable` | Starts at login; `enable-linger` needed for reboot persistence |

> [!NOTE]
> **Platform Guarantee Matrix:**
>
> | Event | Windows | macOS | Linux (no linger) | Linux (with linger) |
> |---|---|---|---|---|
> | Boot (no login) | ✅ Runs | ❌ Not running | ❌ Not running | ✅ Runs |
> | User login | ✅ Already running | ✅ Starts | ✅ Starts | ✅ Already running |
> | User logout | ✅ Keeps running | ❌ Stops | ❌ Stops | ✅ Keeps running |
> | Process crash | ✅ Auto-restart | ✅ Auto-restart | ✅ Auto-restart | ✅ Auto-restart |
> | Reboot | ✅ Auto-start | ✅ At next login | ❌ At next login only | ✅ Auto-start |

> [!IMPORTANT]
> **Windows elevation:** `net start`/`net stop` require admin privileges. The GUI uses [`sudo-prompt`](https://www.npmjs.com/package/sudo-prompt) (or [`@vscode/sudo-prompt`](https://www.npmjs.com/package/@vscode/sudo-prompt)) to trigger a single UAC dialog when the user clicks Start/Stop/Restart. Status queries via `sc query` require no elevation.

---

## 10.1: Service Configuration Files

### 10.1a: Windows — WinSW Service Configuration

> WinSW (Windows Service Wrapper) is the same tool used internally by `node-windows`. It wraps any executable as a native Windows Service visible in `services.msc`.

**File**: Bundled as `resources/service/zorivest-service.xml` in the Electron app.

```xml
<!-- resources/service/zorivest-service.xml -->
<service>
  <id>zorivest-backend</id>
  <name>Zorivest Backend</name>
  <description>Zorivest REST API, Scheduler, and Database Engine</description>

  <!-- Path to PyInstaller-built backend binary -->
  <executable>%ZORIVEST_BACKEND_PATH%</executable>

  <!-- Logging: WinSW manages stdout/stderr capture -->
  <log mode="roll-by-size">
    <sizeThreshold>10240</sizeThreshold>
    <keepFiles>8</keepFiles>
    <logpath>%LOCALAPPDATA%\zorivest\logs</logpath>
  </log>

  <!-- Auto-restart on failure -->
  <onfailure action="restart" delay="5 sec"/>
  <onfailure action="restart" delay="10 sec"/>
  <onfailure action="restart" delay="30 sec"/>
  <resetfailure>1 hour</resetfailure>

  <!-- Startup type: automatic -->
  <startmode>Automatic</startmode>

  <!-- Run as the installing user's account (NOT LocalSystem) -->
  <!-- This ensures %LOCALAPPDATA% resolves to the user's data directory -->
  <serviceaccount>
    <username>.\%USERNAME%</username>
    <allowservicelogon>true</allowservicelogon>
  </serviceaccount>

  <!-- Graceful shutdown: send Ctrl+C, wait 15s before kill -->
  <stopparentprocessfirst>true</stopparentprocessfirst>
  <stoptimeout>15 sec</stoptimeout>

  <!-- Environment variables -->
  <env name="ZORIVEST_ENV" value="production"/>
  <env name="ZORIVEST_LOG_DIR" value="%LOCALAPPDATA%\zorivest\logs"/>
</service>
```

**WinSW binary**: `zorivest-service.exe` (renamed copy of `WinSW-x64.exe`) is bundled alongside the XML config. Electron-builder includes both in `extraResources`.

**Install/uninstall commands:**
```powershell
# Install (runs during NSIS postinstall)
zorivest-service.exe install

# Start
net start zorivest-backend

# Stop
net stop zorivest-backend

# Uninstall (runs during NSIS uninstall)
net stop zorivest-backend
zorivest-service.exe uninstall
```

### 10.1b: macOS — LaunchAgent Plist

> User-level LaunchAgent in `~/Library/LaunchAgents/` — no admin password required.

**Generated on first launch** by the Electron main process:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.zorivest.backend</string>

  <key>Program</key>
  <string>/Applications/Zorivest.app/Contents/Resources/backend/zorivest-api</string>

  <key>ProgramArguments</key>
  <array>
    <string>/Applications/Zorivest.app/Contents/Resources/backend/zorivest-api</string>
  </array>

  <!-- Start at login -->
  <key>RunAtLoad</key>
  <true/>

  <!-- Auto-restart on crash -->
  <key>KeepAlive</key>
  <true/>

  <!-- Throttle restarts (min 10s between launches) -->
  <key>ThrottleInterval</key>
  <integer>10</integer>

  <!-- Log output -->
  <key>StandardOutPath</key>
  <string>~/Library/Application Support/zorivest/logs/service-stdout.log</string>
  <key>StandardErrorPath</key>
  <string>~/Library/Application Support/zorivest/logs/service-stderr.log</string>

  <!-- Environment -->
  <key>EnvironmentVariables</key>
  <dict>
    <key>ZORIVEST_ENV</key>
    <string>production</string>
    <key>ZORIVEST_LOG_DIR</key>
    <string>~/Library/Application Support/zorivest/logs</string>
  </dict>
</dict>
</plist>
```

**Install/uninstall commands:**
```bash
# Install (write plist + load)
cp com.zorivest.backend.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.zorivest.backend.plist

# Stop
launchctl unload ~/Library/LaunchAgents/com.zorivest.backend.plist

# Start
launchctl load ~/Library/LaunchAgents/com.zorivest.backend.plist

# Uninstall
launchctl unload ~/Library/LaunchAgents/com.zorivest.backend.plist
rm ~/Library/LaunchAgents/com.zorivest.backend.plist
```

### 10.1c: Linux — systemd User Service Unit

> User-level systemd service in `~/.config/systemd/user/` — no sudo required.

**Generated on first launch** by the Electron main process:

```ini
# ~/.config/systemd/user/zorivest-backend.service
[Unit]
Description=Zorivest Backend — REST API, Scheduler, and Database Engine
After=network.target

[Service]
Type=simple
ExecStart=%h/.local/share/zorivest/backend/zorivest-api
Restart=always
RestartSec=5
Environment=ZORIVEST_ENV=production
Environment=ZORIVEST_LOG_DIR=%h/.local/share/zorivest/logs

# Graceful shutdown
TimeoutStopSec=15
KillSignal=SIGINT

# Logging goes to journald (also written to files by the app)
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

**Install/uninstall commands:**
```bash
# Install (write unit + enable + start)
mkdir -p ~/.config/systemd/user
cp zorivest-backend.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now zorivest-backend

# Status
systemctl --user is-active zorivest-backend

# Start / Stop / Restart
systemctl --user start zorivest-backend
systemctl --user stop zorivest-backend
systemctl --user restart zorivest-backend

# Enable reboot persistence (requires sudo ONCE, or admin pre-configuration)
loginctl enable-linger $USER

# Uninstall
systemctl --user disable --now zorivest-backend
rm ~/.config/systemd/user/zorivest-backend.service
systemctl --user daemon-reload
```

> [!NOTE]
> **`enable-linger` caveat:** Without `loginctl enable-linger $USER`, systemd user services stop when the user logs out. The first-launch setup prompts the user to run this command once (requires admin). If `enable-linger` is not available, the service restarts at next login.

---

## 10.2: Service Manager Class (Electron Main Process)

A TypeScript class in the Electron main process that wraps platform-specific service commands. The GUI renderer communicates with this class via Electron IPC.

### Platform Detection

```typescript
// ui/src/main/service/platform.ts

export type Platform = 'windows' | 'macos' | 'linux';

export function detectPlatform(): Platform {
  switch (process.platform) {
    case 'win32': return 'windows';
    case 'darwin': return 'macos';
    default: return 'linux';
  }
}
```

### Service Manager

```typescript
// ui/src/main/service/ServiceManager.ts

import { execSync, exec } from 'child_process';
import { app, shell } from 'electron';
import path from 'path';
import fs from 'fs';
import { detectPlatform, type Platform } from './platform';

export interface ServiceStatus {
  state: 'running' | 'stopped' | 'unknown' | 'error';
  pid: number | null;
  uptime_seconds: number | null;
  auto_start: boolean;
  error_message: string | null;
}

const SERVICE_NAME = 'zorivest-backend';
const PLIST_LABEL = 'com.zorivest.backend';
const PLIST_PATH = path.join(
  app.getPath('home'), 'Library', 'LaunchAgents', `${PLIST_LABEL}.plist`
);
const SYSTEMD_UNIT = `${SERVICE_NAME}.service`;
const SYSTEMD_UNIT_PATH = path.join(
  app.getPath('home'), '.config', 'systemd', 'user', SYSTEMD_UNIT
);

export class ServiceManager {
  private platform: Platform;

  constructor() {
    this.platform = detectPlatform();
  }

  // ── Status ────────────────────────────────────────────────

  async getStatus(): Promise<ServiceStatus> {
    try {
      switch (this.platform) {
        case 'windows': return this.getWindowsStatus();
        case 'macos':   return this.getMacStatus();
        case 'linux':   return this.getLinuxStatus();
      }
    } catch (err) {
      return {
        state: 'error',
        pid: null,
        uptime_seconds: null,
        auto_start: false,
        error_message: (err as Error).message,
      };
    }
  }

  private getWindowsStatus(): ServiceStatus {
    // sc query does NOT require elevation
    const output = execSync(`sc query ${SERVICE_NAME}`, { encoding: 'utf8' });
    const isRunning = output.includes('RUNNING');
    const isStopped = output.includes('STOPPED');

    // Check auto-start config
    const configOutput = execSync(`sc qc ${SERVICE_NAME}`, { encoding: 'utf8' });
    const autoStart = configOutput.includes('AUTO_START');

    return {
      state: isRunning ? 'running' : isStopped ? 'stopped' : 'unknown',
      pid: isRunning ? this.extractWindowsPid(output) : null,
      uptime_seconds: null, // Windows SCM doesn't expose uptime; use /health
      auto_start: autoStart,
      error_message: null,
    };
  }

  private getMacStatus(): ServiceStatus {
    try {
      const output = execSync(
        `launchctl list ${PLIST_LABEL} 2>/dev/null`, { encoding: 'utf8' }
      );
      const pidMatch = output.match(/"PID"\s*=\s*(\d+)/);
      const pid = pidMatch ? parseInt(pidMatch[1], 10) : null;

      return {
        state: pid ? 'running' : 'stopped',
        pid,
        uptime_seconds: null,
        auto_start: fs.existsSync(PLIST_PATH),
        error_message: null,
      };
    } catch {
      return {
        state: 'stopped',
        pid: null,
        uptime_seconds: null,
        auto_start: fs.existsSync(PLIST_PATH),
        error_message: null,
      };
    }
  }

  private getLinuxStatus(): ServiceStatus {
    try {
      const isActive = execSync(
        `systemctl --user is-active ${SYSTEMD_UNIT}`, { encoding: 'utf8' }
      ).trim();
      const isEnabled = execSync(
        `systemctl --user is-enabled ${SYSTEMD_UNIT}`, { encoding: 'utf8' }
      ).trim();

      let pid: number | null = null;
      if (isActive === 'active') {
        const showOutput = execSync(
          `systemctl --user show ${SYSTEMD_UNIT} --property=MainPID`,
          { encoding: 'utf8' }
        );
        const pidMatch = showOutput.match(/MainPID=(\d+)/);
        pid = pidMatch ? parseInt(pidMatch[1], 10) : null;
      }

      return {
        state: isActive === 'active' ? 'running' : 'stopped',
        pid,
        uptime_seconds: null,
        auto_start: isEnabled === 'enabled',
        error_message: null,
      };
    } catch {
      return {
        state: 'stopped',
        pid: null,
        uptime_seconds: null,
        auto_start: false,
        error_message: null,
      };
    }
  }

  // ── Start / Stop / Restart ────────────────────────────────
  //
  // On Windows, start/stop require elevation. The GUI uses
  // sudo-prompt to trigger a UAC dialog. On macOS/Linux,
  // user-level service commands require no elevation.

  async start(): Promise<void> {
    switch (this.platform) {
      case 'windows':
        await this.elevatedExec(`net start ${SERVICE_NAME}`);
        break;
      case 'macos':
        execSync(`launchctl load ${PLIST_PATH}`);
        break;
      case 'linux':
        execSync(`systemctl --user start ${SYSTEMD_UNIT}`);
        break;
    }
  }

  async stop(): Promise<void> {
    switch (this.platform) {
      case 'windows':
        await this.elevatedExec(`net stop ${SERVICE_NAME}`);
        break;
      case 'macos':
        execSync(`launchctl unload ${PLIST_PATH}`);
        break;
      case 'linux':
        execSync(`systemctl --user stop ${SYSTEMD_UNIT}`);
        break;
    }
  }

  async restart(): Promise<void> {
    switch (this.platform) {
      case 'windows':
        await this.elevatedExec(`net stop ${SERVICE_NAME} & net start ${SERVICE_NAME}`);
        break;
      case 'macos':
        execSync(`launchctl unload ${PLIST_PATH}`);
        execSync(`launchctl load ${PLIST_PATH}`);
        break;
      case 'linux':
        execSync(`systemctl --user restart ${SYSTEMD_UNIT}`);
        break;
    }
  }

  // ── Auto-Start Toggle ─────────────────────────────────────

  async setAutoStart(enabled: boolean): Promise<void> {
    switch (this.platform) {
      case 'windows': {
        const startType = enabled ? 'auto' : 'demand';
        await this.elevatedExec(`sc config ${SERVICE_NAME} start= ${startType}`);
        break;
      }
      case 'macos': {
        // Toggle RunAtLoad in plist — rewrite the file
        // In practice, the GUI writes the updated plist and reloads
        if (enabled) {
          execSync(`launchctl load ${PLIST_PATH}`);
        } else {
          execSync(`launchctl unload ${PLIST_PATH}`);
        }
        break;
      }
      case 'linux': {
        const action = enabled ? 'enable' : 'disable';
        execSync(`systemctl --user ${action} ${SYSTEMD_UNIT}`);
        break;
      }
    }
  }

  // ── Open Log Folder ───────────────────────────────────────

  async openLogFolder(): Promise<void> {
    const logDir = this.getLogDirectory();
    await shell.openPath(logDir);
  }

  private getLogDirectory(): string {
    // Matches Phase 1A log directory resolution
    switch (this.platform) {
      case 'windows':
        return path.join(
          process.env.LOCALAPPDATA || path.join(app.getPath('home'), 'AppData', 'Local'),
          'zorivest', 'logs'
        );
      case 'macos':
        return path.join(app.getPath('home'), 'Library', 'Application Support', 'zorivest', 'logs');
      case 'linux':
        return path.join(
          process.env.XDG_DATA_HOME || path.join(app.getPath('home'), '.local', 'share'),
          'zorivest', 'logs'
        );
    }
  }

  // ── First-Launch Setup ────────────────────────────────────

  async isInstalled(): Promise<boolean> {
    switch (this.platform) {
      case 'windows':
        try {
          execSync(`sc query ${SERVICE_NAME}`, { encoding: 'utf8' });
          return true;
        } catch { return false; }
      case 'macos':
        return fs.existsSync(PLIST_PATH);
      case 'linux':
        return fs.existsSync(SYSTEMD_UNIT_PATH);
    }
  }

  // ── Private Helpers ───────────────────────────────────────

  private extractWindowsPid(scOutput: string): number | null {
    // sc query doesn't return PID directly; use tasklist
    try {
      const task = execSync(
        `tasklist /FI "IMAGENAME eq zorivest-api.exe" /FO CSV /NH`,
        { encoding: 'utf8' }
      );
      const match = task.match(/"(\d+)"/);
      return match ? parseInt(match[1], 10) : null;
    } catch { return null; }
  }

  private elevatedExec(command: string): Promise<void> {
    // Uses sudo-prompt for UAC dialog on Windows
    // Falls back to execSync on macOS/Linux (where elevation isn't needed)
    return new Promise((resolve, reject) => {
      if (this.platform === 'windows') {
        // Using @vscode/sudo-prompt for UAC elevation
        const sudo = require('@vscode/sudo-prompt');
        sudo.exec(command, { name: 'Zorivest' }, (err: Error | null) => {
          if (err) reject(err);
          else resolve();
        });
      } else {
        try {
          execSync(command);
          resolve();
        } catch (err) {
          reject(err);
        }
      }
    });
  }
}
```

### IPC Bridge (Main ↔ Renderer)

```typescript
// ui/src/main/service/ipc.ts

import { ipcMain } from 'electron';
import { ServiceManager } from './ServiceManager';

const manager = new ServiceManager();

export function registerServiceIPC(): void {
  ipcMain.handle('service:status', () => manager.getStatus());
  ipcMain.handle('service:start', () => manager.start());
  ipcMain.handle('service:stop', () => manager.stop());
  ipcMain.handle('service:restart', () => manager.restart());
  ipcMain.handle('service:setAutoStart', (_event, enabled: boolean) =>
    manager.setAutoStart(enabled)
  );
  ipcMain.handle('service:openLogFolder', () => manager.openLogFolder());
  ipcMain.handle('service:isInstalled', () => manager.isInstalled());
}
```

Register in Electron main entry:

```typescript
// ui/src/main/index.ts (addition)
import { registerServiceIPC } from './service/ipc';

app.whenReady().then(() => {
  registerServiceIPC();
  // ... existing window creation
});
```

---

## 10.3: REST API Extensions

### Health Endpoint Enhancement

The existing `GET /health` endpoint ([Phase 4](04-rest-api.md)) is extended with service-relevant fields:

```python
# packages/api/src/zorivest_api/routes/health.py (extension)

@router.get("/health")
async def health_check() -> dict:
    """Health check for service monitoring.

    Already returns: {"status": "ok", "version": "1.0.0"}
    Extended with:
    """
    uptime = time.time() - APP_START_TIME
    scheduler_status = scheduler_service.get_status()

    return {
        "status": "ok",
        "version": __version__,
        "uptime_seconds": int(uptime),
        "scheduler": {
            "active_policies": scheduler_status.active_count,
            "next_run": scheduler_status.next_run_iso,
        },
        "database": {
            "unlocked": db_manager.is_unlocked,
        },
    }
```

### Graceful Restart Endpoint

```python
# packages/api/src/zorivest_api/routes/service.py

from fastapi import APIRouter, BackgroundTasks
import signal
import os

router = APIRouter(prefix="/api/v1/service", tags=["service"])


@router.get("/status")
async def service_status(
    _user = Depends(get_current_user),  # Auth required
) -> dict:
    """Service self-status for GUI polling.

    Returns process-level info (PID, uptime, memory).
    OS-level service state is queried by the Electron
    ServiceManager class directly.
    """
    import psutil
    proc = psutil.Process(os.getpid())

    return {
        "pid": os.getpid(),
        "uptime_seconds": int(time.time() - APP_START_TIME),
        "memory_mb": round(proc.memory_info().rss / 1024 / 1024, 1),
        "cpu_percent": proc.cpu_percent(interval=0.1),
        "python_version": platform.python_version(),
    }


@router.post("/graceful-shutdown")
async def graceful_shutdown(
    background_tasks: BackgroundTasks,
    _user = Depends(get_current_user),  # Auth required
) -> dict:
    """Request graceful shutdown. The OS service wrapper will restart the process.

    This is the backend's self-shutdown — the OS service wrapper (WinSW/launchd/systemd)
    handles the restart. Used by the GUI "Restart" button flow:
    1. GUI calls POST /service/graceful-shutdown
    2. Backend shuts down gracefully (flush logs, close DB)
    3. OS service wrapper detects exit and restarts the process
    4. GUI polls GET /health until backend is back
    """
    def _shutdown():
        import time
        time.sleep(0.5)  # Allow response to be sent
        os.kill(os.getpid(), signal.SIGINT)

    background_tasks.add_task(_shutdown)
    return {"status": "shutting_down", "message": "Service will restart via OS service wrapper"}
```

### REST Endpoint Summary

| Method | Endpoint | Purpose | Auth Required | Elevation |
|---|---|---|---|---|
| `GET` | `/api/v1/health` | Health check (existing, extended) | No | No |
| `GET` | `/api/v1/service/status` | Process-level self-status | Yes | No |
| `POST` | `/api/v1/service/graceful-shutdown` | Trigger graceful restart | Yes | No |

---

## 10.4: MCP Tools for Service Control

> **Primary spec location:** [05b-mcp-zorivest-diagnostics.md](05b-mcp-zorivest-diagnostics.md). The code below is retained as implementation reference — the category file is authoritative for tool contracts.
>
> Extends [Phase 5 MCP Server](05-mcp-server.md) with service lifecycle tools.

### Tool Registration

```typescript
// mcp-server/src/tools/service.ts

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';

const API = process.env.ZORIVEST_API_URL ?? 'http://localhost:8765/api/v1';

export function registerServiceTools(server: McpServer): void {

  // ── zorivest_service_status ─────────────────────────────
  server.tool(
    'zorivest_service_status',
    'Get the current status of the Zorivest backend service, including PID, uptime, memory, CPU, and scheduler state.',
    {},
    async () => {
      try {
        const [health, status] = await Promise.all([
          fetch(`${API}/health`).then(r => r.json()),
          fetch(`${API}/service/status`, {
            headers: { 'Authorization': `Bearer ${getToken()}` },
          }).then(r => r.json()),
        ]);

        return {
          content: [{
            type: 'text' as const,
            text: JSON.stringify({
              backend: 'running',
              pid: status.pid,
              uptime_seconds: status.uptime_seconds,
              memory_mb: status.memory_mb,
              cpu_percent: status.cpu_percent,
              version: health.version,
              scheduler: health.scheduler,
              database: health.database,
            }, null, 2),
          }],
        };
      } catch (err) {
        return {
          content: [{
            type: 'text' as const,
            text: JSON.stringify({
              backend: 'unreachable',
              error: (err as Error).message,
              hint: 'The backend service may not be running. Check OS service status or start it from the Zorivest GUI Settings > Service Manager.',
            }, null, 2),
          }],
          isError: true,
        };
      }
    }
  );

  // ── zorivest_service_restart ────────────────────────────
  server.tool(
    'zorivest_service_restart',
    'Restart the Zorivest backend service. Triggers a graceful shutdown; the OS service wrapper handles the restart. Returns when the service is back online.',
    {},
    async () => {
      try {
        // Trigger graceful shutdown
        await fetch(`${API}/service/graceful-shutdown`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${getToken()}` },
        });

        // Poll for restart (max 30 seconds)
        const start = Date.now();
        while (Date.now() - start < 30_000) {
          await new Promise(r => setTimeout(r, 2000));
          try {
            const health = await fetch(`${API}/health`).then(r => r.json());
            if (health.status === 'ok') {
              return {
                content: [{
                  type: 'text' as const,
                  text: JSON.stringify({
                    status: 'restarted',
                    version: health.version,
                    uptime_seconds: health.uptime_seconds,
                  }, null, 2),
                }],
              };
            }
          } catch { /* still restarting */ }
        }

        return {
          content: [{
            type: 'text' as const,
            text: 'Service restart timed out after 30 seconds. Check the Zorivest GUI or OS service manager.',
          }],
          isError: true,
        };
      } catch (err) {
        return {
          content: [{
            type: 'text' as const,
            text: `Restart failed: ${(err as Error).message}`,
          }],
          isError: true,
        };
      }
    }
  );

  // ── zorivest_service_logs ──────────────────────────────
  server.tool(
    'zorivest_service_logs',
    'Get the path to the Zorivest log directory. Returns the absolute path where JSONL log files are stored, per the Phase 1A logging infrastructure.',
    {},
    async () => {
      // Resolve log directory (same logic as Phase 1A get_log_directory)
      let logDir: string;
      if (process.platform === 'win32') {
        logDir = `${process.env.LOCALAPPDATA || ''}\\zorivest\\logs`;
      } else if (process.platform === 'darwin') {
        logDir = `${process.env.HOME}/Library/Application Support/zorivest/logs`;
      } else {
        const xdg = process.env.XDG_DATA_HOME || `${process.env.HOME}/.local/share`;
        logDir = `${xdg}/zorivest/logs`;
      }

      // List available log files
      const fs = await import('fs/promises');
      let files: string[] = [];
      try {
        files = (await fs.readdir(logDir))
          .filter(f => f.endsWith('.jsonl'))
          .sort();
      } catch { /* directory may not exist yet */ }

      return {
        content: [{
          type: 'text' as const,
          text: JSON.stringify({
            log_directory: logDir,
            log_files: files,
            hint: 'Log files are in JSONL format (one JSON object per line). Use jq or grep to filter. Feature log files: trades.jsonl, marketdata.jsonl, scheduler.jsonl, etc.',
          }, null, 2),
        }],
      };
    }
  );
}
```

### MCP Tool Summary

| Tool | Description | Requires Auth | Backend Must Be Running |
|---|---|---|---|
| `zorivest_service_status` | PID, uptime, memory, CPU, scheduler, DB status | Yes (for `/service/status`) | Yes (shows "unreachable" if down) |
| `zorivest_service_restart` | Graceful restart via OS wrapper; polls until back | Yes | Yes |
| `zorivest_service_logs` | Returns log directory path + file listing | No | No (reads filesystem) |

---

## 10.5: GUI Service Manager Panel

> Part of **Settings** sidebar ([06f-gui-settings.md](06f-gui-settings.md)). Added as **§6f.10: Service Manager**.

### Wireframe

```
┌──────────────────────────────────────────────────────────┐
│  Settings > Service Manager                               │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─ Status ─────────────────────────────────────┐        │
│  │ 🟢 Backend Service: Running                  │        │
│  │    PID: 12847     Port: 8765                  │        │
│  │    Uptime: 4h 23m                             │        │
│  │    Memory: 84 MB  CPU: 2.3%                   │        │
│  │                                               │        │
│  │ Scheduler: 3 active policies                  │        │
│  │ Database: 🟢 Unlocked                         │        │
│  └───────────────────────────────────────────────┘        │
│                                                          │
│  ── Controls ───────────────────────────────────          │
│                                                          │
│  ┌──────────┐ ┌───────────┐ ┌──────────┐                │
│  │ ⏹ Stop   │ │ 🔄 Restart│ │ ▶️ Start  │                │
│  └──────────┘ └───────────┘ └──────────┘                │
│                                                          │
│  Auto-start on boot: [✅ Enabled]                        │
│                                                          │
│  ── Logs ───────────────────────────────────────          │
│                                                          │
│  Log files location:                                     │
│  📁 C:\Users\Mat\AppData\Local\zorivest\logs             │
│  [📂 Open Log Folder]                                    │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**When service is stopped:**

```
│  ┌─ Status ─────────────────────────────────────┐        │
│  │ 🔴 Backend Service: Stopped                  │        │
│  │                                               │        │
│  │    The backend service is not running.         │        │
│  │    Scheduled jobs will not execute until       │        │
│  │    the service is started.                     │        │
│  └───────────────────────────────────────────────┘        │
```

### React Component

```tsx
// ui/src/renderer/pages/settings/ServiceManagerPage.tsx

import { useState, useEffect } from 'react';

interface ServiceStatus {
  state: 'running' | 'stopped' | 'unknown' | 'error';
  pid: number | null;
  uptime_seconds: number | null;
  auto_start: boolean;
  error_message: string | null;
}

interface BackendHealth {
  pid: number;
  uptime_seconds: number;
  memory_mb: number;
  cpu_percent: number;
  scheduler: { active_policies: number; next_run: string | null };
  database: { unlocked: boolean };
}

function formatUptime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

export function ServiceManagerPage() {
  const [status, setStatus] = useState<ServiceStatus | null>(null);
  const [health, setHealth] = useState<BackendHealth | null>(null);
  const [loading, setLoading] = useState(false);
  const [logDir, setLogDir] = useState('');

  // Poll service status every 5 seconds
  useEffect(() => {
    const poll = async () => {
      const s = await window.electronAPI.invoke('service:status');
      setStatus(s);

      // If running, also fetch backend health
      if (s.state === 'running') {
        try {
          const [h, s] = await Promise.all([
            fetch(`${API}/health`).then(r => r.json()),
            fetch(`${API}/service/status`, {
              headers: { 'Authorization': `Bearer ${getToken()}` },
            }).then(r => r.json()),
          ]);
          setHealth({ ...s, scheduler: h.scheduler, database: h.database });
        } catch { setHealth(null); }
      } else {
        setHealth(null);
      }
    };

    poll();
    const interval = setInterval(poll, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleAction = async (action: 'start' | 'stop' | 'restart') => {
    setLoading(true);
    try {
      await window.electronAPI.invoke(`service:${action}`);
      // Re-poll after action
      setTimeout(async () => {
        const s = await window.electronAPI.invoke('service:status');
        setStatus(s);
        setLoading(false);
      }, 2000);
    } catch (err) {
      setLoading(false);
    }
  };

  const handleAutoStartToggle = async () => {
    if (!status) return;
    await window.electronAPI.invoke('service:setAutoStart', !status.auto_start);
    const s = await window.electronAPI.invoke('service:status');
    setStatus(s);
  };

  const handleOpenLogFolder = () => {
    window.electronAPI.invoke('service:openLogFolder');
  };

  const isRunning = status?.state === 'running';

  return (
    <div className="service-manager-settings">
      <h2>Service Manager</h2>

      {/* Status card */}
      <div className={`status-card ${isRunning ? 'active' : 'inactive'}`}>
        <span className="status-indicator">
          {isRunning ? '🟢' : '🔴'}
          {' '}Backend Service: {isRunning ? 'Running' : 'Stopped'}
        </span>

        {isRunning && health && (
          <div className="status-details">
            <p>PID: {health.pid} &nbsp; Port: 8765</p>
            <p>Uptime: {formatUptime(health.uptime_seconds)}</p>
            <p>Memory: {health.memory_mb} MB &nbsp; CPU: {health.cpu_percent}%</p>
            <p>Scheduler: {health.scheduler.active_policies} active policies</p>
            <p>Database: {health.database.unlocked ? '🟢 Unlocked' : '🔴 Locked'}</p>
          </div>
        )}

        {!isRunning && (
          <p className="stopped-message">
            The backend service is not running. Scheduled jobs will not execute
            until the service is started.
          </p>
        )}
      </div>

      {/* Controls */}
      <fieldset disabled={loading}>
        <legend>Controls</legend>
        <div className="button-group">
          <button
            onClick={() => handleAction('stop')}
            disabled={!isRunning}
            className="btn-secondary"
          >
            ⏹ Stop
          </button>
          <button
            onClick={() => handleAction('restart')}
            disabled={!isRunning}
            className="btn-primary"
          >
            🔄 Restart
          </button>
          <button
            onClick={() => handleAction('start')}
            disabled={isRunning}
            className="btn-primary"
          >
            ▶️ Start
          </button>
        </div>

        <label className="toggle">
          <input
            type="checkbox"
            checked={status?.auto_start ?? false}
            onChange={handleAutoStartToggle}
          />
          Auto-start on boot
        </label>
      </fieldset>

      {/* Log folder access */}
      <fieldset>
        <legend>Logs</legend>
        <p className="log-path">
          Log files location:<br/>
          <code>{logDir || 'Loading...'}</code>
        </p>
        <button onClick={handleOpenLogFolder} className="btn-secondary">
          📂 Open Log Folder
        </button>
      </fieldset>
    </div>
  );
}
```

### REST Endpoints Consumed (by GUI)

| Data | Source | Polling |
|---|---|---|
| Service OS state | Electron IPC `service:status` | 5s interval |
| Process health (PID, memory, CPU) | `GET /api/v1/service/status` | 5s (if running) |
| Scheduler state | `GET /api/v1/health` | 5s (if running) |
| Start/stop/restart | Electron IPC `service:start/stop/restart` | On-demand |
| Auto-start toggle | Electron IPC `service:setAutoStart` | On-demand |
| Open log folder | Electron IPC `service:openLogFolder` | On-demand |

---

## 10.6: Installer Integration

### 10.6a: Windows — NSIS Postinstall Script

> electron-builder NSIS supports custom `.nsh` scripts via the `include` directive.

```nsh
; build/installer.nsh — Custom NSIS postinstall/uninstall hooks

!macro customInstall
  ; Copy WinSW binary and service config to install dir
  ; (already included via electron-builder extraResources)

  ; Resolve backend path and update service XML
  SetOutPath "$INSTDIR\resources\service"

  ; Install the Windows Service
  nsExec::ExecToLog '"$INSTDIR\resources\service\zorivest-service.exe" install'
  Pop $0
  ${If} $0 == "0"
    ; Start the service immediately
    nsExec::ExecToLog 'net start zorivest-backend'
  ${EndIf}
!macroend

!macro customUnInstall
  ; Stop and uninstall the service
  nsExec::ExecToLog 'net stop zorivest-backend'
  nsExec::ExecToLog '"$INSTDIR\resources\service\zorivest-service.exe" uninstall'
!macroend
```

**electron-builder config addition:**

```javascript
// electron-builder.config.js (additions)
module.exports = {
  // ... existing config
  extraResources: [
    { from: 'dist-python/zorivest-api${ext}', to: 'backend/' },
    { from: 'resources/service/', to: 'service/' },  // WinSW + XML
  ],
  nsis: {
    // ... existing NSIS config
    include: 'build/installer.nsh',
  },
};
```

### 10.6b: macOS — First-Launch Setup

The Electron main process generates and loads the LaunchAgent plist on first launch:

```typescript
// ui/src/main/service/firstLaunchSetup.ts

import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';
import { app } from 'electron';

const PLIST_LABEL = 'com.zorivest.backend';
const LAUNCH_AGENTS_DIR = path.join(app.getPath('home'), 'Library', 'LaunchAgents');
const PLIST_PATH = path.join(LAUNCH_AGENTS_DIR, `${PLIST_LABEL}.plist`);

export function setupMacService(): void {
  if (fs.existsSync(PLIST_PATH)) return; // Already installed

  const backendPath = path.join(
    process.resourcesPath, 'backend', 'zorivest-api'
  );
  const logDir = path.join(
    app.getPath('home'), 'Library', 'Application Support', 'zorivest', 'logs'
  );

  // Ensure directories exist
  fs.mkdirSync(logDir, { recursive: true });
  fs.mkdirSync(LAUNCH_AGENTS_DIR, { recursive: true });

  const plistContent = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${PLIST_LABEL}</string>
  <key>Program</key>
  <string>${backendPath}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${backendPath}</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>ThrottleInterval</key>
  <integer>10</integer>
  <key>StandardOutPath</key>
  <string>${logDir}/service-stdout.log</string>
  <key>StandardErrorPath</key>
  <string>${logDir}/service-stderr.log</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>ZORIVEST_ENV</key>
    <string>production</string>
  </dict>
</dict>
</plist>`;

  fs.writeFileSync(PLIST_PATH, plistContent);
  execSync(`launchctl load ${PLIST_PATH}`);
}
```

### 10.6c: Linux — First-Launch Setup

```typescript
// ui/src/main/service/firstLaunchSetup.ts (continued)

export function setupLinuxService(): void {
  const unitDir = path.join(app.getPath('home'), '.config', 'systemd', 'user');
  const unitPath = path.join(unitDir, 'zorivest-backend.service');
  if (fs.existsSync(unitPath)) return; // Already installed

  const backendPath = path.join(
    process.resourcesPath, 'backend', 'zorivest-api'
  );

  fs.mkdirSync(unitDir, { recursive: true });

  const unitContent = `[Unit]
Description=Zorivest Backend — REST API, Scheduler, and Database Engine
After=network.target

[Service]
Type=simple
ExecStart=${backendPath}
Restart=always
RestartSec=5
Environment=ZORIVEST_ENV=production
TimeoutStopSec=15
KillSignal=SIGINT
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
`;

  fs.writeFileSync(unitPath, unitContent);
  execSync('systemctl --user daemon-reload');
  execSync('systemctl --user enable --now zorivest-backend');
}
```

### 10.6d: Uninstall Cleanup

> [!NOTE]
> **Best-effort only.** The `will-quit` handler runs during Electron's quit lifecycle, which may not fire during OS-level uninstall. Platform-specific uninstall hooks provide the reliable cleanup path.
>
> | Platform | Reliable Cleanup Path |
> |---|---|
> | **Windows** | NSIS `customUnInstall` macro (see §10.6a) |
> | **macOS** | `preremove` script in `.pkg` installer (future) |
> | **Linux** | `postrm` script in `.deb`/`.rpm` package (future) |

On macOS/Linux, register best-effort cleanup in Electron's `will-quit` handler:

```typescript
// ui/src/main/index.ts (addition)

app.on('will-quit', () => {
  // Best-effort cleanup — may not fire during OS uninstall
  if (process.env.ZORIVEST_UNINSTALLING === 'true') {
    const manager = new ServiceManager();
    manager.stop().catch(() => {});
    // Service config files are removed by the platform uninstaller
  }
});
```

---

## 10.7: Logging Integration

> Cross-reference: [Phase 1A Logging Infrastructure](01a-logging.md)

### Log Directory

The backend writes JSONL log files to the same directory defined in Phase 1A:

| Platform | Path |
|---|---|
| Windows | `%LOCALAPPDATA%\zorivest\logs\` |
| macOS | `~/Library/Application Support/zorivest/logs/` |
| Linux | `~/.local/share/zorivest/logs/` |

### Service-Specific Log Files

In addition to the Phase 1A feature log files (`trades.jsonl`, `scheduler.jsonl`, etc.), the OS service wrapper captures:

| File | Source | Content |
|---|---|---|
| `service-stdout.log` | WinSW / launchd | Raw stdout from the Python process |
| `service-stderr.log` | WinSW / launchd | Raw stderr from the Python process |
| Systemd journal | `journalctl --user -u zorivest-backend` | Linux: stdout/stderr via journald |

### GUI Log Access

The GUI does **not** display log contents inline. Instead, the **"📂 Open Log Folder"** button calls `shell.openPath()` to open the log directory in the native file manager (Explorer / Finder / Files).

```typescript
// Electron shell.openPath — cross-platform folder opening
import { shell } from 'electron';
await shell.openPath(logDir);
// Opens in: Explorer (Windows) / Finder (macOS) / Files (Linux)
```

---

## 10.8: Test Plan

### Unit Tests (TypeScript — Vitest)

```typescript
// ui/src/__tests__/ServiceManager.test.ts

import { describe, it, expect, vi } from 'vitest';

describe('ServiceManager', () => {
  describe('getStatus', () => {
    it('returns running status on Windows when sc query shows RUNNING', async () => {
      vi.spyOn(cp, 'execSync').mockReturnValueOnce(
        '        STATE              : 4  RUNNING'
      );
      const manager = new ServiceManager();
      const status = await manager.getStatus();
      expect(status.state).toBe('running');
    });

    it('returns stopped status on macOS when launchctl list fails', async () => {
      vi.spyOn(cp, 'execSync').mockImplementation(() => {
        throw new Error('Could not find service');
      });
      const manager = new ServiceManager();
      const status = await manager.getStatus();
      expect(status.state).toBe('stopped');
    });

    it('returns active status on Linux from systemctl is-active', async () => {
      vi.spyOn(cp, 'execSync').mockReturnValueOnce('active\n');
      const manager = new ServiceManager();
      const status = await manager.getStatus();
      expect(status.state).toBe('running');
    });
  });

  describe('start/stop', () => {
    it('calls net start on Windows with elevation', async () => {
      const sudoExec = vi.fn((_cmd, _opts, cb) => cb(null));
      vi.spyOn(require('@vscode/sudo-prompt'), 'exec').mockImplementation(sudoExec);
      const manager = new ServiceManager();
      await manager.start();
      expect(sudoExec).toHaveBeenCalledWith(
        expect.stringContaining('net start'),
        expect.any(Object),
        expect.any(Function)
      );
    });

    it('calls launchctl load on macOS without elevation', async () => {
      const execSyncSpy = vi.spyOn(cp, 'execSync');
      const manager = new ServiceManager();
      await manager.start();
      expect(execSyncSpy).toHaveBeenCalledWith(
        expect.stringContaining('launchctl load')
      );
    });

    it('calls systemctl --user start on Linux without elevation', async () => {
      const execSyncSpy = vi.spyOn(cp, 'execSync');
      const manager = new ServiceManager();
      await manager.start();
      expect(execSyncSpy).toHaveBeenCalledWith(
        expect.stringContaining('systemctl --user start')
      );
    });
  });
});
```

### Integration Tests (Python — pytest)

```python
# tests/integration/test_service_endpoints.py

import pytest
from httpx import AsyncClient

class TestServiceEndpoints:
    async def test_health_extended(self, client: AsyncClient):
        """GET /health returns extended service fields."""
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "uptime_seconds" in data
        assert "scheduler" in data
        assert "database" in data

    async def test_service_status(self, authed_client: AsyncClient):
        """GET /service/status returns process metrics."""
        resp = await authed_client.get("/api/v1/service/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "pid" in data
        assert "memory_mb" in data
        assert data["pid"] > 0

    async def test_graceful_shutdown_returns_200(self, authed_client: AsyncClient):
        """POST /service/graceful-shutdown returns 200."""
        # Note: In test mode, don't actually shut down
        resp = await authed_client.post("/api/v1/service/graceful-shutdown")
        assert resp.status_code == 200
        assert resp.json()["status"] == "shutting_down"
```

### MCP Tool Tests (TypeScript — Vitest)

```typescript
// mcp-server/src/__tests__/service-tools.test.ts

import { describe, it, expect, vi } from 'vitest';

describe('zorivest_service_status', () => {
  it('returns running status when backend is reachable', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ status: 'ok', version: '1.0.0', scheduler: {}, database: {} }))
    ).mockResolvedValueOnce(
      new Response(JSON.stringify({ pid: 1234, uptime_seconds: 3600, memory_mb: 84 }))
    );

    const result = await callTool('zorivest_service_status', {});
    const data = JSON.parse(result.content[0].text);
    expect(data.backend).toBe('running');
    expect(data.pid).toBe(1234);
  });

  it('returns unreachable when backend is down', async () => {
    vi.spyOn(global, 'fetch').mockRejectedValue(new Error('ECONNREFUSED'));

    const result = await callTool('zorivest_service_status', {});
    const data = JSON.parse(result.content[0].text);
    expect(data.backend).toBe('unreachable');
    expect(result.isError).toBe(true);
  });
});
```

### Manual Test Matrix

| # | Test Case | Windows | macOS | Linux |
|---|---|---|---|---|
| 1 | Install: service registers during app install | NSIS postinstall | First-launch plist | First-launch systemd unit |
| 2 | Auto-start: service starts on boot/login | `services.msc` → Auto | Login Items | `systemctl --user is-enabled` |
| 3 | GUI Start: click Start button → service starts | UAC prompt → service running | No prompt | No prompt |
| 4 | GUI Stop: click Stop button → service stops | UAC prompt → service stopped | Direct | Direct |
| 5 | GUI Restart: click Restart → service bounces | UAC prompt → restart | Direct | Direct |
| 6 | Status polling: GUI shows running/stopped correctly | `sc query` | `launchctl list` | `systemctl is-active` |
| 7 | Auto-start toggle: enable/disable persists | `sc config` | plist RunAtLoad | `systemctl enable/disable` |
| 8 | Open Log Folder: button opens correct directory | Explorer | Finder | Files |
| 9 | MCP status: `zorivest_service_status` returns data | ✓ | ✓ | ✓ |
| 10 | MCP restart: `zorivest_service_restart` bounces service | ✓ | ✓ | ✓ |
| 11 | MCP logs: `zorivest_service_logs` returns file list | ✓ | ✓ | ✓ |
| 12 | Crash recovery: kill backend → service auto-restarts | WinSW `onfailure` | launchd `KeepAlive` | systemd `Restart=always` |
| 13 | Uninstall: service removed cleanly | NSIS uninstall macro | `will-quit` handler | `will-quit` handler |

---

## Exit Criteria

- Backend runs as native OS service on all three platforms (Windows, macOS, Linux)
- Service installs automatically during app installation (Windows) or first launch (macOS, Linux)
- Service auto-starts on login (macOS/Linux) or boot (Windows) and auto-restarts on crash
- GUI Service Manager panel shows live status with 5-second polling
- GUI Start/Stop/Restart buttons work (with UAC prompt on Windows)
- GUI auto-start toggle persists across reboots
- GUI "Open Log Folder" button opens correct platform-specific directory
- MCP `zorivest_service_status` returns health data or "unreachable" error
- MCP `zorivest_service_restart` triggers graceful restart and polls until back
- MCP `zorivest_service_logs` returns log directory path and file listing
- `GET /health` returns extended fields (uptime, scheduler, database)
- `GET /service/status` returns process metrics (PID, memory, CPU)
- `POST /service/graceful-shutdown` triggers clean restart via OS wrapper
- Uninstall cleans up service configuration files

## Outputs

- **Service configs**: `zorivest-service.xml` (WinSW), `com.zorivest.backend.plist` (launchd), `zorivest-backend.service` (systemd)
- **TypeScript**: `ServiceManager` class, IPC bridge, first-launch setup scripts
- **Python**: `GET /service/status`, `POST /service/graceful-shutdown` REST endpoints
- **MCP tools**: `zorivest_service_status`, `zorivest_service_restart`, `zorivest_service_logs`
- **React component**: `ServiceManagerPage` (Settings > Service Manager)
- **NSIS script**: `build/installer.nsh` with service install/uninstall macros
- **Dependencies**: `@vscode/sudo-prompt` (Windows UAC), `psutil` (Python process metrics)
- Service endpoints consume: `GET /health`, `GET /version`, `GET /service/status`, `POST /service/graceful-shutdown`
