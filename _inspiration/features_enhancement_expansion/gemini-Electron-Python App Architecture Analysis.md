# **Architectural Blueprint for Zorivest: Adapting OpenWhispr Patterns for a Hybrid Electron-FastAPI Environment**

The development of modern desktop applications necessitates navigating a complex intersection of web technologies and native operating system capabilities. The architectural evaluation of OpenWhispr, an open-source voice dictation application, reveals a sophisticated implementation of Electron-specific patterns, particularly concerning window management, state synchronization, and system tray integration. However, adapting these paradigms for Zorivest—a desktop trade review and planning tool that relies on a localized Python FastAPI background daemon and an encrypted SQLCipher database—requires a fundamental architectural paradigm shift.

Zorivest operates under a strict operational constraint: it possesses no capability to execute, modify, or cancel market orders. Its primary domain is the aggregation, analysis, and planning of trading activities. Furthermore, the decoupling of the application into an Electron-based graphical user interface and a headless Python service daemon introduces asynchronous state management challenges that monolithic Electron applications do not typically face. The analysis presented herein exhaustively explores how to adapt OpenWhispr’s architecture to Zorivest’s hybrid constraints, delivering actionable recommendations, structural blueprints, and rigorous risk mitigation strategies across five core engineering domains.

## **1\. System Tray & Window Management**

The multi-window architecture within OpenWhispr utilizes a centralized tray manager to handle interactions between a floating dictation overlay, a control panel, and background transcription services. In that ecosystem, the tray icon's primary responsibility is manipulating window visibility and providing quick access to context menus.1 For Zorivest, the system tray and window management systems must not only reflect the visibility state of the graphical interface but must also serve as a real-time monitor for the underlying Python FastAPI service daemon.2

The native capabilities of the Electron framework regarding system tray icons vary significantly across operating systems. On macOS, the icon is situated in the menu bar extras area and requires specific handling, such as utilizing the setIgnoreDoubleClickEvents property to accurately register isolated click events.4 On Windows, the icon resides within the notification area, while on Linux, the implementation relies heavily on the desktop environment, defaulting to the StatusNotifierItem specification or falling back to the legacy GtkStatusIcon.4 OpenWhispr gracefully handles these discrepancies by generating programmatic canvas fallback icons.1 Zorivest must expand upon this foundation by integrating asynchronous health polling into the main process to continuously assess the FastAPI daemon's status.

Furthermore, OpenWhispr's approach to crash recovery involves completely destroying and rebuilding the control panel window when a render-process-gone event is detected. For a professional financial application, completely destroying the window eliminates unpersisted React state and produces a jarring user experience. When the FastAPI backend crashes or becomes unreachable, the Electron graphical shell should remain active, gracefully degrading the user experience by overlaying a visual disconnection indicator utilizing React Portals or CSS abstraction layers.5

Regarding window framing, applications tailored for the financial sector require high data density and structural predictability. OpenWhispr utilizes frameless windows with custom macOS traffic light positioning. While frameless windows offer profound aesthetic customization, they frequently disrupt native operating system tiling mechanisms, such as Windows Snap Assist or macOS native window management protocols.8 Consequently, retaining native OS window frames is structurally advantageous for Zorivest.

### **Recommendation**

The system architecture should implement a bifurcated window management strategy where the ZorivestTrayManager acts as the definitive source of truth for the application lifecycle, continuously polling the local FastAPI health endpoint to update its native icon dynamically. Concurrently, the WindowManager must implement graceful degradation capabilities utilizing native OS window frames, ensuring that if the backend service crashes, the main window is not destroyed but instead presents an application-level overlay to preserve the user's ephemeral context while the daemon reinitializes.

### **Architecture Diagram**

Code snippet

sequenceDiagram  
    participant OS as Operating System  
    participant Main as Electron Main Process  
    participant Tray as ZorivestTrayManager  
    participant FastAPI as Python Service Daemon  
    participant Window as BrowserWindow (Renderer)

    OS-\>\>Main: Launch Application  
    Main-\>\>FastAPI: Spawn Daemon Process  
    Main-\>\>Tray: Initialize Tray Icon (Yellow/Pending)  

    loop Every 5 Seconds  
        Tray-\>\>FastAPI: GET http://localhost:8765/api/v1/health  
        alt Service Healthy  
            FastAPI--\>\>Tray: 200 OK  
            Tray-\>\>Tray: Update Icon (Green/Active)  
            Tray-\>\>Window: IPC: backend-status (connected)  
        else Service Unreachable  
            Tray-\>\>Tray: Update Icon (Red/Error)  
            Tray-\>\>Window: IPC: backend-status (disconnected)  
            Window-\>\>Window: Render Disconnected Overlay  
        end  
    end

### **Code Sketch**

TypeScript

import { app, Tray, Menu, nativeImage, BrowserWindow } from 'electron';  
import { fetch } from 'electron-main-fetch';

export class ZorivestTrayManager {  
  private tray: Tray | null \= null;  
  private mainWindow: BrowserWindow;  
  private serviceStatus: 'pending' | 'running' | 'stopped' \= 'pending';  
  private healthCheckInterval: NodeJS.Timeout | null \= null;

  constructor(mainWindow: BrowserWindow) {  
    this.mainWindow \= mainWindow;  
    this.initializeTray();  
    this.startHealthMonitor();  
  }

  private initializeTray(): void {  
    const icon \= this.generateStatusIcon(this.serviceStatus);  
    this.tray \= new Tray(icon);  
    this.tray.setToolTip('Zorivest Trade Review');  

    // Explicitly handle macOS double-click idiosyncrasies  
    if (process.platform \=== 'darwin') {  
      this.tray.setIgnoreDoubleClickEvents(true);  
    }  

    this.updateContextMenu();  
    this.tray.on('click', () \=\> {  
      this.mainWindow.isVisible()? this.mainWindow.hide() : this.mainWindow.show();  
    });  
  }

  private async checkServiceHealth(): Promise\<void\> {  
    try {  
      const response \= await fetch('http://localhost:8765/api/v1/health', { timeout: 2000 });  
      const newStatus \= response.ok? 'running' : 'stopped';  
      this.propagateStatus(newStatus);  
    } catch (error) {  
      this.propagateStatus('stopped');  
    }  
  }

  private propagateStatus(newStatus: 'running' | 'stopped'): void {  
    if (this.serviceStatus\!== newStatus) {  
      this.serviceStatus \= newStatus;  
      this.tray?.setImage(this.generateStatusIcon(newStatus));  
      this.updateContextMenu();  
      this.mainWindow.webContents.send('service-status-changed', newStatus);  
    }  
  }

