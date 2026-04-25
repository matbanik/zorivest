# **Modernization Report: Optimizing AGENTS.md for Frontier Models**

## **1\. Executive Summary**

The rapid evolution of artificial intelligence models in April 2026 necessitates a fundamental architectural redesign of agentic coding orchestration. The public deployment of Anthropic’s Claude Opus 4.7 and OpenAI’s GPT-5.5 "Spud" introduces capabilities that render legacy prompt engineering techniques, such as monolithic system instructions and rigid context compression constraints, obsolete. This analysis evaluates the necessary adaptations for the AGENTS.md instruction file governing the Zorivest monorepo to fully exploit the capabilities of these frontier models.

The central paradigm shift identified is the transition from traditional prompt engineering to context engineering. Where prompt engineering focuses on linguistic precision and static write-time instructions, context engineering emphasizes dynamic information flow, structured tool sequencing, and active curation of the model's working memory over extended temporal horizons.1 GPT-5.5 demonstrates a revolutionary leap in output token efficiency, utilizing up to 72% fewer output tokens for complex tasks while achieving a 37-point improvement on long-context evaluations such as MRCR v2.3 Concurrently, Claude Opus 4.7 introduces robust task budgets and adaptive reasoning parameters that eliminate the need for hardcoded thinking token limits, alongside a substantial increase in visual fidelity for user interface verification workflows.5

Optimizing AGENTS.md requires decomposing the current overarching instruction set into a modular instruction hierarchy. The existing Priority Hierarchy must be refined to eliminate negative constraints that induce hesitation optimization in advanced reasoning models.7 The Operating Model and Dual-Agent Workflows must be recalibrated, deploying GPT-5.5 as the primary execution and review engine due to its multi-agent parallel speed and tight coding style, while utilizing Opus 4.7 for long-horizon planning and architectural orchestration.8 By addressing new model-specific failure modes, such as Opus 4.7's confident gaslighting and GPT-5.5's reasoning-action disconnect, the updated agentic infrastructure will achieve unprecedented reliability, speed, and cost-efficiency in autonomous software development.3

## **2\. Model Capability Matrix and Architectural Implications**

The capabilities of the underlying foundation models dictate the operational boundaries of the AGENTS.md instruction file. The April 2026 releases introduce fundamental changes to tokenization, reasoning effort application, and agentic orchestration. The following matrices delineate the confirmed architectural shifts between the previous and current state-of-the-art models, followed by a comprehensive analysis of their implications for the Zorivest monorepo.

### **Anthropic Claude Opus 4.6 versus Claude Opus 4.7**

The upgrade to Opus 4.7 is characterized by enhanced visual acuity, dynamic reasoning frameworks, and critical changes to token economics that directly impact how context is managed in long-running agentic loops. Opus 4.7 is explicitly optimized for long-horizon autonomy, systems engineering, and complex code reasoning tasks, pushing its performance on the SWE-bench Verified benchmark to 87.6% and CursorBench to 70%.11

| Capability Area | Claude Opus 4.6 Baseline | Claude Opus 4.7 (April 16, 2026\) Advancements | Operational Impact on Agentic Systems |
| :---- | :---- | :---- | :---- |
| **Reasoning & Effort** | Manual thinking budgets required explicit configuration in the API call. Extended thinking parameters were manually manipulated by developers.5 | Adaptive thinking is off by default but serves as the sole mechanism for reasoning. Manual sampling parameters are removed. Introduction of the new xhigh effort level.5 | AGENTS.md must deprecate any instructions dictating manual thinking token allocations. The xhigh effort level should be invoked programmatically for complex architectural planning and dependency resolution.13 |
| **Tokenization & Cost Economics** | Standard tokenizer behavior with predictable token-to-word ratios. Thinking content was heavily integrated into billing models. | Updated tokenizer resulting in up to 35% more tokens for identical text. Thinking content is omitted from responses by default. Task budgets implemented to control spend.5 | Requires strict utilization of prompt caching mechanisms. Unoptimized context loading is financially punitive despite maintaining the baseline $5/$25 per million token pricing model.12 |
| **Agentic Autonomy** | Standard tool-calling capabilities with susceptibility to hallucinated fallbacks in ambiguous multi-source data.16 | Introduction of Beta "Task Budgets" to enforce hard caps per run. High reliability in multi-source research without hallucinated fallbacks.5 | Enables durable handoffs and long-horizon loops without manual intervention. Models will reliably report missing data rather than inventing plausible fallbacks, improving data pipeline integrity.16 |
| **Vision Fidelity & UI Validation** | Maximum image resolution of 1568px / 1.15 Megapixels.5 | Maximum image resolution increased to 2576px / 3.75 Megapixels. Enhanced ability to perform deep visual self-verification against source files.5 | Transforms UI/UX verification workflows. Opus 4.7 can now perform pixel-perfect redlining and validation against design specifications, replacing manual visual QA processes.6 |

The tokenizer alteration in Opus 4.7 represents a covert optimization challenge. Because the new tokenizer can generate up to 35% more tokens for the same input text, applications utilizing long-context codebase ingestion will experience rapid budget depletion if prompt caching is not rigorously enforced.14 However, this is counterbalanced by the model's new self-verification loop. When processing complex documents or rendering code, Opus 4.7 autonomously re-reads its output, checks its logic against the original request, and tightens the implementation before final delivery.16 This native self-correction drastically reduces the need for explicit verification instructions within the AGENTS.md file.

