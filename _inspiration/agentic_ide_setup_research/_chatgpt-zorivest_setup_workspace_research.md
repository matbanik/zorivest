# Executive Summary  
We recommend building **`zorivest_setup_workspace`** as a local filesystem-scaffolding MCP tool using Node/TypeScript.  It will create the `.agent/` folder and all subfolders (`context`, `workflows`, etc.) using static templates (packaged with the MCP server via `npm`).  File paths must be resolved relative to the user’s project root, strictly enforcing that writes do not escape this root (e.g. via `path.resolve(root, userPath)` and prefix checks【28†L243-L250】).  Use `fs.mkdir({ recursive: true })` to create directories and write files with safe APIs (e.g. `fs.writeFile`).  Avoid shell-based writes (the example [18] shows a naive `exec("echo … > file")` approach, which is vulnerable to injection and lacks normalization).  Instead use the Node `fs`/`path` API, optionally writing to a temp file then renaming for atomicity.  

To remain **idempotent**, the tool should *not* blindly overwrite existing files.  A recommended strategy is **skip-or-backup**: if a file already exists, move or copy it to a `.bak/` subdirectory before writing the new template.  This allows recovery and alerts the user to changes.  Alternatively, mark scaffolded files with a template-version header (e.g. `# Template version: 1.0`) so the tool can decide not to re-write unchanged files.  Unlike interactive CLI tools, we cannot prompt the user, so aggressive overwrite is risky.  For example, React’s `create-react-app` simply fails if the directory isn’t empty【40†L99-L107】, while Yeoman uses an in-memory filesystem and conflict prompts (not feasible here)【57†L111-L119】.  Thus **overwrite-with-backup** or **skip** is safer for an automated agent.  

For multi-IDE support, we propose **static MD templates** shipped in the package.  Maintain a single *base* `AGENTS.md` template and small IDE-specific overlays (e.g. `GEMINI.md`, `CLAUDE.md`, etc.).  Common content can be in the base; each IDE file can include IDE-specific sections (e.g. “In Gemini, you can use block comments …”).  Implementation: at scaffold time detect the IDE (already done in `client-detection.ts`) and merge appropriate parts.  For simplicity, we recommend generating *all* IDE files with their respective content (since they are small MD files), citing the detected IDE in their content.  For example, a Handlebars/Template system can inject variables like `{{ide_name}}`.  This avoids manual copying and duplication.  

Security must be paramount.  Validate and sanitize all file paths against the project root【28†L243-L250】【30†L363-L368】.  Reject any path that does not reside under the root (no `../` escapes, use `path.resolve`+prefix-check).  Detect and avoid symlink tricks (use `fs.realpath` if needed).  The tool should use the MCP confirmation middleware to require user approval of all write operations (e.g. obtain a confirmation token before writing).  Rate-limiting or guard-circuit-breaker is usually not needed for a one-time setup tool, but we must abide by MCP guard policies to prevent runaway loops.  Signing generated files is overkill, but including a version stamp (in `.agent/.meta.json`) can help integrity and updates.

In implementation, examine analogous tools: e.g. [18] (Node MCP filesystem tool) shows a simplistic approach (using shell `echo` and `path.join`) – but it lacks any input validation and is unsafe.  Yeoman’s pattern (in [57]) shows robust conflict handling via an in-memory FS, which is not practical for MCP.  Instead, write straightforward TS code: 

```ts
import * as fs from 'fs/promises';
import * as path from 'path';

// Example of safe file write within root
async function safeWrite(root: string, relPath: string, content: string) {
  const fullPath = path.resolve(root, relPath);
  if (!fullPath.startsWith(root)) {
    throw new Error(`Invalid path: ${relPath}`);
  }
  // Ensure directory exists
  await fs.mkdir(path.dirname(fullPath), { recursive: true });
  // Backup existing file if it exists
  try {
    await fs.access(fullPath);
    await fs.copyFile(fullPath, fullPath + '.bak');
  } catch { /* ignore if not exists */ }
  // Write content (atomic write example)
  const tempPath = fullPath + '.tmp';
  await fs.writeFile(tempPath, content, { mode: 0o600 });
  await fs.rename(tempPath, fullPath);
}
```

