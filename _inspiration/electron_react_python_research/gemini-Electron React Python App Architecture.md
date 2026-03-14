# **Architectural Blueprint for Zorivest: Electron, React, and Python Integration**

The development of Zorivest, a specialized trading portfolio management desktop application, demands an architectural design that rigorously balances local execution security, high-throughput rendering performance, and seamless inter-process orchestration. The application relies on a sophisticated tech stack: a Python backend operating via FastAPI to manage domain entities and a SQLCipher encrypted database, paired with a modern React frontend rendered within an Electron shell. The frontend is tasked with displaying dense financial data grids using TanStack Table, asynchronous state synchronization via TanStack Query, and real-time visualization via Lightweight Charts.

Constructing this hybrid architecture necessitates distinct strategies for build pipeline integration, security isolation, component library rendering in a Chromium context, and lifecycle management of the Python sidecar. This comprehensive blueprint analyzes the available patterns, extracts industry-standard practices, and formulates an optimal architectural pathway for the Zorivest application.

## **1\. Electron and Vite Integration Analysis**

The build pipeline is the critical infrastructure that bridges the Node.js environment (Electron's main process) and the Chromium browser environment (the renderer process). Historically, Webpack dominated this space, but Vite has emerged as the superior choice due to its esbuild-powered native ECMAScript Module (ESM) resolution and significantly faster Hot Module Replacement (HMR) capabilities. However, integrating Vite into Electron's multi-process paradigm introduces complexity, as distinct Vite configurations must be orchestrated for the main process, preload scripts, and renderer.

The evaluation of three dominant Vite-based Electron build systems reveals distinct philosophical approaches to managing this dual-context environment.

### **Approach A: electron-vite (by alex8088)**

electron-vite acts as a dedicated, fully-fledged build system that wraps Vite specifically for the nuances of Electron development.1 It abstracts away the complexity of managing parallel Vite instances.

* **Maintenance Status:** This project is highly active and serves as the foundation for modern Electron development. It boasts frequent commits, prompt resolution of issues related to newer Vite versions, and a robust community backing.1 Open issues generally relate to edge cases in V8 bytecode compilation rather than core framework instability.3  
* **Project Directory Structure:** It enforces a highly opinionated, security-first directory structure out of the box. Source code is cleanly bifurcated into src/main, src/preload, and src/renderer directories.5 This physical separation prevents developers from accidentally importing Node.js native modules (like fs or crypto) into the React frontend, which would break the build under strict context isolation.  
* **Process Handling and HMR:** HMR is handled with exceptional efficiency. For the renderer, it utilizes standard Vite HMR injected via an environment variable (ELECTRON\_RENDERER\_URL).6 Crucially, for the main and preload scripts, it implements a Rollup watcher. When a modification is detected in src/main, it triggers a graceful hot restart of the entire Electron application. When src/preload is modified, it triggers a page reload in the renderer.6  
* **TypeScript Configuration:** TypeScript is supported natively. It automatically manages the dual tsconfig.json requirements—one targeting Node.js environments for the main/preload scripts, and another targeting DOM environments for the renderer.1  
* **Electron Builder Integration:** The integration is native and seamless. The tool compiles all output into a unified out/ directory, which maps perfectly to the file inclusion arrays utilized by electron-builder.7 Furthermore, it includes specialized plugins to compile source code into V8 bytecode, protecting proprietary trading algorithms from being reverse-engineered via ASAR unpacking.8

### **Approach B: electron-forge (with Vite Plugin)**

Electron Forge is the official, battery-included toolkit maintained by the core Electron team. It aims to handle everything from initialization to distribution.

* **Maintenance Status:** While Electron Forge itself is the industry standard, its specific Vite plugin is currently flagged as "experimental" as of version 7.5.0.9 The documentation explicitly warns that future minor releases may contain breaking changes regarding Vite support.9  
* **Project Directory Structure:** Forge is less opinionated about directory layouts but requires manual, meticulous wiring within the forge.config.js file to map entry points for the main and renderer processes to their respective Vite configuration files.9  
* **Process Handling and HMR:** To facilitate HMR, the Vite plugin injects global variables (e.g., MAIN\_WINDOW\_VITE\_DEV\_SERVER\_URL and MAIN\_WINDOW\_VITE\_NAME) into the main process.9 The main process code must include conditional logic to determine whether to use loadURL (for HMR in development) or loadFile (for the static build in production). This pollutes the entry file with build-specific boilerplate.  
* **TypeScript Configuration:** TypeScript is supported via the vite-typescript template, but developers must manually declare the aforementioned dynamic HMR global variables in a global.d.ts file to satisfy the strict TypeScript compiler.11  
* **Electron Builder Integration:** Integrating electron-forge with electron-builder is fundamentally incompatible. Electron Forge operates its own distribution pipeline using "Makers" (e.g., @electron-forge/maker-squirrel) and "Publishers".12 Using Forge means committing entirely to its ecosystem and abandoning electron-builder.

### **Approach C: vite-plugin-electron**

Maintained by core contributors to the Vite ecosystem, this is a lower-level, unopinionated plugin designed to drop into an existing standard Vite web project to grant it Electron capabilities.2

* **Maintenance Status:** The plugin is actively maintained and frequently updated, though it functions more as a micro-library. Because it provides fewer abstractions, a higher maintenance burden falls upon the developer to keep the configuration aligned with upstream Vite changes.2  
* **Project Directory Structure:** It leaves the structure entirely to the developer's discretion. Typically, this results in an electron/ folder placed at the root for main/preload scripts, while the React renderer resides in the standard Vite src/ directory.2  
* **Process Handling and HMR:** It implements hot reloading by hijacking the Vite build completion hooks to execute the electron. command.2 While HMR works standardly for the renderer, reloading the preload script relies on manual IPC message broadcasting (electron-vite\&type=hot-reload) to instruct the main process to refresh the webContents.2  
* **TypeScript Configuration:** TypeScript is fully supported, but the developer must manually configure the module resolution paths and target environments to prevent import pollution between the Node environment and the React DOM.  
* **Electron Builder Integration:** Requires manual configuration within electron-builder.json to ensure that both the dist-electron (main output) and dist (renderer output) folders are correctly targeted for packaging.13

### **1\. Recommendation with Rationale**

**Recommendation: Implement electron-vite (by alex8088) paired with electron-builder.**

*Rationale:* Zorivest is a greenfield desktop application with strict security and architectural requirements, not a legacy web application being retrofitted for the desktop. Therefore, an architecture that treats Electron as a first-class citizen rather than an afterthought is mandatory. electron-vite drastically reduces the cognitive load of managing Vite's behavior across Electron's isolated contexts, allowing developers to focus on financial domain logic rather than build-tool boilerplate.5

The explicit separation of src/main, src/preload, and src/renderer directly enforces the security boundaries necessary for a financial application that communicates with a local Python sidecar.5 Furthermore, its native synergy with electron-builder is critical. Because Zorivest relies on a FastAPI backend compiled via PyInstaller, electron-builder's advanced extraResources configuration is required to bundle the Python binary outside of the strict ASAR archive format. Electron Forge's "Makers" lack the nuanced control over external binary packaging that electron-builder provides.

### **2\. Code Snippets**

The following configuration demonstrates the optimal setup for electron-vite with strict React integration and externalized native dependencies.

TypeScript

// electron.vite.config.ts  
import { defineConfig, externalizeDepsPlugin } from 'electron-vite'  
import react from '@vitejs/plugin-react'  
import { resolve } from 'path'

export default defineConfig({  
  main: {  
    // Automatically externalize Node.js built-ins and dependencies   
    // to prevent Vite from attempting to bundle them into the main process  
    plugins:,  
    build: {  
      rollupOptions: {  
        input: { index: resolve(\_\_dirname, 'src/main/index.ts') }  
      }  
    }  
  },  
  preload: {  
    plugins:,  
    build: {  
      rollupOptions: {  
        input: { index: resolve(\_\_dirname, 'src/preload/index.ts') }  
      }  
    }  
  },  
  renderer: {  
    resolve: {  
      alias: {  
        // Enforce strict path mapping for the React frontend  
        '@renderer': resolve('src/renderer/src')  
      }  
    },  
    plugins: \[react()\]  
  }  
})

### **3\. Risk Assessment**

| Risk Vector | Severity | Mitigation Strategy |
| :---- | :---- | :---- |
| **Vite Dependency Caching Bloat** | High | Vite aggressively caches dependencies in node\_modules/.vite during development. If electron-builder packages the application without strict exclusions, the final executable will be bloated by hundreds of megabytes of unnecessary cache data.14 *Mitigation:* Explicitly add ".vite" and node\_modules/.vite to the build.files exclusion list in electron-builder.json5. |
| **Monorepo Plugin Complexity** | Medium | electron-vite abstracts the underlying Rollup configurations. Attempting to inject custom Rollup plugins meant for the browser into the main process build can cause silent failures. *Mitigation:* Strictly isolate Vite plugins. Ensure UI plugins (like Tailwind or SVGR) are exclusively defined in the renderer object of the configuration. |
| **Dual Context Typing Collisions** | Low | TypeScript may throw errors if DOM types (e.g., window, document) bleed into the main process, or if Node types (fs, child\_process) bleed into the renderer. *Mitigation:* Utilize three strictly separated configurations: tsconfig.node.json, tsconfig.web.json, and a base tsconfig.json that references them via project references. |

### **4\. Version-Locked Dependency List**

JSON

{  
  "devDependencies": {  
    "electron": "30.0.0",  
    "electron-builder": "24.13.3",  
    "electron-vite": "2.3.0",  
    "vite": "5.2.0",  
    "@vitejs/plugin-react": "4.2.1",  
    "typescript": "5.4.5"  
  }  
}

## ---

**2\. Reference Architecture Extraction**

To construct a resilient desktop application handling sensitive trading data and cryptographic keys, it is imperative to extract architectural patterns from industry-leading repositories. The evaluation focused on electron-react-boilerplate (ERB) for directory logistics, Signal-Desktop for uncompromising security models, and community Python-Electron paradigms for IPC integration.

### **Architectural Extractions**

**a) electron-react-boilerplate (ERB)** ERB is a foundational repository that has shaped Electron application structure for years.15

