# Phase 5k: MCP Tools — Workspace Setup

> Part of [Phase 5: MCP Server](05-mcp-server.md) | Toolset: `core`
>
> Scaffolds an `.agent/` workspace directory with AI agent configuration files for Zorivest end users.
> Research: [`_inspiration/agentic_ide_setup_research/research-synthesis.md`](../../_inspiration/agentic_ide_setup_research/research-synthesis.md)

---

## Overview

`zorivest_setup_workspace` generates `AGENTS.md` and IDE-specific shim files in the user's project root, and optionally creates an `.agent/` directory with configuration files that teach AI agents how to use Zorivest's MCP tools effectively. The tool supports three progressive scopes, detects the active IDE via [§5.12 client detection](05-mcp-server.md), and generates thin shim files for each IDE alongside a universal `AGENTS.md`.

### Design Principles

| Principle | Implementation |
|-----------|---------------|
| **Progressive disclosure** | Three scopes: `minimal` → `standard` → `full` |
| **Hub-and-spoke model** | `AGENTS.md` is canonical; IDE files are thin shims referencing it |
| **Idempotent** | Hash-tracked files in `.scaffold-meta.json`; backup-and-replace for updates |
| **Secure** | Path confinement, symlink resolution, atomic writes, provenance headers |
| **User-safe** | Never overwrites user-modified files without backup; content below `<!-- USER RULES BELOW -->` marker preserved across updates |

### Scope Tiers

| Scope | What Gets Created | When to Use |
|-------|-------------------|-------------|
| `minimal` | `AGENTS.md` + all IDE shims | Quick setup, minimal config |
| `standard` (default) | `AGENTS.md` + all IDE shims + basic `.agent/` (context, docs) | Recommended for most users |
| `full` | Everything in `standard` + workflows, roles, rules, skills | Power users, multi-agent setups |

---

## Tool

### `zorivest_setup_workspace` [Specified]

Bootstrap AI agent workspace configuration for Zorivest MCP tools.

