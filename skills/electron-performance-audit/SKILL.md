---
name: electron-performance-audit
description: 'Automated performance audit for Electron apps. Covers startup, main thread blocking, IPC, memory leaks, perceived performance, and native code opportunities. Triggers: "electron performance audit", "electron performance scan", "check electron performance".'
license: MIT
metadata:
  tier: execution
  category: analysis
---

# Electron Performance Audit

> **Quick Ref:** Automated performance scan for Electron apps. Output: `.agents/research/YYYY-MM-DD-electron-performance-audit.md`

**YOU MUST EXECUTE THIS WORKFLOW. Do not just describe it.**

All findings use the **Issue Rating Table** format. Do not use prose severity tags.

---

## Pre-flight: Git Safety Check

```bash
git status --short
```

If uncommitted changes exist:

```
AskUserQuestion with questions:
[
  {
    "question": "You have uncommitted changes. Commit before proceeding?",
    "header": "Git",
    "options": [
      {"label": "Commit first (Recommended)", "description": "Save current work so you can revert if this skill modifies files"},
      {"label": "Continue without committing", "description": "Proceed — I accept the risk"}
    ],
    "multiSelect": false
  }
]
```

If "Commit first": Ask for a commit message, stage changed files, and commit. Then proceed.

---

## Step 1: Scope Selection

```
AskUserQuestion with questions:
[
  {
    "question": "What type of performance audit do you want?",
    "header": "Scope",
    "options": [
      {"label": "Full audit (Recommended)", "description": "All categories: startup, main thread, IPC, memory, perceived performance, native code"},
      {"label": "Quick scan", "description": "Startup + main thread blocking only — highest-impact categories"},
      {"label": "Focused audit", "description": "I'll specify which categories to scan"}
    ],
    "multiSelect": false
  }
]
```

If "Focused audit", ask which categories:

```
AskUserQuestion with questions:
[
  {
    "question": "Which performance categories should I scan?",
    "header": "Focus",
    "options": [
      {"label": "Startup Performance", "description": "Lazy loading, code splitting, bundle size, Chromium flags"},
      {"label": "Main Thread Blocking", "description": "Sync operations, heavy computation, blocking IPC"},
      {"label": "IPC Patterns", "description": "Sync IPC, chatty IPC, large payloads"},
      {"label": "Memory & Resource Leaks", "description": "Event listeners, timers, child processes, cache bloat"},
      {"label": "Perceived Performance", "description": "Optimistic updates, prefetching, transitions, pre-warming"},
      {"label": "Native Code Opportunities", "description": "CPU-bound work that could use native bindings or WASM"}
    ],
    "multiSelect": true
  }
]
```

### Freshness

Base all findings on current source code only. Do not read or reference
files in `.agents/`, `scratch/`, or prior audit reports. Ignore cached
findings from auto-memory or previous sessions. Every finding must come
from scanning the actual codebase as it exists now.

---

## Step 2: Automated Scanning

Run patterns for each enabled category. **Quick scan** runs only 2.1 and 2.2. **Full audit** runs all sections.

Every grep hit is a CANDIDATE — verify by reading the file before reporting (see Step 3).

### 2.1 Startup Performance