Package templates under `mcp-server/templates/agent/` and include them in `package.json` via the `"files"` or `"directories"` field【34†L161-L166】 so they ship with the npm. Overall, this pattern (static templates + safe writes) has been used by CLI tools like CRA or Yeoman, but tailored for MCP: trust the tool if presented by a confirmed agent, handle conflicts by backup, and log actions.  This approach minimizes user surprise while allowing future updates (with diffs or version checks).  

**Recommended Architecture**: The `zorivest_setup_workspace` tool lives in the `core` toolset.  Upon invocation, it: 
1. Reads the detected client/IDE (`mcpContext.client`) to know which IDE-specific variants to generate.  
2. Resolves the absolute project root (given by MCP `roots` capability) and ensures all operations stay within it【28†L243-L250】.  
3. Creates `.agent/` subdirectories recursively.  
4. Copies each template file (e.g. `.agent/context/README.md`, `AGENTS.md`, and the IDE variants) from the static assets to the filesystem.  For each file: if an existing file is found, rename it to `.bak/filename`, then write the new file.  Alternatively, if a template-version header is present, skip if not newer.  
5. Records metadata in `.agent/.meta.json` (timestamp, tool version, file list) for future reference.  

This design ensures safe file operations, respects idempotency, and cleanly supports multi-IDE templates.  The following sections detail the patterns and reasoning behind these choices. 

# File System Operation Patterns  

**Path Resolution & Confinement:** Always resolve user-specified paths against the project root to avoid surprises【28†L243-L250】.  In Node/TS, use `path.resolve(root, rel)` and then enforce `resolvedPath.startsWith(root)`.  For example:  
```ts
const fullPath = path.resolve(projectRoot, userPath);  
if (!fullPath.startsWith(projectRoot)) {
  throw new Error(`Path traversal detected: ${userPath}`);
}
```  
This guards against inputs like `../../etc/passwd`.  Also prefer `fs.realpath` when following symlinks to ensure the ultimate target stays in the workspace.  

**Directory Creation:** Use recursive mkdir. For example:  
```ts
await fs.mkdir(path.dirname(fullPath), { recursive: true });
```  
This ensures all parent directories exist. Unlike some CLI tools, no need for manual recursion.  It’s idempotent (won’t error if already exists).  

**Atomic Writes:** To avoid partial files on interruption, consider writing to a temp file then renaming:  
```ts
const tmp = fullPath + '.tmp';
await fs.writeFile(tmp, content);
await fs.rename(tmp, fullPath);
```  
This makes the write appear atomic on most OSes. Without this, an agent crash could leave half-written files.  

**Permission Model:** Write with safe modes (e.g. `0o600` for files) so other users can’t read agent data. Handle write failures gracefully: e.g., catch `EACCES` or disk-full and return an error result to the agent. Log or surface errors clearly.  

**Path Traversal/Symlinks:** Always normalize and check path prefixes【28†L243-L250】. Do not use string concatenation (`base + "/../evil"`) or unvalidated `path.join` (as in [18]). In [18], the code used `path.join(root, file)` and an `exec("echo...")`; it had no check for `../` and even used shell quoting (which could inject). We must not replicate that pattern【18†L281-L289】. 

