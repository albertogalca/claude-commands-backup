---
name: electron
description: "Architect and build secure, cross-platform Electron desktop apps. Use when designing Electron Main/Renderer architecture, implementing IPC with contextBridge, integrating React, optimizing startup/memory, or packaging with code signing and notarization. Keywords: electron, electron-vite, electron-forge, contextBridge, IPC, security, sandbox, CSP, react, packaging, code signing, notarization, auto-update, playwright, desktop app."
---

# Electron Development Expert

Expert assistant for building secure, performant, cross-platform desktop applications with Electron: Main/Renderer architecture, type-safe IPC, React integration, security hardening, OS-level integration, packaging, code signing/notarization, and testing.

## When to Use

- Designing or scaffolding Electron app architecture (Main/Renderer/preload)
- Implementing secure IPC (Main ↔ Renderer) via contextBridge
- Migrating web apps to desktop with native capabilities (file system, notifications)
- Integrating React (or other SPA frameworks) into the renderer
- Configuring electron-vite / Electron Forge
- Optimizing startup time and memory usage
- Configuring auto-updaters (electron-updater)
- Signing and notarizing apps for distribution / app stores
- Testing Electron apps with Playwright

Do NOT use for: Tauri apps (different paradigm), pure web apps with no desktop needs, or Electron versions below 20 (security defaults differ).

## Thinking Process

Follow this structured approach when designing an Electron app.

### Step 1: Requirements Analysis

- Core functionality? (editor, dashboard, utility, media)
- System resources needed? (file system, network, hardware)
- Target platforms? (macOS, Windows, Linux, or all)
- Offline requirements?
- Data sensitivity? (local files, credentials, user data)

Then: list features needing system access, identify interaction patterns (single/multi-window, tray), determine persistence needs, map integration points. You should be able to state: "This app needs [X] system resources", "main flows are [Y]", "security sensitivity is [Z]".

### Step 2: Architecture Design (Security First)

Principles: **Least Privilege** (renderer has minimal capabilities), **Defense in Depth** (multiple protection layers), **Explicit Communication** (all IPC channels explicit and validated).

| Capability Needed   | Where to Implement     | Security Consideration              |
|---------------------|------------------------|-------------------------------------|
| UI Rendering        | Renderer process       | Treat as untrusted (like a browser) |
| File system access  | Main process           | Expose via validated IPC            |
| Network requests    | Main process preferred | Avoid renderer CORS issues          |
| Native dialogs      | Main process           | User consent for file access        |
| Crypto operations   | Main process           | Protect keys from renderer          |
| Shell commands      | Main process only      | Never expose to renderer            |

For each feature ask: "Does this need Main process access?" and "What is the minimal IPC surface needed?"

### Step 3: IPC Design

Ask: what data flows between Main and Renderer, who initiates, what validation each end needs.

| Communication Need | Pattern            | Direction      |
|--------------------|--------------------|----------------|
| Request/response   | invoke/handle      | Renderer → Main |
| Fire and forget    | send               | Renderer → Main |
| Push notification  | webContents.send   | Main → Renderer |
| Two-way stream     | MessagePort        | Bidirectional   |

IPC security checklist:
- [ ] All channels have explicit names
- [ ] Input validation on Main process handlers
- [ ] No arbitrary code execution from renderer input
- [ ] Sensitive operations require user confirmation
- [ ] Rate limiting for expensive operations

### Step 4: Preload Script Design

Ask: "What is the absolute minimum the renderer needs? Am I exposing more than necessary? Is each exposed function validated?"

Principles: minimal surface, no raw IPC (wrap `ipcRenderer`, never expose it), provide TypeScript types, prefer `invoke` over `send`/`on` pairs.

### Step 5: Window Management

| App Type            | Pattern                                |
|---------------------|----------------------------------------|
| Single document     | One main window                        |
| Multi-document      | Window per document, shared state in Main |
| Dashboard + details | Parent-child windows                   |
| System utility      | Tray app with hidden/popup window      |