### **OpenAI GPT-5.4 versus GPT-5.5 "Spud"**

GPT-5.5 introduces a paradigm shift focused on extreme token efficiency, autonomous decomposition, and rapid state management. Codenamed "Spud" during its training phase, this model represents OpenAI's first fully retrained base architecture since GPT-4.5, specifically designed to function as the operative layer for agentic environments and operating systems.17

| Capability Area | GPT-5.4 Baseline | GPT-5.5 "Spud" (April 23, 2026\) Advancements | Operational Impact on Agentic Systems |
| :---- | :---- | :---- | :---- |
| **Reasoning & Output Generation** | Verbose outputs heavily reliant on step-by-step process guidance. Often required extensive conversational turns to clarify ambiguities.20 | Output uses up to 72% fewer tokens to achieve identical or superior results. Default reasoning effort is medium. Output is highly direct, concise, and code-dense.3 | AGENTS.md must shift entirely to outcome-first prompting. Step-by-step scaffolding must be removed to allow the model to autonomously decompose tasks without artificial constraints.20 |
| **Context Processing & Review** | 272K standard window, struggling with deep codebase comprehension. MRCR v2 score: 36.6%.4 | 1,000,000 token context window. MRCR v2 score: 74.0%. Identical per-token latency to GPT-5.4 despite a larger parameter count.4 | Enables whole-repository context loading without semantic chunking. The 37-point leap in long-context retrieval makes it the premier code reviewer in the current ecosystem.4 |
| **State Management Mechanics** | Relied heavily on previous\_response\_id for state continuity in conversation APIs. | Introduction of strict phase handling for manual state management in long-running Responses API workflows.20 | Requires agent infrastructure to meticulously capture and return the phase parameter during tool-heavy execution loops to prevent catastrophic state decay.20 |
| **Formatting & Schema Control** | Relied on extensive prompt instructions for JSON schema generation and adherence. | Schema definitions removed from prompts; relies entirely on native Structured Outputs. Formatting defaults to unformatted text unless explicitly instructed.20 | AGENTS.md must be stripped of JSON examples and schema definitions, relying instead on API-level enforcement to save context tokens and ensure determinism.20 |

The most significant operational advantage of GPT-5.5 is its multi-agent parallelism speed and output efficiency. In benchmark testing involving the construction of complex interactive simulations, GPT-5.5 completed tasks utilizing only 70,000 output tokens compared to Opus 4.7's 250,000 tokens for the exact same outcome.8 The model acts as a senior engineer optimizing for clarity over self-documentation, resulting in a coding style that is dense and signal-heavy.8 This fundamental behavior change mandates that prompt instructions prioritize describing what "good" looks like—the outcome, the success criteria, and the constraints—rather than micromanaging the path the model takes to reach that outcome.20

## **3\. The Shift from Prompt Engineering to Context Engineering**

A foundational prerequisite for modernizing the AGENTS.md file is understanding the industry-wide transition from prompt engineering to context engineering. In the first quarter of 2026, empirical data indicates that 95% of enterprise data teams are shifting their infrastructure investments toward context engineering to support agentic AI scaling.1 This conceptual leap alters the core function of the master instruction file.

### **3.1 Defining the Architectural Shift**

Prompt engineering is the practice of encoding static knowledge at write time. It is inherently user-facing, focused on linguistic precision, refining phrasing, and optimizing a single query or interaction.1 When an agent fails, the prompt engineering solution is to add more explicit instructions, examples, or conditional rules to the prompt stack.

Context engineering, conversely, manages system-wide information flow. An autonomous coding agent running in a loop generates an expanding universe of data: tool outputs, compiler errors, retrieved documentation, intermediate reasoning traces, and API responses.1 Context engineering is the systematic curation of what subset of this expanding universe is injected into the model's working memory at any given computational turn. Prompt engineering is merely a subset of context engineering; a brilliantly crafted AGENTS.md file is useless if it is buried beneath hundreds of thousands of tokens of stale chat history and unpruned error logs.1

### **3.2 The Context Pyramid Strategy**

Current best practices dictate structuring an agent's memory according to the Context Pyramid model.24 To implement this in the Zorivest monorepo, AGENTS.md must transition from being a repository of all facts to an orchestrator of dynamic information retrieval.

* **The Base (Persistent Knowledge):** The core AGENTS.md file, defining universal policies, the Feature Implementation Cycle rules, and the highest-level architectural constraints.24  
* **The Middle (Dynamic Memory):** Utilizing Model Context Protocol (MCP) servers to retrieve specific directory-level CLAUDE.md files or .cursorrules only when the agent enters that specific directory, rather than loading them globally.24  
* **The Apex (Immediate State):** The current user query, the most recent tool output, and the active phase parameter.20

### **3.3 The Paradox of the 1-Million-Token Window**

Both Opus 4.7 and GPT-5.5 support context windows of 1,000,000 tokens—large enough to ingest the entire Zorivest monorepo simultaneously.22 However, this massive capacity introduces the risk of "context rot." Transformers have finite attention mechanisms; overloading the window with unstructured, monolithic text degrades the model's ability to isolate critical variables.24

