# **Landscape Survey of Agentic IDE Workspace Scaffolding**

## **Executive Summary**

The paradigm of software development is undergoing a structural transformation, shifting from autocomplete-driven assistants to autonomous, agentic Integrated Development Environments (IDEs). These advanced environments possess deep contextual awareness, execute multi-file modifications, and interact natively with local build systems. To function effectively, these AI agents require highly structured, deterministic workspace scaffolding. This report delivers an exhaustive landscape survey of the tools, Model Context Protocol (MCP) servers, extensions, and framework utilities utilized to configure agentic workspaces, providing critical intelligence for the development of the Zorivest trading portfolio management application.

The analysis indicates a highly fragmented configuration ecosystem that is rapidly attempting to coalesce around standardized protocols. While proprietary, IDE-specific configuration files such as .cursorrules, .windsurfrules, and CLAUDE.md currently dominate the landscape, a definitive movement toward cross-platform standardization is accelerating. This convergence is primarily driven by the Agentic AI Foundation (AAIF), which is stewarding the AGENTS.md specification and the universal mcp.json protocol. Furthermore, the industry is abandoning monolithic, root-level instruction files in favor of hierarchical .agent/ directory structures that modularize rules, personas, and reusable workflow skills, effectively mitigating context window degradation.

Despite these advancements, the ecosystem suffers from severe security and architectural vulnerabilities. The capability of MCP servers to write executable configurations to the local filesystem has introduced critical attack vectors, most notably the "Confused Deputy" privilege escalation via maliciously modified mcp.json files. Additionally, existing scaffolding tools frequently lack programmatic Abstract Syntax Tree (AST) parsing, resulting in destructive overwrites rather than idempotent configuration merging.

By synthesizing patterns from adjacent domains—such as package management initialization and Infrastructure-as-Code state isolation—this report identifies the architectural prerequisites for secure, idempotent workspace scaffolding. The ensuing sections provide a meticulous mapping of the current ecosystem, analyze standardization trajectories, and deliver specific architectural recommendations for the Zorivest MEU-165 build plan.

## **Ecosystem Map of Agentic IDE Configurations**

The current landscape of agentic workspace scaffolding can be taxonomized into four distinct sectors: Native MCP Scaffolding, IDE-Specific Agent Configurations, Cross-IDE Standardization Frameworks, and Project Scaffolding CLIs. The following subsections provide exhaustive technical analyses of the entities populating each sector.

### **Native MCP Scaffolding**

The Model Context Protocol (MCP) serves as the primary transport layer connecting artificial intelligence models with secure local and remote resources. Native MCP scaffolding involves tools explicitly engineered to configure these connections, generate boilerplate server code, and manage agent execution contexts.

| Tool Name | Scaffolding Type | Generated Artifacts | Trigger Mechanism | Idempotent Execution | Ecosystem Support | Licensing / Adoption |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| **mcp-cli** 1 | CLI Bootstrapper | Boilerplate Python/TS server code | mcp-cli create command | No (Directory must be empty) | Framework Agnostic | Open Source / Moderate |
| **VS Code AI Toolkit** 2 | IDE Extension | .vscode/mcp.json config files | IDE Command Palette | Yes (Deep JSON Merge) | Visual Studio Code | Proprietary / High |
| **Everything-Claude-Code (ECC)** 4 | Agent Harness | .agents/, hooks/, rules/ | Initialization script | Yes (Directory Merge) | Claude Code, Cursor | Open Source / High |
| **AgentShield** 4 | Security CLI | N/A (Configuration Scans) | npx ecc-agentshield | Yes (State-free analysis) | Cross-IDE | Open Source / Emerging |

The mcp-cli package represents the foundational layer of MCP scaffolding. It requires Python 3.10 or later and provides a boilerplate generation mechanism for new server implementations.1 By generating the underlying JSON-RPC communication structures, the CLI abstracts the complexities of tool discovery and execution. However, the tool operates purely as a day-zero bootstrapper and lacks the capability to continuously manage or merge configurations in an actively evolving codebase.

Microsoft's Visual Studio Code AI Toolkit introduces a more sophisticated configuration paradigm. The extension provides an interactive agent builder that discovers, configures, and tests MCP servers directly within the IDE UI.2 Upon configuring a server, the toolkit programmatically modifies the workspace's .vscode/mcp.json file. The underlying mechanism utilizes a deep-merge algorithm, ensuring that newly added MCP server definitions do not destructively overwrite existing user-defined server blocks.3 This represents a critical leap toward safe, idempotent configuration management.

Everything-Claude-Code (ECC) stands as one of the most structurally advanced agent harnesses currently available. Unlike basic JSON generators, ECC scaffolds an entire performance optimization system.4 It generates an .agents/ directory containing metadata-driven subagent definitions utilizing YAML frontmatter.4 Furthermore, ECC introduces event-driven lifecycle hooks (such as PreToolUse and PostToolUse) that scaffold safety boundaries and automation directly into the agent's execution loop.4 ECC effectively demonstrates that advanced agent scaffolding must move beyond static prompts and incorporate programmable hooks and continuous learning workflows.

### **IDE-Specific Agent Configuration**

The most heavily populated, yet highly fragmented, segment of the ecosystem consists of proprietary configuration files designed for specific IDEs. These configurations dictate coding standards, operational boundaries, and context retrieval strategies.