```typescript
// mcp-server/src/tools/setup-tools.ts

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';
import * as fs from 'fs/promises';
import * as path from 'path';
import * as crypto from 'crypto';
import * as url from 'url';
import { getDetectedClient } from '../toolsets/client-detection.js';

const TEMPLATE_DIR = path.resolve(
  import.meta.dirname ?? __dirname,
  '../../templates/agent'
);

// ── Types ──

interface ScaffoldResult {
  created: string[];
  skipped: string[];
  backed_up: string[];
  warnings: string[];
}

interface ScaffoldMeta {
  version: string;
  created_at: string;
  updated_at: string;
  tool_version: string;
  files: Record<string, { hash: string; template_hash: string }>;
}

// ── Path Safety ──

async function validatePath(root: string, relPath: string): Promise<string> {
  const fullPath = path.resolve(root, relPath);
  const realRoot = await fs.realpath(root);

  // Resolve real path, walking up to nearest existing ancestor for new files
  let realPath: string;
  try {
    realPath = await fs.realpath(fullPath);
  } catch {
    // Walk up to find nearest existing ancestor
    let current = path.dirname(fullPath);
    const pending: string[] = [path.basename(fullPath)];
    let resolved = false;
    while (current !== path.dirname(current)) {
      try {
        const resolvedAncestor = await fs.realpath(current);
        realPath = path.join(resolvedAncestor, ...pending.reverse());
        resolved = true;
        break;
      } catch {
        pending.push(path.basename(current));
        current = path.dirname(current);
      }
    }
    if (!resolved) {
      // Fell all the way to filesystem root — resolve from project root
      realPath = path.join(realRoot, ...pending.reverse());
    }
  }

  if (!realPath!.startsWith(realRoot + path.sep) && realPath! !== realRoot) {
    throw new Error(`Path traversal blocked: ${relPath}`);
  }
  return fullPath;
}

// ── Atomic Write with Backup ──

async function safeWrite(
  root: string,
  relPath: string,
  content: string,
  result: ScaffoldResult,
  meta: ScaffoldMeta,
): Promise<void> {
  const fullPath = await validatePath(root, relPath);
  const existingMeta = meta.files[relPath];

  // Check if file already exists
  let existingContent: string | null = null;
  try {
    existingContent = await fs.readFile(fullPath, 'utf-8');
  } catch { /* file doesn't exist */ }

  // Compute template-only hash BEFORE splice (for user-modification guard)
  const templateHash = crypto.createHash('sha256').update(content).digest('hex');

  // Preserve user rules: if existing file has USER RULES marker,
  // splice user content below marker into new template BEFORE
  // any hash comparison or early-return decisions
  if (existingContent !== null) {
    const markerIdx = existingContent.indexOf(USER_RULES_MARKER);
    if (markerIdx !== -1) {
      const userSection = existingContent.slice(
        markerIdx + USER_RULES_MARKER.length
      );
      // Strip marker from new template to avoid duplication
      const templateMarkerIdx = content.lastIndexOf(USER_RULES_MARKER);
      if (templateMarkerIdx !== -1) {
        content = content.slice(0, templateMarkerIdx);
      }
      content = content + USER_RULES_MARKER + userSection;
    }
  }

  // Compute hash from post-splice content (matches what will be written)
  const contentHash = crypto.createHash('sha256').update(content).digest('hex');

  if (existingContent !== null) {
    const existingHash = crypto.createHash('sha256').update(existingContent).digest('hex');

    // Same content after splice — skip
    if (existingHash === contentHash) {
      // Refresh meta hash to track current file state (user may have
      // edited below marker since last write — hash must stay current
      // so the next template update doesn't false-positive as user-modified)
      if (existingMeta) {
        meta.files[relPath] = { hash: existingHash, template_hash: templateHash };
      }
      result.skipped.push(relPath);
      return;
    }

    // User modified the file outside the USER RULES section
    // (hash differs from both full written hash AND template-only hash)
    if (!force && existingMeta
        && existingHash !== existingMeta.hash
        && existingHash !== existingMeta.template_hash) {
      result.warnings.push(`${relPath}: user-modified outside marker, backed up but not overwritten`);
      const backupDir = path.join(root, '.agent', '.backup');
      await fs.mkdir(backupDir, { recursive: true });
      const backupName = `${path.basename(relPath)}.${Date.now()}.bak`;
      await fs.copyFile(fullPath, path.join(backupDir, backupName));
      result.backed_up.push(relPath);
      result.skipped.push(relPath);
      return;
    }

    // Template updated or user edited only below marker — backup old, write new
    const backupDir = path.join(root, '.agent', '.backup');
    await fs.mkdir(backupDir, { recursive: true });
    const backupName = `${path.basename(relPath)}.${Date.now()}.bak`;
    await fs.copyFile(fullPath, path.join(backupDir, backupName));
    result.backed_up.push(relPath);
  }

  // Atomic write: temp file → rename
  await fs.mkdir(path.dirname(fullPath), { recursive: true });

  const tmp = fullPath + '.tmp';
  await fs.writeFile(tmp, content, { mode: 0o644 });
  await fs.rename(tmp, fullPath);

  // Track in meta: hash = full written content, template_hash = template only
  meta.files[relPath] = { hash: contentHash, template_hash: templateHash };
  result.created.push(relPath);
}

// ── Template Loading ──

const TOOL_VERSION = '0.1.0';
const USER_RULES_MARKER = '<!-- USER RULES BELOW -->';

async function loadTemplate(templatePath: string): Promise<string> {
  const raw = await fs.readFile(path.join(TEMPLATE_DIR, templatePath), 'utf-8');
  const templateHash = crypto.createHash('sha256').update(raw).digest('hex').slice(0, 8);
  const header = `<!-- Generated by Zorivest MCP v${TOOL_VERSION} | Template hash: ${templateHash} | Do not edit above USER RULES marker -->\n`;
  return header + raw + '\n' + USER_RULES_MARKER + '\n';
}

// ── Registration ──

export function registerSetupTools(server: McpServer) {
  server.tool(
    'zorivest_setup_workspace',
    'Bootstrap AI agent workspace configuration. Creates AGENTS.md, IDE-specific config files, and optional .agent/ directory with trading workflows, roles, and docs for using Zorivest MCP tools. Safe to run multiple times (idempotent).',
    {
      project_root: z.string().optional().describe(
        'Project root directory. Defaults to CWD or MCP roots[0].'
      ),
      scope: z.enum(['minimal', 'standard', 'full']).default('standard').describe(
        'Scaffolding scope: minimal (AGENTS.md + all IDE shims), standard (+ .agent/context + docs), full (+ workflows, roles, rules, skills)'
      ),
      force: z.boolean().default(false).describe(
        'Force overwrite all files, even user-modified ones (backups still created)'
      ),
    },
    async ({ project_root, scope, force }) => {
      // Resolve project root: explicit param > MCP roots[0] > CWD
      let root: string;
      if (project_root) {
        root = project_root;
      } else {
        // Access MCP roots if available (server reference from closure)
        const mcpRoots = server.server?.roots;
        root = mcpRoots?.[0]?.uri
          ? url.fileURLToPath(mcpRoots[0].uri)
          : process.cwd();
      }
      try { await fs.access(root); } catch {
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({
            success: false, data: null,
            error: `Project root not found: ${root}`,
          }) }],
          isError: true,
        };
      }

      const result: ScaffoldResult = {
        created: [], skipped: [], backed_up: [], warnings: [],
      };

      // Load or create scaffold meta (at project root, not under .agent/)
      const metaPath = path.join(root, '.scaffold-meta.json');
      let meta: ScaffoldMeta;
      try {
        meta = JSON.parse(await fs.readFile(metaPath, 'utf-8'));
        meta.updated_at = new Date().toISOString();
      } catch {
        meta = {
          version: '1',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          tool_version: '0.1.0',
          files: {},
        };
      }

      // If force mode, clear tracked hashes so everything gets overwritten
      if (force) { meta.files = {}; }

      const client = getDetectedClient();

      // Helper: write a template file with per-file error handling
      const writeTemplate = async (relPath: string, templateName: string) => {
        try {
          await safeWrite(root, relPath, await loadTemplate(templateName), result, meta);
        } catch (err) {
          result.warnings.push(`${relPath}: ${(err as Error).message}`);
        }
      };

      try {
        // ── Tier 1: AGENTS.md + IDE shims ──
        await writeTemplate('AGENTS.md', 'AGENTS.md');

        // IDE shims — always generate all (thin files, <20 lines each)
        for (const ide of ['GEMINI', 'CLAUDE', 'CURSOR', 'CODEX']) {
          await writeTemplate(`${ide}.md`, `${ide}.md`);
        }

        if (scope === 'minimal') {
          await writeMeta(metaPath, meta);
          return formatResponse(result, scope, client);
        }

        // ── Tier 2: .agent/context + .agent/docs ──
        await writeTemplate('.agent/context/current-focus.md', 'context/current-focus.md');
        await writeTemplate('.agent/context/known-issues.md', 'context/known-issues.md');
        await writeTemplate('.agent/docs/getting-started.md', 'docs/getting-started.md');
        await writeTemplate('.agent/docs/tool-catalog.md', 'docs/tool-catalog.md');
        await writeTemplate('.agent/docs/troubleshooting.md', 'docs/troubleshooting.md');

        if (scope === 'standard') {
          await writeMeta(metaPath, meta);
          return formatResponse(result, scope, client);
        }

        // ── Tier 3: workflows, roles, rules, skills ──
        await writeTemplate('.agent/workflows/trade-analysis.md', 'workflows/trade-analysis.md');
        await writeTemplate('.agent/workflows/portfolio-review.md', 'workflows/portfolio-review.md');
        await writeTemplate('.agent/workflows/market-research.md', 'workflows/market-research.md');
        await writeTemplate('.agent/roles/trade-analyst.md', 'roles/trade-analyst.md');
        await writeTemplate('.agent/roles/portfolio-reviewer.md', 'roles/portfolio-reviewer.md');
        await writeTemplate('.agent/roles/risk-manager.md', 'roles/risk-manager.md');
        await writeTemplate('.agent/rules/trading-rules.md', 'rules/trading-rules.md');
        await writeTemplate('.agent/skills/trade-evaluation/SKILL.md', 'skills/trade-evaluation/SKILL.md');

        await writeMeta(metaPath, meta);
        return formatResponse(result, scope, client);
      } catch (err) {
        // Catch-all: convert unexpected errors into response (never throws)
        result.warnings.push(`Unexpected error: ${(err as Error).message}`);
        try { await writeMeta(metaPath, meta); } catch { /* best effort */ }
        return formatResponse(result, scope, client);
      }
    }
  );
}

// ── Helpers ──

async function writeMeta(metaPath: string, meta: ScaffoldMeta): Promise<void> {
  await fs.mkdir(path.dirname(metaPath), { recursive: true });
  await fs.writeFile(metaPath, JSON.stringify(meta, null, 2));
}

function formatResponse(
  result: ScaffoldResult,
  scope: string,
  client: string,
): { content: { type: 'text'; text: string }[] } {
  return {
    content: [{
      type: 'text' as const,
      text: JSON.stringify({
        success: true,
        data: {
          scope,
          detected_ide: client,
          files_created: result.created.length,
          files_skipped: result.skipped.length,
          files_backed_up: result.backed_up.length,
          created: result.created,
          skipped: result.skipped,
          backed_up: result.backed_up,
          warnings: result.warnings,
        },
        error: null,
      }, null, 2),
    }],
  };
}
```