**Example (combining above patterns):**  
```ts
import { promises as fs } from 'fs';
import * as path from 'path';

async function writeFileSafe(root: string, relPath: string, data: string) {
  // Resolve and validate path
  const target = path.resolve(root, relPath);
  if (!target.startsWith(root)) {
    throw new Error(`Invalid write path ${relPath}`);
  }
  // Ensure directory exists
  await fs.mkdir(path.dirname(target), { recursive: true });
  // Backup existing if needed
  try {
    await fs.access(target);
    await fs.copyFile(target, `${target}.old`);
  } catch {
    // file did not exist
  }
  // Atomic write
  const tmp = `${target}.tmp`;
  await fs.writeFile(tmp, data, { mode: 0o600 });
  await fs.rename(tmp, target);
}
```  
This pattern is common in node-based tools and avoids both partial writes and path attacks. Use of `fs` APIs is preferable to `exec` (no shell injection risk). For reference, some MCP fileservers simply exec shell commands (e.g. [18]) which is **not recommended**. 

# Idempotency Strategy Recommendation  

To make `zorivest_setup_workspace` idempotent, we must define how it handles pre-existing files. The main strategies are:

- **Skip existing files:** The tool only writes a file if it does *not* already exist. This is safe but fails to update outdated templates.  
- **Overwrite existing files:** Simply replace any existing file. This ensures the latest templates but destroys any user edits (dangerous!).  
- **Backup-and-replace:** Copy existing files to a backup location (e.g. `.agent/old/`) then overwrite. This preserves user content at least in a `.bak` area.  
- **Merge:** Perform a three-way diff/merge between *old content*, *new template*, and some “base” (complex for Markdown).  
- **Versioned headers:** Embed a version stamp in scaffolded files (`# Template version: x.x`). Only overwrite if the template version is newer than the existing file’s version.  

Because an MCP tool cannot interactively prompt per-file, we avoid interactive conflict resolution.  CLI tools follow various approaches: e.g., **`create-react-app`** aborts on any conflict (refuses to run if target directory is non-empty)【40†L99-L107】, forcing manual cleanup. **Yeoman** would normally prompt the user on conflict【57†L111-L119】, but we can’t do that here.  **NPM init** (with `-y`) simply creates `package.json` if missing; if it exists, it typically leaves it untouched.  

For our use case, a hybrid skip/backup strategy is recommended:  

- If a file *does not exist*, simply write the new template.  
- If a file *already exists*, first copy it to `.agent/.backup/` (or `.agent/.old/`), then overwrite it with the template. Log or inform the agent of the backup path. Optionally, if the existing file contains a template-version header, compare versions and skip overwrite if the existing version is equal or newer.  

This way, user changes aren’t lost — they can inspect the `.backup` folder to recover any needed custom content. It also allows the tool to update templates if needed, while still being safe. For example:  
```ts
if (await fsAccess(path)) {
  // backup existing
  await fs.copyFile(path, path.replace(/(\.\w+)$/, '.bak$1'));
}
// write new file
await fs.writeFile(path, templateContent);
```  
Yeoman’s design (in [57]) is more complex: it routes all writes through a memory FS and resolves conflicts interactively【57†L111-L119】. We can simplify: always backup then overwrite.  

We can summarize these strategies in a decision matrix:

| Strategy            | Overwrite? | Preserve User Edits? | Update Capability | Ideal When…         |
|---------------------|------------|----------------------|-------------------|---------------------|
| **Skip**            | No         | Yes                  | No                | User-edited files; only first-time scaffold |
| **Overwrite**       | Yes        | No                   | Yes               | Clean templates, no user edits expected     |
| **Backup+Replace**  | Yes (to .bak) | Partial (in .bak) | Yes               | Safe update with recoverability (preferred) |
| **Merge (3-way)**   | Yes        | Yes                  | Yes               | Very advanced, ensures perfect merges (complex) |
| **Interactive Prompt** | -      | Depends              | Depends           | CLI tools (not viable here)                |

Given an agent context (no UI), **Backup+Replace** strikes the best balance. We would also stamp generated files with a header (e.g. `# Version: 1.2`) so on subsequent runs the tool can check whether the template changed. If the version matches, the tool can *skip* rewriting to avoid unnecessary backups.  

The tool should also record state in a manifest (e.g. `.agent/.meta.json` listing generated files and template version). This aids idempotency and future diffs.  

# Template Architecture Design  