| Tool / Platform | Configuration Files | IDE Support | Parsing Mechanism | Merge Strategy | Market Adoption |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **Cursor** 4 | .cursorrules, .cursor/rules/, mcp.json | Cursor | Active Context Injection | Manual / Append | Very High |
| **Claude Code** 6 | CLAUDE.md | Claude CLI | Context Memory Window | Automatic Append | High |
| **Windsurf** 8 | .windsurfrules, global\_rules.md | Windsurf | Active Context Injection | Manual | High |
| **Continue.dev** 10 | config.yaml, .continue/rules/ | VS Code, JetBrains | Lexicographical File Load | Array Concatenation | High |
| **Sourcegraph Cody** 12 | .cody/instructions.md, .cody/ignore | VS Code, JetBrains | Codebase Search Indexing | Manual | High |
| **Cline** 5 | .clinerules, cline\_mcp\_settings.json | VS Code | Active Context Injection | JSON Merge | High |
| **JetBrains AI** 15 | .junie/guidelines.md | IntelliJ, WebStorm | Task-based Execution | Manual | Moderate |
| **Amazon Q Dev** 17 | .amazonq/default.json | VS Code, JetBrains | JSON Schema Validation | IDE Managed | High |
| **GitHub Copilot** 5 | .github/copilot-instructions.md | Visual Studio, VS Code | Suggest-first pattern | Manual | Very High |

Cursor pioneered the modern file-based instruction paradigm with .cursorrules. However, as projects scaled, the monolithic .cursorrules file repeatedly triggered context window exhaustion. Consequently, the ecosystem is rapidly migrating toward a .cursor/rules/ directory structure, allowing for modular, glob-matched rules defined via YAML frontmatter.4 Cursor also utilizes a discrete .cursor/mcp.json file for server registration, separating operational tools from behavioral rules.20

Anthropic's Claude Code CLI relies heavily on the CLAUDE.md file. The technical architecture of Claude Code treats this file as a persistent memory vector rather than traditional documentation.6 When executing commands, the agent evaluates the workspace structure; if it identifies new build commands or stylistic patterns, it autonomously prompts the user to append these findings to CLAUDE.md.6 Official documentation strictly mandates that this file remain under 200 lines to prevent signal loss, indicating that large-scale scaffolding tools must aggressively curate the data injected into root-level configuration files.7

Continue.dev employs a uniquely deterministic approach to rule loading. Configurations are stored within the .continue/rules/ directory and are processed in strict lexicographical order (e.g., 01-general.md, 02-frontend.md).11 This allows developers to construct hierarchical rule cascades, where baseline constraints are established first, followed by language-specific overrides. Continue.dev also utilizes a unified config.yaml file to define context providers, allowing the agent to dynamically reference terminal outputs, external URLs, and local MCP servers via @ triggers.10

Sourcegraph Cody fundamentally diverges from the active context injection model utilized by Cursor and Windsurf. Cody is built upon a "search-first" architecture that indexes the entire codebase before generating responses.12 Consequently, Cody's primary scaffolding mechanisms rely on .cody/ignore files to explicitly define which directories and repositories should be excluded from the vector search index, satisfying enterprise compliance requirements.12 Its behavioral constraints are typically housed in .cody/instructions.md.13

Windsurf, utilizing its integrated Cascade agent, relies on .windsurfrules and global\_rules.md.8 The Windsurf architecture excels at deep local environment integration, reading these configuration files to automatically trigger local linters, formatters (such as Black or Flake8 in Python), and test suites directly from the agent's workflow.8

Amazon Q Developer implements an enterprise-grade scaffolding approach anchored by strict JSON schema validation.17 Configurations are housed in \~/.aws/amazonq/cli-agents globally or .amazonq/default.json locally.17 The schema strictly types server definitions, enforcing transport protocols, authentication mechanisms, and timeout variables, providing a highly structured alternative to the often free-form markdown rules utilized by other platforms.17

JetBrains has introduced the autonomous Junie agent, which coordinates execution via .junie/guidelines.md.15 Junie scans the project, reads the high-level goals from the guidelines file, and translates them into executable markdown task lists, allowing the developer to track the agent's progress across multiple files.23

### **Cross-IDE Agent Configuration**

The proliferation of IDE-specific configuration files has created significant friction for teams utilizing diverse development environments. To resolve this, specialized utilities and universal standards are being engineered.

| Standard / Tool | Target Paradigm | Primary Configuration | Implementation Mechanism | Standardization Body |
| :---- | :---- | :---- | :---- | :---- |
| **AGENTS.md** 24 | Universal Spec | AGENTS.md | Standard Markdown parsing | Agentic AI Foundation (AAIF) |
| **Xyzen** 5 | Synchronization | Universal linking | Automated shell scripting | Open Source Community |
| **The .agent/ Spec** 25 | Directory Structure | /rules, /skills | File system indexing | Unofficial Ecosystem Consensus |

The AGENTS.md specification has emerged as the definitive standard for cross-IDE instructions. Stewarded by the Agentic AI Foundation (AAIF) under the Linux Foundation, this specification is currently utilized by over 60,000 open-source repositories.24 The technical philosophy behind AGENTS.md treats the file akin to a structured Product Requirements Document (PRD).27 Rather than forcing the entire document into the agent's context window, the standard encourages the use of built-in file system tools (grep, read) to dynamically consume local context on demand.25 Furthermore, the specification supports nested scoping in monorepos; an agent operating in a specific sub-directory will automatically read the nearest AGENTS.md file, allowing root policies to be overridden by localized constraints.24

Xyzen directly addresses the file fragmentation problem. Operating as a configuration multiplexer, Xyzen establishes a single source of truth within an AGENTS.md file.5 It provides an automated shell script (setup-ai-rules.sh) that generates hard or symbolic links to all corresponding IDE-specific files (e.g., linking AGENTS.md to .cursorrules, .windsurfrules, and .github/copilot-instructions.md).5 This guarantees that modifications to the central ruleset immediately propagate across all development environments used by a team.

The .agent/ directory convention is rapidly superseding flat-file configurations. This architectural pattern isolates agentic state from source code. A typical structure includes .agent/rules/ for language-specific style guides and .agent/skills/ for reusable workflow packages documented in SKILL.md files.26 The primary advantage of this directory structure is progressive disclosure; agents only retrieve the specific skill or rule file necessary for the immediate task, drastically optimizing token utilization.29

### **Project Scaffolding CLIs Bundling AI Configuration**

