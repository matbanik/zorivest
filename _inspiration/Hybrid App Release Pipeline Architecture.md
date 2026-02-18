# **Comprehensive Release Pipeline Architecture for Zorivest: A Hybrid Python/TypeScript Monorepo System**

## **1\. Strategic Foundations of Hybrid Release Architectures**

### **1.1. The Evolution of Release Engineering in 2026**

The landscape of software delivery has undergone a fundamental transformation in recent years, shifting from a focus on mere automation to a rigorous emphasis on supply chain security, provenance, and immutability. For a complex, hybrid application like Zorivest—which integrates a Python backend, a TypeScript Model Context Protocol (MCP) server, and an Electron desktop interface within a single monorepo—the release pipeline acts as the central nervous system of the project. It is no longer sufficient to simply compile code and upload binaries; the modern release process must guarantee that the artifacts distributed to users are cryptographically verifiable, functionally validated in production-like environments, and resilient to the compromise of individual developer credentials.

In the context of 2026, the "works on my machine" paradigm has been entirely supplanted by ephemeral Continuous Integration (CI) environments that leverage OpenID Connect (OIDC) for identity federation.1 This architectural shift eliminates long-lived secrets, such as API tokens, which have historically been the primary vector for supply chain attacks. For Zorivest, this means that the identity of the release engineer is replaced by the identity of the specific GitHub Actions workflow run, authenticated directly against package registries like PyPI and npm and cloud providers like Azure and AWS.

The architecture proposed in this report is designed to solve the specific "impedance mismatches" inherent in hybrid development. Python and Node.js ecosystems have divergent philosophies regarding versioning, dependency resolution, and packaging. Python relies on venv and pip (or modern successors like uv) and often struggles with path resolution when "frozen" into executables.3 The Node.js ecosystem, particularly within Electron, assumes a different module resolution strategy and heavily utilizes asynchronous patterns. The release pipeline acts as the translation layer, ensuring that a semantic version bump in the Python core propagates correctly to the Electron bundler, and that the resulting artifacts maintain strict parity across Windows, macOS, and Linux platforms.

### **1.2. Architectural Pillars**

To manage this complexity, the Zorivest release architecture is built upon four foundational pillars that guide every technical decision detailed in this report:

1. **Immutable Artifacts & Deep Provenance:** Every release artifact—whether a Python wheel, an npm tarball, or an Electron installer—must be traceable back to a specific, immutable git commit SHA. We leverage the SLSA (Supply-chain Levels for Software Artifacts) framework, targeting Level 3 compliance. This involves generating signed attestations and Software Bill of Materials (SBOMs) during the build process, ensuring that consumers (and the auto-updater) can verify that the binary they are executing was built by the authorized CI pipeline and has not been tampered with.2  
2. **Ephemeral Identity & Zero-Trust Access:** The architecture adheres to a zero-trust model for CI/CD. Long-lived secrets are deprecated in favor of short-lived OIDC tokens. This ensures that even if a repository is compromised, attackers cannot extract persistent credentials to inject malicious code into future releases. Authentication exists only for the duration of the build job.1  
3. **Environment Parity via Deterministic Locking:** The pipeline enforces strict parity between development, testing, and build environments. This is achieved through the rigorous use of lockfiles—uv.lock for Python and package-lock.json for Node.js. By pinning dependencies (including transitive ones) to specific hashes, we eliminate "dependency drift," a common failure mode where production builds fail or behave differently due to subtle version discrepancies in underlying libraries.5  
4. **Resilience and Graceful Recovery:** Recognizing that failures are inevitable in distributed systems, the architecture includes automated rollback capabilities. This utilizes Electron’s differential update channels to facilitate rapid downgrades and maintains strict "yank" procedures for registry packages to mitigate the impact of bad releases.7

## ---

**2\. Monorepo Governance and Version Control Strategy**

### **2.1. Directory Structure and Separation of Concerns**

The physical organization of the Zorivest monorepo must explicitly separate concerns while enabling shared tooling to operate effectively. A flat structure where distinct packages reside at the top level is generally discouraged in favor of a categorized packages/ directory, although the MCP server and UI often warrant their own root-level directories due to their distinct build lifecycles. The recommended structure for Zorivest facilitates the isolation required for independent publishing while maintaining the unified context needed for the desktop bundle.