We propose a **base-plus-overlays** template design. Maintain one canonical `AGENTS.md` in the `templates/agent/` directory. Then have separate small templates for each IDE variant (`CLAUDE.md`, `GEMINI.md`, `CURSOR.md`, `CODEX.md`, etc.) that pull in common content from the base. This can be done by template inclusion or by simple duplication with placeholder differences. For example, a Handlebars template might use `{{client}}` or partials:

```md
{{> header}}

- This is general agent instruction ...

{{#if isGemini}}
**Gemini-specific tip:** In Gemini, use block comments for mode hints.
{{/if}}

{{> footer}}
```

In practice, we might ship static `.md` files and fill in IDE sections programmatically.  For instance:

- Copy `AGENTS.md` to `.agent/AGENTS.md`.  
- Copy IDE templates to `.agent/GEMINI.md`, etc.  The tool can inject a note like “*(tailored for Gemini IDE)*” at the top if needed.

We can auto-generate these variants at runtime by reading the base content and appending a short IDE-specific section. For example, using TypeScript:  

```ts
const baseContent = fs.readFileSync('templates/agent/AGENTS.md', 'utf8');
const gemsSuffix = fs.readFileSync('templates/agent/GEMINI.md', 'utf8');
fs.writeFileSync('.agent/GEMINI.md', `${baseContent}\n\n${gemsSuffix}`);
```

Alternatively, use a templating engine (Handlebars/EJS) with placeholders for shared parts and IDE-specific flags. 

For multi-IDE support, we have two choices: generate *only* the detected IDE file, or generate *all* files. Generating all (`GEMINI.md`, `CLAUDE.md`, etc.) upfront is simplest and ensures no missing docs if the user later uses a different IDE. These files are small, so extra generation cost is minimal. We can conditionally include the IDE’s name/metadata. 

**Template Maintenance:** Keep shared sections DRY. For example, common sections (like explaining the `.agent/` directory) live in `AGENTS.md`, while IDE-specific conventions (e.g. “Cursor expects `.cursorrules` files”) live in each variant. This avoids duplicating long text. In Git, we might even have partial includes, but at runtime the tool simply concatenates files.

*(Diagram: The base `AGENTS.md` feeds into each IDE-specific MD by appending an overlay.)*

# Security Analysis  

**Threat Model:** The main risks are unauthorized file writes (escaping the project), malicious template content, and abuse of the MCP protocol to overwrite sensitive files. Because MCP tools run with user permissions, we must enforce safety.

- **Path Validation (Traversal/Sandboxing):** Strictly enforce that *all* write paths lie under the project root【28†L243-L250】【30†L363-L368】. Reject any attempt to write to absolute paths or `..` above the root. For symlinks, resolve real paths and check the destination. This mirrors file-server MCP best practices: “Filesystem MCP: Root directory confinement, Path traversal protection”【30†L363-L368】.  

- **Template Integrity:** Since our templates are static assets, ensure they’re not modifiable at runtime. An attacker could try to modify the templates before scaffolding. To prevent this, ship them in the npm package (read-only) and verify the `mcp-server` code signature if possible. Optionally, include a hash of templates in `.meta.json` for tamper-detection (though with an installed npm package this is low-risk). The agent itself only writes controlled content.  

- **Confirmation & Permissions:** Use MCP’s confirmation middleware to get explicit permission (token) before writing files. This ensures an end-user authorizes the operation. The guard service (approval flow) can rate-limit such operations if needed, but scaffolding is a single batch job, so rate-limits are unlikely to trigger.  

- **No Code Injection:** Do not evaluate or execute any template logic provided by the agent’s prompt. All content comes from vetted static templates. If any variable interpolation is used, treat it as data-only.  

- **Watch for Malformed Inputs:** If the tool supports renaming or taking user-supplied names for roles/docs, validate those names (sanitize, block special chars). In our case, the directory names (`context/`, etc.) are fixed, so not an issue.