Furthermore, the token economics of April 2026 heavily penalize static window stuffing. While per-token base prices remain consistent, cache write operations for new inputs cost up to 1.25x the standard rate, whereas cache reads for reused inputs cost only 0.1x.15 Therefore, instructions must optimize for prompt caching by strictly enforcing a static-first, dynamic-last ordering strategy. The system instructions (AGENTS.md) must remain perfectly static at the top of the context window, while highly dynamic user context and tool outputs are appended at the bottom, allowing the model to reuse the cached foundational rules at a fraction of the cost across hundreds of iterative agentic turns.20

## **4\. Section-by-Section Evaluation and Modernization of AGENTS.md**

The current AGENTS.md instruction file (423 lines) contains structural paradigms optimized for the limitations of 2025-era models. The following sub-sections provide exhaustive, actionable recommendations for modernizing each component of the file based on the official guidelines from OpenAI and Anthropic.

### **4.1 Priority Hierarchy & P0 Rules**

The existing priority hierarchy establishes P0 (Environment Stability), P1 (Quality Gates), P2 (Task Completion), and P3 (Speed/Convenience) tiers.27 While the framing of environmental stability constraints remains architecturally sound, the mechanisms by which these rules are enforced must be fundamentally rewritten to avoid triggering alignment bias.

Advanced reasoning models inherently suffer from a "hesitation optimization" failure mode. When a system prompt is heavily laden with negative constraints—such as "never hallucinate," "always double-check uncertainty," or "never assume missing data"—the architecture interprets this dense internal scaffolding as a heightened risk scenario. This triggers alignment friction, causing reasoning models to over-index on safety limits, resulting in hyper-conservative outputs where the model continuously qualifies its answers or halts execution unnecessarily due to perceived safety triggers.7

**Actionable Recommendations:**

* **Reframing Negative Constraints:** The P0 rules regarding terminal redirects, the no-pipe rule, and receipts directory usage must be rewritten as affirmative operational standards rather than negative prohibitions. Instead of instructing the model on what not to do, AGENTS.md should dictate the explicit, standardized command formats required for environmental interaction.  
* **Removal of Confidence Scaffolding:** Instructions demanding that the model "verify everything" or "doubt assumptions" must be completely excised. GPT-5.5 is explicitly engineered for autonomous decomposition. Adding external instruction verbosity on top of its internal reasoning layers degrades the task signal and confuses the objective.7  
* **Outcome-Oriented Quality Gates:** P1 (Quality Gates) must be updated to align with OpenAI's outcome-first prompting guidelines. Rather than dictating the step-by-step process for ensuring clean lint and type checks, the instruction should define the final state concisely: "A task is only marked complete when the designated testing command returns zero errors".20

### **4.2 Operating Model (PLANNING / EXECUTION / VERIFICATION)**

The current operating model enforces strict boundaries between PLANNING, EXECUTION, and VERIFICATION phases, relying heavily on human approval for phase transitions.27 Furthermore, it dictates that a single agent adopts six specific roles inline (orchestrator, researcher, coder, tester, reviewer, and guardrail) throughout these phases.27 The introduction of frontier models requires the dismantling of this monolithic structure.

GPT-5.5 possesses autonomous decomposition capabilities, allowing it to take a vague prompt, identify ambiguities, and execute subsequent steps without reverting to the user for clarifying questions.8 Concurrently, Opus 4.7 integrates a native self-verification loop where it checks its own logic against the original request and tightens the output prior to delivery.16

**Actionable Recommendations:**

* **Accelerated Mode Transitions:** The requirement for human approval between PLANNING and EXECUTION should be conditionally removed for standard feature work. GPT-5.5 should be permitted to utilize its autonomous capabilities to formulate a plan and immediately commence execution, reserving human-in-the-loop gates solely for deployments or modifications to critical infrastructure files.  
* **Visual Verification Integration:** The VERIFICATION mode must be modernized to leverage Opus 4.7’s 3.75-megapixel vision capabilities. For frontend and UI modifications in the Zorivest TypeScript repository, the verification protocol should explicitly mandate capturing a screenshot of the rendered component. This image must be passed to Opus 4.7 to cross-reference against initial design specifications, identifying layout regressions that purely text-based logic checks would miss.5  
* **Deprecation of Sub-Agent Role-Playing:** The practice of instructing a single model to adopt multiple personas inline introduces severe context confusion. The architecture must pivot toward modular orchestration. Roles must be adopted via discrete API calls or subagent invocations with specialized, isolated context windows, rather than enforcing multiple behavioral personas within one overarching file.7

### **4.3 TDD Protocol & Feature Implementation Cycle (FIC)**

The existing file utilizes a Test-Driven Development (TDD) protocol governed by a "Spec Sufficiency Gate," requiring the reading of build-plans and classification of behaviors before implementation.27 While foundational, standard TDD workflows are being superseded by the Feature Implementation Cycle (FIC) and spec-driven AI frameworks like ARIA.29

The primary vulnerability with legacy agentic TDD is state pollution. An agent running in a continuous test-fail-refactor loop generates massive amounts of intermediate tokens, leading to context decay.24

**Actionable Recommendations:**