  private startHealthMonitor(): void {  
    this.healthCheckInterval \= setInterval(() \=\> this.checkServiceHealth(), 5000);  
  }

  private updateContextMenu(): void {  
    const template \=;  
    this.tray?.setContextMenu(Menu.buildFromTemplate(template));  
  }

  private generateStatusIcon(status: string): Electron.NativeImage {  
    // Generates an empty native image; in production, this dynamically renders a colored indicator  
    return nativeImage.createEmpty();  
  }  

  private toggleDaemon(): void { /\* Implementation for invoking WinSW/systemd/launchd \*/ }  
}

### **Trade-Offs**

| Decision Criterion | Option A: Monolithic GUI-Bound Architecture | Option B: Decoupled Tray-Daemon Architecture | Architectural Implication |
| :---- | :---- | :---- | :---- |
| **Window Frame Styling** | Frameless with custom CSS drag regions and traffic light controls. | Native OS window frames and standard window chrome. | Custom frames provide modern aesthetics but frequently break OS-native tiling features. Native frames ensure Zorivest behaves predictably alongside professional financial tools and eliminates edge-case rendering bugs.8 |
| **Crash Recovery Methodology** | Destroy the window and rebuild entirely on render-process-gone. | Retain the window shell; render a CSS/Portal "Disconnected" overlay. | Rebuilding the window purges the React state tree entirely. Retaining the shell and overlaying a disconnection notice preserves the user's unpersisted input (e.g., drafting a trade plan) while the daemon restarts asynchronously.5 |
| **System Tray Context** | Purely manages window visibility and UI toggles. | Manages both GUI visibility and Python Daemon orchestration. | Transforms the tray from a simple window toggler into a comprehensive mission control for the background service, necessitating main-process HTTP polling and elevating the tray's systemic importance.1 |
| **Background Lifecycle** | Exiting the GUI terminates the entire application. | Exiting the GUI leaves the daemon running; tray icon persists. | Requires specific logic mapping to app.on('window-all-closed') to prevent the application from terminating when the user merely wishes to dismiss the interface while allowing automated trade ingestion to continue.1 |

### **Risk Assessment**

The primary risk in this architectural component involves the lifecycle synchronization between the Node.js main process and the Python daemon. If the Electron application initiates the FastAPI daemon but the local SQLCipher database is locked by another process, or the designated network port (8765) is occupied, the health check will fail indefinitely. This scenario creates an infinite loop of silent failures where the user cannot ascertain why the GUI remains frozen in a disconnected state.

To mitigate this risk, the polling mechanism must implement an exponential backoff algorithm. If the daemon fails to achieve a healthy status after three consecutive polling attempts, the system tray must break the silent polling loop and trigger a dedicated native error dialog. This dialog must expose the Python stderr log stream directly to the user, providing transparent diagnostic information regarding the initialization failure. Furthermore, the application must carefully manage the window-all-closed event protocol.1 When a user attempts to quit the application via standard window controls, the system must intercept the command and prompt the user to clarify their intent: whether to leave the backend service running headlessly for continuous data ingestion, or to terminate the complete technological stack.

## **2\. Settings Architecture**

The architecture observed in OpenWhispr utilizes a monolithic Zustand store coupled with robust schema versioning to manage application settings. This store employs a debouncedPersistToEnv() function to synchronize internal application state to a local .env file after a standardized delay, effectively treating localStorage as the primary source of truth while utilizing the file system as a fallback mechanism.12 While this approach is highly effective for applications where the Electron renderer process maintains sole ownership of the data, Zorivest operates under a fundamentally different constraint.

In Zorivest, all persistent state—including user preferences, risk tolerance parameters, default accounts, and encrypted API keys—resides securely within the SQLCipher database. This database is exclusively managed by the Python FastAPI backend to guarantee cryptographic integrity.13 Consequently, allowing the GUI to act as the source of truth introduces unacceptable risks of desynchronization between the client interface and the database layer. The GUI must instead reflect the database settings in real-time while providing the illusion of zero-latency interactivity expected from native desktop applications.

To achieve this, the architecture requires a bifurcated state management approach. Zustand should be utilized exclusively for ephemeral, GUI-local state that does not require database persistence—such as sidebar visibility toggles, active tab indexes, and localized sorting criteria.14 For persistent settings, Zorivest must deploy a REST-driven optimistic update pattern. By utilizing data synchronization libraries like React Query in tandem with Zustand, the application can instantly reflect a user's setting modification in the UI while asynchronously transmitting the PUT /api/v1/settings request to the Python backend.15

If the database transaction encounters an error—such as a SQL lock timeout or a validation failure—the optimistic update must automatically roll back to the previous normalized state.18 Furthermore, schema migrations cannot be safely handled in the renderer process on boot. The Python daemon must take absolute ownership of database schemas using migration tools like Alembic, ensuring that the database remains stable and consistent regardless of the specific version of the Electron client connecting to it.19

### **Recommendation**

Zorivest should enforce a strict separation of state: Zustand must be employed solely for volatile, ephemeral GUI state, while persistent application settings must be managed via a custom useSettings hook that orchestrates React Query and Zustand. This hook will cache data for instant reads, perform optimistic UI updates during user interactions, and automatically roll back the client state utilizing normalized data snapshots if the asynchronous REST API mutation fails, leaving schema migrations entirely under the purview of the Python backend.

### **Architecture Diagram**

Code snippet

flowchart TD  
    UI \--\>|User changes setting| Hook  
    Hook \--\>|1. Instant Update| Zustand\[Zustand Ephemeral Cache\]  
    Zustand \--\>|Updates View| UI  
    Hook \--\>|2. Async PUT Request| REST  

    REST \--\>|Success: 200 OK| Cache  
    REST \--\>|Failure: 500 Error| Rollback  

    Rollback \--\>|Reverts to Previous State| Zustand  
    Rollback \--\>|Triggers Notification| Toast  

    Cache \--\>|Data synchronized| UI

### **Code Sketch**

TypeScript

import { create } from 'zustand';  
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

interface SettingsState {  
  theme: 'light' | 'dark' | 'system';  
  defaultAccountId: string | null;  
  riskPercentageLimit: number;  
}

// 1\. Ephemeral cache for instant synchronous reads across components  
const useLocalSettingsStore \= create\<{  
  settings: SettingsState | null;  
  setOptimisticSettings: (newSettings: Partial\<SettingsState\>) \=\> void;  
}\>((set) \=\> ({  
  settings: null,  
  setOptimisticSettings: (newSettings) \=\>  
    set((state) \=\> ({ settings: state.settings? {...state.settings,...newSettings } : null }))  
}));