* **Directory Layout:** It enforces a rigid separation of concerns, isolating the main process code into an app/main directory and the React code into app/renderer.17 This structural isolation prevents the accidental bundling of Node.js logic into the frontend payload.  
* **Build Pipeline:** Historically, ERB relies heavily on Webpack and implements a "two-package.json" structure.19 Dependencies intended for the final production application (especially native C++ modules like SQLite) are placed in app/package.json, while build tooling remains at the root. This guarantees that electron-builder packages only the necessary runtime modules.19 While Zorivest will use Vite instead of Webpack, the philosophy of isolating runtime native dependencies remains highly relevant.

**b) Signal Desktop** Signal's Electron implementation is widely regarded as a masterclass in desktop security, meticulously mitigating the inherent vulnerabilities of Chromium wrappers.20

* **Security Patterns:** Signal explicitly enforces nodeIntegration: false, contextIsolation: true, and sandbox: true across all BrowserWindow instances.20 This is paramount. If a cross-site scripting (XSS) vulnerability is discovered in the React renderer (e.g., via malicious trading data injection), context isolation ensures the attacker cannot access the Node.js runtime to execute arbitrary code on the host operating system.21 Furthermore, Signal disables enableRemoteModule and forces all URL navigation to be intercepted by the main process.20  
* **Preload Patterns:** Signal uses a highly optimized preload.wrapper.ts script.22 Rather than compiling the entire preload logic on every launch, it leverages the node:vm module and V8 caching (createCachedData()) to load a pre-compiled preload.bundle.cache file. This dramatically reduces cold boot times.22 APIs are meticulously exposed via contextBridge.exposeInMainWorld, mapping strictly typed IPC channels to the window object without exposing the raw ipcRenderer.23  
* **electron-store Usage:** In applications prioritizing security, storing sensitive data in plain-text configurations (the default behavior of electron-store) is an anti-pattern. While electron-store is excellent for persisting window state (X/Y coordinates, width, height) 24, financial keys or API tokens must be routed through the OS's native keychain. Signal relies on Electron's native safeStorage API to encrypt local databases using DPAPI on Windows and Keychain on macOS.25