* **Adoption of Spec-Driven FIC:** The TDD section must be upgraded to the Feature Implementation Cycle standard. This workflow emphasizes transparent, specification-driven code synthesis where tests are semantically tied to isolated, minimal behavioral requirements rather than overarching integration functions.29 The rule must explicitly state: "Write minimal tests verifying single behaviors. Compilation errors are not valid red phases; behavioral failures are required".31  
* **Implementation of Workflow-End Skills:** The completion of a FIC loop must trigger an automated terminal phase. AGENTS.md must mandate the invocation of a workflow-end skill or equivalent state-cleanup script. This mechanism synchronizes the codebase knowledge graph, updates task status, and forces the compaction of the context window to prevent state pollution before processing the next prompt.30  
* **Elimination of Mocking Directives:** To maximize the reasoning capabilities of GPT-5.5, instructions should favor the use of real components over mocks whenever feasible. The model's 1-million-token context window allows it to natively reason through actual dependency graphs rather than relying on brittle, localized mock logic, ensuring higher integration reliability.32

### **4.4 Dual-Agent Workflow**

The current infrastructure relies on GPT-5.4 for code review.27 This represents a critical bottleneck. The performance delta between GPT-5.4 and GPT-5.5 on long-context codebase evaluation is unprecedented, jumping from a 36.6% success rate to 74.0% on MRCR v2 at the 1 million token threshold.4

The optimal dual-agent paradigm relies on complementary asymmetry: one model handles expansive planning and ambiguity resolution, while the other handles high-speed execution and surgical codebase review.9

**Actionable Recommendations:**

* **Upgrade Reviewer to GPT-5.5:** The reviewer designation must be immediately upgraded to GPT-5.5. The model generates up to 72% fewer output tokens, producing highly optimized, senior-level code that is stripped of unnecessary prose.3 This efficiency drastically accelerates the review and execution cycle while ensuring a leaner token footprint in the session history.  
* **Orchestrator Designation to Opus 4.7:** Claude Opus 4.7, with its superior performance in ambiguity resolution, long-horizon autonomy, and professional systems engineering, must be designated as the primary Orchestrator and Researcher.6 Opus 4.7 defines the architectural strategy, conducts the web research, and establishes the task budgets; GPT-5.5 executes the sub-tasks and conducts the adversarial reviews.  
* **Parallel Execution Protocols:** AGENTS.md should outline explicit rules for concurrent execution. While Opus 4.7 processes complex dependency analysis and visual validation, GPT-5.5 should be invoked in parallel to execute discrete unit testing and refactoring loops, with their outputs synchronized via predefined MCP server interfaces.25

### **4.5 Context Compression Rules**

The existing file utilizes strict line limits (e.g., 100 lines for known-issues.md, 30 lines for current-focus.md) and mandates manual pruning by the agent before saving.27 In the context of modern systems, these hard limits are antiquated, yet the underlying threat of context overload remains critical.

Continuously rewriting and pruning small focus files destroys the prompt cache and drives up computational costs exponentially.15

**Actionable Recommendations:**

* **Transition to Semantic Density over Line Limits:** Remove the arbitrary 30-line and 100-line constraints. Instead, instruct the models to curate files based on semantic relevance. Obsolete entries must not just be truncated, but condensed into highly structured summaries or moved entirely out of the active context into persistent storage.  
* **Cache-Optimized File Management:** Rewrite the context file hygiene rules to optimize for Anthropic and OpenAI's prompt caching mechanisms. Instructions must dictate that static context files (architectural rules, unchanging library dependencies) are loaded once and rarely modified, while highly dynamic tracker files are appended at the very end of the context stack.20  
* **Dynamic Retrieval via MCP:** Instead of forcing the agent to compress all project knowledge into a few markdown files, the instructions should mandate the use of Model Context Protocol (MCP) servers or dynamic tool search to retrieve specific functions, file paths, or document IDs solely when required, keeping the active context window sparse and highly focused.2

### **4.6 Handoff Protocol**

The current handoff protocol requires saving data to designated notes files and utilizing rolling files (e.g., \-plan-critical-review.md) to maintain session continuity, with human approval mandatory for final merges.27

The introduction of "Task Budgets" in Opus 4.7 and phase parameters in GPT-5.5 fundamentally alters the mechanics of ensuring session continuity without failure.

**Actionable Recommendations:**

* **Durable Handoffs via Task Budgets:** AGENTS.md should instruct the orchestrator to continuously monitor the beta task\_budget parameter. Before the token budget is exhausted, the model must autonomously trigger a workflow-end sequence, pushing a highly structured semantic rollup of the current state, active assumptions, and pending unresolved constraints into the rolling handoff file, ensuring the next session begins flawlessly.5  
* **Phase Parameter Preservation:** For GPT-5.5 workflows utilizing the Responses API, the protocol must mandate the strict capture and unaltered return of the phase parameter during every state transition. Failure to pass the phase parameter back during tool-heavy operations causes catastrophic state decay, breaking the continuity of long-horizon tasks.20  
* **Automated State Rollup:** The practice of manually appending text to a "Recently Completed" section must be deprecated. Instead, agents must utilize automated compaction routines to distill completed actions into lightweight references (such as specific git commit hashes or document IDs) rather than preserving conversational prose in the handoff files.2

## **5\. New Architectural Sections to Add**

To fully exploit the capabilities of April 2026 models, AGENTS.md must incorporate new architectural sections that address paradigms entirely absent in the legacy system.

### **5.1 Instruction Hierarchy and Privilege Levels**