#### Annotations

- `readOnlyHint`: false
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: core
- `alwaysLoaded`: true

**Input:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project_root` | string? | CWD or MCP roots[0] | Project root directory |
| `scope` | enum | `"standard"` | `minimal` / `standard` / `full` |
| `force` | boolean | `false` | Force overwrite user-modified files |

**Output:** Standard response envelope: `{ success, data: { scope, detected_ide, files_created, files_skipped, files_backed_up, created[], skipped[], backed_up[], warnings[] }, error }`

**Side Effects:** Creates/updates files in the project directory. Backs up modified files to `.agent/.backup/`.

**Error Posture:** Returns `isError: true` if project root not found. Never throws — all file errors are caught and added to `warnings[]`.

---

## Template Structure

Templates are static Markdown files bundled in `mcp-server/templates/agent/`:

```
mcp-server/templates/agent/
├── AGENTS.md                          # Universal instructions (~100 lines)
├── GEMINI.md                          # Thin shim → AGENTS.md + Gemini hints
├── CLAUDE.md                          # Thin shim → AGENTS.md + Claude hints
├── CURSOR.md                         # Thin shim → AGENTS.md + Cursor hints
├── CODEX.md                          # Thin shim → AGENTS.md + Codex hints
├── context/
│   ├── current-focus.md              # Active work items template
│   └── known-issues.md              # Known issues template
├── docs/
│   ├── getting-started.md           # Zorivest MCP getting started guide
│   ├── tool-catalog.md              # Available tools reference
│   └── troubleshooting.md          # Common issues and solutions
├── workflows/
│   ├── trade-analysis.md            # Trade evaluation workflow
│   ├── portfolio-review.md          # Portfolio review workflow
│   └── market-research.md          # Market research workflow
├── roles/
│   ├── trade-analyst.md             # Analytical trading persona
│   ├── portfolio-reviewer.md       # Review-focused persona
│   └── risk-manager.md             # Risk assessment persona
├── rules/
│   └── trading-rules.md            # Domain-specific agent rules
└── skills/
    └── trade-evaluation/
        └── SKILL.md                  # Trade evaluation skill