| Path | Component | Ecosystem | Responsibility |
| :---- | :---- | :---- | :---- |
| packages/core | zorivest-core | Python (FastAPI) | Domain logic, REST API, Database ORM. Published to PyPI. |
| packages/api | Shared Schemas | Polyglot (JSON/IDL) | Shared types or protocol definitions (optional). |
| mcp-server | @zorivest/mcp-server | TypeScript | AI Context Protocol implementation. Published to npm. |
| ui | zorivest-desktop | Electron/React | Desktop GUI, orchestrator of the sidecar processes. |
| .github/workflows | CI/CD | YAML | Definition of build, test, and release pipelines. |
| tools | Dev Tooling | Shell/Python | Local development scripts, seed data, and scaffolding. |

This structure supports the specific requirements of the pipeline. For instance, the ui directory contains the electron-builder.yml configuration, which references build artifacts from packages/core. By keeping zorivest-core in a distinct package, we enable it to be tested and released independently of the desktop UI, which is critical for headless deployments or usage by other clients.9

### **2.2. Branching Strategy: Trunk-Based Development**

For a project of this complexity, **Trunk-Based Development** provides a significant advantage over GitFlow. In a hybrid monorepo, long-lived feature branches frequently lead to "merge hell," particularly regarding lockfiles. When a developer updates a Python dependency in a feature branch while another updates a Node dependency in main, merging the divergent lockfiles (uv.lock and package-lock.json) can be error-prone and time-consuming.

The Zorivest pipeline is optimized for a workflow where the main branch is the single source of truth and is always in a deployable state.

* **Main Branch (main)**: Commits to this branch trigger immediate "canary" builds or pre-release deployments to an internal update channel. This ensures that integration issues between the Python backend and the Electron frontend are detected immediately.10  
* **Feature Branches**: These are short-lived and merged via Pull Request (PR). Every PR must pass the "Commit Gate" pipeline, which runs the full suite of linting, type-checking, and tests across both languages.  
* **Release Branches (Optional)**: While generally discouraged in pure trunk-based development, release branches (e.g., release/v2.0) may be utilized for stabilizing a major release. However, the preferred method is to tag directly from main to trigger the release workflow.

### **2.3. Automated Version Management**

Managing versions in a monorepo containing multiple languages is a notorious friction point. A unified versioning approach (lock-step) simplifies the desktop app's identity (e.g., "Zorivest v2.0") but forces unnecessary version bumps on internal libraries that haven't changed. Conversely, independent versioning increases the complexity of tracking compatibility between the frontend and backend.

This architecture employs **Release Please** (Google) as the primary versioning engine. It analyzes commit messages following the **Conventional Commits** specification to determine the scope and magnitude of changes.11 For example, a commit message feat(core): add new user endpoint triggers a minor version bump for zorivest-core but keeps mcp-server unchanged.

#### **2.3.1. The "Extra-Files" Pattern for Hybrid Syncing**

A critical challenge in hybrid repos is synchronizing version numbers across different manifest formats. release-please natively handles package.json for Node.js but requires configuration to manage pyproject.toml for Python effectively.12

We mitigate this by configuring the release-please-config.json to treat the Python manifest as an "extra file" linked to the release logic. This ensures that when the release automation decides to bump the version based on the changelog, it atomically updates both the package.json (if present in the core package for tooling) and the pyproject.toml.

**Synchronization Logic:** To prevent the Python backend from diverging from the Electron frontend, the pipeline enforces a dependency constraint. The ui package's build process reads the version directly from the zorivest-core package during the build. This ensures that the bundled executable reports a coherent version number to the Operating System, avoiding situations where the "About" dialog shows v2.0 but the internal API reports v1.9.13

The configuration enables a unified "Release PR." When a developer merges feature PRs into main, Release Please accumulates the changes. It then opens a special PR that, when merged, triggers the tagging and publishing workflows. This human-in-the-loop step allows for final review of the generated CHANGELOG.md before publication.14

## ---

**3\. The Python Core Pipeline: Security and Provenance**

The zorivest-core package is the computational engine of the application. Its release pipeline prioritizes correctness, performance, and strict supply chain security. Unlike the TypeScript components, the Python ecosystem relies on specific packaging standards (PEP 517/518) that the pipeline must respect.

### **3.1. Modern Dependency Management with uv**

