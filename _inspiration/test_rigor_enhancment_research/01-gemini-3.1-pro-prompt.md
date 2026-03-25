# Deep Research Prompt — Gemini 3.1 Pro

> **Model strength leveraged**: Gemini's large context window, multimodal reasoning, systematic enumeration, and strong capacity for surveying broad technical landscapes with structured output.

---

## Prompt

I'm building a desktop trading journal application with the following architecture:

**Stack**:
- **Domain/Core**: Python monorepo (`packages/core/`) — pure domain entities, value objects, ports (abstract interfaces), position calculator, analytics, pipeline engine. No external dependencies.
- **Infrastructure**: Python (`packages/infrastructure/`) — SQLAlchemy + SQLCipher encrypted database, Unit of Work pattern, repository implementations.
- **API**: Python FastAPI (`packages/api/`) — REST endpoints on localhost, dependency injection, mode-gating (locked/unlocked states).
- **MCP Server**: TypeScript (`mcp-server/`) — Model Context Protocol server exposing 40+ tools to AI coding assistants (Claude, Cursor, etc.) via JSON-RPC 2.0 over stdio. Toolset-based organization (core, discovery, trade-analytics, trade-planning, market-data).
- **GUI**: Electron + React (`ui/`) — desktop application with encrypted local database access, settings management, trade visualization.

**Current testing state**:
- 1,357 tests across 75 files (69 unit, 6 integration), all passing
- Python: pytest with frozen-dataclass checks, AC traceability, import-surface constraints, mock UoW pattern
- TypeScript: vitest with 15+ test files for MCP tools
- **No E2E tests**, no GUI tests, no cross-layer integration tests, no security-focused tests

**What I need you to research comprehensively**:

### Part 1: E2E Testing for Electron + React + Python Backend

Research the current state-of-the-art (2025-2026) for end-to-end testing of Electron desktop apps that communicate with a local Python backend:

1. **Framework comparison**: Compare Playwright (Electron mode), Spectron (if still maintained), WebDriverIO, Cypress (Electron support), and any newer frameworks. For each, evaluate:
   - Electron-specific support quality
   - Ability to test IPC communication (renderer ↔ main process)
   - Ability to verify data reaches the Python backend and returns correctly
   - Support for testing encrypted database state changes
   - CI/CD compatibility (headless mode, GitHub Actions)
   - Community adoption and maintenance status

2. **Full-path E2E patterns**: How to test the complete flow:
   ```
   User input in React UI → Electron IPC → Python FastAPI call → Service layer → SQLCipher DB → Response back → UI update displayed
   ```
   - What intermediate assertion points exist?
   - How do you verify the database actually changed (not just the API returned 200)?
   - How do you verify the UI actually displays the correct result (not just that a component rendered)?

3. **Test data management for encrypted databases**: Strategies for:
   - Setting up test fixtures with SQLCipher encrypted databases
   - Resetting database state between E2E tests without re-encryption overhead
   - Testing with realistic financial data (trades, balances, PnL) without exposing real data

4. **Visual regression testing**: Tools and approaches for catching UI regressions in Electron apps:
   - Screenshot comparison tools that work with Electron
   - Component-level visual testing vs full-page snapshots
   - Handling dynamic financial data in screenshots (masking, seeding)

### Part 2: MCP Server Testing — IDE Input/Output Validation

The MCP server accepts JSON-RPC 2.0 messages from AI coding assistants and returns structured tool results. Research:

1. **MCP protocol testing patterns**: How are other MCP server implementations tested?
   - Testing JSON-RPC message parsing and response generation
   - Testing tool execution with realistic IDE-like request sequences
   - Simulating different MCP clients (Claude Desktop, Cursor, VS Code Copilot, Windsurf, Antigravity)
   - Testing toolset registration and discovery

2. **E2E MCP testing**: How to test the full path:
   ```
   IDE sends tools/call → MCP server parses → Routes to handler → Calls Python API → Gets DB result → Formats response → Returns to IDE
   ```
   - Contract testing between MCP server (TypeScript) and Python API
   - Schema validation for tool input/output
   - Testing error propagation across the TypeScript/Python boundary

3. **Security testing for MCP**:
   - Preventing prompt injection via tool arguments
   - Input sanitization for tool parameters that touch the database
   - Rate limiting and circuit breaker testing
   - Path traversal prevention for file I/O tools

### Part 3: Cross-Layer Communication Testing

Research patterns for testing communication between architectural layers in Clean Architecture:

1. **Contract testing between layers**:
   - Consumer-driven contract testing for the domain → infrastructure boundary
   - API contract testing (OpenAPI schema validation)
   - Repository contract tests (ensuring implementations match port interfaces)

2. **Integration testing patterns for layered architectures**:
   - Testing the Unit of Work + Repository + Database stack without mocks
   - Testing dependency injection wiring (are the right implementations injected?)
   - Testing middleware chains (auth → validation → handler → error mapping)

3. **Event/message flow testing**:
   - Testing domain events propagate correctly through layers
   - Verifying side effects (e.g., creating a trade also creates a round-trip match)
   - Testing eventual consistency in multi-step operations

### Part 4: Security-Focused Testing

Research security testing approaches beyond typical functional tests:

1. **OWASP testing for local-first applications**:
   - SQL injection testing for SQLAlchemy + SQLCipher
   - API input validation testing (FastAPI + Pydantic boundaries)
   - Local file access security (preventing path traversal from API/MCP inputs)
   - Encryption key management testing

2. **Financial data security testing**:
   - Testing that PII/financial data never leaks to logs
   - Testing API key encryption/decryption lifecycle
   - Testing database encryption at rest (SQLCipher key derivation)
   - Testing that error responses don't expose sensitive data

3. **Intent-based security testing**:
   - Testing that the application's business rules prevent unauthorized state transitions
   - Testing mode-gating (locked DB should reject all write operations)
   - Testing that the backup system maintains encryption

### Part 5: Minimizing Human GUI Testing

Research strategies for reducing manual GUI testing effort:

1. **Automated accessibility testing**: Tools that catch UI issues without human eyes
2. **Interaction recording and replay**: Playwright codegen, Cypress Studio alternatives for Electron
3. **State-machine based testing**: Generating test cases from UI state machines
4. **AI-assisted visual testing**: Using vision models to verify UI correctness
5. **Snapshot testing for React components**: Jest snapshots vs Storybook visual tests

### Output Format

For each section, provide:
1. **Tools/frameworks with URLs** — name, GitHub/npm link, last release date, stars
2. **Concrete code examples** — real test code snippets showing the pattern
3. **Pros/cons table** — for each tool/approach
4. **Adoption evidence** — which companies/projects use this approach
5. **Recommendation** — what would you choose for this specific architecture and why

Focus on patterns that can be **incrementally adopted** — we already have 1,357 unit/integration tests and need to layer E2E and security tests on top without disrupting the existing suite.