```

### Provenance Header

Every generated file includes a provenance header as the first line:

```markdown
<!-- Generated by Zorivest MCP v{version} | Template hash: {sha256_first8} | Do not edit above USER RULES marker -->
```

### AGENTS.md Content Outline (~100 lines)

1. **Project identity** — What Zorivest is (trading portfolio manager), tech stack (Python/FastAPI + TypeScript/MCP + Electron/React)
2. **MCP connection** — How to connect (`npx @zorivest/mcp-server --api-url ...`)
3. **Available toolsets** — Core (always), trade-analytics (default), market-data (deferred), etc.
4. **Common commands** — Exact tool invocations for frequent tasks
5. **Domain vocabulary** — Trade, Account, Position, Watchlist, TradePlan, TradeReport
6. **Security boundaries** — Never: execute real trades, expose API keys, modify production data
7. **File structure** — Key project directories and their purposes
8. **User rules marker** — `<!-- USER RULES BELOW -->` section at end of file for user-specific customizations preserved across template updates

### IDE Shim Structure (~15 lines each)

```markdown
<!-- Generated by Zorivest MCP v0.1.0 | Template hash: abc12345 -->
# Zorivest — {IDE Name} Configuration

For full Zorivest instructions, see [AGENTS.md](./AGENTS.md).