- **Least Privilege:** The MCP server should run with the same privileges as the user (as MCP guidelines note). It shouldn’t elevate permissions. Log any filesystem errors and fail-safe on denied writes.  

In summary, our tool strictly confines to the project folder and uses safe APIs. This matches MCP security guidance【28†L243-L250】【30†L363-L368】 and prevents path traversal or unintended access.

# Implementation Analysis  

**Existing MCP Filesystem Tools:** We examined several open-source MCP file servers. Many simply expose read/write (see [18]). For example, *save-filesystem-mcp* uses `exec("echo > file")` which is insecure【18†L281-L289】. Other servers (e.g. [30]) emphasize root confinement. We did not find a published MCP tool specifically for project scaffolding, so we rely on patterns from similar tools.

**VS Code Extension APIs:** A VS Code extension can create files via `workspace.fs.writeFile()` (async, safe)【56†L11-L13】. However, since our tool is a standalone MCP server (not a VS extension), we’ll use Node fs instead. If integrating in VS Code in the future, similar path checks and `Uri.file` must be used.

**Scaffolding CLIs:** Traditional scaffolders (Yeoman, Create-React-App) all copy static templates. *CRA* copies entire directories into a new app and errors on conflicts【40†L99-L107】. *Yeoman* uses a mem-fs layer to detect conflicts【57†L111-L119】, but ultimately it just writes chosen files. Neither is directly applicable, but lessons are:
- Always copy whole folders (like `.agent/context/*`, `.agent/roles/*`). 
- Check for existing files first.  
- No built-in rollback – we must implement backups ourselves.

For example, Yeoman’s conflict logic (from [57]) shows that **every pre-existing file write normally triggers a user prompt**【57†L111-L119】. We cannot do that, but we can imitate it by backing up. Yeoman’s file-utility snippet shows how templates are usually placed under a `templates/` folder and then copied to `destinationPath()`. Our MCP tool will similarly embed a `templates/agent/` directory and copy its contents.

**Tool Source Examples:** A deep dive into Yeoman or CRA code is beyond scope, but both use simple copy methods. We will use Node’s `fs.copyFile` for binary/text files. For text templates (like MD), no special merge is needed since these are mostly introductory docs. We can even do string replacement for placeholders if needed.

# Distribution & Update Strategy  

**Packaging Static Assets:** In the `mcp-server` package (npm), include `mcp-server/templates/agent/` in `"files"` or `"directories"` in `package.json`【34†L161-L166】 so that running `npm publish` includes the Markdown templates. For example:
```json
{
  "files": [
    "dist/",
    "templates/"
  ],
  "directories": {
    "templates": "templates"
  }
}
```
This ensures end users get the templates when they install/upgrade the MCP server.  

**Versioning:** Tie template versions to the npm package version. The tool can read its own `package.json` or `process.env.npm_package_version`. When running, compare this version to any stored `.agent/.meta.json` version. If templates have been updated, notify the user (or agent) that new scaffolding is available. We could also include a header in each generated file like `# Template version: x.y.z`.

**Updates & Diffs:** On a new MCP server release, the templates may change. If a project reruns `zorivest_setup_workspace` (e.g. after `npm update`), we want to update `.agent/` files without destroying local edits.  A possible approach:
- Compute diff (e.g. `diff3` or a JS library) between old file, old template, new template, then attempt a three-way merge.  
- If merging is too heavy, simpler is to backup old file and write new file, then let the developer manually merge changes by examining `.agent/.backup`.  
Since `.agent/` is primarily machine-generated helper content, heavy merging may not be worth it. However, a semi-automated merge (for Markdown) could be scripted.

**Notification:** The tool could return a structured result including `"updatedFiles": [...], "skippedFiles": [...]` so the calling agent can report what changed. We should log warnings if an existing file was overwritten. 

**Package Size:** Keep templates minimal. Markdown docs are tiny, so including them has negligible size impact. Still, use `.npmignore` or `files` to include only needed template directories (not e.g. tests or dev scratch).  

