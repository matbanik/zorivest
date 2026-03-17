# Deep Research Prompt — Claude Opus 4.6

> **Model strength leveraged**: Opus 4.6's extended thinking with deep analysis, architectural reasoning, nuanced trade-off evaluation, ability to synthesize complex multi-constraint problems, and strong understanding of software engineering principles.

---

## Prompt

I need your deep analysis on designing a comprehensive testing strategy for a complex desktop application. I want you to think deeply about the architectural implications, trade-offs, and the interaction between testing layers. This is not a framework comparison exercise — I need you to reason through the **design** of a testing system.

### Application Context

**Zorivest** is a local-first desktop trading journal with Clean Architecture:

- **Domain** (Python, pure): Entities (Trade, Account, TradePlan, Watchlist), value objects, ports, calculator, analytics engine, pipeline engine with policy validation
- **Infrastructure** (Python): SQLAlchemy + SQLCipher (encrypted at rest), Unit of Work, repositories, backup manager with AES-encrypted zip
- **API** (Python, FastAPI): REST on localhost:8765, mode-gating (locked/unlocked), Pydantic validation, dependency injection
- **MCP** (TypeScript): 40+ tools exposed to AI assistants via JSON-RPC stdio, toolset-based registration, circuit breaker security
- **GUI** (Electron + React): Desktop app, IPC to main process, REST calls to Python backend

**Testing maturity**: 1,357 tests (pytest + vitest), excellent unit coverage with AC traceability, mock-based service tests, 6 integration tests with real SQLite/SQLCipher. **Zero E2E, zero GUI, zero security-specific tests.**

**The gap**: Tests verify individual components work in isolation but do NOT verify:
1. Data flows correctly from GUI input → through all layers → to encrypted DB → and back to GUI display
2. The MCP server correctly mediates between IDE requests and the Python backend
3. Security properties hold under adversarial conditions (not just happy path)
4. The system's behavioral intent (not just function correctness)

### Analysis 1: Designing a Testing Pyramid for Multi-Runtime Clean Architecture

Think through how the classical testing pyramid should be **adapted** for this architecture:

```
                    ┌─────────┐
                    │  E2E    │  GUI → API → DB → GUI
                    │ (few)   │  MCP → API → DB → MCP
                   ─┤─────────├─
                  │ Integration │  API → Service → Repo → DB
                  │ (moderate)  │  MCP → REST contract
                 ─┤────────────├─
               │   Unit Tests   │  Domain, Service (mocked), API handlers
               │   (many)       │  MCP tools (vitest)
               ─┴───────────────┴─
```

For this specific architecture, analyze:

1. **Where should the integration layer boundaries be drawn?**
   - Currently the 6 integration tests go: Repository → SQLite. Is this the right boundary?
   - Should there be an integration tier for: API → Service → Repository (without mocks)?
   - What about the MCP → REST boundary — is this integration or E2E?
   - How does the encrypted database (SQLCipher) change the integration testing strategy?

2. **What is the minimum viable E2E test set?**
   - Define the critical user journeys that must be E2E tested (not every feature, just the ones where cross-layer bugs are most likely)
   - For each journey, specify exactly which layers are exercised and what assertions are needed
   - Consider: trade creation, position sizing, backup/restore, lock/unlock, MCP tool execution

3. **How should the testing pyramid handle the TypeScript ↔ Python boundary?**
   - The MCP server (TypeScript) calls the Python API over HTTP — this is a cross-runtime boundary
   - Contract testing vs integration testing: which is more valuable here?
   - How to test that TypeScript type expectations match FastAPI's actual response schemas?

### Analysis 2: Testing System Intent vs Testing Code Correctness

Think about the difference between "does the code work" and "does the system do what it's supposed to":

1. **Define what "intent testing" means for a trading journal**:
   - Example: "The system must never lose a trade record" — how do you test this? Unit tests verify `save()` is called, but do they verify the trade survives a crash, a backup restore, or a database migration?
   - Example: "The system must correctly match round-trips" — unit tests verify the algorithm, but does the full pipeline (import → match → display) work end-to-end?
   - Example: "Locked mode must prevent all mutations" — mode-gating tests verify individual routes, but is there a systematic way to ensure no new route bypasses the guard?