## {IDE}-Specific Settings
{2-5 lines of IDE-specific configuration hints}
```

---

## Security

### Path Confinement

All file operations use `validatePath()` which:
1. Resolves the full path via `path.resolve()`
2. Resolves symlinks via `fs.realpath()` (prevents symlink-based escapes)
3. Verifies the resolved path starts with the resolved project root
4. Throws `Error` on path traversal attempts

### Atomic Writes

Files are written to a `.tmp` suffix first, then renamed. This prevents partial files on crash or interruption.

### Template Integrity

Templates are static files bundled in the npm package. SHA-256 hashes of template content are recorded in `.scaffold-meta.json` for integrity verification on subsequent runs.

### Defense-in-Depth Summary

| Layer | Mechanism |
|-------|-----------|
| Path confinement | `validatePath()` with `realpath` + prefix check |
| Symlink protection | `fs.realpath()` resolves before validation |
| Atomic writes | `writeFile(tmp)` → `rename(tmp, target)` |
| Template integrity | SHA-256 in `.scaffold-meta.json` (dual-hash: `hash` for full content, `template_hash` for template-only) |
| User file safety | Backup before overwrite; skip if user modified above marker. Content below `<!-- USER RULES BELOW -->` marker preserved across template updates |
| Content safety | Static templates only; no dynamic code generation |
| MCP Guard | Respects existing circuit breaker (unguarded like `zorivest_diagnose`) |

---

## Idempotency Flow

```
zorivest_setup_workspace called
  │
  ├── Load .scaffold-meta.json (or create new)
  │
  For each template file:
  │
  ├── 1. Splice: if existing file has USER RULES marker,
  │      extract user content below marker and append to new template
  │
  ├── 2. Hash: compute templateHash (pre-splice) and contentHash (post-splice)
  │
  ├── 3. File doesn't exist → create (atomic write)
  │
  ├── 4. File exists, contentHash matches existingHash → skip, refresh meta
  │
  ├── 5. File exists, hash differs:
  │   ├── Modified outside marker? (existing ≠ meta.hash AND ≠ meta.template_hash)
  │   │   → backup, skip, warn
  │   └── Otherwise (template updated or user edited only below marker)
  │       → backup, write new (user rules preserved via splice)
  │
  └── 6. Force mode? → backup, overwrite regardless (user rules still preserved)
```

---

## npm Packaging

Templates are included in the npm package via the `files` field in `mcp-server/package.json`:

```json
{
  "files": [
    "dist/",
    "templates/"
  ]
}
```

---

## Vitest Tests

```typescript
// mcp-server/tests/setup-tools.test.ts

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import * as fs from 'fs/promises';
import * as path from 'path';
import * as os from 'os';