The Python packaging landscape has evolved significantly. We select **uv** (by Astral) over traditional tools like Pipenv or Poetry for its superior speed and compatibility with standard standards.5 uv serves as a drop-in replacement for pip and pip-tools but operates orders of magnitude faster due to its Rust-based implementation.

**Lockfile Strategy:** The uv.lock file is the source of truth for the Python environment. It creates a deterministic build graph, resolving not just direct dependencies but the entire transitive tree with specific hashes. This is critical for the "frozen" environment of the Electron app; we cannot afford for the bundled Python environment to differ from the tested environment due to a minor patch in a sub-dependency.15

**Caching in CI:** In GitHub Actions, we cache the uv environment to speed up builds. However, simply caching the venv directory can lead to stale binaries. The optimal strategy is to cache the global uv cache directory (\~/.cache/uv) and allow uv sync to reconstruct the virtual environment. This operation is nearly instantaneous and ensures that the environment is always fresh and correct according to the lockfile.5

### **3.2. Build and Test Matrix**

The backend must be validated against the diverse environments it will encounter in the desktop distribution. We employ a **Matrix Testing Strategy** that runs the test suite across Linux (Ubuntu), Windows, and macOS runners.16

1. **Static Analysis**: Before running tests, the pipeline executes ruff for linting and formatting. ruff replaces the slower combination of Flake8, Black, and isort.  
2. **Type Consistency**: mypy is executed to ensure strict type compliance. This is particularly important for the FastAPI models, which define the contract consumed by the TypeScript frontend.  
3. **Integration Testing**: pytest runs the test suite. The pipeline specifically targets tests that involve file system operations or OS-specific syscalls, as these are the most likely to fail when cross-platform.17

### **3.3. Trusted Publishing to PyPI**

The publishing step utilizes PyPI's **Trusted Publishing** mechanism, which leverages OIDC to eliminate the need for persistent PYPI\_API\_TOKEN secrets in GitHub.1

**The OIDC Workflow:**

1. **Token Exchange**: The publish-pypi job requests an OIDC token from GitHub's identity provider.  
2. **Verification**: This token is sent to PyPI. PyPI validates the token's signature and checks the claims against the configured "Publisher" trust relationship (e.g., verifying that the token comes from the zorivest repo, the release.yml workflow, and the main branch).  
3. **Short-Lived Access**: If validated, PyPI issues a short-lived API token scoped strictly to the zorivest-core project for the duration of the upload.

**Attestations:** The pipeline enables the generation of digital attestations. These are cryptographically signed metadata files that link the published wheel back to the specific GitHub Actions run that created it. This provides a verifiable trail of provenance, satisfying high-level security requirements.19

### **3.4. Dependency Auditing**

Security scanning is integrated directly into the pipeline ("shift-left"). Before any build artifact is produced, pip-audit scans the uv.lock file against the Open Source Vulnerability (OSV) database.20

* **Policy**: The pipeline is configured to fail if any vulnerabilities with a "High" or "Critical" severity are found.  
* **Resolution**: If a vulnerability is detected, the release is blocked until the dependency is updated via uv lock \--upgrade-package \<name\>. This prevents the propagation of known security flaws into the desktop executable.21

## ---

**4\. The MCP Server Pipeline: Standardization and Registry Integration**

The @zorivest/mcp-server component acts as the bridge for AI context, exposing the application's data and tools to Large Language Models (LLMs). As a TypeScript project, it follows standard Node.js practices but requires specific validation to ensure compliance with the Model Context Protocol.

### **4.1. Protocol Compliance and Validation**

The MCP server must adhere to a strict JSON schema to be usable by clients like Claude Desktop or generic MCP inspectors. The release pipeline includes a validation step that checks the server.json manifest against the official schema.22

**Schema Validation:**

The build script validates the server.json to ensure:

* **Naming**: The name field follows the io.github.\<user\>.\<repo\> or com.\<company\>.\<product\> format required for registry discovery.23  
* **Capabilities**: The defined tools and resources are correctly structured.  
* **Version**: The version in server.json matches the package.json version.

### **4.2. Build and Type Safety**

The build process utilizes tsc (TypeScript Compiler) to transpile the source code to JavaScript. We enforce strict: true in tsconfig.json to prevent runtime errors. The build produces both CommonJS (CJS) and ECMAScript Module (ESM) formats if necessary, though ESM is preferred for modern Node.js environments.24

### **4.3. Trusted Publishing to npm**

