# End-to-End Testing for Multi-Runtime Apps

- **Dual-process orchestration:** A common pattern is to start the Python backend in a test fixture or script, then launch the Electron app and run GUI actions (often via Playwright). For example, a pytest fixture can `spawn` a Uvicorn/FastAPI server in a background process, wait for it to be ready, yield to tests, then kill it on teardown【43†L389-L398】. In Node/Playwright tests, one can similarly spawn the Python process (e.g. via `child_process.spawn("uvicorn", …)`) before launching Electron via `const app = await _electron.launch({...})`【50†L29-L37】. Careful polling or retry logic is needed to wait for each service to be live before proceeding. In CI, this is often handled with setup scripts or GitHub Actions “pre-test” steps that install deps, build the Python API (or bundle it), and launch both services.

- **Test harness patterns:** Many projects rely on Playwright for the GUI (using its _electron.launch() API) and use Python’s pytest for backend validation. For instance, one team used Playwright in a Jest/Vitest test to launch their Electron app (`await _electron.launch({args:['main.js']})`), then exercised the UI and asserted on window state before closing the app【50†L29-L37】. On the Python side, pytest can start the FastAPI server with `multiprocessing.Process` (as shown above) so that HTTP endpoints are accessible via `requests` during the GUI-driven test. Helpers like the [`electron-playwright-helpers`](https://www.npmjs.com/package/electron-playwright-helpers) library can stub dialogs or IPC calls. In CI, it’s common to use headless mode (or xvfb on Linux) and ensure the server is ready (e.g. by retrying a health-check endpoint). In practice, the harness might look like: start database (or use an in-memory DB), start the FastAPI server, then use `playwright test` which in a `beforeAll` hook launches Electron and obtains the window. After tests, all processes are torn down.

- **Assertions across boundaries:** A typical strategy is “GUI action → backend verification → UI update check.” For example, after clicking a UI button that should save a record, a test might `await window.click(…)` in Playwright, then `await window.waitForResponse(/api\/save/)`, then use SQLAlchemy (or raw SQL) in the test code to directly query the encrypted SQLite and confirm the expected row was inserted. Finally, it might `await expect(window.locator("#status")).toHaveText("Saved")`. There’s no standardized hook mechanism, but tools like Playwright let you intercept network requests (`page.waitForResponse`) or stub IPC (`ipcMainInvokeHandler`). In some Electron tests, teams inject a hidden HTTP endpoint or use a WebSocket inside the app for test instrumentation. As one example, Electron-playwright-helpers allows capturing IPC invocations: 
  ```js
  const result = await electronApp.ipcMainInvokeHandler("tool-run", null);
  expect(result.success).toBe(true);
  ```
  These techniques let tests observe that the API was called correctly and that the UI eventually reflects the change. 

```python
@pytest.fixture
def server():
    proc = Process(target=run_server, daemon=True)
    proc.start()
    yield
    proc.kill()
```
*Example (pytest fixture) for starting a FastAPI server in-process for testing【43†L389-L398】.*

**Approach Ratings (Maturity/Effort/Value):** Playwright/Electron testing (4/3/5) is quite mature and high-value for GUI flows. Orchestrating multi-language processes (3/4/4) is harder to set up. Direct IPC/network assertions (3/3/4) depend on good tooling. **Adoption path:** first write reliable pytest fixtures to spin up/down the Python service; next set up Playwright tests to launch Electron; then flesh out tests that drive the UI and verify state by querying the API or DB. Gaps remain in unified frameworks for combined Electron+Python E2E: most teams glue together existing tools rather than using a turnkey solution.

# Intent-Based & Contract Testing

- **Intent-driven testing:** This new paradigm (often called “vibe coding” or “declarative testing”) focuses on *what* the user intends, not *how* to click. For example, Harness’s AI Test Automation lets QA write assertions like “the latest transaction is a deposit” in natural language and uses AI to map that to UI checks【52†L149-L157】【52†L211-L219】. CloudQA’s “Vibium” similarly lets testers write plain-English prompts like “Log into the app with test user” and uses an AI agent to perform the steps【55†L49-L57】【55†L82-L90】. While promising (reducing fragility), these tools are still emerging. In a financial context, intent tests might say “does transferring $100 result in a $100 debit and $100 credit entry?” rather than validating specific code paths. As of 2026, intent-based frameworks (Harness AI, Vibium AI) are low-maturity (3/5) and high-effort to integrate, so they may be useful for high-level user flows or visual validation, but not yet standard in finance apps.

- **Behavioral contracts:** Consumer-driven contract testing (e.g. Pact) can ensure the GUI ↔ API or API ↔ DB boundaries behave correctly. For example, the `pact-python` library has an example where a Python “consumer” client and a FastAPI “provider” server agree on request/response formats【62†L257-L265】. Even if both parts live in one repo, you can use Pact to codify the API schema as a contract: write a consumer test that expects certain endpoints and payloads, generate a pact file, then verify the FastAPI provider against it. Another approach is schema-based testing: tools like [Schemathesis](https://schemathesis.readthedocs.io) use your OpenAPI spec to fuzz endpoints. In FastAPI, you can run `schemathesis run http://localhost:8000/openapi.json` to perform hundreds of checks (e.g. status codes, content-type, schema conformance)【64†L93-L102】【64†L104-L113】. These approaches catch mismatches early. In practice, a team might use Pact (M4/E3/V4) to define key API contracts (e.g. journal entries API), and Schemathesis (M4/E2/V4) to fuzz all endpoints for edge cases (including security issues【64†L104-L113】). 

- **Property-based testing:** In financial logic (position sizing, P&L, etc.), define invariants and let Hypothesis generate data. For instance, one team wrote Hypothesis tests for their statement-of-account service: they asserted that `balance = credits - debits`【69†L82-L90】, that refunds count as credits, reversals don’t create value, etc.【69†L112-L121】. They even generated random transactions and found a bug in dispute handling. Importantly, they used `hypothesis-jsonschema` to generate full HTTP request bodies from the FastAPI schema and hit the live `/statement` endpoint【69†L139-L148】. This found issues missed by example tests. For our journal, similar properties could be: “total realized PnL equals sum of trades’ PnL” or “sum of tax lots equals total position value.” Those can be coded as Hypothesis tests. For example:
  ```python
  @given(transaction_strategy)
  def test_balance_is_credits_minus_debits(transactions):
      res = compute_statement(transactions)
      assert res["balance"] == res["credits"] - res["debits"]
  ```
  Hypothesis then finds corner cases (like refund+dispute edge cases in【69†L159-L168】). 

```python
@given(transaction_strategy)
def test_balance_correctness(transactions):
    result = compute_statement(transactions)
    assert result["balance"] == result["credits"] - result["debits"]
```
*Example Hypothesis property: “balance = credits – debits”【69†L82-L90】. Similar invariants caught subtle P&L bugs.*

**Approach Ratings:** Intent-based (AI/vibe) is early (2/5 maturity, 5/effort, 3/value). Pact-style contracts are mature (4/5, effort 3, value 4) when APIs are well-defined. Schemathesis (schema-based API fuzzing) is mature (4/5, effort 2, value 4). Property testing (Hypothesis) is highly valuable for finance (4/5, 3/effort, 5/value). 

**Adoption path:** Begin by writing critical invariants as Hypothesis tests (especially for calculations) and add contract tests (e.g. using pact or JSON-schema validation) for key API calls. Then layer on openAPI-based fuzzing (Schemathesis) in CI. Exploring AI intent-based tools can come later to complement explicit tests (e.g. using GPT-style assertions for complex workflows).

**Gaps:** True intent-based testing is nascent and relies on AI; there’s no standard tool yet for writing tests in plain-English (beyond commercial offerings). Contract testing on a monorepo is more a process decision (teams often skip pact if both sides are under one codebase). Finally, domain-specific invariants still need to be manually defined by experts.

# Security Testing as Code

- **SAST (Static Analysis):** Use modern scanners in CI. For example, **Semgrep** now supports Python and TypeScript out of the box (and can enforce custom rules)【70†L1-L8】. **CodeQL** (GitHub Advanced Security) can find cross-language issues in our monorepo. For Python, tools like **Bandit** (for common Python security issues) and **Pylint** with security plugins help. For TypeScript/JS, ESLint with security rules or specialized scanners (e.g. NodeJS’s built-in `npm audit`, Snyk) are recommended. Running pip-audit for Python and npm audit/Snyk for JS in the pipeline is also essential. These are high-maturity (5/5) and relatively low-effort (2/5), giving broad coverage of known issue patterns.

- **DAST for FastAPI:** Even a localhost API can be fuzzed and tested. Tools like **Schemathesis** can double as security testers: in addition to correctness, it will discover spec violations or unexpected errors (some security issues, e.g. injection or missing validation)【64†L104-L113】. You could also run an API fuzzer or SAST-like **OWASP ZAP** or **Burp Suite** against the running server to detect common vulnerabilities (CSRF is irrelevant locally, but check for SQLi or improper CORS if any front-end is involved). Ensuring Pydantic validation is strict helps. Schemathesis has specific security examples (e.g. Robocon 2024 talk)【76†L210-L218】. This is medium maturity (4/5) and low effort (2/5 once configured).

- **SQLCipher-specific tests:** It’s crucial to verify the database is truly encrypted and keys are handled correctly. For example, after creating/rotating a key, run an integrity check:
  ```python
  cursor.execute("PRAGMA integrity_check")
  assert cursor.fetchone()[0] == "ok"
  ```
  This confirms the DB isn’t corrupted or plaintext【74†L618-L626】. For key rotation, use `PRAGMA rekey = 'new_key'`, then reconnect with the old key (should fail) and the new key (should succeed)【74†L641-L650】【74†L658-L667】. In tests, one can simulate forgetting the key (catching the failure) and then ensure the rekey worked. Automating these flows (create DB with one key, rotate, attempt opens) ensures encryption is enforced. This is specialized (maturity 2/5 effort 3/5) but critical for security.

- **Localhost API security:** Even if the API is only on localhost, treat it like any backend. Tests should verify request validation (e.g. invalid payloads are rejected with 4xx), that CORS is not overly permissive (though if it’s not exposed, this may be moot), and that error responses don’t leak stack traces or sensitive info. Fuzzing endpoints (again Schemathesis or QuickCheck techniques) can find unhandled cases. For example, send random or malicious inputs to all endpoints and check for 5xx or debug info leaks. Tools like **Protégé** or **fuzz-api** could be integrated. This is moderate (3/5, effort 3/5, value 4/5).

- **Log redaction:** Implement tests that capture log output during sensitive operations and scan for forbidden patterns (API keys, account numbers, PII regexes). For instance, use pytest’s `caplog` fixture or a custom logging handler: after a test that hits a balance endpoint, `assert not re.search(r"\b\d{12}\b", caplog.text)`. This practice (simple regex scanning) should be automated. It’s a bit custom (3/5, 3/5, 4/5) but pays off by catching accidental leaks. 

```python
# Example: Verify encrypted DB integrity
cursor.execute("PRAGMA integrity_check")
assert cursor.fetchone()[0] == "ok"
```
*Running `PRAGMA integrity_check` to confirm the SQLCipher database is intact and encrypted【74†L618-L626】.*

**Approach Ratings:** Static scanners (Semgrep, CodeQL) are mature (5/5, effort 2). API fuzzing (Schemathesis) is mature (4/5, 2). SQLCipher testing is custom (2/5, 3). Local API auditing is standard (4/5, 3). Log-redaction checks are custom but straightforward (3/5, 3).

**Adoption path:** First, add SAST and dependency scans to CI. Next, integrate Schemathesis-based API tests. Then write targeted SQLCipher tests (integrity and rekey) and incorporate them into CI. Finally, add log assertions in existing tests or a specific audit step to catch any PII. 

**Gaps:** Few ready-made tools exist for SQLCipher validation or for checking in-memory data cleanup. Localhost APIs are often assumed safe—adding dedicated DAST for localhost is uncommon. Log redaction testing is usually home-grown, so establishing a library for common sensitive patterns could help.

# MCP Protocol Testing

- **Protocol conformance:** The [Model Context Protocol](https://modelcontextprotocol.io) is new, so dedicated frameworks are few. Some implementations (like the official TypeScript SDK) include unit tests to validate JSON-RPC 2.0 compliance and tool metadata parsing. In general, MCP servers should test that unknown methods return the correct error, that required fields are validated, and that tool discovery (e.g. a `tool.search` or `tools.list` RPC call) returns the expected tool list. Many open-source MCP servers use example scripts or manual testing rather than formal suites. To build tests, one can use the TypeScript SDK’s client libraries: write a test client that connects (e.g. via WebSocket/stdio) and performs a sequence like: list tools → invoke a known tool → check JSON-RPC result → attempt an invalid call and check the error code. Repositories like [modelcontextprotocol/typescript-sdk](https://github.com/modelcontextprotocol/typescript-sdk) and example servers can guide expected behavior.

- **Simulating AI clients:** You can create mock clients by sending JSON-RPC payloads. For example, using Python’s `subprocess` or `asyncio` to launch a CLI LLM client, or using the TS SDK’s `MCPClient` class. A test might look like:
  ```ts
  const client = new MCPClient(...);
  await client.send('tools.list', {});
  const tools = await client.on('tools.list.response');
  expect(tools).toContain('run-python');
  await client.send('tools.invoke', { name: 'run-python', args: ['2+2'] });
  const result = await client.on('tools.invoke.response');
  expect(result.stdout).toBe('4\n');
  ```
  You can also simulate concurrent clients by launching multiple threads or tasks to issue tool calls in parallel and ensure the server handles them. Testing session management (e.g. stateful streams) may require instrumenting the server with hooks to track tool calls. The test strategy is essentially black-box: drive the MCP interface as an AI would, and verify the server’s outputs and error handling.

- **Cross-language contracts (TS MCP ↔ Python API):** Since the MCP server (TypeScript) calls the Python FastAPI, we must ensure they agree on HTTP semantics. One approach is consumer-driven contract: treat the MCP server as a consumer of the Python API. Use Pact (or Schemathesis) on the Python side: define expected HTTP interactions (JSON bodies, headers) in a pact, then verify FastAPI meets them. On the TypeScript side, you can mock HTTP calls with tools like **nock** or **msw** in unit tests: e.g., `nock("http://localhost:8000").post("/compute").reply(200, { result: ... })`, then test that `apiClient.compute(...)` yields the right JSON. For larger flows, record real interactions (Polly.js or VCR-like tools) and replay them in tests. Also, sharing schemas helps: generate Pydantic models from OpenAPI that match Zod schemas in TypeScript, so serialization aligns. This is relatively low-maturity (3/5) as MCP itself is young; effort is high (4/5) because you need to set up stubs and validators, but value is high (4/5) to catch cross-language mismatches early.

**Approach Ratings:** MCP testing is early (3/5 maturity). Writing custom JSON-RPC client tests is moderate effort (4/5) but valuable (4/5) to catch protocol bugs. Simulating clients is effortful (4/5, since building realistic LLM-like sequences is hard), value high (4/5). Cross-language stubs (nock/msw) are mature (4/5), moderately easy (3/5), and important (4/5). 

**Adoption path:** Start by writing basic JSON-RPC flow tests: ensure tool registration and invocation work as expected. Then write Python HTTP provider tests (e.g. Pact or simple unit tests) for the endpoints that MCP will call. Finally, in CI include a step where the TS server is run against a stub Python API (or vice versa) to catch any schema drift.

**Gaps:** No widely-used MCP test frameworks exist yet. Mocking an “AI agent” often requires custom scripts. Automated contract testing tools seldom target MCP specifically, so teams must adapt existing JSON-RPC or HTTP mocking libraries.  

# GUI Automation & AI Testing

- **Electron GUI automation:** Playwright currently has experimental Electron support (via `_electron.launch()`)【50†L29-L37】. It’s fairly stable for basic flows, but codegen (record-and-replay) is not yet available for Electron【89†L220-L225】. Best practice is to write tests explicitly, often using the Page Object Model or React component testing. For complex UIs, isolating React components and testing them with Jest/React Testing Library can reduce end-to-end burden. GUI selectors should use accessible IDs or labels to reduce fragility. Playwright’s ecosystem also offers “auto-wait” which helps with asynchronous UI updates. Overall, GUI E2E with Electron and Playwright is mid-maturity (3/5); it works but requires dev effort (4/5) to maintain, yet delivers high value (4/5) by catching regressions.

- **Record/replay approaches:** Current tools like Playwright’s codegen do not support Electron apps【89†L220-L225】, so record/playback must be manual or via snapshots. Some teams use image-based recording (Selenium IDE? not very effective). For React UIs, using Storybook + Chromatic or Percy can serve as automated visual regression: each component/story is rendered and visually diffed. Chromatic (Storybook’s SaaS) can run CI checks on the component library. Maintainability is moderate (3/5), since these rely on visual comparisons (which can have false positives on minor style changes). There is no turnkey recorder for Electron as of 2026, so efforts still often resort to writing Playwright tests by hand.

- **AI-assisted GUI testing:** Emerging tools aim to make GUI testing smarter. **Applitools** and **Percy** provide AI-driven visual testing: they take screenshots and use smart diffing to spot UI changes, which is useful for Electron’s web views. For Electron specifically, some teams embed Applitools visual checkpoints in Playwright tests to catch layout bugs. **Vision-based testing** (e.g. using GPT-4V or Gemini on screenshots) is experimental, but some companies are exploring it to “assert” scene semantics (like “login button is visible”). Another trend is “self-healing selectors”: tests that adapt when element locators change. Some Cypress plugins or Playwright-later versions try this. These approaches are low-maturity (2/5, still research/alpha) and often vendor-locking, but can reduce maintenance. Tools like **Testim** or **mabl** claim AI auto-tests (not yet mainstream for Electron). 

**Approach Ratings:** Traditional automation (Playwright) is mature for web but limited for Electron (3/5). POM/component testing (Jest/Storybook) is high maturity (5/5) and moderate effort (3/5) – good for logic-level tests. Record/replay is immature for Electron (2/5, 4/5 effort). AI/visual testing (Applitools, Percy) is maturing (3/5) with moderate effort (4/5) and can add value (3/5) by catching unexpected UI diff. 

**Adoption path:** First, focus on writing robust Playwright tests with clear selectors and timeouts. Supplement with Jest/React Testing Library for non-networked component tests. Next, integrate a visual testing tool (like Percy or Applitools) into CI to catch UI regressions automatically. Explore AI tools cautiously — maybe start with “oracle” tests using GPT prompts on screenshots. Record-replay tools should be a lower priority due to lack of support. 

**Gaps:** Electron-specific test automation is less developed than for web. Record/playback tools lag. AI-based GUI testing is nascent and mostly in proprietary platforms. There’s a lack of community examples on using GPT-like models to validate desktop UIs. 

**Sources:** We drew on recent blogs and examples of testing Electron/Python apps【50†L29-L37】【43†L389-L398】, articles on intent-driven testing【52†L149-L157】【55†L49-L57】, Pact/contract testing examples【62†L257-L265】, Hypothesis finance cases【69†L82-L90】【69†L112-L121】, SQLCipher usage guides【74†L618-L626】【74†L658-L667】, and the Schemathesis docs【64†L93-L102】【76†L210-L217】. These illustrate patterns and best practices for each strategy.