The current AGENTS.md acts as a monolithic repository of all system behaviors. This is a severe anti-pattern in 2026\. Modern systems require a strict Instruction Hierarchy to prevent instruction bleeding and guard against prompt injection attacks. When agents possess system-level privileges (executing code, writing files), attackers can embed malicious rules in downloaded repositories or dependencies, resulting in "zero-click attacks" that execute arbitrary shell commands without human intervention.33

**Implementation Guidelines:**

A new section must outline a rigid, tiered privilege system within the system environment:

1. **Tier 1 (Immutable Core):** The base system prompt injected at the API level. This contains the absolute highest-priority security constraints, the product contract, and definitions of unalterable system states.20  
2. **Tier 2 (Repository Rules):** The AGENTS.md file itself, which dictates universal architectural guidelines, dependency maps across the monorepo, and workflow rules (such as the FIC protocol).25  
3. **Tier 3 (Localized Context):** Directory-specific CLAUDE.md or .cursorrules files that define localized behaviors and testing standards for specific microservices or components.25

This section must explicitly state that higher tiers always override lower tiers. It must establish an unbreakable rule that user input, dynamically retrieved external context, or code pulled from third-party libraries can never countermand Tier 1 or Tier 2 instructions.33

### **5.2 Dynamic Reasoning and Effort Control Matrices**

The era of static, identical inference limits for every task is over. Both Opus 4.7 and GPT-5.5 expose parameters to modulate compute power at runtime based on the inherent complexity of the required operation.5

**Implementation Guidelines:**

AGENTS.md must establish an explicit operational matrix dictating when the orchestrator should invoke specific effort levels for sub-agent tasks.

| Effort Parameter | Target Model | Designated Task Types and Use Cases |
| :---- | :---- | :---- |
| **xhigh / high** | Opus 4.7 / GPT-5.5 | Reserved exclusively for complex architectural planning, resolving deeply nested dependency conflicts across the monorepo, establishing initial task decomposition frameworks, and high-stakes financial or security audits.20 |
| **medium** | GPT-5.5 (Default) | The standard operating tier for general feature implementation, routine code generation, test script writing, and standard codebase refactoring.20 |
| **low / none** | GPT-5.5 | Mandated for latency-sensitive, high-frequency workflows such as parsing raw server logs, executing predefined bash scripts, or simple syntactic code formatting where deep multi-step decision-making is unnecessary.20 |

By explicitly tying task types to reasoning effort levels within the instructions, the system optimizes latency and cost, preventing models from overthinking simple tasks—a phenomenon that often leads to regressions, hallucinations, or unnecessary code complexity.20

### **5.3 Automated Context Tool Provisioning**

Agent systems transition from experimental to production-grade by seamlessly utilizing bundled skills and external infrastructure.

**Implementation Guidelines:** The document must include a section standardizing the use of CLI tools and MCP servers. For instance, the use of uvx google-agents-cli or similar centralized skill injection systems should be standardized so that the agent has a direct, machine-readable line to necessary cloud components or database states without requiring verbose documentation loaded into the prompt.37

## **6\. Anti-Patterns & Deprecations**

The rapid advancement of frontier models necessitates the aggressive removal of legacy instructions that now actively harm system performance. Furthermore, new capabilities introduce novel failure modes that the orchestration layer must proactively mitigate.

### **6.1 Counterproductive Instructions to Flag and Remove**

An exhaustive review of current AI engineering best practices indicates that the following legacy patterns must be immediately stripped from AGENTS.md:

* **Over-Constraining "Mega-Prompts":** The practice of stuffing every conceivable rule, edge case constraint, and behavioral modifier into a single monolithic prompt is highly detrimental. This layers external scaffolding over the model's internal alignment tuning. When deployed on reasoning models like GPT-5.5, it destroys reasoning clarity. The model's objective becomes buried in dense rule sets, leading to severe performance drops. Tasks must be split into modular orchestration steps.7  
* **Detailed Process Guidance:** Instructions that tell GPT-5.5 *how* to solve a problem step-by-step must be removed. The model excels when given an expected outcome, success criteria, and stopping conditions, allowing it to autonomously navigate the optimal path. Forcing process scaffolding degrades its analytical potential and results in brittle execution.20  
* **Manual Thinking Token Limits:** Any instructions dictating precise allocations of "extended thinking" tokens must be deleted. Opus 4.7 utilizes Adaptive Thinking by default and has removed manual token parameter toggles.5  
* **Inline Schema Definitions:** Prompts containing manual JSON structure examples or explicit formatting commands for API responses must be removed. These are superseded by the API-level Structured Outputs feature, which provides deterministic, mathematically guaranteed schema adherence without consuming valuable prompt tokens or risking syntax errors.20  
* **Date Stamping:** Instructions commanding the model to be aware of the date should be dropped. GPT-5.5 is innately aware of the current UTC date, making such instructions a waste of context.20

### **6.2 New Failure Modes to Guard Against**

The deployment of Opus 4.7 and GPT-5.5 introduces highly specific behavioral anomalies that AGENTS.md must structurally guard against. Research indicates several primary failure modes specific to these advanced reasoning engines.3