Similar to the Python pipeline, the npm publishing workflow utilizes OIDC to authenticate with the npm registry, removing the need for NPM\_TOKEN secrets.1

**Mechanism:**

1. **Permission**: The GitHub Action job is granted id-token: write permission.  
2. **Token Exchange**: The npm publish command (v11.5.1+) automatically detects the CI environment and performs the OIDC exchange with the configured npm Trusted Publisher.  
3. **Provenance**: The pipeline executes npm publish \--provenance. This flag instructs npm to generate a provenance attestation (following SLSA Level 1 standards) that links the package to the source repository and build instructions.2

**Registry Integration:** If Zorivest intends to be listed in the public MCP registry (currently in preview), the pipeline includes a step to verify ownership. For GitHub-based namespaces, this verification is often automatic via the OIDC link, but for custom domains, a DNS verification record may be required. The pipeline can automate the metadata submission using the mcp-publisher CLI tool provided by the Model Context Protocol organization.25

## ---

**5\. The Desktop Bundle: Integrating Heterogeneous Runtimes**

The Electron desktop application (ui) represents the integration point where the Python backend and React frontend converge. This is the most complex segment of the pipeline, requiring the bundling of the Python environment, cross-compilation, and OS-specific code signing.

### **5.1. The Sidecar Pattern: Bundling Python with PyInstaller**

The desktop application cannot assume the end-user has Python installed. Therefore, zorivest-core is bundled as a standalone executable using **PyInstaller**. This executable runs as a "sidecar" process managed by the Electron main process.

#### **5.1.1. Solving the "Frozen" Path Problem**

A ubiquitous failure mode in bundled Python apps involves path resolution. When running from source, Python uses standard file paths. When bundled, PyInstaller unpacks dependencies to a temporary directory (sys.\_MEIPASS).

* **Runtime Hooks**: The pipeline injects a runtime hook that detects if the application is "frozen" (getattr(sys, 'frozen', False)) and normalizes paths accordingly.26  
* **Electron Integration**: The Electron main.js must implement logic to locate the backend executable.  
  * **Development**: It spawns python packages/core/src/main.py.  
  * **Production**: It uses app.isPackaged to determine if it should spawn the bundled executable located in process.resourcesPath.27

#### **5.1.2. Metadata and Discovery Issues**

Modern Python packages often use importlib.metadata to retrieve version info or entry points. In frozen PyInstaller environments, the standard dist-info directories are often missing or relocated, causing calls like version('zorivest-core') to fail.28

* **Mitigation**: The build pipeline generates a \_version.py file during the build process, baking the version string directly into the code. This removes the runtime dependency on package metadata lookup for version information.

### **5.2. Cross-Platform Build Matrix**

To support Windows, macOS, and Linux, the pipeline utilizes a **Matrix Strategy** in GitHub Actions. We cannot cross-compile signed binaries easily (e.g., signing a Windows .exe on Linux is possible but complex; signing a macOS app on Linux is impossible). Therefore, the build runs on native runners.30

| OS | Runner | Build Target | Signing Tool |
| :---- | :---- | :---- | :---- |
| **Windows** | windows-latest | nsis (Installer), portable | Azure Trusted Signing |
| **macOS** | macos-latest | dmg, zip | Apple Notary Service (notarytool) |
| **Linux** | ubuntu-latest | AppImage, deb | GPG (optional) |

### **5.3. Electron Builder Configuration**

The electron-builder.yml acts as the master orchestrator for the final artifact. It is configured to include the PyInstaller output as an "extra resource."

**Configuration Strategy:**

YAML

extraResources:  
  \- from: "../packages/core/dist/zorivest-backend"  
    to: "backend"  
    filter: \["\*\*/\*"\]

This directive instructs Electron Builder to copy the executable generated by PyInstaller into the resources/backend directory of the installed application.31 This separation ensures that the Python environment is isolated from the Electron runtime but accessible via standard IPC or HTTP calls.

### **5.4. Code Signing Automation**

Code signing is mandatory for the desktop app to avoid "Unknown Publisher" warnings and to function on macOS.

#### **5.4.1. Windows: Azure Trusted Signing**

The pipeline adopts **Azure Trusted Signing** (formerly Azure Code Signing), which modernizes the signing process by removing the requirement for physical hardware tokens (HSMs) or local PFX file management.32