Checklist: appropriate `webPreferences` per window, window state persistence (position/size), proper close/quit behavior (hide vs destroy), deep linking / protocol handling.

### Step 6: Data Persistence

| Data Type        | Solution                | Security              |
|------------------|-------------------------|-----------------------|
| User preferences | electron-store          | Plain or encrypted    |
| Structured data  | SQLite (better-sqlite3, in Main) | File-level encryption |
| Large files      | File system             | OS-level permissions  |
| Credentials      | System keychain (keytar)| OS secure storage     |

Checklist: encrypt sensitive data at rest, credentials in keychain not files, backup/export, migration strategy for updates.

### Step 7: Packaging & Distribution — see [Packaging & Distribution](#packaging--distribution).

### Step 8: Testing — see [Testing](#testing).

## Core Principles

### 1. Security First Architecture

Modern Electron security relies on three defaults standard since Electron 20+: **context isolation**, **sandbox mode**, and **nodeIntegration disabled**. Disabling any allows XSS to escalate to full remote code execution. All Main-Renderer communication must flow through contextBridge.

**Decision flow:**
- Context Isolation? → **Yes** (standard since v12)
- Node Integration? → **No** (never in renderer)
- Preload Scripts? → **Yes** (bridge API)

**Red flags (escalate to a security audit):**
- `nodeIntegration: true` in production
- Disabling `contextIsolation`
- Loading remote content (`https://`) without a strict CSP
- Using the deprecated `remote` module
- Binding a local server to `0.0.0.0` instead of `127.0.0.1`

Set a Content Security Policy via HTTP headers for apps loading local files, restricting script sources to `'self'`.

### 2. Type-Safe IPC

The invoke/handle pattern is preferred over send/on for request-response, giving proper async/await semantics and error propagation. For typed channels use a mapped type:

```typescript
type IpcChannelMap = {
  'load-prefs': { args: []; return: UserPreferences };
  'save-file': { args: [content: string]; return: { success: boolean } };
};
```

For complex apps, electron-trpc provides full type safety via tRPC's router pattern with Zod validation:

```typescript
export const appRouter = t.router({
  greeting: t.procedure
    .input(z.object({ name: z.string() }))
    .query(({ input }) => `Hello, ${input.name}!`),
});
```

Electron only serializes the `message` property of Error objects across the IPC boundary. Wrap responses in a `{ success, data, error }` result type to preserve full error context.

### 3. Modern Project Setup

Recommended stack: **electron-vite** for development (unified config for main/preload/renderer, sub-second dev server, instant HMR) and **Electron Forge** for packaging (first-party signing/notarization). Bundle the Main process (esbuild/webpack), not just the renderer.

## Project Structure

```
src/
├── main/                    # Main process (Node.js environment)
│   ├── index.ts             # Main process entry
│   ├── ipc/                 # IPC handlers
│   │   └── file-handlers.ts
│   ├── services/            # Backend services (e.g. database.ts)
│   └── menu.ts              # Application menu
├── preload/
│   ├── index.ts             # Context bridge
│   └── index.d.ts           # TypeScript declarations for exposed APIs
├── renderer/                # React/Svelte/Vue app (pure web, no Node access)
│   ├── src/ (App.tsx, components/)
│   └── index.html
└── shared/
    └── types.ts             # Shared type definitions
```

## Security & IPC

### BrowserWindow Configuration

```typescript
const win = new BrowserWindow({
  width: 1200,
  height: 800,
  webPreferences: {
    preload: path.join(__dirname, '../preload/index.js'),
    contextIsolation: true,   // Enable context isolation
    sandbox: true,            // Sandbox mode
    nodeIntegration: false,   // Disable Node.js in renderer
    webSecurity: true,        // Enforce same-origin
  },
});
```

Always enable contextIsolation and sandbox; never enable nodeIntegration. The preload path must resolve to the built output location.

### Preload Script (contextBridge)