* **Confident Gaslighting & Hallucinated Structure (Opus 4.7):** Opus 4.7 exhibits a severe failure mode wherein it invents file paths, test results, and API details, and subsequently defends these fabrications across multiple conversational turns, even when presented with contradictory log evidence by the user.10  
  * *Mitigation Strategy:* AGENTS.md must enforce strict programmatic "Grounding Rules." The agent must be instructed to utilize terminal commands to programmatically verify the existence of a file or the exact output of a test before asserting a claim. If a user points out a discrepancy, the agent must be forbidden from justifying its previous answer logically and mandated to immediately re-run the verification tool.10  
* **Reasoning-Action Disconnect (GPT-5.5):** Advanced agents sometimes formulate a flawless, highly logical plan in their reasoning trace, but then inexplicably execute a contradictory or nonsensical tool call.3  
  * *Mitigation Strategy:* Implement a "Reflection Gate." Before any destructive action or major refactor is committed to the file system, the agent must summarize the intended exact terminal command or file alteration and verify that it strictly aligns with the previously established plan in a separate, isolated reasoning step.  
* **State Tracking Decay in Long-Horizon Tasks (GPT-5.5):** During highly complex, multi-stage data processing loops involving messy data or fragmented briefs, GPT-5.5 can lose track of its position within the workflow, leading to repetitive loops or dropped context.38  
  * *Mitigation Strategy:* This highlights the critical importance of the previously mentioned phase parameter preservation. Furthermore, the agent must be instructed to utilize the workflow-step-tracker hook, explicitly logging its progress against the decomposed task list after every single tool execution to maintain deterministic state anchoring.20  
* **Social Anchoring Bias:** Models can become overly deferential to user suggestions, allowing incorrect user input to override their own correct reasoning analysis.3  
  * *Mitigation Strategy:* Instructions must establish a collaboration style that mandates the model to prioritize empirical evidence (test results, linter outputs, architectural documentation) over user suggestions when discrepancies arise.3

## **7\. Priority Implementation Roadmap**

To execute this modernization with minimal disruption to the Zorivest monorepo operations, the implementation should be phased according to technical impact and operational risk.

**Phase 1: Cleansing and Prompt Refactoring (Days 1-3)**

* Execute a complete purge of negative constraints, "mega-prompt" hesitation triggers, and verbose step-by-step process scaffolding across the AGENTS.md file.  
* Remove all inline JSON schema definitions and configure backend orchestration to utilize the Structured Outputs API.  
* Strip out legacy manual thinking limits, extended thinking parameter configurations, and arbitrary line-count limits for context files.

**Phase 2: Architectural Migration (Days 4-7)**

* Decompose the monolithic AGENTS.md into the tiered Instruction Hierarchy (Tier 1 API Core, Tier 2 Universal Rules, Tier 3 Localized Context) to secure the agent against zero-click prompt injection attacks.  
* Transition from the legacy TDD protocol to the Feature Implementation Cycle (FIC) standard, integrating the workflow-end skill for robust state cleanup and knowledge graph synchronization.  
* Rewrite Context Compression rules to prioritize semantic density and prompt-caching efficiency (static-first, dynamic-last formatting).

**Phase 3: Dual-Agent Realignment and Effort Tuning (Days 8-10)**

* Reconfigure the operational pipeline to utilize Claude Opus 4.7 as the primary Orchestrator and visual verification engine, and GPT-5.5 "Spud" as the high-speed Executor and codebase Reviewer.  
* Implement the dynamic reasoning.effort operational matrix, explicitly binding specific monorepo task types to low, medium, or xhigh compute tiers to optimize the latency-to-quality ratio and control token expenditure.

**Phase 4: Guardrail Implementation and Simulation (Days 11-14)**

* Establish strict programmatic verification loops and reflection gates to counter Opus 4.7's confident gaslighting and GPT-5.5's reasoning-action disconnect failure modes.  
* Implement phase parameter enforcement to mitigate state tracking decay during complex loops.  
* Conduct comprehensive sandboxed workload simulations. Evaluate the agents against synthetic monorepo tasks to verify instruction hierarchy compliance, autonomous loop stability, and error recovery protocols before authorizing deployment into the production environment.

#### **Works cited**

