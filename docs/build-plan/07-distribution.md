# Phase 7: Distribution & Release

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) | Prerequisites: All previous phases

---

## Goal

Package the application for end-user distribution, publish library packages for developers, and automate the entire release lifecycle with secure, reproducible CI/CD pipelines.

---

## 7.1 Versioning Architecture

### Single Source of Truth

A root `.version` file is the canonical version for the entire product. All manifest files are derived from it at release time.

```
# .version — ecosystem-neutral, one line
1.0.0
```

### Version Sync Script

`scripts/sync_version.py` reads `.version` and propagates into:

| Target | Field | Translation |
|---|---|---|
| `packages/core/pyproject.toml` | `[project].version` | SemVer → PEP 440 (`1.0.0-rc.1` → `1.0.0rc1`) |
| `mcp-server/package.json` | `version` | Verbatim SemVer |
| `ui/package.json` | `version` | Verbatim SemVer |

Pre-release mapping (SemVer → PEP 440):
- `1.0.0-alpha.1` → `1.0.0a1`
- `1.0.0-beta.2` → `1.0.0b2`
- `1.0.0-rc.1` → `1.0.0rc1`

### Runtime Version Resolution

The backend resolves its version using a 3-context fallback:

```python
def get_version() -> str:
    # 1. Frozen executable (PyInstaller)
    if getattr(sys, "frozen", False):
        return _VERSION  # baked in by build script

    # 2. Installed package
    try:
        from importlib.metadata import version
        return version("zorivest-core")
    except Exception:
        pass

    # 3. Development mode — ascend to repo root
    current = Path(__file__).resolve().parent
    for _ in range(10):  # safety bound
        candidate = current / ".version"
        if candidate.exists():
            return candidate.read_text().strip()
        if current.parent == current:
            break
        current = current.parent
    raise FileNotFoundError("Could not find .version in any parent directory")
```

The REST API exposes `GET /version` returning `{"version": "1.0.0", "context": "frozen|installed|dev"}` for diagnostics.

### Pre-Release Support

| Channel | Version Format | npm dist-tag | PyPI Suffix |
|---|---|---|---|
| Stable | `1.0.0` | `latest` | (none) |
| Beta | `1.0.0-beta.1` | `next` | `1.0.0b1` |
| RC | `1.0.0-rc.1` | `next` | `1.0.0rc1` |

---

## 7.2 Version Bump Workflow

### `scripts/bump_version.py`

Pre-flight validation before any version change:

1. **Clean tree** — `git diff --exit-code` (abort if uncommitted changes)
2. **Branch policy** — must be on `main` (or `release/*`)
3. **Format validation** — must match `X.Y.Z` or `X.Y.Z-pre.N`
4. **Collision check** — query PyPI, npm, and GitHub API to confirm version is unreleased
5. **Sync** — run `sync_version.py` to update all manifests
6. **Commit & tag** — `git commit -m "chore: bump version to X.Y.Z"` + `git tag vX.Y.Z`

### Conventional Commits