The integration of AI configuration into foundational project bootstrapping represents the final layer of the ecosystem. Modern scaffolding CLIs are no longer solely generating source code; they are generating the cognitive frameworks required for AI agents to maintain that code.

| Scaffolding CLI | Core Technology Target | Generated AI Configurations | State Management | Merge Strategy |
| :---- | :---- | :---- | :---- | :---- |
| **create-12-factor-agent** 30 | General TS/Python Agents | agent.baml, tools.py | Local SQLite / Redis | Fails on existing directory |
| **create-cloudflare/agents** 31 | Cloudflare Workers | WebSocket schemas, SQL DBs | Distributed Durable Objects | Overwrite / Abort |
| **create-mastra** 32 | Web Automation Agents | .env variables, workflows | Local execution | Scaffold from template |

The create-12-factor-agent CLI is designed to bootstrap applications adhering strictly to the twelve-factor app methodology.30 When executed, the utility prompts the developer for technology stack preferences (e.g., TypeScript vs. Python, OpenAI vs. Anthropic, SQLite) and generates a highly standardized directory structure including agent.ts, tool definition files, and .env templates.30 The tool utilizes BAML (a domain-specific language for AI prompts) to manage prompt logic, keeping natural language instructions entirely separate from execution code.30

Cloudflare's create-cloudflare@latest \--template cloudflare/agents-starter solves the complex problem of agent state management.31 Traditional agents suffer from statelessness, requiring extensive external database configurations to maintain memory across sessions. This CLI scaffolds a full stateful architecture utilizing Cloudflare's Durable Objects, automatically generating the TypeScript classes, embedded SQL databases, and real-time WebSocket routing required for persistent agent memory.31

The create-mastra utility focuses on highly specialized browser automation agents.32 By executing npx create-mastra@latest \--template browsing-agent, developers scaffold an environment pre-configured with Puppeteer integration and session management logic, demonstrating how CLIs can deploy highly specialized agentic tools directly into a workspace.32

## **Comparative Matrix and Structural Analysis**

The following matrix synthesizes the structural paradigms, execution characteristics, and merge strategies of the ecosystem's most critical configuration mechanisms.

| Tool / Mechanism | Operational Type | Generated Artifacts | Cross-IDE Support | Idempotent | Configuration Merge Strategy | Maintenance |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| **AGENTS.md** 24 | Open Standard | AGENTS.md | Yes (Universal) | N/A | Manual File Edit | Active (AAIF) |
| **CLAUDE.md** 6 | Persistent CLI Memory | CLAUDE.md | No (Claude CLI) | Yes | LLM Context Append | Active |
| **Xyzen** 5 | Shell Linker Utility | Symlinks | Yes | Yes | Destructive Overwrite (Symlink) | Experimental |
| **Everything-Claude-Code** 4 | Agent Harness | .agents/, hooks/ | Cursor, Claude | Yes | Additive Directory Merge | Active |
| **mcp.json** 33 | Protocol Standard | mcp.json | Yes | Client Dep. | Deep JSON Merge | Active |
| **Continue.dev** 34 | IDE Extension | config.yaml, .continue/ | VS Code, JB | Yes | YAML Array Concatenation | Active |
| **create-12-factor-agent** 30 | Bootstrapper CLI | Source, .env, baml | Framework Agnostic | No | Abort on conflict | Active |
| **VS Code AI Toolkit** 2 | IDE Extension | .vscode/mcp.json | VS Code | Yes | Deep JSON Merge | Active (MSFT) |
| **Windsurf Rules** 8 | IDE Config | .windsurfrules | Windsurf | Manual | Manual File Edit | Active |
| **Cline MCP** 14 | IDE Extension | cline\_mcp\_settings.json | VS Code | Yes | Deep JSON Merge | Active |
| **Amazon Q Dev** 17 | IDE Extension | .amazonq/default.json | VS Code, JB | Yes | Strict Schema Validation | Active (AWS) |
| **JetBrains Junie** 15 | IDE Agent | .junie/guidelines.md | IntelliJ, WebStorm | Manual | Manual File Edit | Active |
| **create-cloudflare** 31 | Bootstrapper CLI | Worker scripts, SQL | Framework Agnostic | No | Destructive Overwrite | Active |
| **AgentShield** 4 | Security Analyzer | N/A (Scans only) | Cross-IDE | Yes | Diff Patch Application | Active |
| **Sourcegraph Cody** 35 | IDE Extension | .cody/ignore | VS Code, JB | Manual | Manual File Edit | Active |
| **Copilot Workspace** 5 | Extension Config | .github/copilot-\* | VS Code, VS | Manual | Manual File Edit | Active |

### **Technical Implications of Merge Strategies**

A critical analysis of the matrix reveals profound technical disparities in configuration handling. The division lies primarily between structured data manipulation and unstructured text generation.

JSON-based configuration mechanisms—such as the VS Code AI Toolkit, Cline MCP settings, and Amazon Q Developer—demonstrate robust programmatic maturity. When appending a new MCP server to a .vscode/mcp.json file, these tools utilize deterministic deep-merge algorithms.2 They parse the existing Abstract Syntax Tree (AST), locate the mcpServers object, and inject the new server key without disrupting custom user parameters (such as unique environment variables or specific timeout settings).3