* **Identity**: An Azure Identity is linked to the GitHub Runner via OIDC.  
* **Process**: The azure/trusted-signing-action is invoked. It uploads the digest of the binary to Azure, where it is signed by a Microsoft-managed certificate, and the signature is returned and attached to the binary.32  
* **Benefit**: This eliminates the risk of private key theft, as the key never leaves the Azure HSM.

#### **5.4.2. macOS: Notarization**

For macOS, we utilize the standard Apple Developer ID Application certificate but implement it securely using ephemeral keychains.

* **Keychain Management**: A script runs on the runner to create a temporary keychain, import the base64-encoded certificate from GitHub Secrets, and unlock it for the duration of the build.30  
* **Notarization**: The electron-builder configuration includes a notarize block using notarytool. It submits the signed app to Apple's notarization service, waits for approval, and staples the ticket to the app.33

## ---

**6\. CI/CD Orchestration and Environment Management**

The orchestration layer ties the individual build components together into a coherent release workflow. This section details the logic governing the GitHub Actions pipelines.

### **6.1. Concurrency Control**

To prevent race conditions and conserve resources, we utilize GitHub Actions concurrency groups.

* **PRs**: For Pull Requests, cancel-in-progress: true is enabled. If a developer pushes a new commit to the PR while a build is running, the old build is cancelled immediately.34  
* **Releases**: For the release workflow (triggered by tags), cancel-in-progress is set to false. This ensures that every tagged release is fully processed, preventing partial deployments if tags are pushed in quick succession.

### **6.2. Caching Strategies**

Performance is critical for a large monorepo. The pipeline implements aggressive caching:

* **Python**: The uv cache is persisted across runs. The cache key is derived from the hash of uv.lock. If the lockfile hasn't changed, dependency installation is nearly instantaneous.5  
* **Node**: The npm cache (\~/.npm) is cached based on package-lock.json.  
* **Electron**: electron-builder caches the Electron binaries and other download artifacts to prevent re-downloading large files on every run.

### **6.3. Artifact Management**

The pipeline uses the upload-artifact and download-artifact actions to pass data between jobs.

1. **Build Phase**: The build-core job builds the Python executable and uploads it as an artifact named backend-dist.  
2. **Package Phase**: The build-desktop job downloads backend-dist and places it into the correct directory before invoking Electron Builder.  
   This decoupling allows the Python build to fail independently of the UI build, facilitating easier debugging.

### **6.4. The Release Gate Pattern**

The pipeline implements a "Release Gate" workflow.

1. **Trigger**: Merging a PR with conventional commits to main.  
2. **Action**: release-please calculates the new version and updates CHANGELOG.md, package.json, and pyproject.toml.  
3. **Result**: It opens a "Release PR".  
4. **Merge**: When the Release PR is merged, release-please creates a GitHub Release Tag. This tag triggers the final publish workflow.

This pattern puts a human in the loop for the final verification of the changelog, preventing accidental releases from automated commits.

## ---

**7\. Quality Assurance: From Unit Tests to E2E Verification**

Deploying a desktop application is high-stakes; unlike a web app, you cannot simply "refresh" the user's client to fix a bug. Therefore, the QA gates in the pipeline are rigorous.

### **7.1. Smoke Testing with Playwright**

Unit tests verify logic, but they do not verify that the packaged application actually launches. We use **Playwright** for End-to-End (E2E) testing of the Electron app.35

* **Strategy**: The test suite launches the *packaged* Electron executable, not the source code. This catches issues related to bundling, such as missing assets or incorrect path resolution in the production build.36  
* **Test Case**: The "Smoke Test" verifies that the main window opens, the title is correct, and—crucially—that the UI can communicate with the Python backend (e.g., verifying that the backend health-check endpoint returns 200 OK).  
* **Observability**: If the test fails, Playwright captures a video recording and screenshots of the application state. These are uploaded as GitHub Actions artifacts, allowing developers to replay the failure visually.

### **7.2. Dry-Run Validations**

Before any artifact is pushed to a public registry, the pipeline executes dry-runs.

* **npm**: npm publish \--dry-run is executed to validate the package contents and ensure no files are missing from the files allowlist in package.json.37  
* **PyPI**: uv build combined with twine check (if using twine) or uv publish \--dry-run validates that the package metadata (README rendering, version format) meets PyPI standards.

### **7.3. Checksum Verification**

To ensure download integrity for the desktop installers, the pipeline includes a final job that generates SHA-256 checksums for all assets (e.g., Zorivest-Setup.exe, Zorivest.dmg).

