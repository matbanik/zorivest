# **Multi-IDE Agentic Cooperation Patterns (2025-2026)**

## **1\. Executive Summary**

The transition from isolated, chat-based artificial intelligence assistants to orchestrations of autonomous, multi-agent systems marks the defining architectural shift in software engineering between 2025 and 2026\. The evidence analyzed demonstrates that the industry has fundamentally reorganized the software development lifecycle around collaborative agentic patterns, moving beyond single Integrated Development Environments (IDEs) toward decentralized ecosystems where multiple specialized agents collaborate across disparate platforms.1 This evolution is driven by the realization that monolithic Large Language Models (LLMs) suffer from context degradation and reasoning bottlenecks when tasked with simultaneous planning, implementation, and verification across large codebases.

The structural bifurcation of the development lifecycle into an "Inner Loop" and an "Outer Loop" represents the most significant workflow adaptation. The Inner Loop is characterized by high-velocity, synchronous interactions within AI-native IDEs—such as Windsurf and Cursor—where developers collaborate in real-time with execution-focused agents.5 Conversely, the Outer Loop relies on asynchronous, headless agents operating within Continuous Integration (CI) pipelines or terminal multiplexers to handle long-horizon tasks, architectural enforcement, and rigorous security evaluations.5

Crucially, the friction of manually ferrying context between these disparate agents is being eradicated through novel communication protocols and shared state architectures. The Model Context Protocol (MCP) has achieved universal consensus as the standard bridging layer, allowing different IDEs to interface with identical external data sources and shared memory vectors.10 Simultaneously, the Agent2Agent (A2A) protocol has standardized direct, API-less task delegation between autonomous entities.13 Furthermore, the industry has abandoned fragmented configuration files in favor of the AGENTS.md universal standard and the .agent/ directory convention, providing a single source of truth for agent behavior.15

Finally, the verification of agentic output has transitioned from heuristic reviews to deterministic evaluations modeled on the SWE-bench framework. The utilization of strict FAIL\_TO\_PASS and PASS\_TO\_PASS validation matrices ensures that cross-IDE handoff artifacts provide infallible, mathematical boundaries for task completion.18 Collectively, these patterns constitute a robust, enterprise-grade architecture for multi-agent software development.

## **2\. Dual-Agent Coding Workflows Across IDEs**

The deployment of multiple AI agents, each powered by varied underlying foundation models and hosted in separate environments, establishes a robust division of labor that mirrors human engineering teams. This separation mitigates context window pollution, reduces hallucination through adversarial verification, and ensures that complex architectural tasks are broken down deterministically before execution.21

### **2.1 The Prompt Creator and Executor Paradigm**

A prominent implementation of multi-IDE cooperation relies on the "Planner-Executor" architectural pattern. In this design, a high-level orchestration platform, such as Google Antigravity, is utilized to spawn a "Prompt Creator" or "Architect" agent.2 Operating within Antigravity's designated "Planning Mode," this Architect Agent utilizes a model biased toward deep reasoning (such as Gemini 3 Pro or Claude 3.5 Sonnet) to analyze natural language requirements, explore the existing repository architecture, and formulate a comprehensive strategy without writing operational code.24