In sum, distribute templates via npm (with proper `files` field【34†L161-L166】) and include version metadata so updates are manageable.

# Architecture Recommendation  

**Tool Design:** `zorivest_setup_workspace` will be a TypeScript module in the `core` toolset. On initialization, it uses the MCP SDK (`McpServer`) with tools like:

```ts
server.tool("zorivest_setup_workspace", "Bootstrap AI agent workspace", {}, async () => {
  // Determine project root from MCP 'roots' or CWD
  const projectRoot = ...; 
  await setupAgentFolder(projectRoot, detectedClient);
  return { success: true };
});
```

Inside `setupAgentFolder(root, client)`, implement the patterns above:

1. **File System Operations:** Use `fs.mkdir` and `fs.writeFile` (as in previous section), after resolving/validating paths. For each directory listed in the spec (`context/`, `workflows/`, etc.), recursively create it.  

2. **Template Rendering:** Load static template files from `mcp-server/templates/agent/` (e.g. via `path.join(__dirname, '../templates/agent', relPath)`). For each file (including `AGENTS.md` and IDE files), read the template text, optionally replace placeholders, then call our safe write.  

3. **Client Detection:** Use the MCP client detection (already in `client-detection.ts`). If `client === "Gemini"`, we can note that (e.g. including "This file is tailored for Gemini"). But we still write all variants (e.g. `GEMINI.md`, `CLAUDE.md`, etc.), since multiple IDE use is possible.  

4. **Idempotency:** Before writing a file, check if it exists. If it does, copy it to `.agent/.backup/` (and append a timestamp or version to the name). Then write the new file. Optionally skip writing if the content is identical.  

5. **Meta Tracking:** Create or update `.agent/.meta.json` containing `{ "templateVersion": "1.2.0", "generatedOn": "...", "files": [ ... ] }`. Use this to prevent unnecessary re-generation and for debugging.  

6. **Error Handling:** If any step fails (permission error, path error), return a structured error to the agent. The MCP SDK’s error-handling will propagate to the calling AI.  

**TypeScript Snippet Example (illustrative):**  
```ts
async function scaffoldAgentWorkspace(root: string, client: string) {
  const templateDir = path.join(__dirname, 'templates', 'agent');
  const agentDir = path.join(root, '.agent');
  // Ensure .agent folder
  await fs.mkdir(agentDir, { recursive: true });
  
  // Common files
  const filesToCopy = [
    'AGENTS.md',
    ...clientVariants(client)  // e.g. ['GEMINI.md', 'CLAUDE.md', ...]
  ];
  for (const file of filesToCopy) {
    const src = path.join(templateDir, file);
    const dest = path.join(agentDir, file);
    let content = await fs.readFile(src, 'utf8');
    // Optionally replace placeholders, e.g. {{client}}
    content = content.replace(/{{client}}/g, client);
    await writeFileSafe(root, `.agent/${file}`, content);
  }
  // Similarly copy .agent/context/*, roles/*, etc.
}
```
Here `clientVariants` could be `["AGENTS.md", "GEMINI.md", ...]` always all.  

This architecture follows MCP patterns (tool name, JSON-RPC I/O, using `McpServer.tool()` callbacks) and meets the requirements with safe file operations, static templates, and idempotency. All code references file paths and operations explicitly, ensuring clarity.  

# References  

- MCP Specification – *Security Considerations* (validate roots, prevent traversal)【28†L243-L250】.  
- SylphxAI Filesystem-MCP – *Filesystem MCP features*: “Root directory confinement, Path traversal protection…”【30†L363-L368】.  
- Example MCP Filesystem Code – using `path.join` with `echo` (unsafe)【18†L281-L289】.  
- Yeoman Doc – *Conflict resolution*: pre-existing file writes require user confirmation【57†L111-L119】.  
- NPM Packaging – include static assets via `files`/`directories` fields【34†L161-L166】.  