**c) Electron \+ Python Applications** Extracted from repositories demonstrating sidecar execution (e.g., fyears/electron-python-example) 26:

* **Spawning Approach:** The prevailing pattern involves dynamic environment detection. In development, the main process spawns the Python interpreter directly against the source code (spawn('python', \['app.py'\])). In production, the Python application is compiled into a standalone executable using PyInstaller, and the main process executes this binary without invoking a shell.26  
* **IPC Patterns:** Communication is achieved by establishing a local TCP server in Python (FastAPI/Uvicorn) and executing REST or ZeroMQ requests from the Electron application.26

### **1\. Recommendation with Rationale**

**Recommendation: Adopt a strict Hybrid Architecture leveraging Signal's zero-trust security model, ERB's structural logic, and a Token-Authenticated Context Bridge.**

*Rationale:* Because Zorivest processes sensitive financial data and relies on a SQLCipher database, security must be impenetrable. The contextIsolation: true and sandbox: true flags are non-negotiable.21 The renderer process must be entirely devoid of Node.js capabilities.21

Furthermore, because Zorivest uses a FastAPI sidecar, an architectural vulnerability exists: **Localhost SSRF (Server-Side Request Forgery)**. If the FastAPI server binds openly to localhost:8765, any other application or malicious script running on the user's machine could theoretically send REST requests to the database. Therefore, the architecture must implement a zero-trust local network. The Electron main process must generate a cryptographically secure, ephemeral Bearer token upon boot. This token is passed to the FastAPI sidecar via command-line arguments upon spawn, and simultaneously exposed to the React renderer via the contextBridge. Every REST request originating from React (via TanStack Query) must include this Bearer token, which FastAPI will validate, ensuring only the authenticated Electron frontend can query the trading data.

### **2\. Code Snippets**

**BrowserWindow Security Configuration (Signal Pattern)**

TypeScript

// src/main/index.ts  
import { app, BrowserWindow, safeStorage } from 'electron'  
import { join } from 'path'  
import crypto from 'crypto'

// Generate an ephemeral runtime secret for the Python REST API  
// This prevents rogue local processes from accessing the FastAPI endpoints  
const API\_SECRET \= crypto.randomBytes(32).toString('hex')

function createWindow() {  
  const mainWindow \= new BrowserWindow({  
    width: 1200,  
    height: 800,  
    webPreferences: {  
      nodeIntegration: false,          // Critical: Enforce Signal security pattern  
      contextIsolation: true,          // Critical: Isolate DOM from Node  
      sandbox: true,                   // Critical: Isolate renderer from OS  
      webSecurity: true,               // Enforce strict CORS  
      preload: join(\_\_dirname, '../preload/index.js')  
    }  
  })

  mainWindow.loadFile(join(\_\_dirname, '../renderer/index.html'))  
    
  // Prevent arbitrary navigation to malicious external URLs  
  mainWindow.webContents.on('will-navigate', (event, url) \=\> {  
    if (\!url.startsWith('http://localhost') &&\!url.startsWith('file://')) {  
      event.preventDefault()  
    }  
  })  
}

**Preload Script utilizing Context Bridge**

TypeScript

// src/preload/index.ts  
import { contextBridge, ipcRenderer } from 'electron'

// Expose minimal, strictly typed APIs to the renderer  
// Never expose the generic \`ipcRenderer.send\` or \`invoke\` methods directly  
contextBridge.exposeInMainWorld('zorivestAPI', {  
  // Retrieve the dynamic port and ephemeral secret required for FastAPI requests  
  getBackendConfig: () \=\> ipcRenderer.invoke('get-backend-config'),  
    
  // Non-sensitive window persistence logic (suitable for electron-store)  
  saveWindowState: (state: { x: number, y: number }) \=\>   
    ipcRenderer.send('save-window-state', state)  
})

### **3\. Risk Assessment**

| Risk Vector | Severity | Mitigation Strategy |
| :---- | :---- | :---- |
| **Localhost API Hijacking** | Critical | If the FastAPI backend binds to localhost without authentication, local malware can query the SQLCipher database. *Mitigation:* Implement an ephemeral runtime Bearer token generated by Electron, passed to both FastAPI (via spawn args) and React (via contextBridge). All REST calls must validate this token. |
| **Preload Script Tampering** | High | Even with context isolation, a compromised renderer could attempt prototype pollution on exposed APIs.29 *Mitigation:* Use Object.freeze() on the APIs exposed through contextBridge. Strictly validate all IPC payload structures in the main process.29 |
| **electron-store Secret Leakage** | High | Utilizing electron-store to save API keys or database passwords writes them in plain text JSON to the user's AppData directory.30 *Mitigation:* Restrict electron-store entirely to UI preferences (themes, window sizes). Utilize Electron's native safeStorage API to securely encrypt sensitive database credentials.25 |

### **4\. Version-Locked Dependency List**

JSON

{  
  "dependencies": {  
    "electron-store": "8.2.0"  
  },  
  "devDependencies": {  
    "@types/crypto-js": "4.2.2"  
  }  
}

## ---

**3\. Component Library Compatibility Matrix**

Building a highly dense data-grid application for trading portfolios requires a UI library capable of sustaining immense rendering performance. The architectural alignment between React 19 (which introduces concurrent rendering primitives and deprecates forwardRef 31), TanStack Table v8+ (a headless data grid 32), TanStack Query v5+ (asynchronous state synchronization 33), and the strict Electron renderer context dictates the optimal framework.

Electron rendering performance is highly sensitive to CSS execution. Heavy CSS-in-JS libraries (like traditional Emotion or Styled Components) parse and inject style tags at runtime, which consumes significant Chromium main-thread CPU time, causing frame drops during rapid scrolling of large data sets.34

### **Compatibility Evaluation**

**a) shadcn/ui \+ Tailwind CSS** shadcn/ui represents a modern "copy-paste" architecture rather than a traditional NPM dependency. It is fundamentally built upon Radix UI headless primitives.36