describe('zorivest_setup_workspace', () => {
  let tmpDir: string;

  beforeEach(async () => {
    tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), 'zorivest-test-'));
  });

  afterEach(async () => {
    await fs.rm(tmpDir, { recursive: true, force: true });
  });

  it('creates AGENTS.md and all IDE shims with minimal scope', async () => {
    // Invoke handler with scope='minimal', project_root=tmpDir
    // Verify AGENTS.md exists with provenance header
    // Verify GEMINI.md, CLAUDE.md, CURSOR.md, CODEX.md exist
    // Verify .agent/ directory does NOT exist (minimal scope)
    // Verify .scaffold-meta.json exists at project root (not under .agent/)
  });

  it('creates .agent/context and docs with standard scope', async () => {
    // Invoke handler with scope='standard'
    // Verify .agent/context/current-focus.md exists
    // Verify .agent/docs/getting-started.md exists
    // Verify .agent/workflows/ does NOT exist (standard, not full)
  });

  it('creates full directory structure with full scope', async () => {
    // Invoke handler with scope='full'
    // Verify .agent/workflows/trade-analysis.md exists
    // Verify .agent/roles/trade-analyst.md exists
    // Verify .agent/rules/trading-rules.md exists
    // Verify .agent/skills/trade-evaluation/SKILL.md exists
  });

  it('skips unchanged files on second run (idempotent)', async () => {
    // Run once → all created
    // Run again → all skipped
    // Verify result.skipped contains all files
    // Verify result.created is empty
  });

  it('backs up user-modified files without overwriting', async () => {
    // Run once → AGENTS.md created
    // Modify AGENTS.md manually
    // Run again → AGENTS.md skipped, warning emitted, backup created
    // Verify .agent/.backup/ contains backup file
  });

  it('force mode overwrites user-modified files', async () => {
    // Run once → AGENTS.md created
    // Modify AGENTS.md manually
    // Run with force=true → AGENTS.md overwritten, backup created
  });

  it('returns error for non-existent project root', async () => {
    // Invoke with project_root='/nonexistent/path'
    // Verify isError: true
    // Verify error message
  });
});

describe('validatePath', () => {
  it('rejects path traversal via ../', async () => {
    // validatePath(tmpDir, '../../../etc/passwd')
    // Expect Error: 'Path traversal blocked'
  });

  it('rejects symlink escape', async () => {
    // Create symlink inside tmpDir → outside tmpDir
    // validatePath(tmpDir, 'symlink/file')
    // Expect Error: 'Path traversal blocked'
  });

  it('allows nested paths within project root', async () => {
    // validatePath(tmpDir, '.agent/docs/getting-started.md')
    // Expect: resolved path within tmpDir
  });
});

describe('.scaffold-meta.json', () => {
  it('records file hashes on creation', async () => {
    // Run setup, read .scaffold-meta.json
    // Verify meta.files['AGENTS.md'].hash is valid SHA-256
    // Verify meta.version === '1'
    // Verify meta.created_at is ISO timestamp
  });

  it('preserves creation timestamp across runs', async () => {
    // Run once, record created_at
    // Run again, verify created_at unchanged
    // Verify updated_at changed
  });

  it('preserves user rules below marker across template updates', async () => {
    // Step 1: Initial scaffold — creates AGENTS.md with template v1
    // Step 2: User edits AGENTS.md, adding content below <!-- USER RULES BELOW -->
    // Step 3: Re-run with same template v1 — verify skip, but meta.hash refreshed
    // Step 4: Update template to v2 — re-run scaffold
    // Verify: AGENTS.md contains template v2 content ABOVE marker
    // Verify: User rules content BELOW marker is preserved
    // Verify: meta.hash reflects the actually-written (post-splice) content
    // Verify: meta.template_hash reflects template v2 (pre-splice)
  });
});
```

---

## MEU Breakdown

This spec is implemented across 2 MEUs:

| MEU | Slug | Description | Key Deliverables |
|-----|------|-------------|-----------------|
| MEU-165a | `setup-workspace-core` | Tool infrastructure + path safety + idempotency | `setup-tools.ts`, `validatePath()`, `safeWrite()`, `.scaffold-meta.json`, tool registration in core toolset, vitest tests |
| MEU-165b | `setup-workspace-templates` | Template content authoring | All `.md` template files in `mcp-server/templates/agent/`, AGENTS.md, IDE shims, docs, workflows, roles, rules, skills |

### Dependencies

- MEU-42 (ToolsetRegistry + client detection) — ✅ approved
- No other dependencies

### Build Order

Place after Phase 9 scheduling domain foundation (per user decision Q4=D):

```
Phase 9 (domain): MEU-77..80 ✅
→ MEU-165a (setup-workspace-core)
→ MEU-165b (setup-workspace-templates)
```