```bash
# Large synchronous requires at top level (should be dynamic imports)
Grep pattern="^(const|let|var)\s+.+=\s+require\(" glob="**/main.{js,ts,mjs,cjs}" output_mode="content"
Grep pattern="^import\s+" glob="**/main.{js,ts,mjs,cjs}" output_mode="content"

# Missing code splitting — no dynamic imports anywhere
Grep pattern="import\(" glob="**/*.{js,ts,jsx,tsx}" output_mode="count"

# Heavy dependencies loaded eagerly (check if these are dynamically imported)
Grep pattern="require\(['\"](sharp|canvas|pdf-|ffmpeg|sqlite|better-sqlite)" glob="**/*.{js,ts}" -i

# Chromium flags — check if unused features are disabled
Grep pattern="app\.commandLine\.appendSwitch" glob="**/*.{js,ts}" output_mode="content"

# BrowserWindow show-before-ready (causes white flash)
# FALSE POSITIVE: if show:false is set and window.show() is called on ready-to-show
Grep pattern="new BrowserWindow" glob="**/*.{js,ts}" output_mode="content"
Grep pattern="ready-to-show" glob="**/*.{js,ts}" output_mode="files_with_matches"

# Preload scripts — check size and complexity
Glob pattern="**/preload.{js,ts,mjs,cjs}"

# Check bundle size if webpack/vite config exists
Glob pattern="**/webpack.config.{js,ts,mjs}"
Glob pattern="**/vite.config.{js,ts,mjs}"
Glob pattern="**/electron-builder.{yml,json,js}"
```

**Common false positives:**

- `require()` in config files or build scripts — not runtime code
- Imports in test files — not shipped to users
- `import()` in build tool configs — not dynamic splitting

### 2.2 Main Thread Blocking

```bash
# Synchronous fs operations (should be async)
Grep pattern="(readFileSync|writeFileSync|mkdirSync|readdirSync|statSync|existsSync|accessSync|copyFileSync|renameSync|unlinkSync|appendFileSync)" glob="**/*.{js,ts}" output_mode="content"
# FALSE POSITIVE: existsSync in startup config check may be acceptable

# Synchronous child_process calls
Grep pattern="(execSync|execFileSync|spawnSync)" glob="**/*.{js,ts}"

# Synchronous IPC (CRITICAL anti-pattern)
Grep pattern="ipcRenderer\.sendSync" glob="**/*.{js,ts,jsx,tsx}"
Grep pattern="\.sendSync\(" glob="**/*.{js,ts,jsx,tsx}"

# Heavy computation without Worker Threads
# Look for tight loops, JSON.parse of large data, crypto operations
Grep pattern="JSON\.parse\(" glob="**/*.{js,ts,jsx,tsx}" output_mode="content"
Grep pattern="for\s*\(.*;\s*.*<\s*\w+\.length" glob="**/*.{js,ts}" output_mode="content"

# Synchronous dialog calls (block main process)
Grep pattern="dialog\.showMessageBoxSync|dialog\.showOpenDialogSync|dialog\.showSaveDialogSync" glob="**/*.{js,ts}"

# Blocking the renderer with synchronous operations wrapped in Promises
# Anti-pattern: await new Promise((resolve) => { heavySync(); resolve(); })
Grep pattern="new Promise.*resolve.*\n.*Sync" glob="**/*.{js,ts}" multiline=true
```

**Common false positives:**

- `existsSync` for quick file existence check at startup — often acceptable
- `JSON.parse` on small config objects — not a performance issue
- Loops in test files — not production code

### 2.3 IPC Patterns

```bash
# Synchronous IPC (already covered in 2.2, but critical enough to double-check)
Grep pattern="sendSync" glob="**/*.{js,ts,jsx,tsx}"

# Chatty IPC — multiple rapid-fire IPC calls that should be batched
# Look for multiple ipcRenderer.invoke/send calls in the same function
Grep pattern="ipcRenderer\.(invoke|send)\(" glob="**/*.{js,ts,jsx,tsx}" output_mode="content"
Grep pattern="ipcMain\.(handle|on)\(" glob="**/*.{js,ts}" output_mode="content"

# Large data over IPC (should use SharedArrayBuffer or file-based transfer)
# Read flagged files to check payload sizes
Grep pattern="(webContents\.send|ipcRenderer\.send)\(" glob="**/*.{js,ts,jsx,tsx}" output_mode="content"

# Missing error handling on IPC invoke
Grep pattern="ipcRenderer\.invoke\(" glob="**/*.{js,ts,jsx,tsx}" output_mode="content"

# IPC handlers that do heavy work (should offload to worker)
Grep pattern="ipcMain\.handle\(" glob="**/*.{js,ts}" output_mode="content"
```