Conversely, markdown-based rule systems (.cursorrules, AGENTS.md) currently suffer from a severe lack of programmatic sophistication. Because markdown is largely treated as unstructured string data by scaffolding tools, automation relies on blunt EOF (End of File) appending. Running a scaffolding script multiple times results in duplicated instructions, conflicting rulesets, and broken document formatting. True idempotency for markdown requires semantic AST parsing (e.g., utilizing libraries like remark or mdast), allowing a tool to locate specific header nodes (e.g., \#\# Testing Protocols) and intelligently merge new bullet points without duplication. This represents a massive architectural gap in the current ecosystem.

## **Adjacent Domain Analysis: Scaffolding Patterns**

The challenges encountered in scaffolding agentic environments—specifically regarding idempotency, deep merging, and state isolation—have been rigorously solved in adjacent software domains. Analyzing the architectural patterns of package managers, development linters, and Infrastructure-as-Code (IaC) provides critical blueprints for the Zorivest MCP tool.

### **Package Manager Initialization Strategies**

Foundational package managers such as npm, Cargo, and Poetry handle workspace initialization through a highly refined combination of interactive prompting and non-destructive state merging. When a developer executes npm init within a directory that already contains a package.json file, the utility does not indiscriminately overwrite the configuration. Instead, it parses the existing JSON into memory, prompts the user interactively to fill missing metadata (e.g., repository URLs or author names), and safely writes the updated keys back to the file while preserving existing dependencies and scripts.37

This non-destructive schema validation is directly applicable to the generation of mcp.json files. An agentic scaffolding tool must be capable of recognizing an existing MCP configuration, validating its schema, and injecting new server definitions safely. If the AI agent detects a conflicting configuration, it must halt and prompt the developer, mirroring the interactive safety mechanisms of mature package managers.

### **Developer Tool Setup and AST Parsing**

Code quality tools, particularly ESLint and Prettier, represent the gold standard for complex configuration scaffolding. The initialization process triggered by eslint \--init (now modernized via @eslint/create-config 38) dynamically evaluates the host project, analyzing the presence of frameworks (React, Vue) and languages (TypeScript, JavaScript) before generating the appropriate .eslintrc.json or flat config file.39

Crucially, ESLint excels in handling deep logical configuration overrides. The tool utilizes advanced AST parsing to comprehend the structure of the user's code.41 When developers utilize extending rule sets—such as eslint-config-airbnb-base—the engine systematically evaluates hundreds of individual rules, allowing localized configuration files to selectively disable or modify specific inherited constraints without corrupting the entire schema.42

The .agent/rules/ directory structure must adopt an identical cascading logic. Just as ESLint resolves conflicting rules by prioritizing the most localized configuration file, an AI agent should merge rules logically. For example, baseline constraints defined in a root AGENTS.md should be safely overridden by specific constraints defined in .agent/rules/fastapi-rules.md when the agent is operating within the backend directory.24 The scaffolding tool must structure these files to support this precise logical cascade.

### **Infrastructure-as-Code (IaC) State Isolation**

Terraform's initialization sequence (terraform init) provides a masterclass in dependency management and workspace isolation.43 When executed, Terraform reads the configuration definitions (main.tf) and constructs a hidden .terraform/ directory. This directory securely caches provider plugins, manages remote modules, and maps the active environment to the correct state workspace (terraform.tfstate.d/).44

This pattern directly correlates to the philosophical design of the .agent/ folder. Just as Terraform uses the hidden .terraform/ directory to separate execution state and binary dependencies from the declarative source code, the .agent/ directory isolates the cognitive state, role definitions, and workflow scripts from the application logic.44 Furthermore, Terraform's init command is strictly idempotent; it can be executed continuously to verify state, synchronize lock files, and repair dependencies without risk of data loss.44 Any MCP tool deploying agent configurations must guarantee identical idempotency, allowing developers to execute the scaffolding command repeatedly to "heal" or update the .agent/ environment without wiping out customized workflows.

### **Multi-Environment Configuration Management**

The management of environment variables across distinct deployment stages (development, staging, production) is handled masterfully by tools such as dotenv-vault and 1Password CLI. These systems utilize a dual-file strategy: a .env.example file acts as a structural template committed to version control, while the actual .env file containing cryptographic secrets is strictly isolated and excluded via .gitignore.32

Agentic configurations require the exact same cryptographic hygiene. MCP server configurations (mcp.json) frequently require highly sensitive API keys, database credentials, or OAuth tokens to function.3 The scaffolding tool must generate template files (e.g., mcp.example.json) for source control, while simultaneously injecting exclusion rules into the local .gitignore file to ensure that active configurations and operational secrets are never accidentally committed.4

## **Emerging Standards and Conventions**

The evolution of agentic IDE configurations is moving from an era of proprietary fragmentation to rapid, collaborative standardization. This convergence is highly visible across transport protocols, instruction formats, and file architectures.

### **MCP Configuration Convergence (mcp.json)**

A definitive standard is crystallizing around the structure and naming of the mcp.json schema. Major clients—including Visual Studio Code, Cursor, and the Claude Desktop application—have uniformly adopted a standard JSON object structure requiring a command string, an args array, and an optional env map to define server initialization.33 This unified schema enables developers to write a single MCP server configuration that executes flawlessly across competing IDEs.33

Furthermore, an emerging draft RFC is proposing the adoption of a .well-known/mcp.json endpoint.47 This protocol dictates that IDEs and agents can automatically perform discovery requests against local domains or network resources to autonomously identify available MCP servers.47 This transition indicates that future scaffolding tools may rely less on generating static configuration files and more on exposing dynamic endpoints that IDEs interrogate upon initialization.

### **Agent Instructions Convergence (AGENTS.md vs. CLAUDE.md)**

Two distinct, occasionally conflicting philosophies define the standardization of agent instructions: the active injection model and the passive retrieval model.

The Anthropic paradigm, embodied by the CLAUDE.md standard, champions the active injection model. Official guidelines dictate that CLAUDE.md must remain extremely concise—strictly under 200 lines.7 Because this file is loaded into the LLM's context window for every single interaction, any extraneous information severely degrades the model's performance via "context rot".7 The file serves purely as an operational memory cache for critical bash commands, stylistic overrides, and brief architectural summaries.6

Conversely, the Agentic AI Foundation (AAIF) promotes the AGENTS.md specification, which champions the passive retrieval model.24 Modeled after a comprehensive Product Requirements Document (PRD), AGENTS.md allows for expansive detail.27 The standard assumes the AI agent will utilize intrinsic file-system tools (such as grep and semantic search) to dynamically extract only the specific sections of the document relevant to its current task, rather than flooding the initial context window.24

As the ecosystem matures, AGENTS.md is winning the battle for universal cross-IDE adoption. However, best practices indicate a hybrid approach: utilizing a brief, root-level AGENTS.md for essential triggers, while delegating complex instructions to highly specific, passive files located deeper within the project structure.24

### **Folder Structure Conventions (The .agent/ Taxonomy)**

The industry is rapidly abandoning the "flat file" approach (e.g., dropping a massive .cursorrules file in the root directory) due to its lack of scalability. The consensus standard replacing it is the .agent/ directory structure.25

This taxonomy introduces rigid modularity. A standardized .agent/ directory typically houses:

1. **Roles (/roles)**: Dedicated markdown files defining explicit personas (e.g., @security-agent, @tester), outlining their specific operational boundaries and allowed toolsets.4  
2. **Rules (/rules)**: Segmented guideline documents covering language-specific constraints (e.g., typescript-rules.md, python-rules.md), preventing Python context from polluting a React refactoring task.4  
3. **Skills (/skills)**: Reusable workflow packages formalized as SKILL.md files.29 These files define multi-step processes (e.g., a Test-Driven Development workflow) that the agent can execute autonomously, complete with specific triggers and expected outputs.26

This directory-based architecture provides the highest degree of modularity and perfectly aligns with the passive retrieval strategy, ensuring optimum LLM performance across massive codebases.

## **Gaps, Failure Modes, and Opportunities**

Despite the rapid trajectory of innovation, the ecosystem suffers from significant failure modes, severe security vulnerabilities, and developer experience anti-patterns. Addressing these gaps presents a tremendous opportunity for the Zorivest application.

### **1\. What is nobody doing yet that Zorivest could pioneer?**

Currently, no scaffolding utility on the market executes **AST-aware, semantic merging of Markdown configuration files**. While deep-merge algorithms for mcp.json are standard 3, tools that modify AGENTS.md or .cursorrules rely entirely on destructive overwriting or primitive string concatenation. If the Zorivest MCP tool implements a Markdown Abstract Syntax Tree parser (utilizing libraries such as remark or mdast), it could intelligently analyze a developer's existing AGENTS.md file, identify existing header nodes, and gracefully insert Zorivest-specific rules under the correct sections without duplicating content. This would represent a massive leap in configuration idempotency.

Furthermore, no tool seamlessly combines configuration scaffolding with immediate security validation. By integrating static analysis protocols (similar to the 102 security rules defined by the AgentShield framework 4), the Zorivest tool could automatically audit the .agent/ folder upon generation, ensuring that no overly permissive tool assignments or reverse prompt injections are present.

### **2\. What are the most common failure modes in existing scaffolding tools?**

The most pervasive failure mode is **Context Window Exhaustion** resulting from monolithic file generation.48 Scaffolding tools that generate massive, multi-thousand-line instruction files cause the LLM to suffer from "catastrophic forgetting," where the agent loses track of the developer's immediate instructions in a sea of boilerplate rules.49

The second major failure mode is **Destructive Overwrites**. Basic CLI bootstrappers (like create-cloudflare or early iterations of AI templates) lack state awareness.30 When executed in a populated repository, they either abort entirely or overwrite custom user configurations, forcing developers to rely on Git resets to salvage their work.

### **3\. What developer experience anti-patterns should we avoid?**

* **The "Unbounded Execution" Anti-Pattern**: Failing to define strict operational boundaries within the generated scaffolding allows agents to autonomously execute destructive commands.48 The generated rules must explicitly dictate what the agent is *never* allowed to do (e.g., force-pushing to Git or modifying environment variables without explicit human approval).50  
* **The "Global Rules for Local Code" Anti-Pattern**: Injecting backend configuration rules into the global context while the agent is operating on the frontend. Scaffolding must support isolated rule execution to maintain context relevance.4  
* **The "Hidden Magic" Anti-Pattern**: Obfuscating the agent's instructions. Developers must have full visibility and editing rights over the .agent/ files. Configurations hidden within compiled binaries or proprietary IDE settings lead to profound frustration when the agent hallucinates or behaves erratically.

### **4\. What conventions are most likely to become standard in 12 months?**

Within the next year, the industry will entirely standardize around the **.agent/ directory taxonomy** for context management, supplemented by a minimal, root-level **AGENTS.md** file acting as a table of contents or router.24 The mcp.json specification will solidify as the absolute standard for tool registration, universally supported across all major IDEs.33 Finally, the adoption of specialized subagents (orchestrators, coders, testers) managed via specific metadata files within the .agent/roles/ directory will become the default architecture for complex software engineering tasks.4

### **5\. Are there any security concerns with MCP tools that write to the filesystem?**

The capability of MCP tools and AI agents to write to the filesystem introduces catastrophic security vulnerabilities, explicitly highlighted by the discovery of **CVE-2025-54136 (codenamed "MCPoison")**.51

Because IDEs like Cursor currently trust approved mcp.json configurations indefinitely, an attacker can execute a "Confused Deputy" supply chain attack.51 The attacker submits a seemingly benign .cursor/rules/mcp.json configuration to a shared repository.51 Once a victim pulls the repository and the IDE approves the connection, the attacker can silently alter the configuration payload (e.g., swapping a linter command for calc.exe or a reverse shell payload).51 Because the file is already trusted, the AI agent executes the malicious payload without triggering a secondary security prompt, achieving remote and persistent code execution.51

Furthermore, AI agents are susceptible to **Reverse Prompt Injection** and **Context Poisoning**. If a generated rule file instructs the agent to read an external URL or an untrusted dependency file, an attacker can embed invisible Unicode characters or HTML comments within that file.4 When the agent reads the file, the malicious payload overrides the agent's core instructions, potentially commanding it to exfiltrate active API keys or environment variables to an external server.4 Any tool writing agent configurations must implement strict zero-trust boundaries, utilizing .gitignore policies for sensitive configurations and injecting explicit defensive constraints into the agent's base prompt.

## **Recommendations for Zorivest**

Based on the exhaustive analysis of the agentic scaffolding ecosystem, the following highly technical, actionable recommendations are provided for the implementation of the Zorivest MCP workspace scaffolding tool (Build Plan Slot: MEU-165).

1. **Deploy a Hierarchical .agent/ Taxonomy as the Architecture Foundation** To ensure scalability and combat context window exhaustion, the MCP tool must bypass root-level monolithic files and directly scaffold a comprehensive .agent/ directory.26 This directory must be programmatically structured to include /rules, /skills, and /roles.4 The requested root-level IDE files (such as CLAUDE.md, GEMINI.md, and .cursorrules) should be generated strictly as lightweight symbolic links or minimal pointer files that instruct the specific IDE's agent to utilize its native file-search capabilities to ingest the detailed documentation located within the .agent/ directory.5 This approach guarantees universal cross-IDE compatibility while perfectly aligning with the passive retrieval standards championed by the Agentic AI Foundation.24  
2. **Engineer AST-Aware, Fully Idempotent Configuration Mergers** To guarantee idempotency and prevent the destructive overwriting of developer configurations, the MCP tool must utilize advanced Abstract Syntax Tree (AST) parsing.41 For structured data formats (e.g., .vscode/mcp.json or config.yaml), implement a deep-merge algorithm that validates the schema and intelligently injects or updates specific server definitions without mutating adjacent user-defined keys.3 Critically, for Markdown artifacts (AGENTS.md or SKILL.md), the tool must deploy a markdown AST parser (such as mdast). This permits the tool to programmatically scan the document, identify existing header nodes (e.g., \#\# Rules), and inject Zorivest-specific constraints seamlessly under the appropriate sections, completely eliminating the data corruption associated with primitive string concatenation.  
3. **Enforce a Three-Tiered Cryptographic and Operational Security Boundary** To proactively neutralize "Confused Deputy" privilege escalation and MCPoison supply chain attacks 51, the generated configurations must establish ironclad operational boundaries. The tool must scaffold a three-tier permission matrix within the rules files, explicitly defining actions the agent must "Always" do (run local tests), "Ask First" (modify configurations or install dependencies), and "Never" do (delete files outside the project or expose credentials).48 Furthermore, the tool must automatically inject updates into the project's .gitignore file, guaranteeing that any generated configuration artifacts containing operational secrets, API keys, or active environment variables are explicitly excluded from version control.4 The tool should also inject "immune system" guardrails into the base rules, instructing the LLM to ignore executable commands found within dynamically fetched external content.4  
4. **Implement Isolated, Context-Aware Rule Segmentation** Given the polyglot nature of the Zorivest architecture—combining a React/Electron frontend with a Python FastAPI backend—the scaffolding tool must rigorously segregate the cognitive context. Generating a single rule file will result in cross-contamination, where Python stylistic rules are erroneously applied during React refactoring tasks.4 The MCP tool must populate the .agent/rules/ directory with strictly separated documents (e.g., react-architecture.md and fastapi-guidelines.md).24 This ensures that when the AI agent operates within the backend directory, it retrieves only the FastAPI context, maximizing the efficiency of the context window and drastically improving the semantic accuracy of the generated code.54  
5. **Utilize Static Template Registries with Dynamic Variable Interpolation** To ensure maximum reliability and ease of distribution, the base templates for the .agent/ directory, context files, workflows, and roles must be shipped as immutable static assets bundled directly within the TypeScript MCP server package. Upon execution, the scaffolding tool should utilize a lightweight templating engine to dynamically interpolate project-specific variables (such as IDE client detection parameters, local port numbers, or path configurations) into these static assets prior to writing them to the filesystem.32 This architecture guarantees that the scaffolding tool operates predictably across varied host environments while remaining entirely self-contained within the MEU-165 build plan parameters.

#### **Works cited**

1. How to build a simple agentic AI server with MCP | Red Hat Developer, accessed March 14, 2026, [https://developers.redhat.com/articles/2025/08/12/how-build-simple-agentic-ai-server-mcp](https://developers.redhat.com/articles/2025/08/12/how-build-simple-agentic-ai-server-mcp)  
2. Build agents and prompts in AI Toolkit \- Visual Studio Code, accessed March 14, 2026, [https://code.visualstudio.com/docs/intelligentapps/agentbuilder](https://code.visualstudio.com/docs/intelligentapps/agentbuilder)  
3. Add and manage MCP servers in VS Code, accessed March 14, 2026, [https://code.visualstudio.com/docs/copilot/customization/mcp-servers](https://code.visualstudio.com/docs/copilot/customization/mcp-servers)  
4. affaan-m/everything-claude-code: The agent harness ... \- GitHub, accessed March 14, 2026, [https://github.com/affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code)  
5. ScienceOL/Xyzen: The infrastructure for a world where ... \- GitHub, accessed March 14, 2026, [https://github.com/ScienceOL/Xyzen](https://github.com/ScienceOL/Xyzen)  
6. anthropic-claude-code-rules.md · GitHub, accessed March 14, 2026, [https://gist.github.com/markomitranic/26dfcf38c5602410ef4c5c81ba27cce1](https://gist.github.com/markomitranic/26dfcf38c5602410ef4c5c81ba27cce1)  
7. How to Write a CLAUDE.md File That Actually Works: Best Practices for API Projects, accessed March 14, 2026, [https://www.turbodocx.com/blog/how-to-write-claude-md-best-practices](https://www.turbodocx.com/blog/how-to-write-claude-md-best-practices)  
8. Windsurf IDE Installation & Configuration Guide \- on Fabric, accessed March 14, 2026, [https://fabric.so/p/windsurf-ide-installation-and-configuration-guide-2f116Xz8xZEh2tZLCYeqfP](https://fabric.so/p/windsurf-ide-installation-and-configuration-guide-2f116Xz8xZEh2tZLCYeqfP)  
9. Windsurf IDE Guide: Cascade Agent, Setup & Deployment | DeployHQ, accessed March 14, 2026, [https://www.deployhq.com/guides/windsurf](https://www.deployhq.com/guides/windsurf)  
10. Context Providers \- Continue Docs, accessed March 14, 2026, [https://docs.continue.dev/customize/deep-dives/custom-providers](https://docs.continue.dev/customize/deep-dives/custom-providers)  
11. How to Create and Manage Rules in Continue, accessed March 14, 2026, [https://docs.continue.dev/customize/deep-dives/rules](https://docs.continue.dev/customize/deep-dives/rules)  
12. GitHub Copilot vs Sourcegraph Cody: Which Gets Your Codebase? | Augment Code, accessed March 14, 2026, [https://www.augmentcode.com/tools/github-copilot-vs-sourcegraph-cody-which-gets-your-codebase](https://www.augmentcode.com/tools/github-copilot-vs-sourcegraph-cody-which-gets-your-codebase)  
13. sourcegraph/cody-vs: Cody for Visual Studio \- an AI code assistant that uses advanced search and codebase context to help you write and fix code. \- GitHub, accessed March 14, 2026, [https://github.com/sourcegraph/cody-vs](https://github.com/sourcegraph/cody-vs)  
14. MCP Overview \- Cline Documentation, accessed March 14, 2026, [https://docs.cline.bot/mcp/mcp-overview](https://docs.cline.bot/mcp/mcp-overview)  
15. Coding Guidelines for Your AI Agents | The IntelliJ IDEA Blog, accessed March 14, 2026, [https://blog.jetbrains.com/idea/2025/05/coding-guidelines-for-your-ai-agents/](https://blog.jetbrains.com/idea/2025/05/coding-guidelines-for-your-ai-agents/)  
16. How to define custom guidelines/rules for JetBrains AI Assistant \- Stack Overflow, accessed March 14, 2026, [https://stackoverflow.com/questions/79705571/how-to-define-custom-guidelines-rules-for-jetbrains-ai-assistant](https://stackoverflow.com/questions/79705571/how-to-define-custom-guidelines-rules-for-jetbrains-ai-assistant)  
17. MCP governance for Q Developer \- AWS Documentation, accessed March 14, 2026, [https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/mcp-governance.html](https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/mcp-governance.html)  
18. MCP configuration for Q Developer in the IDE \- AWS Documentation, accessed March 14, 2026, [https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/mcp-ide.html](https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/mcp-ide.html)  
19. Use MCP Servers \- Visual Studio (Windows) | Microsoft Learn, accessed March 14, 2026, [https://learn.microsoft.com/en-us/visualstudio/ide/mcp-servers?view=visualstudio](https://learn.microsoft.com/en-us/visualstudio/ide/mcp-servers?view=visualstudio)  
20. MCP servers, the complete guide inside the MCP mesh, from setup to security \- Levo.ai, accessed March 14, 2026, [https://www.levo.ai/resources/blogs/model-context-protocol-mcp-server-the-complete-guide](https://www.levo.ai/resources/blogs/model-context-protocol-mcp-server-the-complete-guide)  
21. Windsurf Rules & Workflows: AI-Driven Software Delivery Best Practices, accessed March 14, 2026, [https://www.paulmduvall.com/using-windsurf-rules-workflows-and-memories/](https://www.paulmduvall.com/using-windsurf-rules-workflows-and-memories/)  
22. Using MCP with Amazon Q Developer, accessed March 14, 2026, [https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/qdev-mcp.html](https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/qdev-mcp.html)  
23. Harnessing the Power of AI in IntelliJ IDEA \- JetBrains Guide, accessed March 14, 2026, [https://www.jetbrains.com/guide/ai/links/harnessing-power-ai/](https://www.jetbrains.com/guide/ai/links/harnessing-power-ai/)  
24. AGENTS.md, accessed March 14, 2026, [https://agents.md/](https://agents.md/)  
25. Proposal: Standardize a .agent Directory for Comprehensive Project ..., accessed March 14, 2026, [https://github.com/agentsmd/agents.md/issues/71](https://github.com/agentsmd/agents.md/issues/71)  
26. Go Project Structure | Skills Market... \- LobeHub, accessed March 14, 2026, [https://lobehub.com/skills/hoangtran1411-quickvm-go-project-structure](https://lobehub.com/skills/hoangtran1411-quickvm-go-project-structure)  
27. How to write a good spec for AI agents \- Addy Osmani, accessed March 14, 2026, [https://addyosmani.com/blog/good-spec/](https://addyosmani.com/blog/good-spec/)  
28. spec-driven-development | Skills Mar... \- LobeHub, accessed March 14, 2026, [https://lobehub.com/en/skills/addyosmani-agent-skills-spec-driven-development](https://lobehub.com/en/skills/addyosmani-agent-skills-spec-driven-development)  
29. AGENTS.md \- addyosmani/web-quality-skills \- GitHub, accessed March 14, 2026, [https://github.com/addyosmani/web-quality-skills/blob/main/AGENTS.md](https://github.com/addyosmani/web-quality-skills/blob/main/AGENTS.md)  
30. Collaborators Wanted \- npx/uvx create-12-factor-agent \#61 \- GitHub, accessed March 14, 2026, [https://github.com/humanlayer/12-factor-agents/discussions/61](https://github.com/humanlayer/12-factor-agents/discussions/61)  
31. Cloudflare Agents docs, accessed March 14, 2026, [https://developers.cloudflare.com/agents/](https://developers.cloudflare.com/agents/)  
32. Browser Agent \- Mastra Templates, accessed March 14, 2026, [https://mastra.ai/templates/browsing-agent](https://mastra.ai/templates/browsing-agent)  
33. MCP JSON Configuration FastMCP, accessed March 14, 2026, [https://gofastmcp.com/integrations/mcp-json-configuration](https://gofastmcp.com/integrations/mcp-json-configuration)  
34. Context Providers \- Continue Docs, accessed March 14, 2026, [https://docs.continue.dev/customize/custom-providers](https://docs.continue.dev/customize/custom-providers)  
35. How to Secure Your Sourcegraph Cody App | Guide, accessed March 14, 2026, [https://vibeappscanner.com/how-to-secure-cody-app](https://vibeappscanner.com/how-to-secure-cody-app)  
36. config.yaml Reference \- Continue Docs, accessed March 14, 2026, [https://docs.continue.dev/reference](https://docs.continue.dev/reference)  
37. creating-a-new-project | Skills Mark... \- LobeHub, accessed March 14, 2026, [https://lobehub.com/skills/karashiiro-agent-skills-creating-a-new-project](https://lobehub.com/skills/karashiiro-agent-skills-creating-a-new-project)  
38. accessed March 14, 2026, [https://raw.githubusercontent.com/eslint/eslint/main/CHANGELOG.md](https://raw.githubusercontent.com/eslint/eslint/main/CHANGELOG.md)  
39. Top Linters for JavaScript and TypeScript: Simplifying Code Quality Management | Syncfusion Blogs, accessed March 14, 2026, [https://www.syncfusion.com/blogs/post/top-linters-javascript-typescript](https://www.syncfusion.com/blogs/post/top-linters-javascript-typescript)  
40. JavaScript Cookbook: Programming the Web \[3 ed.\] 1492055751, 9781492055754, accessed March 14, 2026, [https://dokumen.pub/javascript-cookbook-programming-the-web-3nbsped-1492055751-9781492055754-g-2190600.html](https://dokumen.pub/javascript-cookbook-programming-the-web-3nbsped-1492055751-9781492055754-g-2190600.html)  
41. eslint-config-eslint \- Yarn, accessed March 14, 2026, [https://classic.yarnpkg.com/en/package/eslint-config-eslint](https://classic.yarnpkg.com/en/package/eslint-config-eslint)  
42. ESLint with Airbnb style guide does not work for all rules \- Stack Overflow, accessed March 14, 2026, [https://stackoverflow.com/questions/70191723/eslint-with-airbnb-style-guide-does-not-work-for-all-rules](https://stackoverflow.com/questions/70191723/eslint-with-airbnb-style-guide-does-not-work-for-all-rules)  
43. terraform init command reference \- HashiCorp Developer, accessed March 14, 2026, [https://developer.hashicorp.com/terraform/cli/commands/init](https://developer.hashicorp.com/terraform/cli/commands/init)  
44. Initialize the Terraform working directory \- HashiCorp Developer, accessed March 14, 2026, [https://developer.hashicorp.com/terraform/cli/init](https://developer.hashicorp.com/terraform/cli/init)  
45. How to Build Terraform Workspace Patterns \- OneUptime, accessed March 14, 2026, [https://oneuptime.com/blog/post/2026-01-30-terraform-workspace-patterns/view](https://oneuptime.com/blog/post/2026-01-30-terraform-workspace-patterns/view)  
46. AGENTS.md – Open format for guiding coding agents | Hacker News, accessed March 14, 2026, [https://news.ycombinator.com/item?id=44957443](https://news.ycombinator.com/item?id=44957443)  
47. SEP-1649: MCP Server Cards \- HTTP Server Discovery via .well-known \- GitHub, accessed March 14, 2026, [https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1649](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1649)  
48. How to write a good spec for AI agents \- Substack, accessed March 14, 2026, [https://open.substack.com/pub/addyo/p/how-to-write-a-good-spec-for-ai-agents?utm\_source=post\&comments=true\&utm\_medium=web](https://open.substack.com/pub/addyo/p/how-to-write-a-good-spec-for-ai-agents?utm_source=post&comments=true&utm_medium=web)  
49. SpecMem: How Kiroween in San Francisco Sparked the First Unified Agent Experience and Pragmatic Memory for Coding Agents | by Shashi Jagtap | Superagentic AI | Medium, accessed March 14, 2026, [https://medium.com/superagentic-ai/specmem-how-kiroween-in-san-francisco-sparked-the-first-unified-agent-experience-and-pragmatic-43306b15579d](https://medium.com/superagentic-ai/specmem-how-kiroween-in-san-francisco-sparked-the-first-unified-agent-experience-and-pragmatic-43306b15579d)  
50. Cursor Security: Key Risks, Protections & Best Practices \- Reco, accessed March 14, 2026, [https://www.reco.ai/learn/cursor-security](https://www.reco.ai/learn/cursor-security)  
51. Cursor AI Code Editor Vulnerability Enables RCE via Malicious MCP File Swaps Post Approval \- The Hacker News, accessed March 14, 2026, [https://thehackernews.com/2025/08/cursor-ai-code-editor-vulnerability.html](https://thehackernews.com/2025/08/cursor-ai-code-editor-vulnerability.html)  
52. Security Risks of Agentic AI: A Model Context Protocol (MCP) Introduction, accessed March 14, 2026, [https://businessinsights.bitdefender.com/security-risks-agentic-ai-model-context-protocol-mcp-introduction](https://businessinsights.bitdefender.com/security-risks-agentic-ai-model-context-protocol-mcp-introduction)  
53. 11 Emerging AI Security Risks with MCP (Model Context Protocol) \- Checkmarx, accessed March 14, 2026, [https://checkmarx.com/zero-post/11-emerging-ai-security-risks-with-mcp-model-context-protocol/](https://checkmarx.com/zero-post/11-emerging-ai-security-risks-with-mcp-model-context-protocol/)  
54. Best Practices for Claude Code, accessed March 14, 2026, [https://code.claude.com/docs/en/best-practices](https://code.claude.com/docs/en/best-practices)