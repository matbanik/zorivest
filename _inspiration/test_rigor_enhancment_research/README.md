# Test Rigor Enhancement Research

Research prompts and results for enhancing Zorivest's testing strategy beyond unit/integration tests.

## Prompts (submit to web interfaces)

| # | File | Model | Strength Leveraged |
|---|------|-------|--------------------|
| 1 | `01-gemini-3.1-pro-prompt.md` | Gemini 3.1 Pro | Large context, systematic enumeration, framework comparison |
| 2 | `02-gpt-5.4-prompt.md` | ChatGPT GPT-5.4 | Deep reasoning + web search, finding real implementations |
| 3 | `03-claude-opus-4.6-prompt.md` | Claude Opus 4.6 | Extended thinking, architectural trade-off analysis |

## Results (place here after submitting)

Name the result files with matching prefixes:
- `01-gemini-3.1-pro-results.md`
- `02-gpt-5.4-results.md`
- `03-claude-opus-4.6-results.md`

## Next Steps (after results are in)

The results will be processed to:
1. Enhance the execution plan at `docs/execution/plans/2026-03-16-test-rigor-audit/`
2. Add new testing workflows and skills to `.agent/workflows/` and `.agent/skills/`
3. Update `AGENTS.md` with test rigor rules for the agentic development process
4. Design the E2E test architecture and GUI testing strategy

## Coverage Areas

| Area | Gemini | GPT-5.4 | Opus |
|------|--------|---------|------|
| E2E GUI testing (Electron + React + Python) | ✅ Framework comparison | ✅ Real implementations | ✅ Design reasoning |
| MCP protocol testing | ✅ Pattern catalog | ✅ GitHub survey | ✅ Strategy design |
| Cross-layer communication | ✅ Contract testing tools | ✅ Pact/Schemathesis | ✅ Boundary analysis |
| Security testing | ✅ OWASP/tools | ✅ Security-as-code | ✅ Invariant-based |
| Minimizing human GUI testing | ✅ Automation tools | ✅ Record/replay | ✅ Speed vs coverage |
| Intent-based testing | — | ✅ Industry practices | ✅ Design pattern |
| Agentic workflow integration | — | — | ✅ AGENTS.md rules |