### 2.4 Memory & Resource Leaks

```bash
# Event listeners without cleanup
Grep pattern="addEventListener\(" glob="**/*.{js,ts,jsx,tsx}" output_mode="content"
Grep pattern="removeEventListener\(" glob="**/*.{js,ts,jsx,tsx}" output_mode="count"

# IPC listeners without cleanup
Grep pattern="ipcRenderer\.on\(" glob="**/*.{js,ts,jsx,tsx}" output_mode="content"
Grep pattern="ipcRenderer\.removeListener\(" glob="**/*.{js,ts,jsx,tsx}" output_mode="count"

# setInterval without clearInterval
Grep pattern="setInterval\(" glob="**/*.{js,ts,jsx,tsx}" output_mode="content"
Grep pattern="clearInterval\(" glob="**/*.{js,ts,jsx,tsx}" output_mode="count"

# setTimeout without clearTimeout (less critical but check for recursive patterns)
Grep pattern="setTimeout\(" glob="**/*.{js,ts,jsx,tsx}" output_mode="count"

# Unclosed resources — DB connections, file handles, child processes
Grep pattern="(spawn|fork|exec)\(" glob="**/*.{js,ts}" output_mode="content"
Grep pattern="\.kill\(" glob="**/*.{js,ts}" output_mode="count"

# React useEffect without cleanup
Grep pattern="useEffect\(\s*\(\)\s*=>\s*\{" glob="**/*.{jsx,tsx}" output_mode="content"

# BrowserWindow/BrowserView not destroyed
Grep pattern="new BrowserWindow\(|new BrowserView\(" glob="**/*.{js,ts}" output_mode="content"
Grep pattern="\.destroy\(\)" glob="**/*.{js,ts}" output_mode="count"

# Cache without expiration
Grep pattern="(Map|Set|WeakMap|cache|Cache)\b" glob="**/*.{js,ts,jsx,tsx}" output_mode="content"

# No handling of system events (suspend, resume, network changes)
Grep pattern="powerMonitor" glob="**/*.{js,ts}" output_mode="files_with_matches"
Grep pattern="(suspend|resume|lock-screen|unlock-screen)" glob="**/*.{js,ts}" output_mode="files_with_matches"
```

**Common false positives:**

- `addEventListener` in React components with proper `useEffect` cleanup
- `setInterval` with corresponding `clearInterval` in cleanup
- `spawn` in build scripts, not runtime code

### 2.5 Perceived Performance

```bash
# No loading states — immediate render without skeleton/placeholder
Grep pattern="(Skeleton|skeleton|Spinner|spinner|Loading|loading)" glob="**/*.{jsx,tsx}" output_mode="files_with_matches"

# No optimistic updates
Grep pattern="(useOptimistic|optimistic)" glob="**/*.{jsx,tsx}" output_mode="files_with_matches"

# No transitions for non-urgent updates
Grep pattern="(startTransition|useTransition)" glob="**/*.{jsx,tsx}" output_mode="files_with_matches"

# No prefetching or pre-warming
Grep pattern="(prefetch|preload|pre-warm|prewarm)" glob="**/*.{js,ts,jsx,tsx}" output_mode="files_with_matches"

# No local data persistence for instant startup
Grep pattern="(electron-store|IndexedDB|sqlite|better-sqlite3|localForage)" glob="**/*.{js,ts,jsx,tsx}" output_mode="files_with_matches"

# Window focus/blur handling (should pause background work)
Grep pattern="(visibilitychange|document\.hidden|window\.blur|window\.focus)" glob="**/*.{js,ts,jsx,tsx}" output_mode="files_with_matches"

# requestIdleCallback usage for non-critical work
Grep pattern="requestIdleCallback" glob="**/*.{js,ts,jsx,tsx}" output_mode="files_with_matches"
```

### 2.6 Native Code Opportunities