```typescript
// preload.ts - SECURE pattern
import { contextBridge, ipcRenderer, IpcRendererEvent } from 'electron';

contextBridge.exposeInMainWorld('electronAPI', {
  // Request-response: Renderer → Main
  openFile: () => ipcRenderer.invoke('dialog:openFile'),
  saveFile: (content: string) => ipcRenderer.invoke('file:save', content),
  loadPreferences: () => ipcRenderer.invoke('load-prefs'),

  // Subscription: Main → Renderer (returns cleanup fn)
  onUpdateCounter: (callback: (value: number) => void) => {
    const handler = (_event: IpcRendererEvent, value: number) => callback(value);
    ipcRenderer.on('update-counter', handler);
    return () => ipcRenderer.removeListener('update-counter', handler);
  },
});

// Type declaration for the renderer
declare global {
  interface Window {
    electronAPI: {
      openFile: () => Promise<string | null>;
      saveFile: (content: string) => Promise<boolean>;
      loadPreferences: () => Promise<UserPreferences>;
      onUpdateCounter: (cb: (value: number) => void) => () => void;
    };
  }
}
```

**Anti-patterns to avoid:**

```typescript
// BAD: exposes raw ipcRenderer
contextBridge.exposeInMainWorld('electron', { ipcRenderer });

// BAD: arbitrary channel execution
contextBridge.exposeInMainWorld('api', {
  send: (channel, data) => ipcRenderer.send(channel, data),
});

// GOOD: explicit, limited API
contextBridge.exposeInMainWorld('api', {
  openFile: () => ipcRenderer.invoke('dialog:openFile'),
  saveFile: (content: string) => ipcRenderer.invoke('file:save', content),
});
```

### Main Process IPC Handlers

Group related handlers into modules. Use the result type for all returns. Validate every argument received from the renderer (Zod or manual checks).

```typescript
// main/ipc/file-handlers.ts
import { ipcMain, dialog } from 'electron';
import { readFile, writeFile } from 'fs/promises';

export function registerFileHandlers(): void {
  ipcMain.handle('dialog:openFile', async () => {
    const { canceled, filePaths } = await dialog.showOpenDialog({
      properties: ['openFile'],
      filters: [{ name: 'Text', extensions: ['txt', 'md'] }],
    });
    if (canceled) return null;
    return readFile(filePaths[0], 'utf-8');
  });

  ipcMain.handle('file:save', async (_event, content: string) => {
    try {
      const { canceled, filePath } = await dialog.showSaveDialog({});
      if (canceled || !filePath) return { success: false };
      await writeFile(filePath, content);
      return { success: true, data: filePath };
    } catch (err) {
      return { success: false, error: (err as Error).message };
    }
  });
}
```

### Deep Linking (Protocol Handler)

Opening the app from a browser (`myapp://open?id=123`):

```typescript
// main.ts
if (process.defaultApp) {
  if (process.argv.length >= 2) {
    app.setAsDefaultProtocolClient('myapp', process.execPath, [path.resolve(process.argv[1])]);
  }
} else {
  app.setAsDefaultProtocolClient('myapp');
}

app.on('open-url', (event, url) => {
  event.preventDefault();
  mainWindow.webContents.send('navigate', url); // parse 'myapp://...' and navigate
});
```

### IPC Patterns Summary

| Pattern                         | Method               | Use Case                                        |
|---------------------------------|----------------------|-------------------------------------------------|
| One-Way (Renderer → Main)       | `ipcRenderer.send`   | logging, analytics, minimizing window           |
| Two-Way (request/response)      | `ipcRenderer.invoke` | DB queries, file reads, heavy computations      |
| Main → Renderer                 | `webContents.send`   | menu actions, system events, push notifications |

## React Integration

React 18 concurrent features work normally in Electron's Chromium renderer. Strict Mode's double-invocation of effects catches IPC listener leaks. Always return cleanup from effects that register IPC listeners:

```typescript
useEffect(() => {
  const cleanup = window.electronAPI.onUpdateCounter((value) => setCount(value));
  return cleanup;
}, []);
```