The primary output of the Architect Agent is not software, but rather a highly structured sequence of prompts—often serialized as Markdown-based Implementation Plans, Task Lists, and Feature Intent Contracts.24 These artifacts are deposited into the local filesystem. Subsequently, an "Executor Agent" residing in a completely separate environment detects these newly generated prompt sequences. For instance, a developer might utilize the Cascade agent within Windsurf (Codeium's agentic VS Code fork) or a standard VS Code instance augmented with the Claude Code CLI.3 The Executor Agent ingests the Architect's complex prompts and rapidly executes the defined micro-tasks, handling syntax generation, file modifications, and import resolution.3 This strict separation prevents the reasoning agent from exhausting its context window on syntactic minutiae and prevents the execution agent from deviating from the overarching architectural intent.

### **2.2 The Inner Loop and Outer Loop Synergy**

The conceptual framework of the inner and outer loop, traditionally applied to cloud-native application deployment, has been seamlessly adapted for agentic AI architectures.5

The Inner Loop encompasses the interactive, synchronous workspace of the human developer. Tools like Cursor, Windsurf, and JetBrains AI dominate this space, offering inline autocomplete, deep multi-file codebase indexing, and real-time generation capabilities. Within the Inner Loop, the feedback cycle is measured in seconds. The developer continuously guides the AI, reviews inline diffs, and relies on the execution agent for immediate syntactic and localized logical assistance, forming a tight, human-in-the-loop collaboration.5

The Outer Loop represents asynchronous, headless execution, occurring outside the immediate awareness of the developer.8 Once the developer commits code generated in the Inner Loop, an Outer Loop agent assumes control. Implementations frequently utilize CLI-based agents running inside continuous integration environments, such as GitHub Actions.7 This Outer Loop agent operates autonomously, executing deep security reviews, checking compliance against the project's foundational rule files, running extensive remote test suites, and definitively gating pull requests based on its automated findings.7 By strictly delineating these loops, organizations maintain high developer velocity within the local IDE while enforcing rigorous, agent-driven governance at the repository boundary.29

### **2.3 Adversarial TDD-First Workflows**

An increasingly standard pattern for cross-agent cooperation relies on strict Test-Driven Development (TDD) protocols, deeply influenced by the SWE-bench evaluation methodology.18

In a typical multi-session implementation, the workflow is split between a "Test Writer Agent" and an "Implementer Agent".30 The process begins when an orchestrating agent creates a technical specification. The Test Writer Agent—often running in an isolated Docker container to prevent environment contamination—writes comprehensive test suites that define the exact expected behavior, specifically targeting the newly requested feature or reported bug.31

The system programmatically confirms that these new tests fail, establishing a baseline. It also verifies that all pre-existing tests continue to pass, establishing a regression baseline.18 Execution is then handed off to the Implementer Agent. Crucially, the Implementer Agent is purposefully blinded; it does not have read access to the test code directly, receiving only the error traces and the initial problem statement.18 The Implementer continuously modifies the application code until the automated testing matrix reports absolute success. This adversarial setup guarantees that the executing agent cannot trivially modify the test assertions to bypass validation, ensuring that the generated code genuinely satisfies the architectural requirements.31

## **3\. Minimizing Human Relay Between Agents**

The primary friction point in multi-agent ecosystems resides in the handoff. Requiring a human developer to manually copy a prompt or an error trace from one IDE, paste it into another, and actively manage the execution context defeats the core utility of autonomous artificial intelligence. Architectural research reveals several robust patterns specifically designed to minimize or entirely eliminate this manual relay.13

### **3.1 Terminal Orchestration and Multiplexers**

For terminal-native agents such as the Claude Code CLI, OpenAI Codex CLI, and Google Gemini CLI, orchestration is frequently handled via sophisticated terminal multiplexers rather than graphical interfaces.34

Projects such as the "Named Tmux Manager" (ntm) function as comprehensive multi-agent command centers.34 Utilizing these tools, a primary orchestrator agent can programmatically spawn multiple specialized sub-agents into distinct, named tmux or screen panes.34 The architecture allows for the automated broadcasting of prompts across all panes simultaneously and features built-in context-limit detection.34 Furthermore, integration with tools like "MCP Agent Mail" provides a Rust-based, threaded inbox/outbox messaging system. This enables agents operating in completely separate tmux sessions or PowerShell jobs to securely exchange Markdown messages, attach server logs, and negotiate file locks to proactively prevent race conditions during concurrent file modifications.34

### **3.2 Shared Filesystem Triggers and AgentFS Disaggregation**

The most resilient communication layer between opaque AI agents remains the filesystem.36 Agents, having been heavily trained on decades of UNIX-style command-line workflows, excel at reading, writing, and monitoring localized files. File-watching daemons using standard OS events (like inotify) can detect when one IDE completes a task and subsequently trigger a script to awaken an agent in another environment.

Advanced enterprise implementations utilize AgentFS, a filesystem abstraction engineered explicitly for the state management of AI agents.38 AgentFS mounts a POSIX-compliant virtual filesystem that is backed entirely by a single, highly optimized SQLite database.38 Because every file operation, read/write action, tool call, and state transition is captured natively within SQLite tables, an agent operating in one IDE can write an artifact to the AgentFS mount. A secondary agent, operating via a separate CLI, can instantly query this SQLite database, access the artifact, and read the exact chronological timeline of the first agent's actions.38 This provides atomic, reproducible, and deeply auditable state sharing without requiring fragile, custom-built API integrations between the distinct development environments.40

### **3.3 Clipboard Automation and Host OS Bridging**

When agents are siloed in different GUI-based IDEs—such as attempting to pass context between a Cursor window and a JetBrains AI session—and lack a shared terminal environment, clipboard automation serves as a highly effective heuristic bridge. Scripts utilizing host OS-level utilities (such as pbcopy and pbpaste on macOS, xclip on Linux, or /dev/clipboard on Windows/Cygwin) can programmatically extract the output payload of one agent and forcefully inject it into the input buffer of another.41

More sophisticated implementations involve wrapping the system clipboard within an MCP server. This architecture permits an agent operating inside a compatible IDE to autonomously invoke a tool to read the latest image or text copied by the user, or by a competing agent, from an entirely different application.43 This complete automation of the host clipboard facilitates seamless visual debugging and cross-application context gathering without human keystrokes.

### **3.4 Model Context Protocol (MCP) as a Shared State Bus**

The Model Context Protocol has rapidly achieved consensus as the universal integration layer for AI applications, functioning conceptually as a USB-C port for agentic systems.10 By explicitly decoupling the AI reasoning model from the underlying tools and data sources, MCP permits multiple, distinct IDEs to interface concurrently with the exact same state machine.

In a practical implementation, an engineering team deploys a local MCP server that wraps a shared Redis instance or a local SQLite database.11 Agent Alpha, operating inside the Google Antigravity IDE, queries the MCP server, performs an asynchronous analysis, and writes a structured summary into the Redis store. Agent Beta, operating simultaneously inside the Windsurf IDE, maintains an active connection to the same MCP server. Through MCP's dynamic capability discovery and two-way streaming communication architecture, Agent Beta autonomously retrieves Agent Alpha's summary and continues the workflow.46 This elegant design eliminates the need for IDE developers to build proprietary integrations with one another; they simply configure their respective agents as MCP clients connecting to a standardized local context provider.48

### **3.5 The Agent2Agent (A2A) Protocol**

While MCP excels at connecting agents to tools and shared databases, the A2A Protocol—governed by the Linux Foundation and the Agentic AI Foundation—is explicitly designed to connect agents to other agents.13 A2A allows a "client" orchestrator agent to discover a "remote" execution agent's specific capabilities through the parsing of an "Agent Card" (agent.json), a standardized metadata document detailing service endpoints and security requirements.50

Utilizing JSON-RPC over Server-Sent Events (SSE), the A2A protocol natively supports asynchronous, long-running task delegation.13 An agent residing in one IDE can trigger an A2A request to a headless background agent. The background agent accepts the task, transitions into an active state, and continuously streams standardized TaskStatusUpdateEvent and TaskArtifactUpdateEvent messages back to the originating orchestrator.13 This framework standardizes task handoffs and progress monitoring without exposing the proprietary system prompts, internal episodic memory, or underlying foundation models of either participating agent.13

## **4\. Universal Agent Configuration Standards**

During the initial proliferation of agentic coding tools in 2024, repository configuration was severely fragmented. A single complex project might necessitate a .cursorrules file to govern the Cursor IDE, a CLAUDE.md file for Anthropic's CLI, a .windsurfrules file for Codeium's platform, and a .github/copilot-instructions.md file for Microsoft's ecosystem.54 This fragmentation resulted in vast duplication of effort, dangerous version drift, and significant maintenance overhead for engineering teams.56 By 2026, the industry consolidated aggressively around universal standards to unify behavior across all major multi-IDE deployments.

### **4.1 The AGENTS.md Specification**

The AGENTS.md file has emerged as the definitive, universally accepted standard for repository-level AI configuration, adopted by over 60,000 open-source projects and officially supported by leading IDEs including Cursor, VS Code, Windsurf, Jules, and Gemini CLI.15

Serving essentially as a "README for agents," AGENTS.md is a plain text Markdown file securely checked into the root of a version-controlled repository.15 It consciously avoids complex JSON or YAML schemas, relying instead on standard Markdown semantic headings to dictate deterministic agent behavior.56 A comprehensively structured AGENTS.md delineates several critical operational parameters:

* **Persona and Role Specifications:** Explicitly defining the agent's function (e.g., instructing the agent to act as a "Senior Rust Systems Architect") to constrain its reasoning style.59  
* **Executable Environment Commands:** Providing exact, copy-pasteable CLI commands for building the project (pnpm dev), running tests (pnpm vitest), and linting. Agents are instructed to run these programmatic checks autonomously and self-correct any resultant failures prior to task completion.15  
* **Architectural Boundaries:** Explicitly defining strict operational guardrails, such as mandating Dependency Injection patterns, strictly prohibiting modifications to the node\_modules directory, and enforcing specific documentation schemas.7  
* **Hierarchical Overrides for Monorepos:** In massive enterprise monorepos, AGENTS.md supports directory-level scoping. A root-level AGENTS.md file establishes global baseline rules, while an AGENTS.override.md placed within a specific microservice directory (e.g., /services/payments/) overrides those global instructions with strict, service-specific constraints.16

### **4.2 The Universal .agent/ Directory Convention**

Moving beyond single-file instructions, the .agent/ directory convention provides a standardized topological structure for housing complex, project-wide contextual assets.17 This directory acts as the central intelligence hub for all connected IDEs, typically housing:

* .agent/spec/: Formal technical design documents, Product Requirement Documents (PRDs), and high-level architecture blueprints.17  
* .agent/rules/: Passive, globally active constraints and guidelines that are dynamically injected into the agent's system prompt prior to every interaction.61  
* .agent/workflows/: Active, user-triggered sequential processes. These workflows consist of deterministic markdown steps that force the agent to follow a strict, multi-stage protocol when invoked via commands like /release-prep or /security-audit.61

### **4.3 Modular Skill Architectures (SKILL.md)**

To prevent the catastrophic context window bloat associated with injecting hundreds of tool descriptions into a system prompt, agent capabilities have transitioned to a modular "Skills" architecture. A skill is defined as a reusable instruction set that extends an agent's capabilities through a progressive disclosure pattern.63

Housed within the .agent/skills/\<skill-name\>/ directory, each skill consists of a SKILL.md file.63 The architecture of this file pairs YAML frontmatter (which defines the tool's name, description, and trigger conditions) with a Markdown body containing step-by-step invocation logic.63 When an agent initializes, it reads only the lightweight YAML headers of the available skills. If the agent's reasoning model determines a specific skill is highly relevant to the user's current prompt, it actively retrieves and reads the full SKILL.md payload.64 This hierarchical, conditionally-loaded approach allows engineering teams to equip their agents with thousands of specialized capabilities—ranging from AWS CloudFormation deployment protocols to advanced React component scaffolding—without overwhelming the underlying model's context capacity.65 The integration of the mcp-skills server further enhances this by enabling agents to autonomously search for, discover, and dynamically install new skills from open ecosystems like skills.sh during runtime.67

## **5\. Handoff Artifact Design for Inter-Agent Communication**

When an Architect Agent completes a planning task and transfers execution to a Developer Agent in a different IDE, the structural integrity of the payload is paramount. Unstructured natural language handoffs routinely lead to severe hallucination, dropped context, and infinite execution loops. Consequently, structured handoff artifacts have become highly formalized protocols.

### **5.1 Core Artifact Components and Serialization**

Optimal handoff documents are serialized in Markdown, as this format is highly native to LLM tokenization while remaining easily readable by human supervisors requiring oversight capabilities. A structurally sound handoff artifact typically contains the following components:

* **The Contextual Synthesis:** A concise, highly compressed summary of the original user intent combined with the current physical state of the codebase.45  
* **Feature Intent Contracts (FIC):** A declarative, bulleted list of the exact business logic requirements that were successfully negotiated and agreed upon during the planning phase. This serves as the unalterable blueprint for the executor.24  
* **Comprehensive Evidence Bundles:** Hard, indisputable data backing up the preceding agent's analytical decisions. This includes the direct outputs of git diff commands, the exact terminal error logs generated during compilation, and full filesystem tree structures (ls \-R outputs).68  
* **Unambiguous Validation Verdicts:** Strict status markers (e.g., , , \`\`) that a subsequent agent's parsing engine can read deterministically to dictate the routing of the control flow.13

### **5.2 SWE-bench Validation Matrices**

Borrowing directly from the rigorous SWE-bench evaluation methodology utilized for benchmarking frontier models, handoff artifacts between Test Writer Agents and Implementation Agents strictly rely on serialized tables categorizing test execution results.18

The receiving implementation agent is required to parse a specific table containing two explicit parameters:

* FAIL\_TO\_PASS: An array of newly written test cases (e.g., test\_declare\_inputs\_when\_multiple\_args) that the agent must successfully turn green through targeted code modification.20  
* PASS\_TO\_PASS: A comprehensive array of existing regression tests that must remain green; any failure registered in this list indicates that the agent has catastrophically broken pre-existing functionality.20

The strict serialization of these testing arrays—often transmitted as nested JSON payloads inside the TaskArtifactUpdateEvent of an active A2A stream—provides an infallible mathematical boundary for agent execution.13 The assigned task is definitively not considered complete, and handoff to the subsequent Outer Loop agent cannot occur, until the IDE's execution engine automatically verifies the passing state of both test arrays.18

## **6\. Meta-Reflection and Prompt Evolution**

As autonomous agents execute complex, long-horizon workflows across interconnected IDEs, static instructional rules inevitably fail when confronting unique edge cases or undocumented legacy code. Modern agentic architectures have circumvented this limitation by incorporating sophisticated meta-cognitive reflection protocols, creating closed-loop, self-improving systems.

### **6.1 Friction Logs and Autonomous Self-Correction**

During complex execution phases—for example, within Windsurf's Cascade environment or Antigravity's multi-agent Manager—agents are programmatically prompted to maintain continuous "friction logs." If an executing agent encounters repeated, cyclical terminal errors, persistent dependency version conflicts, or continually failing FAIL\_TO\_PASS tests, it halts execution to record the failure mode, formulates a hypothesis regarding the root cause of the failure, and logs the eventual successful resolution.33

### **6.2 Dynamic Rule Updates and Quantitative Scoring**

Rather than relying solely on human engineers to manually update AGENTS.md files or workspace rules, self-improving IDE systems empower the agent to recognize its own systemic reasoning patterns. For instance, if an agent repeatedly hallucinates the directory location of a specific authentication class across multiple sessions, a triggered meta-reflection step allows the agent to extract this pattern of failure and propose an autonomous update to the project's foundational rule files.54

The Google Antigravity platform explicitly treats this evolutionary learning as a core system primitive. Its resident agents autonomously save useful contextual clues, highly successful code generation snippets, and critical architectural decisions to a persistent vector knowledge base. This dynamically and perpetually improves the agent's grounding for all future tasks executed within that specific workspace.22

Furthermore, to refine the efficacy of the prompts themselves, Outer Loop systems continuously monitor quantitative execution metrics. Data points such as "time-to-green" (the exact temporal duration taken to resolve a suite of FAIL\_TO\_PASS tests), absolute "tool call volume," and the "findings count" generated during security reviews are logged and scored.74 These metrics are utilized to quantitatively evaluate the efficiency of the SKILL.md prompt structures, allowing infrastructure teams to ruthlessly identify and prune redundant, confusing, or token-heavy instructions from their global skill libraries.74

## **7\. Rules, Roles, Workflows, and Skills Architecture**

The efficacy of an agentic workflow is entirely dependent on the structural design of its underlying instruction set. The distinction between vague, aspirational guidelines and deterministic, enforceable rules is the primary differentiator between successful multi-IDE deployments and endless loops of hallucination.

### **7.1 Effective Rule Design and Enforcement**

Research into thousands of production AGENTS.md files demonstrates that AI agents routinely ignore broad, qualitative instructions (e.g., "write clean, maintainable code"). Effective rules must be hyper-specific and heavily rely on negative constraints. Best practices dictate the use of a "Three-Tier Boundary System": categorizing actions into strict Always Do (e.g., run pnpm lint before commit), Ask First (e.g., modifying database schema configurations), and Never Do (e.g., editing files within node\_modules).60 Providing concrete, contrasting code blocks showing "Good" versus "Bad" implementations directly within the rule file drastically increases compliance rates.7

### **7.2 API Strategies: Tool Use vs. Function Calling vs. Grounding**

Enforcing these workflows requires deeply understanding how different foundation models interface with external systems. Three distinct paradigms exist for tool enforcement:

1. **OpenAI's Function Calling:** This approach relies on strict, rigidly defined JSON schemas. The model is fine-tuned to output highly structured JSON objects that map perfectly to predefined backend API parameters. It is highly deterministic but can struggle with complex, nested logic that defies simple key-value definitions.  
2. **Anthropic's Tool Use:** Claude models utilize an XML-heavy, descriptive approach. Tools are provided to the model enclosed in explicit XML tags, allowing the model to reason more fluidly about *when* and *why* a tool should be used based on the surrounding contextual prose, rather than merely filling out a JSON template.65  
3. **Google's Grounding (Antigravity):** Instead of relying purely on generalized tool definitions, Google's agentic architecture grounds the model directly into the execution environment. The agent has integrated, native access to spawn browser sub-agents, directly actuating DOM elements and visually analyzing the resultant UI changes to verify execution, closing the loop without requiring complex intermediary API calls.2

## **8\. Pattern Catalog**

The following catalog details the primary architectural patterns utilized in advanced multi-IDE agentic workflows.

| Pattern Name | Source Context | Description | Applicability | Implementation Complexity |
| :---- | :---- | :---- | :---- | :---- |
| **Planner-Executor Handoff** | 24 | Strict separation of concerns where a high-reasoning agent formulates structured Markdown plans, and a secondary execution agent processes them sequentially. | **High**: Essential for complex, multi-file refactoring and mitigating token hallucination. | **Medium**: Requires standardized Markdown parsing and clear .agent/handoff directory structures. |
| **Inner Loop / Outer Loop** | 6 | Interactive, synchronous generation within local IDEs (Windsurf/Cursor) paired with headless, asynchronous verification agents in CI/CD pipelines. | **High**: Critical for enterprise compliance, testing governance, and PR security gating. | **Medium**: Requires deep CI/CD integration and proficiency with headless CLI tools. |
| **Adversarial TDD Validation** | 18 | A test-writer agent creates a strict FAIL\_TO\_PASS test matrix that a separate implementation agent must satisfy without having direct read/write access to the test files. | **High**: Guarantees functional intent, prevents "lazy" code generation, and stops test-cheating. | **High**: Demands robust sandboxing, automated headless test runners, and strict isolation boundaries. |
| **AgentFS State Disaggregation** | 38 | Abstracting the agent's filesystem and complete state memory into a highly portable, fully auditable SQLite database, accessible by multiple agents concurrently. | **Medium**: Excellent for environments utilizing ephemeral compute or when rapidly shifting agents between host machines. | **High**: Requires custom OS-level FUSE mounting and deep integration with SQLite drivers. |
| **Progressive Skill Disclosure** | 63 | Defining complex capabilities in modular .agent/skills/SKILL.md files. Agents only read YAML headers until they deem a skill necessary, vastly reducing context window pollution. | **High**: Prevents prompt bloat in massive enterprise monorepos requiring extensive, specialized toolsets. | **Low**: Purely structural, based entirely on standardized file hierarchy and prompt engineering. |
| **MCP Shared Context Bus** | 11 | Deploying a local Model Context Protocol server that multiple distinct IDEs (e.g., VS Code and Claude Desktop) connect to simultaneously, sharing database access and semantic context. | **High**: The undisputed industry standard for standardized tool and external data integration. | **Medium**: Requires deploying local servers and writing standardized MCP client JSON configurations. |
| **A2A Delegation Protocol** | 13 | Standardizing agent-to-agent communication via HTTP/SSE and metadata Agent Cards, allowing orchestrators to delegate specialized tasks cleanly across vendor platforms. | **Medium**: Ideal for massive enterprise deployments orchestrating swarms across diverse vendor ecosystems. | **High**: Requires implementing complex JSON-RPC servers and managing streaming connection states. |

## **9\. Tool and Project Directory**

| Tool / Framework | Domain | Description | Source / Reference |
| :---- | :---- | :---- | :---- |
| **Google Antigravity** | IDE / Orchestration | An agent-first platform featuring an innovative Agent Manager interface, multi-workspace orchestration, and complex Artifact generation capabilities. | 22 |
| **Windsurf (Cascade)** | IDE / Execution | A highly specialized VS Code fork developed by Codeium. Features deep codebase awareness, Turbo mode autonomous terminal execution, and implicit intent tracking. | 3 |
| **AgentFS** | State Infrastructure | A SQLite-based POSIX virtual filesystem providing portable, queryable, and snapshot-capable state management specifically designed for AI agents. | 38 |
| **Model Context Protocol (MCP)** | Networking / API | The universal open standard connecting isolated AI agents to external data sources, APIs, and shared state memory buses. | 10 |
| **Agent2Agent (A2A)** | Networking / API | The Linux Foundation's official protocol enabling autonomous agent task delegation via JSON-RPC, SSE streams, and standardized Agent Cards. | 13 |
| **Named Tmux Manager (ntm)** | CLI Orchestration | A powerful terminal multiplexer wrapper engineered to simultaneously spawn, coordinate, and broadcast prompts to multiple AI agent swarms. | 34 |
| **mcp-skills** | Agent Extension | An MCP server that bridges local agents to the external skills.sh ecosystem, allowing for the autonomous discovery, recommendation, and installation of capabilities. | 67 |

## **10\. Recommended Architecture**

Synthesizing the analysis of 2026 industry best practices, the optimal architecture for deploying a highly resilient, dual-agent, multi-IDE workflow leverages the high-level orchestration capabilities of Google Antigravity combined with the high-velocity execution engine of Windsurf, bound together deterministically by the AGENTS.md standard and the Model Context Protocol.

**Phase 1: Project Initialization and Universal Grounding**

Establish a universal .agent/ directory at the root of the repository to act as the context hub. Implement a strict AGENTS.md file detailing the specific project boundaries, exact build and test CLI commands, and naming conventions. Populate the .agent/skills/ subdirectory with atomic SKILL.md files for common repetitive tasks (such as database migrations and API documentation generation). Deploy a localized MCP server securely attached to the project's vector database and the host machine's system clipboard to ensure unified context.

**Phase 2: The Architect (Antigravity Manager)**

The Lead Developer initializes Google Antigravity's "Agent Manager" surface. The developer dictates a complex, multi-file feature request into the system. The Antigravity Architect Agent, operating exclusively in "Planning Mode," utilizes the MCP connection to read deep historical context, explores the repository architecture, and synthesizes a comprehensive "Implementation Plan" artifact. Concurrently, it generates a strict FAIL\_TO\_PASS test matrix. The Architect Agent programmatically writes these structured artifacts to a designated .agent/handoff/ directory.

**Phase 3: The Executor (Windsurf Cascade)**

The developer transitions to the Windsurf IDE, initiating the Inner Loop. The Windsurf Cascade agent, continuously tracking filesystem changes via local indexers, is prompted to "Execute the latest handoff plan." Cascade shifts into "Fast Mode" with auto-terminal execution enabled. It systematically reads the Markdown plan, generates the required source code, autonomously executes the test commands explicitly defined in the AGENTS.md file, and recursively debugs any terminal errors until the entire FAIL\_TO\_PASS test matrix turns green. Upon completion, Cascade generates a final Walkthrough artifact detailing the precise topological changes applied to the repository.

**Phase 4: The Verifier (Headless Outer Loop)**

The developer stages and commits the Windsurf-generated code to the repository. This action automatically triggers a CI/CD pipeline, spinning up an Outer Loop agent (such as the Claude Code CLI) in a sandboxed, headless environment. This verification agent performs a ruthless architectural review against the constraints defined in AGENTS.md, runs dynamic security audits via the /security-review command, executes the full remote test suite, and definitively gates the pull request from merging if any deviations from the established standard are detected.

## **11\. Automation Playbook**

To effectively minimize the friction of human relay within the recommended multi-IDE architecture, infrastructure teams must implement the following automated configurations:

1. **MCP Clipboard Bridging (mcp-clipboard-uploader):** Configure both the Windsurf editor and the Antigravity platform to connect continuously to a locally hosted clipboard MCP server. This critical integration allows either autonomous agent to programmatically ingest terminal error logs, copied API keys, or visual UI screenshots copied by the user in a standard web browser, entirely eliminating the requirement for manual copy-pasting between disparate windows.43  
2. **Headless Terminal Orchestration (ntm):** For specialized workflows bypassing GUI-based IDEs entirely, deploy the Named Tmux Manager. Utilize the command ntm quick to instantly scaffold a standardized project environment and simultaneously spawn multiple agent panes (e.g., executing one Claude agent and one Codex agent in parallel). Embed the ntm \--robot-send command within standard bash scripts to automatically broadcast identical test failure traces to all agent panes simultaneously, facilitating parallel, multi-model debugging.34  
3. **AgentFS State Disaggregation:** Mount the primary project workspace utilizing AgentFS. Configure the Antigravity Architect Agent to write its Implementation Plans directly to this SQLite-backed virtual filesystem. Correspondingly, configure the Windsurf IDE to read directly from this specific mount point. This robust configuration guarantees that Windsurf receives an atomic, perfectly reproducible snapshot of the Architect's exact state and historical tool usage.38  
4. **Daemon-Driven File-Watching Triggers:** Implement a lightweight local daemon (utilizing standard OS-level file-watchers such as inotify on Linux or fsevents on macOS) to continuously monitor the .agent/handoff/ directory. Upon detecting the creation of a new Implementation Plan generated by the Antigravity Architect, the daemon must automatically execute a localized Windsurf CLI command to spawn a background Cascade process entirely focused on the new artifact, instantly triggering the execution loop without requiring manual developer intervention.

## **12\. Standards Comparison Matrix**

The evolution of AI agent configuration has rapidly consolidated over the past two years, moving from highly proprietary formats to open standards. The following matrix compares legacy implementations against the established 2026 architectural baselines.

| Standard / File Format | Primary Ecosystem | Internal Structure | Scope & Capability | Current Status (2026) |
| :---- | :---- | :---- | :---- | :---- |
| **AGENTS.md** | Universal Standard (60k+ Repos) | Plain Markdown utilizing standard headers and code blocks. | Operates at Project & Workspace level. Defines agent personas, executable commands, and absolute operational boundaries. Hierarchically overridable via AGENTS.override.md. | **Industry Standard**; Natively supported by Cursor, Windsurf, GitHub Copilot, and Google Antigravity. 15 |
| **.cursorrules / .mdc** | Cursor IDE | Proprietary Markdown / Text format. | Enforces project-specific rules. Can be deeply scoped via specific file globs (e.g., triggering only on \*.ts files). | **Deprecated / Legacy**; Largely replaced by universal AGENTS.md compatibility to prevent vendor lock-in. 76 |
| **CLAUDE.md** | Claude Code CLI | Plain Markdown. | Project root context that is heavily loaded into memory prior to session initialization. | **Active**; In modern multi-IDE setups, this is frequently symlinked directly to AGENTS.md to prevent configuration duplication. 54 |
| **SKILL.md (.agent/skills)** | Antigravity, MCP, Vercel | YAML Frontmatter for metadata \+ Markdown body for execution logic. | Provides modular, dynamically loaded capabilities. Follows a strict "When to use" and "How to use" progressive disclosure schema to save context tokens. | **Emerging Standard** for massive capability extension without incurring severe prompt bloat. 63 |

## **13\. Further Reading**

To deeply expand upon the architectural patterns, verification matrices, and deployment implementations detailed within this research report, the following technical domains and primary resources offer critical next steps for AI infrastructure engineers:

1. **The Model Context Protocol (MCP) Core Specification:** Essential reading for systems engineers tasked with deploying localized shared-state servers (such as SQLite or Redis wrappers) designed to bridge multiple IDEs seamlessly. Thoroughly review Anthropic's official MCP SDK documentation and analyze the implementations within the open-source awesome-mcp-servers repository.10  
2. **SWE-bench Methodologies and TDD Validation Matrices:** To successfully master the complex FAIL\_TO\_PASS and PASS\_TO\_PASS validation matrices strictly required for adversarial agent testing and handoff verification, thoroughly review the original SWE-bench academic methodologies and the subsequent SWE-bench Verified technical literature published by OpenAI.18  
3. **The Agentic AI Foundation and the AGENTS.md Standard:** Review the Linux Foundation's official documentation and governance policies regarding the AGENTS.md schema, its directory-level override mechanics, and mass deployment strategies across enterprise monorepos to ensure absolute cross-IDE behavioral compliance.15  
4. **Agent2Agent (A2A) Protocol Implementations:** For enterprise architects designing massive deployments requiring headless, asynchronous agent delegation and orchestration, review the A2A Draft v1.0 specifications, focusing heavily on the construction of JSON-based Agent Cards and the management of long-running Server-Sent Event (SSE) state streaming.13

#### **Works cited**

1. The best agentic IDEs heading into 2026 \- Builder.io, accessed March 6, 2026, [https://www.builder.io/blog/agentic-ide](https://www.builder.io/blog/agentic-ide)  
2. Introducing Google Antigravity, a New Era in AI-Assisted Software Development, accessed March 6, 2026, [https://antigravity.google/blog/introducing-google-antigravity](https://antigravity.google/blog/introducing-google-antigravity)  
3. Windsurf \- The best AI for Coding, accessed March 6, 2026, [https://windsurf.com/](https://windsurf.com/)  
4. Claude Code vs Cursor: Speed, Accuracy & Cost Benchmark 2026 \- SitePoint, accessed March 6, 2026, [https://www.sitepoint.com/claude-code-vs-cursor-developer-benchmark-2026/](https://www.sitepoint.com/claude-code-vs-cursor-developer-benchmark-2026/)  
5. The Three Developer Loops: A New Framework for AI-Assisted Coding \- IT Revolution, accessed March 6, 2026, [https://itrevolution.com/articles/the-three-developer-loops-a-new-framework-for-ai-assisted-coding/](https://itrevolution.com/articles/the-three-developer-loops-a-new-framework-for-ai-assisted-coding/)  
6. Agents in the Outer Loop | Dec 02, 2025 \- OpenHands, accessed March 6, 2026, [https://openhands.dev/blog/20251202-agents-in-the-outer-loop](https://openhands.dev/blog/20251202-agents-in-the-outer-loop)  
7. 5 steps to automate your Code Reviews with Claude Code. Here's How Our AI Code-Review Agent Actually Works. \- Reza Rezvani, accessed March 6, 2026, [https://alirezarezvani.medium.com/5-tipps-to-automate-your-code-reviews-with-claude-code-5becd60bce5c](https://alirezarezvani.medium.com/5-tipps-to-automate-your-code-reviews-with-claude-code-5becd60bce5c)  
8. How to build reliable AI workflows with agentic primitives and context engineering, accessed March 6, 2026, [https://github.blog/ai-and-ml/github-copilot/how-to-build-reliable-ai-workflows-with-agentic-primitives-and-context-engineering/?utm\_source=blog-release-oct-2025\&utm\_campaign=agentic-copilot-cli-launch-2025](https://github.blog/ai-and-ml/github-copilot/how-to-build-reliable-ai-workflows-with-agentic-primitives-and-context-engineering/?utm_source=blog-release-oct-2025&utm_campaign=agentic-copilot-cli-launch-2025)  
9. Tooling | PROSE, accessed March 6, 2026, [https://danielmeppiel.github.io/awesome-ai-native/docs/tooling/](https://danielmeppiel.github.io/awesome-ai-native/docs/tooling/)  
10. What is the Model Context Protocol (MCP)? \- Model Context Protocol, accessed March 6, 2026, [https://modelcontextprotocol.io/](https://modelcontextprotocol.io/)  
11. Introducing the Model Context Protocol \- Anthropic, accessed March 6, 2026, [https://www.anthropic.com/news/model-context-protocol](https://www.anthropic.com/news/model-context-protocol)  
12. What is Model Context Protocol (MCP)? A guide | Google Cloud, accessed March 6, 2026, [https://cloud.google.com/discover/what-is-model-context-protocol](https://cloud.google.com/discover/what-is-model-context-protocol)  
13. A2A Protocol explained: How AI agents communicate across systems \- CodiLime, accessed March 6, 2026, [https://codilime.com/blog/a2a-protocol-explained/](https://codilime.com/blog/a2a-protocol-explained/)  
14. MCP vs A2A: The Complete Guide to AI Agent Protocols in 2026 \- DEV Community, accessed March 6, 2026, [https://dev.to/pockit\_tools/mcp-vs-a2a-the-complete-guide-to-ai-agent-protocols-in-2026-30li](https://dev.to/pockit_tools/mcp-vs-a2a-the-complete-guide-to-ai-agent-protocols-in-2026-30li)  
15. AGENTS.md, accessed March 6, 2026, [https://agents.md/](https://agents.md/)  
16. Custom instructions with AGENTS.md \- OpenAI for developers, accessed March 6, 2026, [https://developers.openai.com/codex/guides/agents-md/](https://developers.openai.com/codex/guides/agents-md/)  
17. Proposal: Standardize a .agent Directory for Comprehensive Project Context \#71 \- GitHub, accessed March 6, 2026, [https://github.com/agentsmd/agents.md/issues/71](https://github.com/agentsmd/agents.md/issues/71)  
18. Introducing SWE-bench Verified \- OpenAI, accessed March 6, 2026, [https://openai.com/index/introducing-swe-bench-verified/](https://openai.com/index/introducing-swe-bench-verified/)  
19. Claude Sonnet 5 SWE-Bench Results 2026: Verdent Verified Scores & Methodology, accessed March 6, 2026, [https://www.verdent.ai/es/guides/claude-sonnet-5-swe-bench-verified-results](https://www.verdent.ai/es/guides/claude-sonnet-5-swe-bench-verified-results)  
20. SWE-World: Building Software Engineering Agents in Docker-Free Environments \- arXiv.org, accessed March 6, 2026, [https://arxiv.org/html/2602.03419v1](https://arxiv.org/html/2602.03419v1)  
21. 2026 Agentic Coding Trends Report \- Anthropic, accessed March 6, 2026, [https://resources.anthropic.com/hubfs/2026%20Agentic%20Coding%20Trends%20Report.pdf](https://resources.anthropic.com/hubfs/2026%20Agentic%20Coding%20Trends%20Report.pdf)  
22. Build with Google Antigravity, our new agentic development platform, accessed March 6, 2026, [https://developers.googleblog.com/build-with-google-antigravity-our-new-agentic-development-platform/](https://developers.googleblog.com/build-with-google-antigravity-our-new-agentic-development-platform/)  
23. I tried Google's new Antigravity IDE so you don't have to (vs Cursor/Windsurf) \- Reddit, accessed March 6, 2026, [https://www.reddit.com/r/ChatGPTCoding/comments/1p35bdl/i\_tried\_googles\_new\_antigravity\_ide\_so\_you\_dont/](https://www.reddit.com/r/ChatGPTCoding/comments/1p35bdl/i_tried_googles_new_antigravity_ide_so_you_dont/)  
24. Getting Started with Google Antigravity, accessed March 6, 2026, [https://codelabs.developers.google.com/getting-started-google-antigravity](https://codelabs.developers.google.com/getting-started-google-antigravity)  
25. Windsurf IDE Guide: Cascade Agent, Setup & Deployment | DeployHQ, accessed March 6, 2026, [https://www.deployhq.com/guides/windsurf](https://www.deployhq.com/guides/windsurf)  
26. A Developer's Guide to Writing Secure Code with Windsurf \- StackHawk, accessed March 6, 2026, [https://www.stackhawk.com/blog/a-developers-guide-to-writing-secure-code-with-windsurf/](https://www.stackhawk.com/blog/a-developers-guide-to-writing-secure-code-with-windsurf/)  
27. Claude Code vs Cursor: The Ultimate Comparison (2026) \- SitePoint, accessed March 6, 2026, [https://www.sitepoint.com/claude-code-vs-cursor-comparison/](https://www.sitepoint.com/claude-code-vs-cursor-comparison/)  
28. Augment Vs Code Extension vs. CLI | PDF | Software Development \- Scribd, accessed March 6, 2026, [https://www.scribd.com/document/983196061/Augment-vs-Code-Extension-vs-CLI](https://www.scribd.com/document/983196061/Augment-vs-Code-Extension-vs-CLI)  
29. Automated Code Review: Benefits, Tools & Implementation (2026 Guide) \- DEV Community, accessed March 6, 2026, [https://dev.to/cpave3/automated-code-review-benefits-tools-implementation-2026-guide-5dgd](https://dev.to/cpave3/automated-code-review-benefits-tools-implementation-2026-guide-5dgd)  
30. wake-word-detectie | Skills Marketplace \- LobeHub, accessed March 6, 2026, [https://lobehub.com/nl/skills/martinholovsky-claude-skills-generator-wake-word-detection](https://lobehub.com/nl/skills/martinholovsky-claude-skills-generator-wake-word-detection)  
31. Those doing "TDD"... Are you really? : r/ClaudeCode \- Reddit, accessed March 6, 2026, [https://www.reddit.com/r/ClaudeCode/comments/1q9vkvh/those\_doing\_tdd\_are\_you\_really/](https://www.reddit.com/r/ClaudeCode/comments/1q9vkvh/those_doing_tdd_are_you_really/)  
32. Vibe Coding: Testing & Quality Assurance \- Synaptic Labs Blog, accessed March 6, 2026, [https://blog.synapticlabs.ai/software-testing-principles-quality-assurance-guide](https://blog.synapticlabs.ai/software-testing-principles-quality-assurance-guide)  
33. When AI Writes Code, Who's Accountable for Quality? | mabl, accessed March 6, 2026, [https://www.mabl.com/blog/when-ai-writes-code-who-accountable-quality](https://www.mabl.com/blog/when-ai-writes-code-who-accountable-quality)  
34. Dicklesworthstone/agentic\_coding\_flywheel\_setup ... \- GitHub, accessed March 6, 2026, [https://github.com/Dicklesworthstone/agentic\_coding\_flywheel\_setup](https://github.com/Dicklesworthstone/agentic_coding_flywheel_setup)  
35. tmux free download \- SourceForge, accessed March 6, 2026, [https://sourceforge.net/directory/?q=tmux](https://sourceforge.net/directory/?q=tmux)  
36. Agent Communication Protocols: A Developer Guide \- Fast.io, accessed March 6, 2026, [https://fast.io/resources/agent-to-agent-communication-protocol/](https://fast.io/resources/agent-to-agent-communication-protocol/)  
37. How to Implement Agent-to-Agent Communication Protocols Using Shared Files \- Fast.io, accessed March 6, 2026, [https://fast.io/resources/agent-to-agent-file-communication-protocols/](https://fast.io/resources/agent-to-agent-file-communication-protocols/)  
38. tursodatabase/agentfs: The filesystem for agents. · GitHub \- GitHub, accessed March 6, 2026, [https://github.com/tursodatabase/agentfs](https://github.com/tursodatabase/agentfs)  
39. agentfs/README.md at main \- GitHub, accessed March 6, 2026, [https://github.com/tursodatabase/agentfs/blob/main/README.md](https://github.com/tursodatabase/agentfs/blob/main/README.md)  
40. The Missing Abstraction for AI Agents: The Agent Filesystem \- Turso, accessed March 6, 2026, [https://turso.tech/blog/agentfs](https://turso.tech/blog/agentfs)  
41. jlevy/the-art-of-command-line: Master the command line, in one page \- GitHub, accessed March 6, 2026, [https://github.com/jlevy/the-art-of-command-line](https://github.com/jlevy/the-art-of-command-line)  
42. Error: Can't open display: (null) when using Xclip to copy ssh public key \[closed\], accessed March 6, 2026, [https://stackoverflow.com/questions/18695934/error-cant-open-display-null-when-using-xclip-to-copy-ssh-public-key](https://stackoverflow.com/questions/18695934/error-cant-open-display-null-when-using-xclip-to-copy-ssh-public-key)  
43. A Developer's Guide to the Clipboard to Supabase MCP Server, accessed March 6, 2026, [https://skywork.ai/skypage/en/developer-guide-clipboard-supabase/1978635005632749568](https://skywork.ai/skypage/en/developer-guide-clipboard-supabase/1978635005632749568)  
44. lm-studio · GitHub Topics, accessed March 6, 2026, [https://github.com/topics/lm-studio?o=desc\&s=updated](https://github.com/topics/lm-studio?o=desc&s=updated)  
45. Engineering for AI Agents \- Redis, accessed March 6, 2026, [https://redis.io/blog/engineering-for-ai-agents/](https://redis.io/blog/engineering-for-ai-agents/)  
46. punkpeye/awesome-mcp-servers \- GitHub, accessed March 6, 2026, [https://github.com/punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers)  
47. Model Context Protocol (MCP) Clearly Explained : r/LLMDevs \- Reddit, accessed March 6, 2026, [https://www.reddit.com/r/LLMDevs/comments/1jbqegg/model\_context\_protocol\_mcp\_clearly\_explained/](https://www.reddit.com/r/LLMDevs/comments/1jbqegg/model_context_protocol_mcp_clearly_explained/)  
48. Beyond APIs: Lessons from Building with the Model Context Protocol (MCP) \- Medium, accessed March 6, 2026, [https://medium.com/@wim.henderickx/beyond-apis-lessons-from-building-with-the-model-context-protocol-mcp-dc85ca83bb89](https://medium.com/@wim.henderickx/beyond-apis-lessons-from-building-with-the-model-context-protocol-mcp-dc85ca83bb89)  
49. What is Model Context Protocol (MCP)? \- IBM, accessed March 6, 2026, [https://www.ibm.com/think/topics/model-context-protocol](https://www.ibm.com/think/topics/model-context-protocol)  
50. Announcing the Agent2Agent Protocol (A2A) \- Google for Developers Blog, accessed March 6, 2026, [https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/)  
51. Agent2Agent and MCP: An End-to-End Tutorial for a complete Agentic Pipeline | Matteo Villosio Personal Blog, accessed March 6, 2026, [https://matteovillosio.com/post/agent2agent-mcp-tutorial/](https://matteovillosio.com/post/agent2agent-mcp-tutorial/)  
52. A2A Protocol Explained: Secure Interoperability for Agentic AI 2026 \- OneReach, accessed March 6, 2026, [https://onereach.ai/blog/what-is-a2a-agent-to-agent-protocol/](https://onereach.ai/blog/what-is-a2a-agent-to-agent-protocol/)  
53. Agent2Agent (A2A) is an open protocol enabling communication and interoperability between opaque agentic applications. · GitHub, accessed March 6, 2026, [https://github.com/a2aproject/A2A](https://github.com/a2aproject/A2A)  
54. The Complete Guide to AI Agent Memory Files (CLAUDE.md, AGENTS.md, and Beyond), accessed March 6, 2026, [https://medium.com/data-science-collective/the-complete-guide-to-ai-agent-memory-files-claude-md-agents-md-and-beyond-49ea0df5c5a9](https://medium.com/data-science-collective/the-complete-guide-to-ai-agent-memory-files-claude-md-agents-md-and-beyond-49ea0df5c5a9)  
55. Is this a good approach? Unified rule management for multiple AI coding assistants (Cursor \+ Claude Code) : r/ClaudeAI \- Reddit, accessed March 6, 2026, [https://www.reddit.com/r/ClaudeAI/comments/1m069n2/is\_this\_a\_good\_approach\_unified\_rule\_management/](https://www.reddit.com/r/ClaudeAI/comments/1m069n2/is_this_a_good_approach_unified_rule_management/)  
56. AGENTS.md \- by Sagar Patil \- Medium, accessed March 6, 2026, [https://medium.com/@sagarpatiler/agents-md-dbc1f69f689d](https://medium.com/@sagarpatiler/agents-md-dbc1f69f689d)  
57. Linux Foundation Announces the Formation of the Agentic AI Foundation (AAIF), Anchored by New Project Contributions Including Model Context Protocol (MCP), goose and AGENTS.md, accessed March 6, 2026, [https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation](https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation)  
58. GitHub \- agentsmd/agents.md: AGENTS.md — a simple, open format for guiding coding agents, accessed March 6, 2026, [https://github.com/agentsmd/agents.md](https://github.com/agentsmd/agents.md)  
59. How to write a good spec for AI agents \- Addy Osmani, accessed March 6, 2026, [https://addyosmani.com/blog/good-spec/](https://addyosmani.com/blog/good-spec/)  
60. How to write a great agents.md: Lessons from over 2,500 repositories \- The GitHub Blog, accessed March 6, 2026, [https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/](https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/)  
61. Tutorial : Getting Started with Google Antigravity Skills, accessed March 6, 2026, [https://medium.com/google-cloud/tutorial-getting-started-with-antigravity-skills-864041811e0d](https://medium.com/google-cloud/tutorial-getting-started-with-antigravity-skills-864041811e0d)  
62. Rules / Workflows \- Google Antigravity Documentation, accessed March 6, 2026, [https://antigravity.google/docs/rules-workflows](https://antigravity.google/docs/rules-workflows)  
63. vercel-labs/skills: The open agent skills tool \- npx skills \- GitHub, accessed March 6, 2026, [https://github.com/vercel-labs/skills](https://github.com/vercel-labs/skills)  
64. Agent Skills \- Google Antigravity Documentation, accessed March 6, 2026, [https://antigravity.google/docs/skills](https://antigravity.google/docs/skills)  
65. Claude Agent Skills: A First Principles Deep Dive \- Han Lee, accessed March 6, 2026, [https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)  
66. I use Skills to orchestrate multiple agents and get much more work done \- Reddit, accessed March 6, 2026, [https://www.reddit.com/r/ClaudeAI/comments/1ql74ui/i\_use\_skills\_to\_orchestrate\_multiple\_agents\_and/](https://www.reddit.com/r/ClaudeAI/comments/1ql74ui/i_use_skills_to_orchestrate_multiple_agents_and/)  
67. mcp-skills | MCP Servers \- LobeHub, accessed March 6, 2026, [https://lobehub.com/mcp/franciscoyuster-mcp-skills](https://lobehub.com/mcp/franciscoyuster-mcp-skills)  
68. FeatureBench: Benchmarking Agentic Coding for Complex Feature Development \- arXiv, accessed March 6, 2026, [https://arxiv.org/html/2602.10975v1](https://arxiv.org/html/2602.10975v1)  
69. Beyond Tool Use: Implementing “Cognitive Patterns” with Google Antigravity Skills \- Medium, accessed March 6, 2026, [https://medium.com/google-cloud/beyond-tool-use-implementing-cognitive-patterns-with-google-antigravity-skills-c0eea90fa430](https://medium.com/google-cloud/beyond-tool-use-implementing-cognitive-patterns-with-google-antigravity-skills-c0eea90fa430)  
70. SWE-rebench: An Automated Pipeline for Task Collection and Decontaminated Evaluation of Software Engineering Agents \- OpenReview, accessed March 6, 2026, [https://openreview.net/pdf?id=nMpJoVmRy1](https://openreview.net/pdf?id=nMpJoVmRy1)  
71. SWE-EVO: Benchmarking Coding Agents in Long-Horizon Software Evolution Scenarios, accessed March 6, 2026, [https://arxiv.org/html/2512.18470v1](https://arxiv.org/html/2512.18470v1)  
72. (PDF) BackportBench: A Multilingual Benchmark for Automated Backporting of Patches, accessed March 6, 2026, [https://www.researchgate.net/publication/398226304\_BackportBench\_A\_Multilingual\_Benchmark\_for\_Automated\_Backporting\_of\_Patches](https://www.researchgate.net/publication/398226304_BackportBench_A_Multilingual_Benchmark_for_Automated_Backporting_of_Patches)  
73. Cascade | Windsurf, accessed March 6, 2026, [https://windsurf.com/cascade](https://windsurf.com/cascade)  
74. What is an Agent? \- Windsurf, accessed March 6, 2026, [https://windsurf.com/blog/what-is-an-agent](https://windsurf.com/blog/what-is-an-agent)  
75. The Agentic AI Infrastructure Landscape in 2025 — 2026: A Strategic Analysis for Tool-Builders | by Sri Srujan Mandava \- Medium, accessed March 6, 2026, [https://medium.com/@vinniesmandava/the-agentic-ai-infrastructure-landscape-in-2025-2026-a-strategic-analysis-for-tool-builders-b0da8368aee2](https://medium.com/@vinniesmandava/the-agentic-ai-infrastructure-landscape-in-2025-2026-a-strategic-analysis-for-tool-builders-b0da8368aee2)  
76. Consensus on using actual cursor rules \`.mdc\` vs \`./docs/\*.md\` files : r/cursor \- Reddit, accessed March 6, 2026, [https://www.reddit.com/r/cursor/comments/1qjekug/consensus\_on\_using\_actual\_cursor\_rules\_mdc\_vs/](https://www.reddit.com/r/cursor/comments/1qjekug/consensus_on_using_actual_cursor_rules_mdc_vs/)  
77. A Complete Guide To AGENTS.md \- AI Hero, accessed March 6, 2026, [https://www.aihero.dev/a-complete-guide-to-agents-md](https://www.aihero.dev/a-complete-guide-to-agents-md)