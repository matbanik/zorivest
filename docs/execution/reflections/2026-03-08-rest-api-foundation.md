# Reflection — REST API Foundation (2026-03-08)

> Project: `rest-api-foundation` | MEUs: 23, 24, 25, 26
> Review passes: 11 (7 rechecks + 4 correction rounds)

## What Went Well

- **TDD discipline held**: All 64 initial tests written Red-first; zero test modifications in Green phase
- **4-MEU batch execution**: Successfully implemented app factory + 3 domain route sets in one session
- **Iterative correction velocity**: Once the review protocol was understood, fixes converged from multi-finding (3-4 per pass) to zero findings in 3 passes

## What Went Wrong

### Original Implementation (Passes 1–3)
- **Scope labeling drift**: MEU-26 labeled "full 04c envelope-encryption contract" despite being stub-only
- **Non-canonical tags**: Router tags invented instead of using the canonical 7 from `04-rest-api.md`
- **DI providers left as NotImplementedError**: Should have been app-state-backed from the start
- **Missing image upload route**: Spec included it (`04a` L104) but it was overlooked
- **Round-trip route called wrong service method**: `match_round_trips` instead of `list_round_trips`

### Stub/Runtime Defects (Passes 4–11)
- **Unlock state not propagated**: `auth.py` routes updated `AuthService` internal state but never set `app.state.db_unlocked`, so the mode gate blocked all routes after unlock
- **No-op `_StubRepo` gave false success**: `save()` discarded writes, `get()` returned `None`, lists returned empty. `POST` returned 201 but `GET` returned 404 — *worse* than a 500 because downstream consumers assume success
- **Write routes missing exception mapping**: `update_trade`, `upload_image`, `update_account`, `record_balance` let `NotFoundError` propagate as unhandled 500s
- **`create_trade` didn't catch `BusinessRuleError`**: Dedup violations became 500 instead of 409
- **`create_trade` didn't catch `ValueError`**: Invalid enum values became 500 instead of 422
- **InMemoryRepo ignored query semantics**: `list_filtered()` returned all items (no `account_id`, `limit`, `offset`), `get_for_owner()` ignored `owner_type`/`owner_id`, `list_for_account()` ignored `account_id`
- **`get_full_data()` returned the entity object** instead of `entity.data` bytes → `GET /images/{id}/full` 500'd
- **`exists_by_fingerprint_since()` checked for nonexistent attribute**: Searched for `entity.fingerprint` but `Trade` has no such attribute — needed to import and call `trade_fingerprint()` on the fly

## Lessons Learned

### For Next MEU Plans

1. **Green tests ≠ working app.** Mock-based unit tests will always pass even when the runtime is completely broken. Every MEU that touches routes must include at least one `create_app()` + `TestClient(raise_server_exceptions=False)` integration test that exercises the full stack without dependency overrides.

2. **Stub repos must honor the service contract, not just compile.** A `__getattr__` catch-all makes everything *compile* but silently violates every service-layer invariant (dedup, filtering, ownership). Stub repos should implement the *behavioral* interface: `exists()` returns correct booleans, `list_filtered()` actually filters, `save()` actually persists.

3. **Every route must map every domain exception.** Codex specifically checks that `NotFoundError → 404`, `BusinessRuleError → 409`, and `ValueError → 422` are caught in *every* write-adjacent route. A single unmapped exception is a HIGH finding.

4. **Live probes are the only reliable verification.** The quality gate (pytest + pyright + ruff + anti-placeholder) was green on every single pass, yet Codex found HIGH defects on passes 4–10. The live probe protocol is:
   - Unlock via keys + unlock
   - Create → Get → List consistency
   - Duplicate rejection (both exec_id and fingerprint)
   - Filter/pagination with multiple entities
   - Owner-scoped image listing
   - Missing-entity error mapping on all write paths
   - Lock → verify 403

5. **State propagation must be tested end-to-end.** The unlock route updated `AuthService.unlocked` but not `app.state.db_unlocked`. This is the kind of wiring defect that mocked tests can never catch.

6. **`__getattr__` catch-alls mask contract violations.** When a repo method falls through to `__getattr__` and returns `None`, the service silently accepts it (e.g., `exists()` returns `None` which is falsy — dedup bypass). Every method that participates in a service-layer contract must be explicitly implemented.

7. **Response shape matters, not just status codes.** Codex checks payload keys, not just 200/404/500. Canon says `create_trade` returns `{"status": "created", "exec_id": ...}` — returning the full trade object is a superset (acceptable) but should be intentional.

8. **Fingerprint dedup requires domain-aware repo methods.** The stub's `exists_by_fingerprint_since()` can't just look for a stored attribute — it must compute fingerprints using the canonical `trade_fingerprint()` function from `domain.trades.identity`.

### Process Lessons

9. **Understand the reviewer's protocol early.** Codex uses: file state > handoff claims, canon docs as contract, live probes as ground truth, pass-to-pass reopening only when re-reproduced. Knowing this saves multiple correction rounds.

10. **Premature "approved" claims trigger more passes.** Declaring "zero 500s" when write paths hadn't been probed cost 3 extra passes. Better to be conservative: "list/read paths clean; write paths not yet verified."

11. **Canon docs define expected behavior, not implementation preference.** The build-plan service layer docs (03-service-layer.md) define exactly what `create_trade` should do — dedup by exec_id AND fingerprint, with specific exception types. Implementing only exec_id dedup is a contract violation.

## Rules Checked

| Rule | Result |
|------|--------|
| TDD Red-first | ✅ |
| No test modifications in Green | ✅ |
| Anti-placeholder scan | ✅ |
| Handoff template complete | ✅ |
| Canonical spec alignment | ❌ → ✅ (tags, DI, image upload — fixed passes 1-3) |
| Honest scope labeling | ❌ → ✅ (MEU-26 — fixed pass 1) |
| Live runtime contract | ❌ → ✅ (stubs, error mapping — fixed passes 4-10) |
| Domain exception mapping | ❌ → ✅ (NotFound, BusinessRule, ValueError — fixed passes 8-9) |
| Dedup contract (exec_id + fingerprint) | ❌ → ✅ (fixed passes 9-10) |
| Query/filter semantics | ❌ → ✅ (fixed pass 9) |
| Full regression before handoff | ✅ |
| Cross-MEU regression | ✅ (531 passed) |

**Rule Adherence**: 6/12 = 50% initially → 12/12 = 100% after 11 passes

## Metrics

| Metric | Value |
|--------|-------|
| Initial tests | 64 |
| Final tests | 531 (full suite) |
| Review passes | 11 |
| Findings total | ~25 (across all passes) |
| Findings per pass (avg) | 2.3 |
| Passes to approved | 11 |
| Correction rounds | 4 (passes 4-5, 8, 9, 10) |
| Files modified in corrections | 6 (`stubs.py`, `main.py`, `auth.py`, `trades.py`, `accounts.py`, `images.py`) |