// 2\. The unified hook orchestrating REST communication and optimistic UI updates  
export const useSettings \= () \=\> {  
  const queryClient \= useQueryClient();  
  const localSettings \= useLocalSettingsStore((state) \=\> state.settings);  
  const setOptimistic \= useLocalSettingsStore((state) \=\> state.setOptimisticSettings);

  const query \= useQuery({  
    queryKey: \['settings'\],  
    queryFn: async () \=\> {  
      const res \= await fetch('http://localhost:8765/api/v1/settings');  
      if (\!res.ok) throw new Error('Network response was not ok');  
      return res.json() as Promise\<SettingsState\>;  
    },  
    // Populate the local Zustand store upon successful fetch  
    onSuccess: (data) \=\> useLocalSettingsStore.setState({ settings: data })  
  });

  const mutation \= useMutation({  
    mutationFn: async (newSettings: Partial\<SettingsState\>) \=\> {  
      const res \= await fetch('http://localhost:8765/api/v1/settings', {  
        method: 'PUT',  
        headers: { 'Content-Type': 'application/json' },  
        body: JSON.stringify(newSettings),  
      });  
      if (\!res.ok) throw new Error('Failed to persist settings');  
    },  
    onMutate: async (newSettings) \=\> {  
      // Cancel outbound fetches to prevent race conditions during mutation  
      await queryClient.cancelQueries({ queryKey: \['settings'\] });  
      const previousSettings \= queryClient.getQueryData(\['settings'\]) as SettingsState;  

      // Optimistically update the local Zustand store for instant UI feedback  
      setOptimistic(newSettings);  
      return { previousSettings };  
    },  
    onError: (err, newSettings, context) \=\> {  
      // Automatic rollback to the exact previous state upon backend failure  
      if (context?.previousSettings) {  
        useLocalSettingsStore.setState({ settings: context.previousSettings });  
      }  
    },  
    onSettled: () \=\> {  
      // Ensure absolute synchronization by invalidating the query cache  
      queryClient.invalidateQueries({ queryKey: \['settings'\] });  
    },  
  });

  return {  
    settings: localSettings?? query.data,  
    isLoading: query.isLoading,  
    updateSettings: mutation.mutate,  
    isSyncing: mutation.isPending  
  };  
};

### **Trade-Offs**

| Decision Criterion | Option A: Zustand Monolithic Store | Option B: REST-Driven Optimistic State | Architectural Implication |
| :---- | :---- | :---- | :---- |
| **Source of Truth** | Client localStorage and memory. | SQLCipher via FastAPI REST interface. | A monolithic store risks dangerous schema desynchronization between the UI and the encrypted database. The REST-driven approach ensures the database remains the ultimate authority while caching techniques maintain UI responsiveness.18 |
| **Schema Migration Handling** | Handled in the renderer process on boot. | Handled in the Python daemon via Alembic. | GUI-side migrations strictly tie the backend schema to the specific client version, severely limiting headless capabilities. Server-side migrations guarantee daemon consistency, regardless of the GUI client's version or availability.19 |
| **Offline Degradation Capability** | Fully functional offline; reads/writes seamlessly. | Requires daemon running; degrades gracefully. | If the daemon stops, the GUI retains the last known settings in the Zustand cache, entering a read-only mode. This prevents the UI from unmounting abruptly while safely disabling writes until the daemon re-establishes connection.15 |

### **Risk Assessment**

Implementing optimistic UI updates inherently introduces the risk of "rubber-banding" visual glitches. This phenomenon occurs when a user interacts with a UI element (e.g., toggling a risk management switch), the UI instantly reflects the "active" state, but the server request subsequently fails due to network latency or database locks. The UI then forcefully snaps back to its original "inactive" state moments later, severely degrading user trust in the application interface.

To mitigate this psychological friction, the architecture must mandate rigorous client-side schema validation (utilizing validation libraries such as Zod) before the mutation is ever dispatched. This ensures that structurally invalid states are caught within the renderer process immediately. Furthermore, the rollback mechanism executed within the onError callback of the mutation must be accompanied by an explicit, non-intrusive toast notification. This notification must clearly articulate the exact cause of the synchronization failure to the user, preventing confusion regarding why their input was apparently ignored by the system.16

## **3\. Command Palette**

The command palette functions as the central nervous system for power users navigating sophisticated desktop software. OpenWhispr implements its command palette utilizing @radix-ui/react-dialog for modal presentation and channels semantic search queries through the Electron IPC bridge to local note structures. While highly effective for a specialized dictation tool, Zorivest's operational domain is substantially more structured and entity-dense. A user interacting with Zorivest must be able to seamlessly search across thousands of historical trade records, complex algorithmic trade plans, watchlist entries, settings menus, and dynamic pipeline policies.

Relying exclusively on the REST API to execute these searches introduces unacceptable latency. The overhead of network communication—even over a localhost loopback interface—combined with database query execution time creates perceptible input lag, destroying the rapid, "native" feel expected of a keyboard-driven command palette.23 Conversely, attempting to load all historical trade data into the React renderer's memory to perform local searches would rapidly exhaust the V8 JavaScript engine's memory constraints, leading to application instability.

To resolve this tension, Zorivest must deploy a hybrid search paradigm managed by a Component Registry Pattern.26 The Component Registry pattern systematically dismantles the monolithic architecture typically associated with global search components. Instead of a massive switch statement evaluating every possible search domain, individual entity providers (e.g., a TradeRecordProvider, a SettingsProvider) register themselves with a central CommandRegistry.

The hybrid search model leverages this registry to execute dual-tier searching. Upon application boot, the client asynchronously hydrates a local in-memory search index (utilizing a library such as Fuse.js) with high-priority metadata—such as active portfolio tickers, open trade plans, and recent watchlist items. When a user queries the command palette, the local index resolves instantly. Concurrently, a debounced background request is dispatched to the FastAPI backend to query deep historical records. The command palette will also feature an interceptor provider for the Model Context Protocol (MCP), surfacing tools like zorivest\_calculate\_position when the user inputs designated invocation syntax.

### **Recommendation**

The application must implement a Component Registry Pattern to modularize the command palette architecture, allowing distinct entity providers to manage their own search logic without inflating the core React component. To ensure native-level responsiveness while querying vast datasets, the providers should utilize a hybrid search algorithm: resolving immediate, high-priority queries against a local in-memory index, while dispatching debounced REST API requests to the Python daemon for deep historical entity retrieval.

### **Architecture Diagram**

Code snippet