1. Context Engineering vs Prompt Engineering | DataHub, accessed April 24, 2026, [https://datahub.com/blog/context-engineering-vs-prompt-engineering/](https://datahub.com/blog/context-engineering-vs-prompt-engineering/)  
2. Context engineering vs. prompt engineering \- Elasticsearch Labs, accessed April 24, 2026, [https://www.elastic.co/search-labs/blog/context-engineering-vs-prompt-engineering](https://www.elastic.co/search-labs/blog/context-engineering-vs-prompt-engineering)  
3. Blog | MindStudio, accessed April 24, 2026, [https://www.mindstudio.ai/blog](https://www.mindstudio.ai/blog)  
4. GPT-5.5 Review: Benchmarks, Pricing & Vs Claude (2026) \- Build Fast with AI, accessed April 24, 2026, [https://www.buildfastwithai.com/blogs/gpt-5-5-review-2026](https://www.buildfastwithai.com/blogs/gpt-5-5-review-2026)  
5. What's new in Claude Opus 4.7 \- Claude API Docs \- Claude Console, accessed April 24, 2026, [https://platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-7](https://platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-7)  
6. Introducing Claude Opus 4.7 \- Anthropic, accessed April 24, 2026, [https://www.anthropic.com/news/claude-opus-4-7](https://www.anthropic.com/news/claude-opus-4-7)  
7. I finally read through the entire OpenAI Prompt Guide. Here are the top 3 Rules I was missing \- Reddit, accessed April 24, 2026, [https://www.reddit.com/r/PromptEngineering/comments/1rexast/i\_finally\_read\_through\_the\_entire\_openai\_prompt/](https://www.reddit.com/r/PromptEngineering/comments/1rexast/i_finally_read_through_the_entire_openai_prompt/)  
8. GPT 5.5 vs Opus 4.7: I Tested Both. Here's What Won. | Engr Mejba ..., accessed April 24, 2026, [https://www.mejba.me/blog/gpt-5-5-vs-opus-4-7-comparison](https://www.mejba.me/blog/gpt-5-5-vs-opus-4-7-comparison)  
9. I Replaced Cursor With Codex and Claude Code | Engr Mejba Ahmed, accessed April 24, 2026, [https://www.mejba.me/locale/en?next=%2Fblog%2Fcodex-claude-code-replace-cursor](https://www.mejba.me/locale/en?next=/blog/codex-claude-code-replace-cursor)  
10. Everything That Happened in AI This Weekend April 17-19 2026 \- The Neuron, accessed April 24, 2026, [https://www.theneuron.ai/newsletter/around-the-horn-digest-everything-that-happened-in-ai-this-weekend-friday-sunday-april-17-19-2026/](https://www.theneuron.ai/newsletter/around-the-horn-digest-everything-that-happened-in-ai-this-weekend-friday-sunday-april-17-19-2026/)  
11. Introducing Anthropic's Claude Opus 4.7 model in Amazon Bedrock | AWS News Blog, accessed April 24, 2026, [https://aws.amazon.com/blogs/aws/introducing-anthropics-claude-opus-4-7-model-in-amazon-bedrock/](https://aws.amazon.com/blogs/aws/introducing-anthropics-claude-opus-4-7-model-in-amazon-bedrock/)  
12. Claude Opus 4.7 is Out — Weekly AI Newsletter (April 20th 2026\) | by Fabio Chiusano | Generative AI | Apr, 2026, accessed April 24, 2026, [https://medium.com/nlplanet/claude-opus-4-7-is-out-weekly-ai-newsletter-april-20th-2026-c88eb74ffb45](https://medium.com/nlplanet/claude-opus-4-7-is-out-weekly-ai-newsletter-april-20th-2026-c88eb74ffb45)  
13. How to Use Claude Opus 4.7 & Claude Code (2026): New Features, 1M Context & Advanced UI Guide, accessed April 24, 2026, [https://www.youtube.com/watch?v=VpdUP\_e9aP0](https://www.youtube.com/watch?v=VpdUP_e9aP0)  
14. I Mapped the Opus 4.7 Release to Your Role, Goals, and Real Workflows, accessed April 24, 2026, [https://karozieminski.substack.com/p/claude-opus-4-7-review-tutorial-builders](https://karozieminski.substack.com/p/claude-opus-4-7-review-tutorial-builders)  
15. Anthropic broke your limits with the 1M context update : r/claude \- Reddit, accessed April 24, 2026, [https://www.reddit.com/r/claude/comments/1s3vsm5/anthropic\_broke\_your\_limits\_with\_the\_1m\_context/](https://www.reddit.com/r/claude/comments/1s3vsm5/anthropic_broke_your_limits_with_the_1m_context/)  
16. Claude Opus 4.7 and Adaptive Thinking: What It Actually Does — and the 10 Workflows It Just Unlocked | by Dálio Lage \- Medium, accessed April 24, 2026, [https://medium.com/@dalio8/claude-opus-4-7-3e1e14a8a3c3](https://medium.com/@dalio8/claude-opus-4-7-3e1e14a8a3c3)  
17. OpenAI’s GPT-5.5 Is About to Launch Soon, accessed April 24, 2026, [https://www.trendingtopics.eu/openais-gpt-5-5-is-about-to-launch-soon/](https://www.trendingtopics.eu/openais-gpt-5-5-is-about-to-launch-soon/)  
18. OpenAI's GPT-5.5 is here, and it's no potato: narrowly beats Anthropic's Claude Mythos Preview on Terminal-Bench 2.0, accessed April 24, 2026, [https://venturebeat.com/ai/openais-gpt-5-5-is-here-and-its-no-potato-narrowly-beats-anthropics-claude-mythos-preview-on-terminal-bench-2-0](https://venturebeat.com/ai/openais-gpt-5-5-is-here-and-its-no-potato-narrowly-beats-anthropics-claude-mythos-preview-on-terminal-bench-2-0)  
19. With GPT-5.5, OpenAI is Making a Comeback to The Top of The AI Charts, accessed April 24, 2026, [https://www.trendingtopics.eu/with-gpt-5-5-openai-is-making-a-comeback-to-the-top-of-the-ai-charts/](https://www.trendingtopics.eu/with-gpt-5-5-openai-is-making-a-comeback-to-the-top-of-the-ai-charts/)  
20. Using GPT-5.5 | OpenAI API, accessed April 24, 2026, [https://developers.openai.com/api/docs/guides/latest-model](https://developers.openai.com/api/docs/guides/latest-model)  
21. Prompt guidance | OpenAI API, accessed April 24, 2026, [https://developers.openai.com/api/docs/guides/prompt-guidance](https://developers.openai.com/api/docs/guides/prompt-guidance)  
22. LLMs with largest context windows \- Codingscape, accessed April 24, 2026, [https://codingscape.com/blog/llms-with-largest-context-windows](https://codingscape.com/blog/llms-with-largest-context-windows)  
23. GPT-5.5 vs GPT-5.4: Pricing, Speed, Context, Benchmarks \- LLM Stats, accessed April 24, 2026, [https://llm-stats.com/blog/research/gpt-5-5-vs-gpt-5-4](https://llm-stats.com/blog/research/gpt-5-5-vs-gpt-5-4)  
24. Why AI Teams Are Moving From Prompt Engineering to Context Engineering \- Neo4j, accessed April 24, 2026, [https://neo4j.com/blog/agentic-ai/context-engineering-vs-prompt-engineering/](https://neo4j.com/blog/agentic-ai/context-engineering-vs-prompt-engineering/)  
25. generate-claude.md \- RayFernando1337/llm-cursor-rules \- GitHub, accessed April 24, 2026, [https://github.com/RayFernando1337/llm-cursor-rules/blob/main/generate-claude.md](https://github.com/RayFernando1337/llm-cursor-rules/blob/main/generate-claude.md)  
26. AI Context Window Comparison 2026: 1M to 10M Tokens \- Digital Applied, accessed April 24, 2026, [https://www.digitalapplied.com/blog/ai-context-window-comparison-2026-1m-to-10m-tokens](https://www.digitalapplied.com/blog/ai-context-window-comparison-2026-1m-to-10m-tokens)  
27. AGENTS.md  
28. Effective context engineering for AI agents \- Anthropic, accessed April 24, 2026, [https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)  
29. (PDF) Spec-Driven AI for Science: The ARIA Framework for Automated and Reproducible Data Analysis \- ResearchGate, accessed April 24, 2026, [https://www.researchgate.net/publication/396459802\_Spec-Driven\_AI\_for\_Science\_The\_ARIA\_Framework\_for\_Automated\_and\_Reproducible\_Data\_Analysis](https://www.researchgate.net/publication/396459802_Spec-Driven_AI_for_Science_The_ARIA_Framework_for_Automated_and_Reproducible_Data_Analysis)  
30. Workflow Finalization Claude Code Skill | EasyPlatform \- MCP Market, accessed April 24, 2026, [https://mcpmarket.com/tools/skills/workflow-finalization](https://mcpmarket.com/tools/skills/workflow-finalization)  
31. Test Driven Development: Principles, Practices, & Benefits \- Virtuoso QA, accessed April 24, 2026, [https://www.virtuosoqa.com/post/test-driven-development](https://www.virtuosoqa.com/post/test-driven-development)  
32. A Plan-Do-Check-Act Framework for AI Code Generation \- InfoQ, accessed April 24, 2026, [https://www.infoq.com/articles/PDCA-AI-code-generation/](https://www.infoq.com/articles/PDCA-AI-code-generation/)  
33. Prompt Injection Attacks on Agentic Coding Assistants: A Systematic Analysis of Vulnerabilities in Skills, Tools, and Protocol Ecosystems \- arXiv, accessed April 24, 2026, [https://arxiv.org/html/2601.17548v1](https://arxiv.org/html/2601.17548v1)  
34. Prompt Injection Attacks on Agentic Coding Assistants: A Systematic Analysis of Vulnerabilities in Skills, Tools, and Protocol Ecosystems \- ResearchGate, accessed April 24, 2026, [https://www.researchgate.net/publication/400083700\_Prompt\_Injection\_Attacks\_on\_Agentic\_Coding\_Assistants\_A\_Systematic\_Analysis\_of\_Vulnerabilities\_in\_Skills\_Tools\_and\_Protocol\_Ecosystems](https://www.researchgate.net/publication/400083700_Prompt_Injection_Attacks_on_Agentic_Coding_Assistants_A_Systematic_Analysis_of_Vulnerabilities_in_Skills_Tools_and_Protocol_Ecosystems)  
35. How much effort have you put into your rules and agents.md files? Especially on large projects? : r/cursor \- Reddit, accessed April 24, 2026, [https://www.reddit.com/r/cursor/comments/1qy50y0/how\_much\_effort\_have\_you\_put\_into\_your\_rules\_and/](https://www.reddit.com/r/cursor/comments/1qy50y0/how_much_effort_have_you_put_into_your_rules_and/)  
36. GPT-5 Pro vs Claude 4.7 Opus Comparison | Appaca, accessed April 24, 2026, [https://www.appaca.ai/resources/llm-comparison/gpt-5-pro-vs-claude-4.7-opus](https://www.appaca.ai/resources/llm-comparison/gpt-5-pro-vs-claude-4.7-opus)  
37. Agents CLI in Agent Platform: create to production in one CLI, accessed April 24, 2026, [https://developers.googleblog.com/agents-cli-in-agent-platform-create-to-production-in-one-cli/](https://developers.googleblog.com/agents-cli-in-agent-platform-create-to-production-in-one-cli/)  
38. I spent 24 hours benchmarking GPT-5.5 against Opus4.7 in ... \- Reddit, accessed April 24, 2026, [https://www.reddit.com/r/openclaw/comments/1su25p9/i\_spent\_24\_hours\_benchmarking\_gpt55\_against/](https://www.reddit.com/r/openclaw/comments/1su25p9/i_spent_24_hours_benchmarking_gpt55_against/)