* **React 18 & React 19 Compatibility:** Fully compatible. Radix UI (the foundational layer) has resolved the React 19 element.ref deprecation warnings in their latest release candidates, ensuring seamless execution in React 19 environments.37  
* **TanStack Table v8+ Integration:** Excellent synergy. shadcn/ui explicitly documents integrating its native \<Table /\> components directly with the TanStack headless API, allowing deep customization of virtualized grids.39  
* **TanStack Query v5+ Integration:** Flawless. Because shadcn/ui components are purely presentational, they gracefully accept the updated isPending or isPlaceholderData props generated by Query v5 hooks.33  
* **Electron Context:** Optimal. It utilizes utility-first CSS (Tailwind) which compiles down to a single static CSS file during the Vite build step.41 This incurs zero runtime styling overhead, preserving Chromium CPU cycles for processing incoming WebSocket ticks and rendering Lightweight Charts.34  
* **TypeScript Strict Mode:** Built inherently for TypeScript strict environments.

**b) Radix UI primitives \+ Custom CSS**

While identical to shadcn/ui mechanically, adopting raw Radix UI requires manual authoring of all CSS logic.

* **Compatibility:** Mechanically identical to shadcn/ui across all matrices.  
* **Drawback:** For an expansive application like Zorivest with 30+ REST endpoints and complex data mutations, authoring custom CSS for intricate elements (like date pickers, comboboxes, and multi-selects) introduces massive technical debt and delays time-to-market.

**c) Mantine v7+** Mantine is a robust, heavily featured, enterprise-grade UI library. Version 7 marked a massive architectural shift away from Emotion (CSS-in-JS) to native CSS modules.42

* **React 18 & React 19 Compatibility:** Mantine v7 fully supports React 18.3 and has integrated the necessary changes to prepare for the React 19 release.42  
* **TanStack Table v8+ Integration:** Outstanding. The community-supported mantine-react-table package is a highly mature, heavily optimized implementation of TanStack Table tailored explicitly for Mantine.44 It offers immediate access to virtualization, grouping, and aggregation without manual assembly.45  
* **TanStack Query v5+ Integration:** Fully compatible.  
* **Electron Context:** The migration to CSS modules in v7 eradicated the runtime CSS-in-JS performance bottlenecks, making it highly performant in Chromium renderers.43

**d) MUI v6+**

Material UI is the traditional enterprise standard but carries architectural baggage.

* **React 18 & React 19 Compatibility:** MUI v6 introduced Pigment CSS (a zero-runtime engine) specifically to achieve React Server Component and React 19 compatibility.46 However, migrating an app to fully utilize Pigment CSS is a complex undertaking.  
* **TanStack Table v8+ Integration:** The material-react-table package wraps TanStack Table brilliantly for MUI environments.47  
* **Electron Context:** If legacy Emotion components are used within MUI v6, the runtime CSS injection will cause severe performance bottlenecks in dense electron data grids, leading to CPU throttling.35 The transition to Pigment CSS mitigates this, but setup in a Vite/Electron environment is significantly more complex than Tailwind.

### **1\. Recommendation with Rationale**

**Recommendation: shadcn/ui \+ Tailwind CSS, manually integrated with TanStack Table v8 and TanStack Virtual.**

*Rationale:* While mantine-react-table offers an incredibly powerful out-of-the-box experience, a trading portfolio application like Zorivest requires hyper-specific, highly dense, customized tabular layouts. Financial grids often require inline sparklines (using Lightweight Charts), custom profit/loss heatmaps, and instantaneous DOM updates on price ticks. shadcn/ui's code-ownership model means the developer literally owns the raw DOM markup of the \<Table\> components.36 This allows the injection of Canvas or WebGL elements (like Lightweight Charts) directly into table cells without fighting the deep abstraction layers of a wrapped library like Mantine. Furthermore, the complete absence of CSS-in-JS guarantees maximum frame rates during rapid grid updates. React 19 compatibility is resolved at the Radix level, and TanStack Query seamlessly acts as the data-fetching backbone for the headless table states.33

### **2\. Code Snippets**

**Tailwind Configuration Optimized for Electron Strict CSP**

JavaScript

// tailwind.config.js  
/\*\* @type {import('tailwindcss').Config} \*/  
module.exports \= {  
  darkMode: \["class"\],  
  // Ensure Tailwind only scans the renderer folder to optimize build times  
  // and prevent accidental inclusion of Node.js files  
  content: \[  
    "./src/renderer/index.html",   
    "./src/renderer/src/\*\*/\*.{ts,tsx}"  
  \],  
  theme: {  
    extend: {  
      colors: {  
        background: "hsl(var(--background))",  
        foreground: "hsl(var(--foreground))",  
        // Semantic trading colors  
        bullish: "hsl(142.1 76.2% 36.3%)", // Green  
        bearish: "hsl(346.8 77.2% 49.8%)"  // Red  
      }  
    },  
  },  
  plugins: \[require("tailwindcss-animate")\],  
}

### **3\. Risk Assessment**

| Risk Vector | Severity | Mitigation Strategy |
| :---- | :---- | :---- |
| **Grid Re-render Performance** | High | React 19's concurrent rendering paired with TanStack Table on thousands of rows can trigger massive, blocking DOM reconciliations if memoization is poorly executed. *Mitigation:* Strictly utilize TanStack Virtual (@tanstack/react-virtual) to only render the rows currently visible within the viewport.40 Wrap all row definitions in React.memo. |
| **Component Code Fragmentation** | Medium | shadcn/ui copies code directly into the source tree. Over time, developers modifying these base components inconsistently can lead to fragmented logic and bloated Git histories.36 *Mitigation:* Isolate all shadcn components in a strict src/renderer/src/components/ui directory and enforce a rule against modifying them without a team review. |
| **Strict CSP Violations** | Low | Inline styles generated dynamically by some UI animation libraries can violate strict Content-Security-Policy headers required by Electron. *Mitigation:* Rely on Tailwind's utility classes for state changes and avoid inline style={} bindings in React wherever possible. |

### **4\. Version-Locked Dependency List**

JSON

{  
  "dependencies": {  
    "react": "19.0.0",  
    "react-dom": "19.0.0",  
    "@tanstack/react-table": "8.16.0",  
    "@tanstack/react-query": "5.32.0",  
    "@tanstack/react-virtual": "3.5.0",  
    "clsx": "2.1.1",  
    "tailwind-merge": "2.3.0",  
    "lucide-react": "0.378.0",  
    "sonner": "1.4.4"  
  },  
  "devDependencies": {  
    "tailwindcss": "3.4.3",  
    "postcss": "8.4.38",  
    "autoprefixer": "10.4.19"  
  }  
}