classDiagram  
    class CommandPaletteCore {  
        \+registerProvider(provider: SearchProvider)  
        \+handleInput(query: string)  
        \+executeAction(actionId: string)  
    }

    class SearchProvider {  
        \<\<interface\>\>  
        \+id: string  
        \+priority: number  
        \+search(query: string): Promise\~CommandResult\~  
    }

    class LocalEntityProvider {  
        \-localFuseIndex: FuseCache  
        \+search(query)  
    }

    class DeepRESTProvider {  
        \-debouncedFetch: Function  
        \+search(query)  
    }

    class MCPToolProvider {  
        \+search(query)  
    }

    CommandPaletteCore \--\> SearchProvider : invokes parallel execution  
    SearchProvider \<|.. LocalEntityProvider : implements  
    SearchProvider \<|.. DeepRESTProvider : implements  
    SearchProvider \<|.. MCPToolProvider : implements

### **Code Sketch**

TypeScript

export interface CommandResult {  
  id: string;  
  title: string;  
  subtitle?: string;  
  icon: React.ReactNode;  
  onSelect: () \=\> void;  
}

export interface SearchProvider {  
  id: string;  
  priority: number;  
  search: (query: string) \=\> Promise\<CommandResult\>;  
}

class CommandRegistry {  
  private providers: Map\<string, SearchProvider\> \= new Map();

  public register(provider: SearchProvider): void {  
    this.providers.set(provider.id, provider);  
  }

  public async searchAll(query: string): Promise\<CommandResult\> {  
    if (\!query.trim()) return;

    // Execute all registered providers in parallel to minimize total latency  
    const promises \= Array.from(this.providers.values())  
     .sort((a, b) \=\> b.priority \- a.priority)  
     .map(provider \=\> provider.search(query));

    const resultsArray \= await Promise.all(promises);  
    return resultsArray.flat();  
  }  
}

export const globalCommandRegistry \= new CommandRegistry();

