# ChatGPT GPT-5.4 — Agentic Workflow & UX Validation

> **Platform:** ChatGPT → Deep Research mode (`/deepresearch`)
> **Why GPT-5.4:** Optimized for multi-step agentic workflow analysis. Its steerable research plan lets you redirect mid-investigation. Best for validating the end-to-end agent authoring loop because it can simulate being the agent and identify friction points. The "poke holes" follow-up method adds a critical validation layer.
> **Mode:** Deep Research with extended reasoning.

---

## Prompt (paste directly into ChatGPT Deep Research)

### Role

You are a senior product architect specializing in **AI-agent-first developer tools**. You have built MCP server integrations for Cursor, Windsurf, and Claude Code. You understand how AI coding agents actually work: what context they need, what tool calling patterns they use, and where they fail.

### Background

I'm building **Zorivest**, a desktop trading portfolio manager (Electron + Python). We're designing a **pipeline policy system** that is meant to be authored primarily by AI agents (not humans). The pipeline:

- Fetches market data from 14 hardcoded providers
- Queries a local SQLCipher database
- Transforms and composes data
- Renders email reports from Jinja2 templates
- Sends emails on a cron schedule

The complete architecture document is attached below. It defines 9 implementation gaps (A–I) and a 4-phase emulator for dry-run validation.

### Your Task: Simulate the Agent Authoring Experience

**Pretend you are an AI agent (Claude, GPT, or Gemini) operating inside an agentic IDE (Cursor, Windsurf, Claude Code).** The user says: *"Create a daily morning check-in report that shows my watchlist tickers, account balances, recent trades, and top market news. Send it to me at 7am EST."*

Walk through the **complete agent workflow** step by step:

1. **Discovery phase:** What MCP tools do you call first? What information do you need before you can start authoring? Identify any gaps where the available tools don't give you enough information.

2. **Template authoring:** Using the `create_email_template` MCP tool, draft the actual Jinja2 template. Identify what `required_variables` you'd declare and what `sample_data_json` you'd provide for the emulator.

3. **Policy composition:** Author the complete policy JSON document. For each step, explain why you chose that step type and what params you set. Identify any friction points where the policy schema is confusing or limiting.

4. **Validation loop:** Call `emulate_policy()` with your policy JSON. What do you expect back? If the emulator reports a missing variable or invalid SQL, how do you iterate? Is the error output structured enough for you to self-correct?

5. **Provider discovery:** You need stock quotes from Yahoo Finance and news from Finnhub. The `list_provider_capabilities` tool gives you `docs_url` links. **Actually web search** the Yahoo Finance API docs and Finnhub API docs. Is the information you find sufficient to compose a valid `fetch` step? What's missing?

6. **Edge cases:** What happens if:
   - The user's watchlist is empty?
   - A provider API is down at 7am?
   - The email template references a variable that no step produces?
   - The user later says "add earnings calendar data to the report" — how much of the policy do you need to rewrite?

### Specific Questions

1. **MCP tool completeness:** Are the 10 proposed MCP tools sufficient for an agent to author a complete policy from scratch? What additional tools would make the workflow significantly smoother?

2. **Error message quality:** When the emulator returns `{valid: false, errors: [...]}`, what information does the error need to contain for the agent to self-correct in 1-2 iterations? Design the ideal error schema.

3. **Template DB vs. inline:** We chose a database entity for templates instead of embedding them in the policy JSON. From an agent workflow perspective, does the extra CRUD step (create template → reference in policy) add friction, or does the reusability justify it?

4. **Provider docs_url approach:** We decided against a static capability catalog in favor of `docs_url` + agent web search. As an agent, would you prefer structured metadata (JSON schema of each endpoint) or a documentation URL? What's the minimum structured metadata you need to avoid web search for common operations?

5. **Default template strategy:** We plan to ship a pre-loaded "Morning Check-In" template. Should this be a complete, ready-to-use template that the agent customizes, or a minimal skeleton that the agent extends? What makes the agent's job easier?

### Follow-Up (after initial research)

After you complete the analysis, I will ask you to:
> *"Act as a skeptical QA engineer who has tested 50 MCP server integrations. Review your analysis and identify 3 places where the proposed design would cause real-world agent failures that you initially overlooked."*

### Document

<paste the full retail-trader-policy-use-cases.md here>

---

### Web Search Guidance

When researching provider APIs, search for:
- `Yahoo Finance API v8 endpoints 2026` — to validate the fetch step can get the data needed
- `Finnhub API news endpoint documentation` — to validate news fetching
- `Jinja2 SandboxedEnvironment security best practices` — to validate template security claims
- `sqlglot SQL parser blocklist bypass` — to validate SQL sandbox claims
- `MCP server tool design patterns best practices` — to validate MCP tool design
- `Prefect 3 pipeline emulator dry-run pattern` — to find simplification opportunities