## ---

**4\. Python Backend Spawning Patterns**

Orchestrating a FastAPI Python backend alongside an Electron frontend is the most complex facet of this architecture. It requires mastering operating system process management, dynamic port allocation, cross-platform path resolution, and lifecycle synchronization. Failure to implement this correctly results in "zombie" Python processes, port collisions, and complete execution failure when the app is packaged.

### **Process Management Analysis**

* **Process Spawn Code:** The Node.js child\_process module provides three primary APIs: exec, fork, and spawn. fork is exclusively designed for spawning new Node.js V8 instances, rendering it useless for Python. exec executes commands within an OS shell and buffers the standard output; if the FastAPI application generates substantial logs, this buffer will overflow, crashing the application.48 Furthermore, exec introduces severe shell injection vulnerabilities. Electron 22 introduced utilityProcess, but this utilizes the Chromium Services API specifically for Node scripts, not external binaries.49 Therefore, child\_process.spawn is the strictly correct and most performant API for invoking a Python executable.26  
* **Port Discovery:** Hardcoding a port (e.g., 8765\) is a catastrophic architectural flaw.50 If the user's system has another service occupying port 8765, or if the user attempts to run two instances of Zorivest simultaneously, Uvicorn will fail to bind and the backend will crash. The Electron main process must request an available port directly from the OS kernel (by attempting to bind to port 0), retrieve the assigned port, and pass it to the FastAPI instance as a command-line argument.  
* **Path Resolution (Dev vs Prod):** During development, the Node.js process can simply call the native Python interpreter available on the PATH (e.g., spawn('python', \['app.py'\])). However, for production, the Python backend must be compiled into a standalone executable using PyInstaller to ensure users do not need Python installed.51 When electron-builder packages the app, it places all code inside a read-only app.asar archive. Binaries *cannot* be executed from within an ASAR archive because the OS cannot memory-map files inside a custom container.48 Thus, PyInstaller output must be configured to extract to the resources/ folder, and Electron must dynamically resolve the path using process.resourcesPath.52  
* **Health Checks:** Invoking child\_process.spawn only confirms that the binary has started executing; it does not confirm that the Uvicorn ASGI server has finished initializing the database and is ready to accept connections. The Electron application must actively poll a FastAPI REST endpoint (e.g., GET /health) with an exponential backoff strategy.54 Only upon receiving a 200 OK should the main React BrowserWindow be revealed to the user.  
* **Graceful Shutdown and Crash Handling:** The standard approach of sending a SIGTERM signal (childProcess.kill()) when Electron quits works reliably on macOS and Linux, but frequently fails on Windows environments, leaving the Uvicorn server running as a background "zombie" process occupying the port.26 A deterministic, cross-platform shutdown requires FastAPI to expose a dedicated /shutdown REST endpoint. When the app.on('will-quit') event fires, Electron sends a POST request to this endpoint, allowing Python to gracefully close SQLCipher connections and self-terminate via os.\_exit(0). In the event of a spontaneous Python crash, the childProcess.on('exit') listener must trigger an IPC event to the React frontend, displaying a sonner toast or modal prompting the user to restart the backend.

### **1\. Recommendation with Rationale**

**Recommendation: Implement a dedicated PythonManager singleton in the main process utilizing child\_process.spawn, OS-level dynamic port binding, and REST-based lifecycle coordination.**

*Rationale:* This pattern ensures absolute cross-platform reliability. By dynamically allocating the port via Node's net.createServer and passing it to Python, port collisions are mathematically eliminated.50 By executing a PyInstaller binary explicitly mapped to process.resourcesPath, the application seamlessly survives electron-builder ASAR constraints.48 Utilizing a dedicated /shutdown REST endpoint bypasses the inherent flaws of Windows process signal handling, guaranteeing that no orphan Uvicorn servers drain the user's system resources after Zorivest closes.56

### **2\. Code Snippets**

**Main Process: Python Lifecycle Manager**

TypeScript

// src/main/pythonManager.ts  
import { spawn, ChildProcess } from 'child\_process'  
import { join } from 'path'  
import { app } from 'electron'  
import net from 'net'  
import axios from 'axios'

export class PythonManager {  
  private childProcess: ChildProcess | null \= null  
  public port: number \= 0

  // Interrogate the OS kernel for an available TCP port  
  private async getFreePort(): Promise\<number\> {  
    return new Promise((resolve, reject) \=\> {  
      const server \= net.createServer()  
      server.listen(0, '127.0.0.1', () \=\> {  
        const port \= (server.address() as net.AddressInfo).port  
        server.close(() \=\> resolve(port))  
      })  
      server.on('error', reject)  
    })  
  }