All commits merged to `main` must follow the [Conventional Commits](https://www.conventionalcommits.org/) specification for automated changelog generation:

- `feat(core):` → minor bump
- `fix(mcp):` → patch bump
- `feat!:` or `BREAKING CHANGE:` → major bump

### Release Please Migration Path

The initial workflow uses `bump_version.py` for explicit control. When the team is ready for full automation, adopt [release-please](https://github.com/googleapis/release-please-action) with the `extra-files` pattern to atomically update `.version`, `pyproject.toml`, and `package.json` files from a single Release PR.

---

## 7.3 Desktop Application (Electron Builder)

The desktop app bundles both the Electron/React frontend and a PyInstaller-built Python backend into a single installer:

```bash
# 1. Build the Python backend as a standalone executable
pyinstaller --name zorivest-api --onefile --distpath dist-python packages/api/src/zorivest_api/__main__.py

# 2. Build the Electron app with the Python binary included as extra resource
npx electron-builder --config electron-builder.config.js
```

```javascript
// electron-builder.config.js
module.exports = {
  appId: 'com.zorivest.app',
  productName: 'Zorivest',
  directories: { output: 'dist' },
  extraResources: [
    { from: 'dist-python/zorivest-api${ext}', to: 'backend/' },
    { from: 'resources/service/', to: 'service/' },  // WinSW binary + XML config (Phase 10)
  ],
  win: { target: ['nsis'], icon: 'assets/icon.ico' },
  mac: { target: ['dmg'], icon: 'assets/icon.icns' },
  linux: { target: ['AppImage'] },
};
```

### Sidecar Runtime Detection

The Electron main process detects whether it's running in development or packaged mode:

```javascript
const backendPath = app.isPackaged
  ? path.join(process.resourcesPath, 'backend', 'zorivest-api' + (process.platform === 'win32' ? '.exe' : ''))
  : null; // dev mode: spawn python -m zorivest_api
```

### Frozen Path Resolution

PyInstaller bundles relocate modules to `sys._MEIPASS`. A runtime hook normalizes paths:

```python
if getattr(sys, "frozen", False):
    base_path = sys._MEIPASS
else:
    base_path = Path(__file__).resolve().parent
```

### Metadata in Frozen Builds

`importlib.metadata.version()` fails in frozen environments. The build process generates `_version.py` with the baked-in version string, removing the runtime dependency on dist-info discovery.

---

## 7.4 Python Library (PyPI)

```bash
# Publish zorivest-core to PyPI for Python developers
cd packages/core
uv build
uv publish  # or: twine upload dist/*
```

This enables other Python projects to `pip install zorivest-core` and use the domain entities, services, and calculator without the UI or MCP.

### OIDC Trusted Publishing

In CI, publishing uses PyPI's Trusted Publishing (OIDC) — no `PYPI_API_TOKEN` secret needed:

1. **Configure** — register the GitHub repo + workflow + environment as a "Trusted Publisher" on pypi.org
2. **Exchange** — the GitHub Actions job requests an OIDC token → PyPI validates claims (repo, workflow, branch)
3. **Publish** — PyPI issues a short-lived, project-scoped upload token

```yaml
# In publish.yml
- uses: pypa/gh-action-pypi-publish@<sha>
  with:
    attestations: true  # SLSA provenance
```

---

## 7.5 TypeScript MCP Server (npm)

```bash
# Publish standalone MCP server for AI agent users
cd mcp-server
npm run build
npm publish --access public  # @zorivest/mcp-server
```

Users install with `npx @zorivest/mcp-server --api-url http://localhost:8765` or add to their IDE's MCP configuration with a `Bearer` API key header for encrypted DB access (see [Phase 5 §5.7](05-mcp-server.md#step-57-mcp-auth-bootstrap)):

```json
{
  "mcpServers": {
    "zorivest": {
      "url": "http://localhost:8766/mcp",
      "headers": {
        "Authorization": "Bearer zrv_sk_<your_api_key>"
      }
    }
  }
}
```

### OIDC Trusted Publishing

npm trusted publishing with OIDC is GA (July 2025). Requires npm CLI ≥ 11.5.1:

1. **Configure** — link GitHub repo as a trusted publisher on npmjs.com
2. **Publish** — `npm publish --provenance --access public` (auto-detects CI, performs OIDC exchange)
3. **Provenance** — `--provenance` generates a SLSA attestation linking the package to the source commit

---

## 7.6 GitHub Actions: CI Pipeline (`ci.yml`)

**Trigger:** Push to `main`, Pull Requests

**Concurrency:** `cancel-in-progress: true` for PRs (save runner minutes on force-pushes)

```yaml
jobs:
  lint-python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<sha>
      - uses: astral-sh/setup-uv@<sha>
      - run: uv sync --frozen
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run pyright packages/core/src

  lint-mcp-server:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<sha>
      - uses: actions/setup-node@<sha>
        with: { node-version: 22, cache: npm }
      - run: npm ci
        working-directory: mcp-server
      - run: npx eslint .
        working-directory: mcp-server
      - run: npx tsc --noEmit
        working-directory: mcp-server

  lint-ui:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<sha>
      - uses: actions/setup-node@<sha>
        with: { node-version: 22, cache: npm }
      - run: npm ci
        working-directory: ui
      - run: npx eslint .
        working-directory: ui
      - run: npx tsc --noEmit
        working-directory: ui

  test-python:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@<sha>
      - uses: astral-sh/setup-uv@<sha>
      - run: uv sync --frozen
      - run: uv run pytest packages/core/tests -v

  test-mcp-server:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<sha>
      - uses: actions/setup-node@<sha>
        with: { node-version: 22, cache: npm }
      - run: npm ci
        working-directory: mcp-server
      - run: npx vitest run
        working-directory: mcp-server

  test-ui:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<sha>
      - uses: actions/setup-node@<sha>
        with: { node-version: 22, cache: npm }
      - run: npm ci
        working-directory: ui
      - run: npx vitest run
        working-directory: ui
```

---

## 7.7 GitHub Actions: Release Pipeline (`release.yml`)

**Trigger:** `push tags v*.*.*`

**Concurrency:** `group: release-${{ github.ref }}`, `cancel-in-progress: false` (every tag fully processed)

### Build Matrix

| Platform | Runner | PyInstaller Output | Electron Target | Signing |
|---|---|---|---|---|
| Windows | `windows-latest` | `zorivest-api.exe` | NSIS installer | Azure Trusted Signing |
| macOS | `macos-latest` | `zorivest-api` (ARM64) | DMG | Apple notarytool |
| Linux | `ubuntu-latest` | `zorivest-api` | AppImage | GPG (optional) |

### Job Flow

```
verify-version → build-backend (matrix) → build-desktop (matrix) → create-release
```

**Step 1 — Verify and normalize version:**
- Strip `v` prefix from tag → `SEMVER` job output (e.g. `1.0.0` or `1.0.0-rc.1`)
- Convert SemVer pre-release → PEP 440 → `PEP440` job output (e.g. `1.0.0rc1`)
- Verify `SEMVER` matches `.version` file content
- All downstream jobs consume `needs.verify-version.outputs.semver` and `needs.verify-version.outputs.pep440`

**Step 2 — Build backend (per OS):**
```yaml
- uses: astral-sh/setup-uv@<sha>
- run: uv sync --frozen  # pyinstaller is a uv dev dependency (see dependency-manifest.md)
- run: uv run pyinstaller --name zorivest-api --onefile --distpath dist-python packages/api/src/zorivest_api/__main__.py
- uses: actions/upload-artifact@<sha>
  with: { name: backend-${{ matrix.os }}, path: dist-python/ }
```

**Step 3 — Build desktop (per OS):**
```yaml
- uses: actions/download-artifact@<sha>
  with: { name: backend-${{ matrix.os }}, path: dist-python/ }
- uses: actions/setup-node@<sha>
  with: { node-version: 22, cache: npm }
- run: npm ci
  working-directory: ui
- run: npx electron-builder --config electron-builder.config.js
  working-directory: ui
# Code signing happens here (see §7.9)
- uses: actions/upload-artifact@<sha>
  with: { name: desktop-${{ matrix.os }}, path: dist/ }
```

**Step 4 — Create release:**
```yaml
- uses: actions/download-artifact@<sha>
  with: { pattern: desktop-*, merge-multiple: true, path: release-assets/ }
- run: sha256sum release-assets/* > release-assets/SHA256SUMS.txt
- uses: softprops/action-gh-release@<sha>
  with:
    files: release-assets/*
    generate_release_notes: true
```

---

## 7.8 GitHub Actions: Publish Pipeline (`publish.yml`)

**Trigger:** `release published` or `workflow_dispatch`

**Environments:** `pypi` and `npm` (configure required reviewers in GitHub repo settings)

### Job Flow

```
audit-deps → publish-pypi + publish-npm → verify-publication
```

**Dependency Audit Gate:**
```yaml
audit-deps:
  runs-on: ubuntu-latest
  steps:
    - run: uv run pip-audit --requirement uv.lock --strict --desc
    - run: npm audit --omit=dev --audit-level=high
```

**Publish PyPI:**
```yaml
publish-pypi:
  needs: audit-deps
  runs-on: ubuntu-latest
  environment: pypi
  permissions:
    id-token: write
    contents: read
  steps:
    - uses: actions/checkout@<sha>
    - uses: astral-sh/setup-uv@<sha>
    - run: uv build
    - uses: pypa/gh-action-pypi-publish@<sha>
      with:
        attestations: true
```

**Publish npm:**
```yaml
publish-npm:
  needs: audit-deps
  runs-on: ubuntu-latest
  environment: npm
  permissions:
    id-token: write
    contents: read
  steps:
    - uses: actions/checkout@<sha>
    - uses: actions/setup-node@<sha>
      with: { node-version: 22, registry-url: 'https://registry.npmjs.org' }
    - run: cd mcp-server && npm ci && npm run build
    - run: cd mcp-server && npm publish --provenance --access public
```

**Post-Publish Verification:**
```yaml
verify-publication:
  needs: [verify-version, publish-pypi, publish-npm]
  runs-on: ubuntu-latest
  steps:
    - run: pip install zorivest-core==${{ needs.verify-version.outputs.pep440 }} && python -c "from importlib.metadata import version; assert version('zorivest-core') == '${{ needs.verify-version.outputs.pep440 }}'"
    - run: npm info @zorivest/mcp-server@${{ needs.verify-version.outputs.semver }} version
```

> **Note:** `verify-version` is defined in `release.yml` (§7.7) and produces `semver` and `pep440` outputs. `publish.yml` must either re-run the normalization or accept these as `workflow_dispatch` inputs when triggered independently.

---

## 7.9 Code Signing

### Windows — Azure Trusted Signing

Azure Trusted Signing uses an HSM-backed certificate managed by Microsoft. No PFX files to store or rotate.

```yaml
- uses: azure/trusted-signing-action@<sha>
  with:
    azure-tenant-id: ${{ secrets.AZURE_TENANT_ID }}
    azure-client-id: ${{ secrets.AZURE_CLIENT_ID }}
    azure-client-secret: ${{ secrets.AZURE_CLIENT_SECRET }}
    endpoint: https://eus.codesigning.azure.net/
    trusted-signing-account-name: ${{ secrets.SIGNING_ACCOUNT }}
    certificate-profile-name: ${{ secrets.CERT_PROFILE }}
    files-folder: dist/
    files-folder-filter: exe
```

### macOS — Apple Notarization

Uses an ephemeral keychain on the runner. The certificate is stored as a base64-encoded GitHub Secret.

```yaml
# electron-builder handles signing + notarization when these env vars are set:
env:
  CSC_LINK: ${{ secrets.MAC_CERTS }}           # base64-encoded .p12
  CSC_KEY_PASSWORD: ${{ secrets.MAC_CERTS_PASSWORD }}
  APPLE_ID: ${{ secrets.APPLE_ID }}
  APPLE_APP_SPECIFIC_PASSWORD: ${{ secrets.APPLE_APP_PASSWORD }}
  APPLE_TEAM_ID: ${{ secrets.APPLE_TEAM_ID }}
```

### Linux — GPG (Optional)

GPG signing for `.deb` packages. Lower priority; AppImage does not require signing.

---

## 7.10 GitHub Actions: Test Release (`test-release.yml`)

**Trigger:** `workflow_dispatch`, PRs touching `electron-builder.config.js`, `pyproject.toml`, or `package.json`

Same matrix as `release.yml` but with key differences:

| Aspect | `release.yml` | `test-release.yml` |
|---|---|---|
| Code signing | Required | Skipped (if secrets absent) |
| GitHub Release | Created | Not created |
| Artifacts | Attached to Release | Upload for inspection only |
| Registry publish | Yes | `--dry-run` only |

```yaml
- run: cd mcp-server && npm publish --dry-run
- run: uv build && twine check dist/*
```

---

## 7.11 Auto-Update

### electron-updater Configuration

```yaml
# electron-builder.config.js (publish section)
publish:
  provider: github
  owner: matbanik
  repo: zorivest

# Update channels
channels:
  - latest    # stable
  - beta      # pre-release
```

### Update Metadata Files

On each release, `electron-builder` auto-generates:

| File | Platform |
|---|---|
| `latest.yml` | Windows |
| `latest-mac.yml` | macOS |
| `latest-linux.yml` | Linux |

These files are attached to the GitHub Release and consumed by `electron-updater` in the running app.

### Differential Updates

Enable `allowDowngrade: true` in updater config for emergency rollback scenarios. Electron Builder supports blockmap-based differential updates to minimize download size.

---

## 7.12 Security & Supply Chain

### GitHub Actions Hardening

| Practice | Implementation |
|---|---|
| Pin actions to SHA | `uses: actions/checkout@a5ac7e...` not `@v4` |
| Minimal permissions | Default `permissions: {}` at workflow level; grant per-job |
| Protected environments | `pypi` and `npm` environments with required reviewers |
| Concurrency controls | Prevent duplicate runs; no cancel-in-progress on release tags |
| Secret scanning | Enable GitHub secret scanning + push protection |

### Dependency Audit Gates

| Ecosystem | Tool | Policy |
|---|---|---|
| Python | `pip-audit` | Block on High/Critical CVEs |
| Node | `npm audit` | Block on High/Critical (`--audit-level=high`) |

Both run as the first job in `publish.yml`. A failed audit blocks all downstream publishing.

### Provenance & Attestations

- **PyPI:** `--attestations` flag on `pypa/gh-action-pypi-publish` generates SLSA provenance
- **npm:** `--provenance` flag on `npm publish` generates SLSA Level 1 attestation
- **Desktop:** SHA256SUMS.txt checksums attached to GitHub Release

---

## 7.13 Rollback & Emergency Procedures

### Desktop Application

**Primary:** Forward-fix — publish `v1.0.1` that reverts the problematic change in `v1.0.0`.

**Emergency (before fix is ready):**
1. Edit `latest.yml` in the GitHub Release to point back to the last working version's binary
2. `allowDowngrade: true` in updater config ensures the app accepts the "downgrade"
3. Users receive the working version on next auto-update check

### PyPI

1. **Yank** the bad version on pypi.org — yanked releases are hidden from `pip install` but remain available for pinned installs
2. Publish a corrected patch version

### npm

1. **Deprecate** the bad version: `npm deprecate @zorivest/mcp-server@1.0.0 "Critical bug — upgrade to 1.0.1"`
2. Cannot unpublish after 72 hours (npm policy) — deprecation is the safe path
3. Publish a corrected patch version

### Pre-Release Channels

Use beta/RC channels to stage-gate releases before promoting to stable:

```bash
# Publish beta to npm
npm publish --tag next --provenance --access public

# Promote to stable after validation
npm dist-tag add @zorivest/mcp-server@1.0.0-beta.3 latest
```

---

## 7.14 Caching Strategy

| Ecosystem | Cache Path | Key | Invalidation |
|---|---|---|---|
| Python (uv) | `~/.cache/uv` | hash of `uv.lock` | Lockfile change |
| Node (npm) | `~/.npm` | hash of `package-lock.json` | Lockfile change |
| Electron | `~/.cache/electron`, `~/.cache/electron-builder` | Electron version | Version change |

Cache is keyed per-OS in matrix builds. `actions/setup-node` and `astral-sh/setup-uv` handle caching natively when configured.

---

## 7.15 Exit Criteria

- [ ] `.version` file exists and `sync_version.py` keeps all manifests in sync
- [ ] Desktop installer builds for Windows, macOS, Linux via `release.yml`
- [ ] All desktop installers are code-signed (Windows + macOS)
- [ ] SHA256 checksums generated and attached to GitHub Release
- [ ] PyPI package publishes via OIDC trusted publishing and installs correctly
- [ ] npm package publishes via OIDC trusted publishing and serves MCP tools
- [ ] `ci.yml` runs lint + typecheck + test on every PR
- [ ] `test-release.yml` validates packaging without publishing
- [ ] `publish.yml` passes dependency audit before publishing
- [ ] Post-publish verification confirms correct versions on registries
- [ ] Auto-updater delivers updates to installed desktop apps

## 7.16 Outputs

| Artifact | Destination | Verification |
|---|---|---|
| Windows NSIS installer (signed) | GitHub Releases | SHA256 checksum |
| macOS DMG (notarized) | GitHub Releases | SHA256 checksum |
| Linux AppImage | GitHub Releases | SHA256 checksum |
| `zorivest-core` wheel | PyPI | `pip install` + version check |
| `@zorivest/mcp-server` tarball | npm | `npm info` + version check |
| SHA256SUMS.txt | GitHub Releases | Manual or automated verification |
| Auto-update metadata | GitHub Releases | `latest.yml` / `latest-mac.yml` / `latest-linux.yml` |

## 7.17 Files Involved

| File | Purpose |
|---|---|
| `.version` | Single source of truth for product version |
| `scripts/sync_version.py` | Propagate version to all manifests |
| `scripts/bump_version.py` | Pre-flight checks + version bump + tag |
| `packages/core/pyproject.toml` | Python package version (derived) |
| `mcp-server/package.json` | npm package version (derived) |
| `ui/package.json` | Electron app version (derived) |
| `electron-builder.config.js` | Desktop packaging configuration |
| `.github/workflows/ci.yml` | Commit gate (lint, typecheck, test) |
| `.github/workflows/release.yml` | Tag-triggered desktop builds |
| `.github/workflows/publish.yml` | Registry publishing (PyPI + npm) |
| `.github/workflows/test-release.yml` | Dry-run packaging validation |

## 7.18 Branch Protection Required Checks

GitHub branch protection rules for `main` must require the following status checks before merge:

### Existing CI Checks (from `ci.yml`)

| Required Check | Job Name | What It Gates |
|---|---|---|
| Python type check | `lint-python` | No type errors in `packages/` |
| Python lint | `lint-python` | No ruff violations |
| Python tests | `test-python` | All pytest suites pass (3-OS matrix) |
| TS type check (MCP) | `lint-mcp-server` | No TypeScript errors in `mcp-server/` |
| TS type check (UI) | `lint-ui` | No TypeScript errors in `ui/` |
| TS tests (MCP) | `test-mcp-server` | All Vitest suites pass |
| TS tests (UI) | `test-ui` | All Vitest suites pass |

### Planned Integrity Checks (added as code arrives)

| Required Check | Job Name | What It Gates | Phase |
|---|---|---|---|
| Feature eval | `feature-eval` | FAIL_TO_PASS + PASS_TO_PASS regression suite passes | Phase 1+ |
| Contract verification | `contract-verify` | Pact provider verification passes | Phase 4+ |
| Mutation score | `mutation-score` | mutmut/StrykerJS threshold met (≥60%, ratcheting) | Phase 1+ |
| Evidence manifest | `evidence-manifest` | Handoff evidence bundle exists and is non-empty | Phase 1+ |

> **Note:** Planned checks are added to `ci.yml` as their corresponding code is implemented. Until then, they are tracked here as the target state for branch protection.

### Configuration

```yaml
# GitHub repo settings → Branches → Branch protection rules → main
# Required status checks before merging:
#   ✅ Require status checks to pass before merging
#   ✅ Require branches to be up to date before merging
#   Status checks:
#     - lint-python
#     - lint-mcp-server
#     - lint-ui
#     - test-python
#     - test-mcp-server
#     - test-ui
#     # Add when implemented:
#     # - feature-eval
#     # - contract-verify
#     # - mutation-score
#     # - evidence-manifest
```