// Example implementation of a dynamic provider handling MCP tools via REST  
globalCommandRegistry.register({  
  id: 'mcp-tools',  
  priority: 100,  
  search: async (query) \=\> {  
    // MCP tool invocation syntax intercepted via leading forward slash  
    if (\!query.startsWith('/')) return;  

    const fetchRes \= await fetch(\`http://localhost:8765/api/v1/mcp/tools?q=${query.slice(1)}\`);  
    if (\!fetchRes.ok) return;  

    const tools \= await fetchRes.json();  
    return tools.map((tool: any) \=\> ({  
      id: \`tool-${tool.name}\`,  
      title: tool.name,  
      subtitle: tool.description,  
      icon: \<CpuIcon /\>,  
      onSelect: () \=\> window.dispatchEvent(new CustomEvent('invoke-mcp', { detail: tool }))  
    }));  
  }  
});

### **Trade-Offs**

| Decision Criterion | Option A: Pure REST Search | Option B: Hybrid Local/REST Search | Architectural Implication |
| :---- | :---- | :---- | :---- |
| **Query Latency Profile** | Strictly network-bound (\~50-150ms depending on database load). | Immediate in-memory (\~2-5ms) combined with delayed deep search. | A pure REST approach causes noticeable input lag while a user types rapidly, severely impacting the perception of a "native" desktop feel.23 The hybrid model mathematically masks network latency for the most common search operations. |
| **Architectural Complexity** | Low. The client UI is purely presentational; the server processes all logic. | High. Requires sophisticated state syncing and client-side invalidation strategies. | Maintaining a local index requires the GUI to subscribe to server-sent events to invalidate local caches whenever a new trade is ingested by the background daemon, elevating architectural complexity.24 |
| **System Extensibility** | Hardcoded monolithic search endpoint. | Component Registry Pattern. | The registry pattern enables developers to construct new search domains (e.g., adding a specific "Macro Indicators" module) without modifying the core Command Palette UI component.26 |

### **Risk Assessment**

A distributed provider approach introduces the severe risk of staggered UI rendering and layout shifting. If the local index returns results in five milliseconds, but the historical REST API search takes two hundred milliseconds to process on the database layer, the command palette UI will experience jarring visual shifts as the delayed results aggressively interject themselves into the rendered list while the user is actively typing.

To counteract this visual instability, the architecture must implement strict debouncing on the master text input (e.g., 150ms delay before firing the search function). More importantly, the user interface must be segmented into visually distinct categories (e.g., a "Recent Items" section separated visually from a "Deep Search Results" section) rather than utilizing a single flat list.29 This distinct categorization ensures that delayed asynchronous results gracefully append to the bottom of the list or populate a specific sub-container, preventing the displacement of instantly rendered local items and protecting the user from accidental mis-clicks.

## **4\. Onboarding Flow**

The initial onboarding experience fundamentally dictates software adoption and user retention. OpenWhispr’s onboarding sequence leverages persistent state in localStorage to navigate users through permission granting and model downloading phases. However, Zorivest requires the initialization of a highly secure financial environment. The critical path for Zorivest involves generating and confirming the SQLCipher database cryptographic passphrase, verifying broker API connectivity, and establishing the foundational account structures.13

A major architectural challenge arises regarding the cryptographic keys. SQLCipher utilizes PBKDF2 with SHA512 for key derivation, leading to AES-256-CBC page-level encryption.13 If the passphrase is lost, the entire trade history database is cryptographically unrecoverable.32 Storing this passphrase locally in plain text defeats the purpose of encryption-at-rest. The application must either require the user to input the password upon every launch or securely negotiate with the operating system's native Keystore (e.g., Windows Credential Manager, macOS Keychain) via an IPC integration to retrieve the credentials.33

Furthermore, the onboarding wizard necessitates the execution of long-running validation tasks. When a user inputs API credentials for Interactive Brokers or Alpaca, the Python daemon must execute a network handshake with the external broker to verify the key's validity before allowing the user to proceed. In traditional React applications, this often results in frozen UI states or the necessity of drilling loading boolean flags deep into the component tree. Zorivest should leverage React 19’s advanced concurrent features, specifically useTransition and useActionState. These hooks natively wrap asynchronous functions, automatically managing the pending state and allowing the UI to remain highly responsive and non-blocking during complex server verifications.34

Finally, the initialization sequence must account for the asynchronous boot time of the Python daemon. If the Electron renderer attempts to load the React application before the FastAPI server binds to port 8765, the application will encounter catastrophic network errors. The system should utilize a lightweight splash screen in the main process that masks the initialization sequence, gracefully holding the user's attention until the daemon passes its first health check.3

### **Recommendation**

The onboarding flow must utilize a persistent state machine for step navigation to survive unexpected application closures. Long-running verification operations, such as broker authentication, must be managed utilizing React 19's useActionState and useTransition hooks to maintain a non-blocking user interface. Crucially, the Electron main process must intercept the initial application boot, presenting a native splash screen while actively polling the FastAPI port; the primary React application must only be instantiated once the backend daemon confirms full operational readiness.

### **Architecture Diagram**

Code snippet

stateDiagram-v2  
    \[\*\] \--\> ElectronSplash  
    ElectronSplash \--\> DaemonCheck : Main Process Boot  
    DaemonCheck \--\> StartDaemon : Port 8765 Unreachable  
    DaemonCheck \--\> MountReact : Port 8765 Active  
    StartDaemon \--\> MountReact : Health Check OK  

    state MountReact {  
        \[\*\] \--\> CheckDatabaseState  
        CheckDatabaseState \--\> Dashboard : DB Initialized  
        CheckDatabaseState \--\> WizardStep1 : DB Missing/Locked  

        WizardStep1 \--\> WizardStep2 : Passphrase Generated (SQLCipher)  
        WizardStep2 \--\> WizardStep3 : Broker Configured (Async Verification)  
        WizardStep3 \--\> Dashboard : Setup Complete  
    }

### **Code Sketch**

TypeScript

import { useActionState, useTransition } from 'react';

// Server action representing the complex API call to the Python daemon  
async function verifyBrokerConnection(prevState: any, formData: FormData) {  
  const apiKey \= formData.get('apiKey');  
  const apiSecret \= formData.get('apiSecret');

  try {  
    const res \= await fetch('http://localhost:8765/api/v1/brokers/verify', {  
      method: 'POST',  
      headers: { 'Content-Type': 'application/json' },  
      body: JSON.stringify({ apiKey, apiSecret }),  
    });

    if (\!res.ok) {  
      const error \= await res.json();  
      return { success: false, message: error.detail |

| 'Cryptographic handshake failed.' };  
    }  
    return { success: true, message: 'Broker authenticated successfully.' };  
  } catch (err) {  
    return { success: false, message: 'Daemon communication timeout.' };  
  }  
}

export function BrokerSetupStep({ onNext }: { onNext: () \=\> void }) {  
  // React 19 concurrent feature integration for seamless state handling  
  const \[state, formAction\] \= useActionState(verifyBrokerConnection, null);  
  const \= useTransition();

  const handleSubmit \= (event: React.FormEvent\<HTMLFormElement\>) \=\> {  
    event.preventDefault();  
    const formData \= new FormData(event.currentTarget);  

    // startTransition keeps the UI entirely responsive during the long API verification  
    startTransition(() \=\> {  
      formAction(formData);  
    });  
  };

  // Automated programmatic navigation upon successful asynchronous verification  
  if (state?.success) onNext();

  return (  
    \<form onSubmit\={handleSubmit} className\="flex flex-col gap-4 max-w-md"\>  
      \<h2 className\="text-xl font-bold"\>Authenticate Broker\</h2\>  
      \<input name\="apiKey" type\="text" placeholder\="API Key" required className\="input" /\>  
      \<input name\="apiSecret" type\="password" placeholder\="API Secret" required className\="input" /\>  

      {state?.success \=== false && \<p className\="text-red-500 text-sm"\>{state.message}\</p\>}  

      \<button type\="submit" disabled\={isPending} className\="btn-primary"\>  
        {isPending? 'Verifying Network Handshake...' : 'Authenticate & Continue'}  
      \</button\>  
    \</form\>  
  );  
}

### **Trade-Offs**

| Decision Criterion | Option A: Hardcoded Local Passphrase Storage | Option B: User-Provided or OS Keystore Integration | Architectural Implication |
| :---- | :---- | :---- | :---- |
| **SQLCipher Key Management** | Electron securely stores the key in localStorage or on the file system. | User inputs key manually upon launch, or Electron utilizes OS native Keystore via IPC. | Storing the key on disk fundamentally bypasses the protection of encryption-at-rest. The key must be requested interactively from the user or securely fetched from the OS native credential manager using an IPC call before being securely passed to the FastAPI daemon.32 |
| **Daemon Startup Sequence** | React framework loads immediately and actively polls for the daemon. | Electron completely delays React rendering until the daemon is verified healthy. | Loading React immediately causes severe network errors to cascade in the console and forces the frontend to handle chaotic failure states. Utilizing the main process to hold at a splash screen abstracts OS-level daemon initialization away from the web layer entirely.3 |
| **Wizard State Persistence** | Redux/Zustand heavy persist middleware logic. | Standard localStorage stringification bound to the application router. | Given the extreme simplicity of step-by-step wizard state, global state middleware is excessive overhead. Basic routing persistence is cleaner and easier to purge upon successful completion.14 |

### **Risk Assessment**

Handling database encryption passphrases introduces critical, unrecoverable risks regarding data sovereignty. If a user loses their SQLCipher passphrase, the SQLite database is cryptographically impenetrable; there is no theoretical backdoor to recover the aggregated financial data.32

To mitigate this catastrophic failure mode, the onboarding flow must implement a mandatory recovery verification step. During the initial passphrase generation, the interface must force the user to save a recovery phrase (a human-readable seed phrase or an exact string copy of the raw key). The UI must absolutely validate that the user has recorded this phrase by requiring them to type it back into an empty validation field before the wizard will permit them to proceed. This friction ensures intentionality and drastically reduces the probability of a user inadvertently permanently locking their financial data behind a forgotten password.

## **5\. IPC Bridge Design**

OpenWhispr heavily relies on the window.electronAPI to shuttle extensive amounts of data between the renderer and main processes, frequently utilizing optional chaining syntaxes (e.g., window.electronAPI?.someMethod?.()). While this loose typing provides rapid developmental flexibility, it obscures missing API implementations and represents an architectural anti-pattern for a hybrid architecture like Zorivest.

In Zorivest, the Python FastAPI backend serves as the core application engine. Therefore, heavy domain data—including vast arrays of historical trades, analytical metrics, and algorithmic plans—must flow over REST directly from the renderer process to localhost:8765, completely bypassing Electron's main Node.js process.40 Routing massive JSON objects through the IPC bridge introduces severe serialization bottlenecks because the communication must pass through the Chromium process boundary, get serialized into memory, traverse the Node.js event loop, and then be re-serialized for transmission.41 Direct REST calls entirely eliminate this performance bottleneck.

However, Inter-Process Communication (IPC) remains an absolute necessity for operating system integrations. Operations such as minimizing the window to the system tray, triggering native OS notifications, invoking file system dialogs for CSV exports, and interacting with the secure OS Keystore cannot be achieved via REST.42

To safely implement these native capabilities, Zorivest must utilize Electron's contextBridge to enforce context isolation. Disabling context isolation exposes the application to severe Cross-Site Scripting (XSS) vulnerabilities, as malicious scripts could potentially execute arbitrary Node.js or OS commands.44 Furthermore, instead of relying on optional chaining and loosely typed IPC events that fail silently, Zorivest must implement a strict Typed Proxy Pattern using contextBridge.exposeInMainWorld. This mechanism guarantees that unavailable methods explicitly throw descriptive errors, and the entire bridge is deeply typed via TypeScript declaration files, ensuring compilation failure if a developer misuses a system integration method.46

### **Recommendation**

A rigid structural boundary matrix must be established governing data flow: network requests for all business logic must utilize direct REST API calls to the local Python daemon to eliminate serialization overhead. Concurrently, the IPC bridge must be strictly reserved for native OS interactions. This bridge must be implemented via a strictly Typed Proxy Pattern using contextBridge, completely eliminating optional chaining to ensure that unauthorized or missing API calls throw immediate, descriptive errors that can be captured by React Error Boundaries.

### **Architecture Diagram**

Code snippet

flowchart LR  
    subgraph Renderer Process (React GUI)  
        UI\[User Interface\]  
        Query  
        Context  
    end

    subgraph Main Process (Electron Node.js)  
        OSNative  
        Dialogs  
        TrayAPI  
    end

    subgraph Daemon Process (Python FastAPI)  
        REST  
        SQL  
        MCP  
    end

    %% Data flow mapping enforcing strict boundaries  
    UI \--\> Query  
    Query \--\>|Domain Data via HTTP:8765| REST  
    REST \--\> SQL  
    REST \--\> MCP

    UI \--\> Context  
    Context \--\>|System Commands via Strict IPC| OSNative  
    OSNative \--\> Dialogs  
    OSNative \--\> TrayAPI

### **Code Sketch**

TypeScript

// preload.ts \- Executed in isolated context before the untrusted renderer loads  
import { contextBridge, ipcRenderer } from 'electron';

// Explicitly define the allowed capabilities, creating a highly restricted API surface  
const electronBridge \= {  
  window: {  
    minimize: () \=\> ipcRenderer.send('window-minimize'),  
    hideToTray: () \=\> ipcRenderer.send('window-hide'),  
  },  
  system: {  
    // Utilizes invoke for asynchronous Promise returns from the main process  
    getSecureCredential: (key: string) \=\> ipcRenderer.invoke('get-credential', key),  
    showOpenDialog: (options: any) \=\> ipcRenderer.invoke('show-open-dialog', options),  
  },  
  events: {  
    onServiceStatusChange: (callback: (status: string) \=\> void) \=\> {  
      // Deliberately stripping the event parameter to prevent IPC object leakage  
      const handler \= (\_event: any, status: string) \=\> callback(status);  
      ipcRenderer.on('service-status-changed', handler);  
      return () \=\> ipcRenderer.removeListener('service-status-changed', handler);  
    }  
  }  
};

// Expose the strictly typed proxy to the window object, freezing the implementation  
contextBridge.exposeInMainWorld('electronAPI', electronBridge);

// types.d.ts \- Ensures the TypeScript compiler enforces the contract within React components  
export type ElectronAPI \= typeof electronBridge;

declare global {  
  interface Window {  
    electronAPI: ElectronAPI;  
  }  
}

### **Trade-Offs**

| Decision Criterion | Option A: Data routed via IPC to Main Process | Option B: Data routed via REST to Localhost | Architectural Implication |
| :---- | :---- | :---- | :---- |
| **Data Fetching Pathway** | Renderer \-\> IPC \-\> Main \-\> REST \-\> Main \-\> IPC \-\> Renderer | Renderer \-\> REST \-\> Renderer | Routing REST calls through the main process via IPC introduces a massive serialization bottleneck. Processing large JSON arrays of trade data will cause the main process to stutter and drop frames. Direct REST calls bypass the Node.js event loop entirely.40 |
| **API Typings & Error Handling** | Optional chaining (e.g., api?.method?.()) | Strict Typed Proxy pattern | Optional chaining masks critical structural failures (e.g., a missing OS permission) by silently returning undefined. A strict proxy throws an explicit error, allowing React Error Boundaries to catch, log, and report the issue accurately.44 |
| **Security (Context Isolation)** | Disabled (Node Integration On) | Enabled (ContextBridge Implementation) | Enabling Node integration directly in the renderer exposes the entire system to XSS attacks. Utilizing contextBridge ensures that even if a malicious script renders in the UI, it cannot access the file system or execute arbitrary Node.js operations.44 |

### **Risk Assessment**

The primary structural risk in utilizing direct REST calls from the renderer is the absolute assumption of port availability. If the Python daemon fails to bind to port 8765 upon launch due to port exhaustion or a zombie process holding the bind, the entire web interface will encounter persistent CORS or ECONNREFUSED errors, entirely paralyzing the application interface.

To structurally mitigate this risk, the application initialization sequence must rely heavily on the Electron main process to verify port binding before loading the web content into the view. Furthermore, the REST client initialized in the React layer (e.g., the global Axios or Fetch instance) must implement a robust global interceptor. If a network request fails with a severe connection error, the interceptor must trigger the ContextBridge proxy to alert the main process (e.g., via a window.electronAPI.system.reportDaemonCrash() call). This interceptor mechanism allows the Electron shell to gracefully intervene from the outside, overriding the broken React render tree and overlaying the native disconnection UI across the main window to inform the user of the critical systemic failure.3

#### **Works cited**

1. Tray Menu \- Electron, accessed April 18, 2026, [https://electronjs.org/docs/latest/tutorial/tray](https://electronjs.org/docs/latest/tutorial/tray)  
2. Building a Health-Check Microservice with FastAPI \- DEV Community, accessed April 18, 2026, [https://dev.to/lisan\_al\_gaib/building-a-health-check-microservice-with-fastapi-26jo](https://dev.to/lisan_al_gaib/building-a-health-check-microservice-with-fastapi-26jo)  
3. I systemd: Running a splash screen, shutting down screens and an IoT service with Python on Raspberry Pi | by Melissa Coleman | Made by Many | Medium, accessed April 18, 2026, [https://medium.com/the-many/fun-with-systemd-running-a-splash-screen-shutting-down-screens-and-an-iot-service-with-python-on-dd51f790444f?responsesOpen=true\&sortBy=REVERSE\_CHRON](https://medium.com/the-many/fun-with-systemd-running-a-splash-screen-shutting-down-screens-and-an-iot-service-with-python-on-dd51f790444f?responsesOpen=true&sortBy=REVERSE_CHRON)  
4. Tray | Electron, accessed April 18, 2026, [https://electronjs.org/docs/latest/api/tray](https://electronjs.org/docs/latest/api/tray)  
5. Innovation in Disconnected Networks: How We Streamline Apps with Electron.js | by Natalie Tan | CSIT tech blog | Jan, 2026 | Medium, accessed April 18, 2026, [https://medium.com/csit-tech-blog/innovation-in-disconnected-networks-how-we-streamline-apps-with-electron-js-0d1c93e9ec00](https://medium.com/csit-tech-blog/innovation-in-disconnected-networks-how-we-streamline-apps-with-electron-js-0d1c93e9ec00)  
6. Question regarding detaching · Issue \#8 · SnosMe/electron-overlay-window \- GitHub, accessed April 18, 2026, [https://github.com/SnosMe/electron-overlay-window/issues/8](https://github.com/SnosMe/electron-overlay-window/issues/8)  
7. Creating multi-window Electron apps using React portals, accessed April 18, 2026, [https://pietrasiak.com/creating-multi-window-electron-apps-using-react-portals](https://pietrasiak.com/creating-multi-window-electron-apps-using-react-portals)  
8. Electron Desktop App Development Guide for Business in 2026 | by Fora Soft \- Medium, accessed April 18, 2026, [https://forasoft.medium.com/electron-desktop-app-development-guide-for-business-in-2026-e75e439fe9d4](https://forasoft.medium.com/electron-desktop-app-development-guide-for-business-in-2026-e75e439fe9d4)  
9. Window Customization | Electron, accessed April 18, 2026, [https://electronjs.org/docs/latest/tutorial/window-customization](https://electronjs.org/docs/latest/tutorial/window-customization)  
10. Here's the thing. You know what the alternative to all of these Electron apps co... \- Hacker News, accessed April 18, 2026, [https://news.ycombinator.com/item?id=14088209](https://news.ycombinator.com/item?id=14088209)  
11. Use the browser Fetch API from the main process in Electron \- GitHub, accessed April 18, 2026, [https://github.com/sindresorhus/electron-main-fetch](https://github.com/sindresorhus/electron-main-fetch)  
12. Mastering Zustand — The Modern React State Manager (v4 & v5 Guide) \- DEV Community, accessed April 18, 2026, [https://dev.to/vishwark/mastering-zustand-the-modern-react-state-manager-v4-v5-guide-8mm](https://dev.to/vishwark/mastering-zustand-the-modern-react-state-manager-v4-v5-guide-8mm)  
13. How to Implement Encryption with SQLCipher \- OneUptime, accessed April 18, 2026, [https://oneuptime.com/blog/post/2026-02-02-sqlcipher-encryption/view](https://oneuptime.com/blog/post/2026-02-02-sqlcipher-encryption/view)  
14. Zustand Middleware: The Architectural Core of Scalable State Management \- Ram Krishnan, accessed April 18, 2026, [https://beyondthecode.medium.com/zustand-middleware-the-architectural-core-of-scalable-state-management-d8d1053489ac](https://beyondthecode.medium.com/zustand-middleware-the-architectural-core-of-scalable-state-management-d8d1053489ac)  
15. Optimistic Updates | TanStack Query React Docs, accessed April 18, 2026, [https://tanstack.com/query/v5/docs/framework/react/guides/optimistic-updates](https://tanstack.com/query/v5/docs/framework/react/guides/optimistic-updates)  
16. Building Lightning-Fast UIs: Implementing Optimistic Updates with React Query and Zustand, accessed April 18, 2026, [https://medium.com/@anshulkahar2211/building-lightning-fast-uis-implementing-optimistic-updates-with-react-query-and-zustand-cfb7f9e7cd82](https://medium.com/@anshulkahar2211/building-lightning-fast-uis-implementing-optimistic-updates-with-react-query-and-zustand-cfb7f9e7cd82)  
17. Implementing Optimistic UI Updates in React: A Deep Dive \- JavaScript in Plain English, accessed April 18, 2026, [https://javascript.plainenglish.io/implementing-optimistic-ui-updates-in-react-a-deep-dive-2f4d91e2b1a4](https://javascript.plainenglish.io/implementing-optimistic-ui-updates-in-react-a-deep-dive-2f4d91e2b1a4)  
18. Automatic Rollback Data in Optimistic Updates: A surprising benefit of Normalized Data, accessed April 18, 2026, [https://dev.to/klis87/automatic-rollback-data-in-optimistic-updates-a-surprising-benefit-of-normalized-data-535l](https://dev.to/klis87/automatic-rollback-data-in-optimistic-updates-a-surprising-benefit-of-normalized-data-535l)  
19. Best way to run a migration on first persist? · pmndrs zustand · Discussion \#1717 \- GitHub, accessed April 18, 2026, [https://github.com/pmndrs/zustand/discussions/1717](https://github.com/pmndrs/zustand/discussions/1717)  
20. How to Migrate to v5 from v4 \- Zustand, accessed April 18, 2026, [https://zustand.docs.pmnd.rs/reference/migrations/migrating-to-v5](https://zustand.docs.pmnd.rs/reference/migrations/migrating-to-v5)  
21. How to properly use optimistic updates to create an offline app? · TanStack query · Discussion \#2597 \- GitHub, accessed April 18, 2026, [https://github.com/TanStack/query/discussions/2597](https://github.com/TanStack/query/discussions/2597)  
22. State Management Patterns \- DEV Community, accessed April 18, 2026, [https://dev.to/thesius\_code\_7a136ae718b7/state-management-patterns-3d2m](https://dev.to/thesius_code_7a136ae718b7/state-management-patterns-3d2m)  
23. What are the trade-offs between real-time and batch indexing? \- Milvus, accessed April 18, 2026, [https://milvus.io/ai-quick-reference/what-are-the-tradeoffs-between-realtime-and-batch-indexing](https://milvus.io/ai-quick-reference/what-are-the-tradeoffs-between-realtime-and-batch-indexing)  
24. HTTP API vs REST API vs Web API: Architectures & How to Monitor Them \- Dotcom-Monitor, accessed April 18, 2026, [https://www.dotcom-monitor.com/blog/http-api-vs-rest-api-vs-web-api/](https://www.dotcom-monitor.com/blog/http-api-vs-rest-api-vs-web-api/)  
25. Unpopular opinion: most "slow" .NET apps don't need microservices, they need someone to look at their queries : r/dotnet \- Reddit, accessed April 18, 2026, [https://www.reddit.com/r/dotnet/comments/1pl0qbx/unpopular\_opinion\_most\_slow\_net\_apps\_dont\_need/](https://www.reddit.com/r/dotnet/comments/1pl0qbx/unpopular_opinion_most_slow_net_apps_dont_need/)  
26. Building a Component Registry in React | by Erasmo Marín | Frontend Weekly | Medium, accessed April 18, 2026, [https://medium.com/front-end-weekly/building-a-component-registry-in-react-4504ca271e56](https://medium.com/front-end-weekly/building-a-component-registry-in-react-4504ca271e56)  
27. Registry Pattern \- Revolutionize Your Object Creation and Management in your applications, accessed April 18, 2026, [https://dev.to/walosha/registry-pattern-revolutionize-your-object-creation-and-management-lms-as-a-case-study-58km](https://dev.to/walosha/registry-pattern-revolutionize-your-object-creation-and-management-lms-as-a-case-study-58km)  
28. React Architecture Pattern and Best Practices \- GeeksforGeeks, accessed April 18, 2026, [https://www.geeksforgeeks.org/reactjs/react-architecture-pattern-and-best-practices/](https://www.geeksforgeeks.org/reactjs/react-architecture-pattern-and-best-practices/)  
29. asabaylus/react-command-palette \- GitHub, accessed April 18, 2026, [https://github.com/asabaylus/react-command-palette](https://github.com/asabaylus/react-command-palette)  
30. Building a Custom Command Palette with React: A Deep Dive into React Portals, Observables, and Event Listeners \- DEV Community, accessed April 18, 2026, [https://dev.to/ashutoshsarangi/building-a-custom-command-palette-with-react-a-deep-dive-into-react-portals-observables-and-event-listeners-4kjm](https://dev.to/ashutoshsarangi/building-a-custom-command-palette-with-react-a-deep-dive-into-react-portals-observables-and-event-listeners-4kjm)  
31. SQLCipher API \- Full Database Encryption PRAGMAs, Functions, and Settings \- Zetetic LLC, accessed April 18, 2026, [https://www.zetetic.net/sqlcipher/sqlcipher-api/](https://www.zetetic.net/sqlcipher/sqlcipher-api/)  
32. Password Recovery \- SQLCipher \- Zetetic Community Discussion, accessed April 18, 2026, [https://discuss.zetetic.net/t/password-recovery/2570](https://discuss.zetetic.net/t/password-recovery/2570)  
33. C\# web app, best practice for SQLCipher password management?, accessed April 18, 2026, [https://discuss.zetetic.net/t/c-web-app-best-practice-for-sqlcipher-password-management/5781](https://discuss.zetetic.net/t/c-web-app-best-practice-for-sqlcipher-password-management/5781)  
34. React Form Form Wizard Overview \- KendoReact \- Telerik.com, accessed April 18, 2026, [https://www.telerik.com/kendo-react-ui/components/form/wizard](https://www.telerik.com/kendo-react-ui/components/form/wizard)  
35. Async React: Building Non-Blocking UIs with useTransition and useActionState | Rubrik, accessed April 18, 2026, [https://www.rubrik.com/blog/architecture/26/2/async-react-building-non-blocking-uis-with-usetransition-and-useactionstate](https://www.rubrik.com/blog/architecture/26/2/async-react-building-non-blocking-uis-with-usetransition-and-useactionstate)  
36. WizardForm — multi-step forms powered by a state machine : r/reactjs \- Reddit, accessed April 18, 2026, [https://www.reddit.com/r/reactjs/comments/1ra1f10/wizardform\_multistep\_forms\_powered\_by\_a\_state/](https://www.reddit.com/r/reactjs/comments/1ra1f10/wizardform_multistep_forms_powered_by_a_state/)  
37. Electron app may crash on Windows during startup when interacting with splash screen · Issue \#17328 · eclipse-theia/theia \- GitHub, accessed April 18, 2026, [https://github.com/eclipse-theia/theia/issues/17328](https://github.com/eclipse-theia/theia/issues/17328)  
38. Everytime I boot, electron automatically starts with this screen. How do I stop this? \- Reddit, accessed April 18, 2026, [https://www.reddit.com/r/archlinux/comments/7tubn5/everytime\_i\_boot\_electron\_automatically\_starts/](https://www.reddit.com/r/archlinux/comments/7tubn5/everytime_i_boot_electron_automatically_starts/)  
39. newbreedofgeek/react-stepzilla: A React multi-step/wizard component for sequential data collection \- GitHub, accessed April 18, 2026, [https://github.com/newbreedofgeek/react-stepzilla](https://github.com/newbreedofgeek/react-stepzilla)  
40. Recommended way to consume REST API. : r/electronjs \- Reddit, accessed April 18, 2026, [https://www.reddit.com/r/electronjs/comments/e33u79/recommended\_way\_to\_consume\_rest\_api/](https://www.reddit.com/r/electronjs/comments/e33u79/recommended_way_to_consume_rest_api/)  
41. node.js \- Electron application architecture \- IPC vs API \- Stack Overflow, accessed April 18, 2026, [https://stackoverflow.com/questions/66083746/electron-application-architecture-ipc-vs-api](https://stackoverflow.com/questions/66083746/electron-application-architecture-ipc-vs-api)  
42. Inter-Process Communication \- Electron, accessed April 18, 2026, [https://electronjs.org/docs/latest/tutorial/ipc](https://electronjs.org/docs/latest/tutorial/ipc)  
43. Deep dive into Electron's main and renderer processes | by Cameron Nokes \- Medium, accessed April 18, 2026, [https://medium.com/cameron-nokes/deep-dive-into-electrons-main-and-renderer-processes-7a9599d5c9e2](https://medium.com/cameron-nokes/deep-dive-into-electrons-main-and-renderer-processes-7a9599d5c9e2)  
44. Electron 'contextBridge' \- javascript \- Stack Overflow, accessed April 18, 2026, [https://stackoverflow.com/questions/59993468/electron-contextbridge](https://stackoverflow.com/questions/59993468/electron-contextbridge)  
45. The Context Bridge class in electronjs | Dustin John Pfister at github pages, accessed April 18, 2026, [https://dustinpfister.github.io/2022/02/21/electronjs-context-bridge/](https://dustinpfister.github.io/2022/02/21/electronjs-context-bridge/)  
46. contextBridge \- Electron, accessed April 18, 2026, [https://electronjs.org/docs/latest/api/context-bridge](https://electronjs.org/docs/latest/api/context-bridge)  
47. linonetwo/electron-ipc-cat: Passing object and type between Electron main process and renderer process simply via preload script. \- GitHub, accessed April 18, 2026, [https://github.com/linonetwo/electron-ipc-cat](https://github.com/linonetwo/electron-ipc-cat)  
48. Auto-Completing the Context Bridge w/ TypeScript & Electron \- YouTube, accessed April 18, 2026, [https://www.youtube.com/watch?v=2gNc\_3YyYqk](https://www.youtube.com/watch?v=2gNc_3YyYqk)