For multi-window apps, the **Main process is the single source of truth** for shared state. Use electron-store for persistence plus IPC broadcasting so any window's mutation updates all others. Prefer Zustand + electron-store over Redux for simple apps.

**Frontend handoff:** UI dev builds the React/Vue app → it gets wrapped by Electron. Custom title bars use CSS `app-region: drag`; consider vibrancy/acrylic effects.

## Performance

**Goal: launch < 2s.**

1. **V8 snapshot** — use `electron-link` or `v8-compile-cache` to pre-compile JS.
2. **Lazy load modules** — don't `require()` everything at the top of `main.ts`:
   ```javascript
   // Bad
   import { heavyLib } from 'heavy-lib';
   // Good
   ipcMain.handle('do-work', () => {
     const heavyLib = require('heavy-lib');
     heavyLib.process();
   });
   ```
3. **Bundle the Main process** — use esbuild/webpack on Main (not just renderer) to tree-shake and minify.

**Worker threads for CPU-intensive tasks** (image processing, large parsing) keep the UI responsive:

```typescript
// main.ts
import { Worker } from 'worker_threads';

ipcMain.handle('process-image', (event, data) => {
  return new Promise((resolve, reject) => {
    const worker = new Worker('./worker.js', { workerData: data });
    worker.on('message', resolve);
    worker.on('error', reject);
  });
});
```

## Packaging & Distribution

| Platform | Signing                          | Distribution                       |
|----------|----------------------------------|------------------------------------|
| macOS    | Developer ID + Notarization      | DMG, PKG, or Mac App Store         |
| Windows  | Code signing certificate (EV)    | NSIS, MSI, or Microsoft Store      |
| Linux    | Optional GPG                     | AppImage, deb, rpm, Snap           |

Prefer **Electron Forge** (first-party signing/notarization) over manual packaging. Integrate code signing into CI; never ship unsigned releases (OS warnings, Gatekeeper blocks).

**Electron Forge config example:**

```json
{
  "config": {
    "forge": {
      "packagerConfig": { "asar": true, "icon": "./assets/icon" },
      "makers": [
        { "name": "@electron-forge/maker-squirrel" },
        { "name": "@electron-forge/maker-dmg" },
        { "name": "@electron-forge/maker-deb" }
      ]
    }
  }
}
```

**Auto-update strategy:** use `electron-updater` (avoid manual update checks). Configure an update server (GitHub releases, S3), use staged rollouts for critical updates, and keep rollback capability.

**DevOps handoff:** Electron dev provides build config → DevOps sets up CI; code signing certs (Apple Developer ID, Windows EV); Electron Builder / notarization scripts.

## Testing

| Layer        | Approach                                            |
|--------------|----------------------------------------------------|
| Unit         | Business logic in Main process (Jest/Vitest)       |
| Integration  | IPC communication; test handlers in isolation      |
| E2E          | **Playwright** (Spectron is deprecated, Electron 13 max) |
| Platform     | CI matrix across all target platforms              |

Checklist: test IPC handlers in isolation, test preload type contracts, E2E for critical flows, platform-specific behavior tests.

## Quick Reference

| Category        | Prefer                              | Avoid                               |
|-----------------|-------------------------------------|-------------------------------------|
| Security        | `contextBridge.exposeInMainWorld()` | `nodeIntegration: true`             |
| IPC             | `invoke/handle` pattern             | `send/on` for request-response      |
| Preload         | Typed function wrappers             | Exposing raw `ipcRenderer`          |
| Build tool      | electron-vite                       | webpack-based toolchains            |
| Packaging       | Electron Forge                      | Manual packaging                    |
| State           | Zustand + electron-store            | Redux for simple apps               |
| Testing         | Playwright E2E                      | Spectron (deprecated)               |
| Updates         | electron-updater                    | Manual update checks                |
| Signing         | CI-integrated code signing          | Unsigned releases                   |
| CSP             | HTTP headers, `'self'` only         | No CSP                              |
| Error handling  | Result type `{success, data, error}`| Raw Error across IPC                |
| Multi-window    | Main process as state hub           | Direct window-to-window             |
| Server binding  | `127.0.0.1`                         | `0.0.0.0`                           |