2. **Propose an "intent test" design pattern**:
   - What should an intent test look like? (Higher-level than integration, more focused than E2E)
   - How do intent tests relate to acceptance criteria? (Are ACs sufficient to define intent, or is intent broader?)
   - How to structure intent tests so they're maintainable as the system evolves?

3. **Testing security as an invariant, not a feature**:
   - Instead of "test the encryption function", think "test that no unencrypted financial data exists at rest under any code path"
   - Instead of "test the auth endpoint", think "test that no mutation endpoint is reachable when locked"
   - How to make these invariant-based security tests that can run against any version of the code?

### Analysis 3: GUI Testing Strategy for Electron + React + Python Backend

Reason through the unique challenges of GUI testing in this architecture:

1. **The coordination problem**: The GUI (Electron), the API (Python process), and the database (SQLCipher file) are three separate concerns that must all be running during a GUI test.
   - Design the test lifecycle: How to start/stop/reset these components?
   - What state isolation guarantees do you need? (Fresh DB per test? Per test file? Per suite?)
   - How to handle test failures without leaving zombie processes?

2. **The assertion problem**: After a GUI action (e.g., user creates a trade), you need to verify:
   - The React UI shows the trade in the list (UI assertion)
   - The API processed it correctly (optional API assertion)
   - The trade exists in the encrypted database (DB assertion)
   - What is the right granularity? All three? Just UI + DB? Just UI?

3. **The maintenance problem**: GUI tests are notoriously brittle.
   - How to design selectors that survive component refactoring?
   - Page Object Model vs Component-based testing — which is better for this app?
   - How to handle dynamic financial data (prices, dates, PnL) in assertions?

4. **The speed problem**: Electron tests are slow.
   - What can be tested at the React component level (without Electron)?
   - What must be tested with full Electron (IPC, window management, tray)?
   - Parallelization strategies for Electron tests

### Analysis 4: MCP Testing as a First-Class Concern

The MCP server is a critical interface — AI agents interact with the application through it. Reason through:

1. **What can go wrong at the MCP boundary?**
   - Tool schema mismatch (MCP tool definition says X, actual behavior is Y)
   - Error code mapping (Python exception → HTTP error → MCP error code)
   - State assumptions (MCP client assumes stateless, but the server has mode-gating)
   - Concurrent tool calls from multiple IDE clients

2. **Design a comprehensive MCP test strategy**:
   - Level 1: Tool-level unit tests (current — vitest)
   - Level 2: Protocol conformance tests (does the server handle all MCP message types correctly?)
   - Level 3: Scenario tests (realistic multi-step AI agent workflows)
   - Level 4: Contract tests (MCP schemas match Python API schemas)
   - How should these levels map to the testing pyramid?

3. **Testing the "AI agent experience"**:
   - AI agents often retry, send malformed requests, or make assumptions about state
   - How to write tests that simulate adversarial or confused AI client behavior?
   - What errors should be graceful (return error message) vs hard (close connection)?

### Analysis 5: Agentic Testing Workflow Design

Given that this project uses AI agents (Opus for implementation, Codex for validation), reason through:

1. **How should test rigor audits be integrated into the agentic workflow?**
   - Currently: Opus writes tests (red phase) → implements → Codex validates
   - How should E2E tests fit? (Opus writes them? Codex validates they're not weak?)
   - Should there be a dedicated "security testing" agent role?

2. **What AGENTS.md instructions would enforce higher test rigor?**
   - Rules for when E2E tests are required (e.g., any MEU touching routes needs at least 1 E2E test)
   - Rules for security testing (e.g., any MEU touching auth needs mode-gating sweep)
   - Rules for GUI testing (e.g., any MEU adding a new page needs a Playwright test)

3. **What new workflows or skills are needed?**
   - `/e2e-testing` workflow — when to run, what to check
   - `/security-audit` workflow — OWASP-based checklist for each MEU
   - GUI test skill — instructions for writing Playwright Electron tests

### Output Format

For each analysis section:
1. **Your reasoning** — explain the trade-offs you considered and why you chose specific approaches
2. **Concrete design proposal** — specific test classes, file structures, assertion patterns
3. **Risk assessment** — what could go wrong with your proposed approach
4. **Adoption roadmap** — phased plan for implementing the strategy
5. **Interaction with existing tests** — how the new tests complement (not duplicate) the existing 1,357 tests
