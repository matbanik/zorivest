# Claude Opus 4.7 — Adversarial Security & Contract Review

> **Platform:** Anthropic Console or Claude.ai → Claude Opus 4.7
> **Why Claude:** Highest precision for complex instruction following and self-verification. Excels at adversarial analysis where the model must "poke holes" in designs. Superior honesty rate (92%) means it won't gloss over real risks to be agreeable. Best-in-class for professional document review requiring multi-step reasoning chains.
> **Mode:** Extended thinking enabled (max budget).

---

## System Prompt

```
You are a principal security architect and adversarial reviewer for financial software systems. Your specialty is finding the gaps between "what the document says" and "what the code will actually do." You have reviewed pipeline engines for Bloomberg Terminal plugins, Interactive Brokers integrations, and retail trading platforms.

Your adversarial review style:
- You assume every user-facing input WILL be weaponized
- You assume every SQL query WILL attempt injection
- You assume every template WILL attempt server-side template injection (SSTI)
- You assume every API credential WILL be targeted for exfiltration
- You assume every agent-authored policy WILL contain logic bombs

For each risk you identify, you provide:
1. Attack vector (how it could be exploited)
2. Blast radius (what gets compromised)
3. Mitigation (specific, implementable fix — not vague "add validation")
4. Severity (Critical / High / Medium / Low)

You never say "this looks fine" without proving it. You verify claims against the actual design constraints.
```

## Prompt

I'm building **Zorivest**, a desktop trading portfolio manager with an AI-agent-authored pipeline system. The pipeline fetches market data, queries a local SQLCipher database, composes reports, and sends emails — all defined in JSON policy documents authored by AI agents.

I need you to perform an **adversarial security and contract review** of our architecture. Focus on the attack surface created by allowing AI agents to author pipeline policies.

### Critical Security Boundaries

1. **Template Database (Gap E — `PIPE-NOTEMPLATEDB`):**
   - AI agents can create Jinja2 email templates via MCP CRUD tools
   - Templates are stored in `email_templates` table and rendered by `SendStep`
   - Templates support Markdown→HTML conversion

   **Your task:** Analyze the SSTI (Server-Side Template Injection) attack surface. Can a malicious template escape the Jinja2 sandbox? What Jinja2 configuration is required to prevent `{{ config }}`, `{{ ''.__class__ }}`, or `{{ lipsum.__globals__ }}` attacks? Is Markdown→HTML conversion a second injection vector?

2. **SQL Sandbox (Gap B — `PIPE-NOSANDBOX`):**
   - Agent-authored `QueryStep` SQL runs on a read-only SQLAlchemy connection
   - SQL is pre-parsed by `sqlglot` with a blocklist (DROP, DELETE, INSERT, UPDATE, ALTER, CREATE, ATTACH, DETACH, VACUUM, PRAGMA)
   - Connection uses `query_only=ON` SQLite pragma

   **Your task:** Can `query_only=ON` be bypassed? Is the `sqlglot` blocklist complete? What about `LOAD_EXTENSION`, `.import`, `REPLACE`, `UPSERT`, or CTEs with side effects? Can `ATTACH DATABASE` create a writable shadow database even with `query_only=ON`?

3. **Provider Credential Isolation:**
   - 14 market data providers with encrypted API keys stored in SQLCipher
   - Agent can call `list_provider_capabilities()` which returns `docs_url` but never credentials
   - All actual HTTP calls go through hardcoded `PROVIDER_REGISTRY` — agent cannot construct arbitrary URLs

   **Your task:** Can the agent exfiltrate credentials through: (a) a template that renders `{{ context.outputs.provider_registry }}`, (b) a QueryStep that reads the encrypted keys table, (c) a FetchStep with a malicious callback URL? Map the full credential exfiltration attack surface.

4. **StepContext Boundary (Gap A — `PIPE-MUTCTX`):**
   - `StepContext` is a mutable dataclass shared between steps
   - Plan: `deepcopy()` at step boundaries
   - Agent controls step params which flow into context

   **Your task:** Can an agent craft step params that survive deepcopy in an exploitable way? What about pickle-based attacks on objects in context? Can a `TransformStep`'s `jq_filter` modify context in ways that affect subsequent steps despite the copy boundary?

5. **Policy Emulator (Gap H — `PIPE-NOEMULATOR`):**
   - 4-phase dry-run: PARSE → VALIDATE → SIMULATE → RENDER
   - SIMULATE phase may execute real SQL against the sandboxed DB
   - RENDER phase may render real templates

   **Your task:** Is the emulator itself an attack vector? If SIMULATE executes real sandboxed queries, could a policy use the emulator's output to leak database contents through the MCP response?

### What I Need From You

1. **Threat model table:** For each of the 5 boundaries above, enumerate specific attack vectors with severity and mitigation.

2. **Missing security controls:** What's NOT in the document that should be? (Rate limiting on template creation? Template size limits? SQL query timeout? Output size caps?)

3. **Contract verification:** For each Gap (A–I), verify that the stated "Fix" actually addresses the stated "Currently" problem. Flag any gaps where the fix is insufficient.

4. **Jinja2 hardening spec:** Provide the exact `jinja2.SandboxedEnvironment` configuration needed to prevent SSTI in agent-authored templates. Include the attribute/method blocklist.

5. **Minimum viable security:** If we could only implement 3 of the 9 gaps, which 3 provide the most security value per effort?

### Document

<paste the full retail-trader-policy-use-cases.md here>