## Scripts

### scaffold-electron-app.ts (Electron + React, secure defaults)

```bash
deno run --allow-read --allow-write scripts/scaffold-electron-app.ts --name "my-app" --with-react
# Full: add --with-trpc --with-tests
# Options: --name (required), --path (default ./), --with-react, --with-trpc, --with-tests
```

### scaffold-project.sh (vanilla/react/svelte/vue, configurable package manager)

```bash
bash scripts/scaffold-project.sh [project-name] [ui-framework] [package-manager]
# ui-framework: vanilla|react|svelte|vue (default vanilla)
# package-manager: pnpm|npm|yarn (default pnpm)
# Security defaults: nodeIntegration false, contextIsolation true, sandbox true
```

### analyze-security.ts (audit for misconfigurations)

```bash
deno run --allow-read scripts/analyze-security.ts <path> [--strict] [--json]
# e.g. CI: deno run --allow-read scripts/analyze-security.ts ./src --strict --json
```

### generate-ipc-types.ts (TS types from IPC handlers)

```bash
deno run --allow-read --allow-write scripts/generate-ipc-types.ts \
  --handlers ./src/main/ipc --output ./src/preload/ipc-types.d.ts
# Validate in CI: add --validate (read-only)
```

## Additional Resources

### Security
- `references/security/context-isolation.md` — contextBridge and isolation patterns
- `references/security/csp-and-permissions.md` — Content Security Policy configuration
- `references/security/security-checklist.md` — full security audit checklist

### IPC Communication
- `references/ipc/typed-ipc.md` — typed channel map patterns
- `references/ipc/electron-trpc.md` — tRPC integration for full type safety
- `references/ipc/error-serialization.md` — result types across the IPC boundary

### Architecture
- `references/architecture/project-structure.md` — directory organization
- `references/architecture/process-separation.md` — Main, preload, and renderer roles
- `references/architecture/multi-window-state.md` — shared state across windows

### React Integration
- `references/integration/react-patterns.md` — useEffect cleanup, Strict Mode
- `references/integration/state-management.md` — Zustand and electron-store patterns

### Packaging & Distribution
- `references/packaging/code-signing.md` — platform-specific signing workflows
- `references/packaging/auto-updates.md` — electron-updater configuration
- `references/packaging/bundle-optimization.md` — size reduction techniques
- `references/packaging/ci-cd-patterns.md` — GitHub Actions matrix builds

### Testing
- `references/testing/playwright-e2e.md` — Playwright Electron support
- `references/testing/unit-testing.md` — Jest/Vitest multi-project configuration
- `references/testing/test-structure.md` — test organization patterns

### Tooling
- `references/tooling/electron-vite.md` — build tool configuration
- `references/tooling/electron-forge.md` — packaging and distribution
- `references/tooling/tauri-comparison.md` — when to choose Tauri instead

### Templates & Configs (under `assets/`)
- `assets/templates/` — main-process, preload-script, ipc-handler, react-root starters
- `assets/configs/` — electron-vite, forge, tsconfig, playwright config examples
- `assets/examples/` — typed-ipc and multi-window end-to-end walkthroughs

**Official docs:** Electron `https://www.electronjs.org/docs/latest/` · Electron Forge `https://www.electronforge.io/` · electron-builder `https://www.electron.build/`

## Troubleshooting

**"require is not defined"** — nodeIntegration is correctly disabled; use a preload script with contextBridge.

**"Cannot access window.electronAPI"** — check the preload path, verify contextIsolation is true, ensure `contextBridge.exposeInMainWorld` is called.

**"IPC message not received"** — verify channel names match exactly, ensure the handler is registered before the window loads, use `invoke` for async responses.
