# Critical Review: Detailed Planning in `docs/build-plan/`

## Scope
- Reviewed planning artifacts in `docs/build-plan/` with focus on newly integrated scheduling/pipeline planning and cross-index consistency.
- Primary files checked: `00-overview.md`, `build-priority-matrix.md`, `dependency-manifest.md`, `input-index.md`, `output-index.md`, `gui-actions-index.md`, `09-scheduling.md`.

## Findings (Severity-Ordered)

### Critical
- Scheduling GUI/API contracts are duplicated with incompatible endpoint families.
  Evidence: legacy schedule actions in `docs/build-plan/gui-actions-index.md:173`, `docs/build-plan/gui-actions-index.md:177`, `docs/build-plan/gui-actions-index.md:180` (`/api/v1/schedules`, `run_pipeline_now`) conflict with Phase 9 policy actions in `docs/build-plan/gui-actions-index.md:273`, `docs/build-plan/gui-actions-index.md:280`, `docs/build-plan/gui-actions-index.md:282` (`/api/v1/scheduling/policies`, `run_pipeline`).
  Impact: implementers can build the wrong API surface and wrong MCP bindings.
  Fix: deprecate Section 15 or remap it explicitly to Section 25 contracts.

- Phase 9 exit criteria include unrelated validators and wrong type-check gate.
  Evidence: `docs/build-plan/09-scheduling.md:2830` (`mypy --strict`) and `docs/build-plan/09-scheduling.md:2843` (`validate_site.py`, `validate_blog.py`).
  Impact: acceptance criteria are not aligned with this repository’s toolchain and can produce false "done".
  Fix: replace with repo-standard gates (`pyright`, `tsc`, `ruff`, `eslint`, `pytest`, `vitest`, `npm run build`).

### High
- Cross-reference metadata in overview is stale.
  Evidence: `docs/build-plan/00-overview.md:92` still says 92 items, but matrix header states 106 items at `docs/build-plan/build-priority-matrix.md:3`.
  Impact: planning docs lose trust and tracking accuracy.
  Fix: update overview cross-reference counts whenever matrix totals change.

- Input index keeps two overlapping scheduling models without migration note.
  Evidence: `docs/build-plan/input-index.md:446` (`Schedule Management` planned schema) vs `docs/build-plan/input-index.md:472` (`Pipeline Policy Authoring` defined schema).
  Impact: unclear whether schedule CRUD remains first-class or is replaced by policy-driven scheduling.
  Fix: add explicit supersession note and route/tool migration mapping.

- Dependency manifest drifts from project validation stack.
  Evidence: `docs/build-plan/dependency-manifest.md:82` lists `mypy`, while commands in this repo use `pyright`.
  Impact: inconsistent tooling guidance across planning docs.
  Fix: align dependency matrix with current validation commands.

### Medium
- Quality policy for TypeScript (`no any`) is not enforced in MCP plan snippets.
  Evidence: `docs/build-plan/09-scheduling.md:2575` uses `z.record(z.any())`.
  Impact: encourages weakly typed tool contracts in a security-sensitive surface.
  Fix: replace with explicit zod schema for `PolicyDocument`.

## Positive Notes
- P2.5 sequencing is present and detailed (`docs/build-plan/build-priority-matrix.md` section P2.5).
- Scheduling outputs/actions/inputs are broadly integrated across indexes (`input-index` 17a, `output-index` 16, `gui-actions-index` 25).
- Phase 9 design choices mostly track the research baseline (ref objects, `skip_if`, registry auto-registration, WeasyPrint, SQLCipher jobstore).

## Recommended Remediation Order
1. Resolve endpoint/tool contract collisions (GUI actions and MCP tool mappings).
2. Fix Phase 9 acceptance criteria to repository-standard validation gates.
3. Reconcile index and overview metadata (counts and supersession notes).
4. Tighten type schemas in MCP docs (`z.any()` removal).

## Verdict
- The documentation set is rich but currently inconsistent in critical integration seams.
- Execution should pause until critical/high issues above are reconciled and re-reviewed.