```bash
# CPU-intensive JavaScript that could use native bindings or WASM
# Look for image processing, crypto, compression, parsing
Grep pattern="(sharp|jimp|canvas|image-size)" glob="**/package.json"
Grep pattern="(crypto\.|createHash|createCipher|pbkdf2)" glob="**/*.{js,ts}" output_mode="content"
Grep pattern="(zlib|pako|compress|decompress|gzip)" glob="**/*.{js,ts}" output_mode="files_with_matches"

# Check for WebAssembly usage (positive signal)
Grep pattern="(WebAssembly|\.wasm)" glob="**/*.{js,ts}" output_mode="files_with_matches"

# Check for Worker Thread usage (positive signal)
Grep pattern="(worker_threads|Worker\(|new Worker)" glob="**/*.{js,ts,jsx,tsx}" output_mode="files_with_matches"

# Check for Utility Process usage (positive signal, Electron 22+)
Grep pattern="utilityProcess" glob="**/*.{js,ts}" output_mode="files_with_matches"

# Native Node addons
Glob pattern="**/*.node"
Grep pattern="node-gyp|napi|node-addon-api" glob="**/package.json"
```

### 2.7 Measurement & Monitoring

```bash
# Check if performance monitoring exists (positive signal)
Grep pattern="(contentTracing|performance\.mark|performance\.measure|PerformanceObserver)" glob="**/*.{js,ts}" output_mode="files_with_matches"

# Electron DevTools enabled in production (should be disabled)
Grep pattern="openDevTools" glob="**/*.{js,ts}" output_mode="content"
# FALSE POSITIVE: behind NODE_ENV or #if DEBUG check

# Console.log in production (overhead + info leak)
Grep pattern="console\.(log|debug|info|warn)\(" glob="**/*.{js,ts,jsx,tsx}" output_mode="count"

# React DevTools or React Scan in production
Grep pattern="(react-devtools|reactDevtools|react-scan)" glob="**/package.json"
```

---

## Step 3: Verification Rule (CRITICAL)

Before reporting ANY finding as a performance issue:

1. **Read the flagged file** — at minimum 20 lines of context around the match
2. **Check if it's test/build code** — performance patterns in test files or build scripts don't affect users
3. **Check for guards** — sync operations behind `if (!app.isPackaged)` or `NODE_ENV !== 'production'` are dev-only
4. **Check for cleanup** — event listeners with corresponding `removeListener` in cleanup functions are fine
5. **Check for worker offloading** — heavy computation sent to a Worker Thread is already handled
6. **Classify** — CONFIRMED, FALSE_POSITIVE, or INTENTIONAL before reporting

**Performance-specific false positives:**

- `readFileSync` in main process startup for config loading — often acceptable one-time cost
- `existsSync` for quick guard checks — negligible overhead
- `console.log` behind debug flags or removed by build tool
- `openDevTools` behind `isDev` or `NODE_ENV` check
- Event listeners with proper cleanup in `useEffect` return
- `setInterval` with matching `clearInterval` in component unmount

---

## Step 4: Grading

### Grade Criteria

| Grade | Criteria                                                                                                                                       |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| A     | Dynamic imports, no sync IPC, Worker Threads for heavy work, proper cleanup everywhere, optimistic UI, local persistence, performance monitoring |
| B     | Mostly async, no sync IPC, some dynamic imports, most cleanup handled, some loading states                                                      |
| C     | Mixed sync/async fs, no sync IPC, some missing cleanup, no dynamic imports, basic loading states                                                |
| D     | Sync IPC present, multiple sync fs calls in hot paths, event listener leaks, no loading states, no code splitting                               |
| F     | Pervasive sync IPC, no async patterns, no cleanup, blocking main thread, no performance awareness                                               |

### Category Grades

Grade each scanned category independently:

| Category                 | What to Evaluate                                                                |
| ------------------------ | ------------------------------------------------------------------------------- |
| Startup Performance      | Code splitting? Lazy loading? Bundle optimized? BrowserWindow show strategy?    |
| Main Thread Blocking     | Sync fs/IPC/dialog calls? Heavy computation on main thread? Worker usage?       |
| IPC Patterns             | Async invoke? Batched calls? Reasonable payload sizes? Error handling?           |
| Memory & Resource Leaks  | Listener cleanup? Timer cleanup? Process cleanup? Cache bounds? System events?  |
| Perceived Performance    | Loading states? Optimistic updates? Transitions? Local persistence? Prefetch?   |
| Native Code              | Worker Threads for CPU work? WASM where appropriate? Utility Processes?         |

### Overall Grade

The weakest category dominates. Formula: start with the average of all categories, then cap at one grade above the lowest category. Performance is only as strong as its weakest link.

Example: If 5 categories are A but Main Thread Blocking is D → Overall is C (capped at one grade above D, regardless of the A categories).

---

## Step 5: Output

**Display the executive summary, grade summary, issue table, and measurement status inline**, then write report to `.agents/research/YYYY-MM-DD-electron-performance-audit.md`.

### Report Structure

```markdown
# Electron Performance Audit Report

**Date:** YYYY-MM-DD
**Project:** [name]
**Scan Type:** Full / Quick / Focused

## Executive Summary

[2-3 sentences: overall performance posture, biggest bottleneck, top recommendation]

## Grade Summary

Overall: [grade] (Startup [grade] | Main Thread [grade] | IPC [grade] | Memory [grade] | Perceived [grade] | Native [grade])

## Positive Findings

[What's done well — async IPC, Worker Threads, code splitting, proper cleanup, loading states]

## Issue Rating Table

| #   | Finding | Urgency     | Risk: Fix | Risk: No Fix | ROI | Blast Radius | Fix Effort |
| --- | ------- | ----------- | --------- | ------------ | --- | ------------ | ---------- |
| 1   | ...     | 🔴 Critical | ...       | ...          | ... | ...          | ...        |

## Measurement Status

| Capability                  | Status |
| --------------------------- | ------ |
| Performance monitoring      | ✓/✗    |
| DevTools disabled in prod   | ✓/✗    |
| Console logging controlled  | ✓/✗    |

## Remediation Examples

[For each critical/high finding, show current problematic code and performant fix]
```

Use the Issue Rating scale:

- **Urgency:** 🔴 CRITICAL (user-visible jank/freeze) · 🟡 HIGH (measurable degradation) · 🟢 MEDIUM (suboptimal but functional) · ⚪ LOW (minor optimization)
- **ROI:** 🟠 Excellent · 🟢 Good · 🟡 Marginal · 🔴 Poor
- **Fix Effort:** Trivial / Small / Medium / Large

---

## Step 6: Follow-up

```
AskUserQuestion with questions:
[
  {
    "question": "How would you like to proceed?",
    "header": "Next",
    "options": [
      {"label": "Fix critical issues now", "description": "Walk through each critical/high issue with fixes"},
      {"label": "Re-scan specific category", "description": "Deeper scan on one area"},
      {"label": "Report is sufficient", "description": "Report saved to .agents/research/"}
    ],
    "multiSelect": false
  }
]
```

If "Fix critical issues now": Walk through each 🔴/🟡 finding, show the problematic code, propose a performant fix, apply after user approval.

---

## Troubleshooting

| Problem                                    | Solution                                                                           |
| ------------------------------------------ | ---------------------------------------------------------------------------------- |
| Too many grep hits for `console.log`       | Narrow glob to `src/` directories, exclude test and build files                    |
| Can't find main process entry              | Check `package.json` `main` field, or look for `electron-main` in build config     |
| False positive rate too high               | Read more context (30+ lines), check if behind dev guards or properly cleaned up   |
| Mixed CommonJS and ESM                     | Scan both `require()` and `import` patterns                                        |
| Monorepo structure                         | Identify the Electron package first, scope scans to that directory                 |