  public async start(apiSecret: string): Promise\<{ port: number }\> {  
    this.port \= await this.getFreePort()  
      
    // Resolve path based on Dev vs Packaged environment  
    const isDev \=\!app.isPackaged  
    const scriptPath \= isDev   
     ? join(\_\_dirname, '../../backend/app.py')  
      : join(process.resourcesPath, 'backend', 'api.exe') // Output of PyInstaller

    const command \= isDev? 'python' : scriptPath  
    // Pass the port and the ephemeral secret to FastAPI  
    const args \= isDev   
     ?   
      :

    // Use spawn and ignore stdio in production to prevent buffer overflows  
    this.childProcess \= spawn(command, args, { stdio: isDev? 'pipe' : 'ignore' })

    this.childProcess.on('exit', (code) \=\> {  
      if (code\!== 0) {  
        console.error(\`Python backend crashed with code ${code}\`)  
        // Here, dispatch an IPC event to the React frontend to trigger a Sonner toast  
      }  
    })

    // Block Electron window creation until FastAPI acknowledges readiness  
    await this.waitForHealthCheck()  
      
    return { port: this.port }  
  }

  private async waitForHealthCheck(retries \= 20): Promise\<void\> {  
    const url \= \`http://127.0.0.1:${this.port}/health\`  
    for (let i \= 0; i \< retries; i++) {  
      try {  
        const response \= await axios.get(url)  
        if (response.status \=== 200) return  
      } catch (err) {  
        await new Promise(res \=\> setTimeout(res, 500)) // 500ms exponential backoff  
      }  
    }  
    throw new Error('FastAPI backend failed to start within the timeout period.')  
  }

  public async stop(apiSecret: string): Promise\<void\> {  
    if (\!this.childProcess) return

    try {  
      // Deterministic shutdown via REST to avoid Windows SIGTERM failures  
      await axios.post(\`http://127.0.0.1:${this.port}/shutdown\`, null, {  
        headers: { Authorization: \`Bearer ${apiSecret}\` }  
      })  
    } catch (err) {  
      // Fallback to hard kernel kill if the server is unresponsive  
      this.childProcess.kill('SIGKILL')  
    }  
  }  
}

**Python FastAPI: Lifecycle, Health, and Shutdown**

Python

\# backend/app.py  
import os  
import argparse  
import uvicorn  
from fastapi import FastAPI, Depends, HTTPException, status  
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app \= FastAPI()  
security \= HTTPBearer()  
API\_SECRET \= ""

\# Dependency to validate the Electron ephemeral token  
def verify\_token(credentials: HTTPAuthorizationCredentials \= Depends(security)):  
    if credentials.credentials\!= API\_SECRET:  
        raise HTTPException(  
            status\_code=status.HTTP\_403\_FORBIDDEN,  
            detail="Invalid authentication token",  
        )

@app.get("/health")  
def health\_check():  
    \# Unprotected route specifically for the startup ping  
    return {"status": "ok"}

@app.post("/shutdown", dependencies=)  
def shutdown\_server():  
    \# Gracefully close DB connections here, then force exit  
    \# This ensures no zombie processes survive Electron termination  
    os.\_exit(0)

if \_\_name\_\_ \== "\_\_main\_\_":  
    parser \= argparse.ArgumentParser()  
    parser.add\_argument("--port", type\=int, required=True)  
    parser.add\_argument("--secret", type\=str, required=True)  
    args \= parser.parse\_args()  
      
    \# Store the secret globally to validate all incoming React requests  
    API\_SECRET \= args.secret  
      
    uvicorn.run(app, host="127.0.0.1", port=args.port, log\_level="warning")

### **3\. Risk Assessment**

| Risk Vector | Severity | Mitigation Strategy |
| :---- | :---- | :---- |
| **Zombie Processes via Hard Crash** | Critical | If the Electron parent process crashes violently (e.g., Segfault), the app.on('will-quit') hook will not execute, leaving the Python server running indefinitely.26 *Mitigation:* The Python backend must implement a background daemon thread that periodically checks the heartbeat of the parent Node.js Process ID (os.getppid()). If the parent PID ceases to exist, Python should auto-terminate. |
| **ASAR Packaging Failure** | High | If electron-builder inadvertently bundles the compiled Python executable into app.asar, child\_process.spawn will fail with an ENOENT error.48 *Mitigation:* Explicitly configure extraResources in electron-builder.json5 to copy the PyInstaller output folder verbatim to the physical resources directory, bypassing the ASAR completely.53 |
| **Stdio Buffer Overflow** | Medium | If the FastAPI application logs extensively to stdout/stderr and Electron does not continuously consume or pipe these streams, the OS-level pipe buffer will fill up. Once full, it will block the Python process from executing further logic, causing the backend to freeze.57 *Mitigation:* Use child\_process.spawn(..., { stdio: 'ignore' }) in production to silently discard logs, or explicitly attach .on('data') listeners to stream outputs to a rotating log file on disk.58 |

### **4\. Version-Locked Dependency List**

*Note: Python dependencies are managed independently via requirements.txt or pyproject.toml. The Node.js dependencies required for orchestration are locked below.*

JSON

{  
  "dependencies": {  
    "axios": "1.6.8"  
  },  
  "devDependencies": {  
    "electron-builder": "24.13.3"  
  }  
}

*Electron Builder Configuration Extract (electron-builder.json5)*:

Code snippet

{  
  "asar": true,  
  "extraResources": \[  
    {  
      "from": "backend/dist",   
      "to": "backend",  
      "filter": \["\*\*/\*"\]  
    }  
  \]  
}

#### **Works cited**

1. alex8088/electron-vite \- GitHub, accessed March 14, 2026, [https://github.com/alex8088/electron-vite](https://github.com/alex8088/electron-vite)  
2. vite-plugin-electron \- GitHub, accessed March 13, 2026, [https://github.com/electron-vite/vite-plugin-electron](https://github.com/electron-vite/vite-plugin-electron)  
3. Issues · alex8088/electron-vite-boilerplate \- GitHub, accessed March 14, 2026, [https://github.com/alex8088/electron-vite-boilerplate/issues](https://github.com/alex8088/electron-vite-boilerplate/issues)  
4. bytecodePlugin doesn't work with electron 27.0.0 (MacOS universal) · Issue \#315 \- GitHub, accessed March 14, 2026, [https://github.com/alex8088/electron-vite/issues/315](https://github.com/alex8088/electron-vite/issues/315)  
5. Development | electron-vite, accessed March 14, 2026, [https://electron-vite.org/guide/dev](https://electron-vite.org/guide/dev)  
6. HMR and Hot Reloading \- electron-vite, accessed March 14, 2026, [https://electron-vite.org/guide/hmr-and-hot-reloading](https://electron-vite.org/guide/hmr-and-hot-reloading)  
7. electron-builder.json5, accessed March 13, 2026, [https://electron-vite.github.io/build/electron-builder.html](https://electron-vite.github.io/build/electron-builder.html)  
8. electron-vite: Easy way to protect your Electron source code \- DEV Community, accessed March 14, 2026, [https://dev.to/alex114/electron-vite-easy-way-to-protect-your-electron-source-code-4pjb](https://dev.to/alex114/electron-vite-easy-way-to-protect-your-electron-source-code-4pjb)  
9. Vite Plugin \- Electron Forge, accessed March 14, 2026, [https://www.electronforge.io/config/plugins/vite](https://www.electronforge.io/config/plugins/vite)  
10. Vite | Electron Forge, accessed March 14, 2026, [https://www.electronforge.io/templates/vite](https://www.electronforge.io/templates/vite)  
11. Vite \+ TypeScript \- Electron Forge, accessed March 13, 2026, [https://www.electronforge.io/templates/vite-+-typescript](https://www.electronforge.io/templates/vite-+-typescript)  
12. Electron Forge: Getting Started, accessed March 14, 2026, [https://www.electronforge.io/](https://www.electronforge.io/)  
13. tomjs/vite-plugin-electron \- GitHub, accessed March 14, 2026, [https://github.com/tomjs/vite-plugin-electron](https://github.com/tomjs/vite-plugin-electron)  
14. \[vite-typescript\]: need to set \`cacheDir\` by default? · Issue \#3298 · electron/forge \- GitHub, accessed March 13, 2026, [https://github.com/electron/forge/issues/3298](https://github.com/electron/forge/issues/3298)  
15. Boilerplates and CLIs | Electron, accessed March 14, 2026, [https://electronjs.org/docs/latest/tutorial/boilerplates-and-clis](https://electronjs.org/docs/latest/tutorial/boilerplates-and-clis)  
16. electron-react-boilerplate/electron-react-boilerplate: A Foundation for Scalable Cross-Platform Apps \- GitHub, accessed March 14, 2026, [https://github.com/electron-react-boilerplate/electron-react-boilerplate](https://github.com/electron-react-boilerplate/electron-react-boilerplate)  
17. Separete main and renderer with folder · Issue \#2346 · electron-react-boilerplate/electron ... \- GitHub, accessed March 14, 2026, [https://github.com/electron-react-boilerplate/electron-react-boilerplate/issues/2346](https://github.com/electron-react-boilerplate/electron-react-boilerplate/issues/2346)  
18. How should be the project architecture ( or structure ) of React \+ Electron? \- Stack Overflow, accessed March 13, 2026, [https://stackoverflow.com/questions/67478808/how-should-be-the-project-architecture-or-structure-of-react-electron](https://stackoverflow.com/questions/67478808/how-should-be-the-project-architecture-or-structure-of-react-electron)  
19. Signal desktop app based on electron \- GitHub, accessed March 13, 2026, [https://github.com/signal-desktop/signal-desktop](https://github.com/signal-desktop/signal-desktop)  
20. moloch--/reasonably-secure-electron \- GitHub, accessed March 14, 2026, [https://github.com/moloch--/reasonably-secure-electron](https://github.com/moloch--/reasonably-secure-electron)  
21. Security | Electron, accessed March 14, 2026, [https://electronjs.org/docs/latest/tutorial/security](https://electronjs.org/docs/latest/tutorial/security)  
22. signalapp/Signal-Desktop: A private messenger for ... \- GitHub, accessed March 13, 2026, [https://github.com/signalapp/Signal-Desktop](https://github.com/signalapp/Signal-Desktop)  
23. Context Isolation \- Electron, accessed March 14, 2026, [https://electronjs.org/docs/latest/tutorial/context-isolation](https://electronjs.org/docs/latest/tutorial/context-isolation)  
24. I kept rebuilding the same Electron boilerplate, so I open-sourced it : r/SideProject \- Reddit, accessed March 13, 2026, [https://www.reddit.com/r/SideProject/comments/1pqe2zh/i\_kept\_rebuilding\_the\_same\_electron\_boilerplate/](https://www.reddit.com/r/SideProject/comments/1pqe2zh/i_kept_rebuilding_the_same_electron_boilerplate/)  
25. Signal-Desktop no longer works with Windows roaming profiles \#7038 \- GitHub, accessed March 13, 2026, [https://github.com/signalapp/Signal-Desktop/issues/7038](https://github.com/signalapp/Signal-Desktop/issues/7038)  
26. fyears/electron-python-example: Electron as GUI of Python ... \- GitHub, accessed March 13, 2026, [https://github.com/fyears/electron-python-example](https://github.com/fyears/electron-python-example)  
27. How would I go about implementing Python for my backend in a React \+ Electron Desktop Application? : r/electronjs \- Reddit, accessed March 13, 2026, [https://www.reddit.com/r/electronjs/comments/1cgbgge/how\_would\_i\_go\_about\_implementing\_python\_for\_my/](https://www.reddit.com/r/electronjs/comments/1cgbgge/how_would_i_go_about_implementing_python_for_my/)  
28. Python on Electron framework \- Stack Overflow, accessed March 14, 2026, [https://stackoverflow.com/questions/32158738/python-on-electron-framework](https://stackoverflow.com/questions/32158738/python-on-electron-framework)  
29. How to use preload.js properly in Electron \- Stack Overflow, accessed March 14, 2026, [https://stackoverflow.com/questions/57807459/how-to-use-preload-js-properly-in-electron](https://stackoverflow.com/questions/57807459/how-to-use-preload-js-properly-in-electron)  
30. Electron store my app datas in 'userData' path \- Stack Overflow, accessed March 13, 2026, [https://stackoverflow.com/questions/61039792/electron-store-my-app-datas-in-userdata-path](https://stackoverflow.com/questions/61039792/electron-store-my-app-datas-in-userdata-path)  
31. Updating Shadcn UI Components to React 19 \- MakerKit, accessed March 14, 2026, [https://makerkit.dev/blog/tutorials/update-shadcn-react-19](https://makerkit.dev/blog/tutorials/update-shadcn-react-19)  
32. A complete guide to TanStack Table (formerly React Table) \- LogRocket Blog, accessed March 14, 2026, [https://blog.logrocket.com/tanstack-table-formerly-react-table/](https://blog.logrocket.com/tanstack-table-formerly-react-table/)  
33. Migrating to TanStack Query v5, accessed March 14, 2026, [https://tanstack.com/query/v5/docs/react/guides/migrating-to-v5](https://tanstack.com/query/v5/docs/react/guides/migrating-to-v5)  
34. Advanced Electron.js architecture \- LogRocket Blog, accessed March 14, 2026, [https://blog.logrocket.com/advanced-electron-js-architecture/](https://blog.logrocket.com/advanced-electron-js-architecture/)  
35. CPU Usage Soars with Signal Desktop App \- Linux PopOS 21.10 \- Reddit, accessed March 13, 2026, [https://www.reddit.com/r/signal/comments/rqm7pg/cpu\_usage\_soars\_with\_signal\_desktop\_app\_linux/](https://www.reddit.com/r/signal/comments/rqm7pg/cpu_usage_soars_with_signal_desktop_app_linux/)  
36. 5 React UI Component Libraries for your next Project \- DEV Community, accessed March 14, 2026, [https://dev.to/riteshkokam/5-react-ui-component-libraries-for-your-next-project-4le7](https://dev.to/riteshkokam/5-react-ui-component-libraries-for-your-next-project-4le7)  
37. React 19 compatibility · Issue \#2900 · radix-ui/primitives \- GitHub, accessed March 14, 2026, [https://github.com/radix-ui/primitives/issues/2900](https://github.com/radix-ui/primitives/issues/2900)  
38. Next.js 15 \+ React 19 \- Shadcn UI, accessed March 14, 2026, [https://ui.shadcn.com/docs/react-19](https://ui.shadcn.com/docs/react-19)  
39. Integrating Shadcn UI with React 19: Step-by-Step Tutorial \- Mobisoft Infotech, accessed March 14, 2026, [https://mobisoftinfotech.com/resources/blog/react-19-shadcn-ui-integration-tutorial](https://mobisoftinfotech.com/resources/blog/react-19-shadcn-ui-integration-tutorial)  
40. Data Table \- Shadcn UI, accessed March 14, 2026, [https://ui.shadcn.com/docs/components/radix/data-table](https://ui.shadcn.com/docs/components/radix/data-table)  
41. A boilerplate Electron desktop application built with React, TanStack Router, and shadcn/ui \- GitHub, accessed March 14, 2026, [https://github.com/examples-hub/electron-tanstack-shadcn](https://github.com/examples-hub/electron-tanstack-shadcn)  
42. Version v7.9.0 \- Mantine, accessed March 14, 2026, [https://mantine.dev/changelog/7-9-0/](https://mantine.dev/changelog/7-9-0/)  
43. What do you think of mantine? Why do you prefer it or why not use it? : r/reactjs \- Reddit, accessed March 14, 2026, [https://www.reddit.com/r/reactjs/comments/16h1a9z/what\_do\_you\_think\_of\_mantine\_why\_do\_you\_prefer\_it/](https://www.reddit.com/r/reactjs/comments/16h1a9z/what_do_you_think_of_mantine_why_do_you_prefer_it/)  
44. Mantine React Table, accessed March 14, 2026, [https://www.mantine-react-table.com/](https://www.mantine-react-table.com/)  
45. mantine-react-table \- NPM, accessed March 14, 2026, [https://www.npmjs.com/package/mantine-react-table](https://www.npmjs.com/package/mantine-react-table)  
46. Upgrade to v6 \- Material UI, accessed March 14, 2026, [https://mui.com/material-ui/migration/upgrade-to-v6/](https://mui.com/material-ui/migration/upgrade-to-v6/)  
47. Material React Table V3, accessed March 14, 2026, [https://www.material-react-table.com/](https://www.material-react-table.com/)  
48. Allow ASAR to work with \`child\_process.spawn()\` · Issue \#9459 \- GitHub, accessed March 14, 2026, [https://github.com/electron/electron/issues/9459](https://github.com/electron/electron/issues/9459)  
49. utilityProcess | Electron, accessed March 14, 2026, [https://electronjs.org/docs/latest/api/utility-process](https://electronjs.org/docs/latest/api/utility-process)  
50. Running Python server with electron : r/electronjs \- Reddit, accessed March 14, 2026, [https://www.reddit.com/r/electronjs/comments/1he2how/running\_python\_server\_with\_electron/](https://www.reddit.com/r/electronjs/comments/1he2how/running_python_server_with_electron/)  
51. Building a deployable Python-Electron App | by Andy Bulka | Medium, accessed March 14, 2026, [https://medium.com/@abulka/building-a-deployable-python-electron-app-4e8c807bfa5e](https://medium.com/@abulka/building-a-deployable-python-electron-app-4e8c807bfa5e)  
52. Python Cross Platform APP using Electron JS and Fast API \- GitHub, accessed March 14, 2026, [https://github.com/gnoviawan/fast-api-electron-js](https://github.com/gnoviawan/fast-api-electron-js)  
53. How to add folders and files to electron build using electron-builder \- Stack Overflow, accessed March 13, 2026, [https://stackoverflow.com/questions/45392642/how-to-add-folders-and-files-to-electron-build-using-electron-builder](https://stackoverflow.com/questions/45392642/how-to-add-folders-and-files-to-electron-build-using-electron-builder)  
54. Cross-platform deploy: Python \+ Electron | by Stefan Pietrusky \- Medium, accessed March 14, 2026, [https://medium.com/pythoneers/cross-platform-deploy-python-electron-c6218ff8f811](https://medium.com/pythoneers/cross-platform-deploy-python-electron-c6218ff8f811)  
55. Building a Health-Check Microservice with FastAPI \- DEV Community, accessed March 14, 2026, [https://dev.to/lisan\_al\_gaib/building-a-health-check-microservice-with-fastapi-26jo](https://dev.to/lisan_al_gaib/building-a-health-check-microservice-with-fastapi-26jo)  
56. Spawning (and killing) Uvicorn/FastAPI backend from Electron (or Node.js) \- Stack Overflow, accessed March 14, 2026, [https://stackoverflow.com/questions/70282149/spawning-and-killing-uvicorn-fastapi-backend-from-electron-or-node-js](https://stackoverflow.com/questions/70282149/spawning-and-killing-uvicorn-fastapi-backend-from-electron-or-node-js)  
57. Electron spawned python child process stdio not functioning properly in development, accessed March 14, 2026, [https://www.reddit.com/r/electronjs/comments/gs3tab/electron\_spawned\_python\_child\_process\_stdio\_not/](https://www.reddit.com/r/electronjs/comments/gs3tab/electron_spawned_python_child_process_stdio_not/)  
58. Integrating Python Flask Backend with Electron (Nodejs) Frontend | by Ahmad Sachal | Red Buffer | Medium, accessed March 13, 2026, [https://medium.com/red-buffer/integrating-python-flask-backend-with-electron-nodejs-frontend-8ac621d13f72](https://medium.com/red-buffer/integrating-python-flask-backend-with-electron-nodejs-frontend-8ac621d13f72)