* **Generation**: The workflow runs sha256sum \* \> checksums.txt on the artifacts.  
* **Publication**: This checksums.txt file is uploaded to the GitHub Release. Users can verify their download against this hash to detect corruption or tampering.38

## ---

**8\. Release Distribution and Rollback Mechanisms**

### **8.1. Distribution Strategy**

The release distribution is multi-channel:

* **PyPI**: Hosts zorivest-core for Python developers.  
* **npm**: Hosts @zorivest/mcp-server for Node.js/MCP consumers.  
* **GitHub Releases**: Hosts the Electron desktop installers and auto-update metadata files (latest.yml, latest-mac.yml).

### **8.2. Rollback Philosophy: The "Forward Fix"**

In modern DevOps, attempting to revert the git history (e.g., git reset \--hard) is often more dangerous than moving forward, especially in a shared monorepo. The primary rollback strategy is a **Forward Fix**.

1. **Revert**: The developer creates a PR that reverts the problematic commit in main.  
2. **Release**: This merge triggers the pipeline to build the *next* version (e.g., v1.2.4), which functionally restores the state of the stable v1.2.2.

### **8.3. Registry Recovery (Yank)**

If a critical security flaw is published to the package registries:

* **PyPI**: The release engineer uses the "Yank" feature on PyPI. The release remains historically available for audit but is ignored by installers (pip install) unless explicitly pinned.  
* **npm**: Unpublishing is restricted after 72 hours to prevent breaking the ecosystem. We use npm deprecate to warn users against installing the compromised version, effectively marking it as "do not use."

### **8.4. Desktop Downgrade Procedures**

Electron Updater supports channel-based updates and downgrades, providing a mechanism to rescue users from a broken release.

* **Scenario**: v2.0.0 is broken and causing crashes.  
* **Recovery Action**:  
  1. Publish v2.0.1 immediately (even if it's just a revert).  
  2. If an immediate stop is required before a new build can finish, we can modify the latest.yml file in the update release bucket. By editing this YAML file to point back to the v1.9.9 binary and ensuring allowDowngrade: true is set in the updater configuration, the application will detect the "update" to the older (working) version and apply it.7

## ---

**9\. Conclusion**

The Zorivest release pipeline architecture represents a synthesis of the most advanced practices available in 2026\. By adopting **OIDC Trusted Publishing**, it eliminates the persistent security risks associated with static API tokens. By integrating **Azure Trusted Signing**, it simplifies and secures the Windows delivery chain. The **Hybrid Monorepo** strategy, governed by **Release Please**, successfully bridges the versioning gap between Python and TypeScript, ensuring that the application evolves as a cohesive unit while respecting the distinct standards of each ecosystem.

This architecture transforms the release process from a manual, error-prone task into a fully automated, verifiable software factory. It ensures that every line of code written is not only tested and integrated but also signed, sealed, and delivered to users with cryptographic proof of its origin, providing a robust foundation for the long-term success of the Zorivest platform.

#### **Works cited**

1. npm trusted publishing with OIDC is generally available \- GitHub Changelog, accessed February 17, 2026, [https://github.blog/changelog/2025-07-31-npm-trusted-publishing-with-oidc-is-generally-available/](https://github.blog/changelog/2025-07-31-npm-trusted-publishing-with-oidc-is-generally-available/)  
2. Trusted publishing for npm packages, accessed February 17, 2026, [https://docs.npmjs.com/trusted-publishers/](https://docs.npmjs.com/trusted-publishers/)  
3. What PyInstaller Does and How It Does It, accessed February 17, 2026, [https://pyinstaller.org/en/stable/operating-mode.html](https://pyinstaller.org/en/stable/operating-mode.html)  
4. PyInstaller | Python Tools, accessed February 17, 2026, [https://realpython.com/ref/tools/pyinstaller/](https://realpython.com/ref/tools/pyinstaller/)  
5. Optimizing uv in GitHub Actions: One Global Cache to Rule Them All | by szeyusim | Medium, accessed February 17, 2026, [https://szeyusim.medium.com/optimizing-uv-in-github-actions-one-global-cache-to-rule-them-all-9c64b42aee7f](https://szeyusim.medium.com/optimizing-uv-in-github-actions-one-global-cache-to-rule-them-all-9c64b42aee7f)  
6. How to Optimize GitHub Actions Performance, accessed February 17, 2026, [https://oneuptime.com/blog/post/2026-02-02-github-actions-performance-optimization/view](https://oneuptime.com/blog/post/2026-02-02-github-actions-performance-optimization/view)  
7. Make it possible to "auto-downgrade" the application on channel change \#1149 \- GitHub, accessed February 17, 2026, [https://github.com/electron-userland/electron-builder/issues/1149](https://github.com/electron-userland/electron-builder/issues/1149)  
8. electron updater.Class.AppUpdater, accessed February 17, 2026, [https://www.electron.build/electron-updater.class.appupdater](https://www.electron.build/electron-updater.class.appupdater)  
9. Monorepo approach to handle multiple projects \- Python Discussions, accessed February 17, 2026, [https://discuss.python.org/t/monorepo-approach-to-handle-multiple-projects/78349](https://discuss.python.org/t/monorepo-approach-to-handle-multiple-projects/78349)  
10. Release Using Channels \- electron-builder, accessed February 17, 2026, [https://www.electron.build/tutorials/release-using-channels.html](https://www.electron.build/tutorials/release-using-channels.html)  
11. googleapis/release-please-action: automated releases ... \- GitHub, accessed February 17, 2026, [https://github.com/googleapis/release-please-action](https://github.com/googleapis/release-please-action)  
12. Update package.json version with release-please-action in monorepo \- Stack Overflow, accessed February 17, 2026, [https://stackoverflow.com/questions/77043024/update-package-json-version-with-release-please-action-in-monorepo](https://stackoverflow.com/questions/77043024/update-package-json-version-with-release-please-action-in-monorepo)  
13. Writing your pyproject.toml \- Python Packaging User Guide, accessed February 17, 2026, [https://packaging.python.org/en/latest/guides/writing-pyproject-toml/](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)  
14. How to Implement Semantic Versioning Automation \- OneUptime, accessed February 17, 2026, [https://oneuptime.com/blog/post/2026-01-25-semantic-versioning-automation/view](https://oneuptime.com/blog/post/2026-01-25-semantic-versioning-automation/view)  
15. dev-dependencies in workspace pyproject.toml not installed with uv run \#7487 \- GitHub, accessed February 17, 2026, [https://github.com/astral-sh/uv/issues/7487](https://github.com/astral-sh/uv/issues/7487)  
16. PyInstaller Documentation \- Read the Docs, accessed February 17, 2026, [https://readthedocs.org/projects/pyinstaller/downloads/pdf/stable/](https://readthedocs.org/projects/pyinstaller/downloads/pdf/stable/)  
17. Steps to Build Binary Executables for Python Code with GitHub Actions \- DEV Community, accessed February 17, 2026, [https://dev.to/rahul\_suryash/steps-to-build-binary-executables-for-python-code-with-github-actions-4k92](https://dev.to/rahul_suryash/steps-to-build-binary-executables-for-python-code-with-github-actions-4k92)  
18. Publishing package distribution releases using GitHub Actions CI/CD workflows, accessed February 17, 2026, [https://packaging.python.org/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/](https://packaging.python.org/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)  
19. pypi-publish · Actions · GitHub Marketplace, accessed February 17, 2026, [https://github.com/marketplace/actions/pypi-publish](https://github.com/marketplace/actions/pypi-publish)  
20. pypa/pip-audit: Audits Python environments, requirements files and dependency trees for known security vulnerabilities, and can automatically fix them \- GitHub, accessed February 17, 2026, [https://github.com/pypa/pip-audit](https://github.com/pypa/pip-audit)  
21. Automated Patching of Python Dependencies: Securing Your Codebase with pip-audit and CI/CD \- Rohit Ranjan, accessed February 17, 2026, [https://rrohitrockss.medium.com/automated-patching-of-python-dependencies-securing-your-codebase-with-pip-audit-and-ci-cd-cdd7c903e30a](https://rrohitrockss.medium.com/automated-patching-of-python-dependencies-securing-your-codebase-with-pip-audit-and-ci-cd-cdd7c903e30a)  
22. Quickstart \- Publish a .NET MCP server to the MCP Registry \- Microsoft Learn, accessed February 17, 2026, [https://learn.microsoft.com/en-us/dotnet/ai/quickstarts/publish-mcp-registry](https://learn.microsoft.com/en-us/dotnet/ai/quickstarts/publish-mcp-registry)  
23. How to find, install, and manage MCP servers with the GitHub MCP Registry, accessed February 17, 2026, [https://github.blog/ai-and-ml/generative-ai/how-to-find-install-and-manage-mcp-servers-with-the-github-mcp-registry/](https://github.blog/ai-and-ml/generative-ai/how-to-find-install-and-manage-mcp-servers-with-the-github-mcp-registry/)  
24. Building MCP servers the right way: a production-ready guide in TypeScript \- Mauro Canuto, accessed February 17, 2026, [https://maurocanuto.medium.com/building-mcp-servers-the-right-way-a-production-ready-guide-in-typescript-8ceb9eae9c7f](https://maurocanuto.medium.com/building-mcp-servers-the-right-way-a-production-ready-guide-in-typescript-8ceb9eae9c7f)  
25. Registry CLI Tool \- Model Context Protocol （MCP）, accessed February 17, 2026, [https://modelcontextprotocol.info/tools/registry/cli/](https://modelcontextprotocol.info/tools/registry/cli/)  
26. When Things Go Wrong — PyInstaller 6.19.0 documentation, accessed February 17, 2026, [https://pyinstaller.org/en/stable/when-things-go-wrong.html](https://pyinstaller.org/en/stable/when-things-go-wrong.html)  
27. Application Packaging | Electron, accessed February 17, 2026, [https://electronjs.org/docs/latest/tutorial/application-distribution](https://electronjs.org/docs/latest/tutorial/application-distribution)  
28. Issue when using importlib\_metadata inside a standalone application \#71 \- GitHub, accessed February 17, 2026, [https://github.com/python/importlib\_metadata/issues/71](https://github.com/python/importlib_metadata/issues/71)  
29. Issue when using importlib\_metadata inside a standalone application \- GitLab, accessed February 17, 2026, [https://gitlab.com/python-devs/importlib\_metadata/-/issues/71](https://gitlab.com/python-devs/importlib_metadata/-/issues/71)  
30. Electron Builder Action \- GitHub Marketplace, accessed February 17, 2026, [https://github.com/marketplace/actions/electron-builder-action](https://github.com/marketplace/actions/electron-builder-action)  
31. accessed December 31, 1969, [https://www.electron.build/configuration/contents.html\#extraresources](https://www.electron.build/configuration/contents.html#extraresources)  
32. Automatically Signing a Windows EXE with Azure Trusted Signing, dotnet sign, and GitHub Actions \- Scott Hanselman, accessed February 17, 2026, [https://www.hanselman.com/blog/automatically-signing-a-windows-exe-with-azure-trusted-signing-dotnet-sign-and-github-actions](https://www.hanselman.com/blog/automatically-signing-a-windows-exe-with-azure-trusted-signing-dotnet-sign-and-github-actions)  
33. electron/notarize: Notarize your macOS Electron Apps \- GitHub, accessed February 17, 2026, [https://github.com/electron/notarize](https://github.com/electron/notarize)  
34. Concurrency \- GitHub Docs, accessed February 17, 2026, [https://docs.github.com/en/actions/concepts/workflows-and-actions/concurrency](https://docs.github.com/en/actions/concepts/workflows-and-actions/concurrency)  
35. Setting up CI \- Playwright, accessed February 17, 2026, [https://playwright.dev/docs/ci-intro](https://playwright.dev/docs/ci-intro)  
36. Testing Electron apps with Playwright and GitHub Actions \- Simon Willison: TIL, accessed February 17, 2026, [https://til.simonwillison.net/electron/testing-electron-playwright](https://til.simonwillison.net/electron/testing-electron-playwright)  
37. dry-run\` does not fail when package version is already published · Issue \#4927 · npm/cli, accessed February 17, 2026, [https://github.com/npm/cli/issues/4927](https://github.com/npm/cli/issues/4927)  
38. How to get a sha256 hash code for a github repo? \- Stack Overflow, accessed February 17, 2026, [https://stackoverflow.com/questions/61332371/how-to-get-a-sha256-hash-code-for-a-github-repo](https://stackoverflow.com/questions/61332371/how-to-get-a-sha256-hash-code-for-a-github-repo)  
39. checksum-action \- GitHub Marketplace, accessed February 17, 2026, [https://github.com/marketplace/actions/checksum-action](https://github.com/marketplace/actions/checksum-action)