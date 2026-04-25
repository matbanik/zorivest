# Optimizing AGENTS.md for GPT-5.5 and Claude Opus 4.7 (2026)

**Executive Summary:** Zorivest’s AGENTS.md should be updated to leverage GPT-5.5’s goal-oriented design and Claude Opus 4.7’s new capabilities. Key changes include using higher “effort” for planning and verification, simplifying verbose instructions to end-goal directives, updating the dual-agent model pairing (now including GPT-5.5), and implementing prompt caching for the static system prompt and AGENTS.md content. For Claude 4.7, we introduce the new `xhigh` effort level, adjust context-compression triggers for the 1.0–1.35× larger tokenizer, add image-based testing tasks to exploit its vision improvements, and integrate task budgets in execution phases. Cross-model, we recommend structuring model-specific context (e.g. separate “CLAUDE.md” and GPT instruction files) and encoding anti-patterns as guardrails. Other teams (Claude Code, Cursor, Copilot) use concise context files with scoped rules【49†L715-L723】【49†L829-L834】. The recommendations below are line-level edits to AGENTS.md (referencing its section headers), each with source and priority.

## Part 1: GPT-5.5 Optimization

- **Effort Level Mapping:**  Given GPT-5.5’s superior self-directed reasoning, map *PLANNING* to the highest effort (analogous to Claude’s `xhigh` or GPT-5.5 Pro), *EXECUTION* to high effort, and *VERIFICATION* to high or xhigh. In practice, prompt GPT-5.5 (or use GPT-5.5 Pro) to spend maximum reasoning on planning and final checks【55†L442-L447】【32†L53-L58】.  _Priority: High. Source: Official Anthropic & OpenAI docs, our analysis._  

- **Simplify Prescriptive Sections:** GPT-5.5 excels with goal-oriented prompts【32†L53-L58】. Rewrite over-detailed instructions (e.g. enumerated steps or explicit command lists) into outcome-based directives. For example, replace “Run `npm run lint` and check output manually” with “Ensure all linters pass, and report any violations.”  Static policy text (Priority Hierarchy, Quick Commands, Validation Pipeline) should focus on *goals* (e.g. “all tests green and code style consistent”) rather than detailed steps【40†L323-L331】【28†L685-L693】.  _Priority: High. Source: GPT-5.5 system card【32†L53-L58】, OpenAI agent guides【40†L323-L331】._

- **Dual-Agent Workflow Update:** Change the “Reviewer model” from GPT-5.4 to GPT-5.5 (or GPT-5.5 Pro) to leverage its improved code-analysis abilities【32†L53-L58】. E.g. in **Dual-Agent Workflow**:  
  > *Before:* “Reviewer model — GPT-5.4 (locked as baseline)”  
  > *After:* “Reviewer model — **GPT-5.5** (base; GPT-5.5 Pro for final sign-off)【32†L53-L58】【55†L442-L447】.”  
  Consider using GPT-5.5 as both implementer and reviewer (or keep one agent Claude, one agent GPT-5.5) to benefit from diverse strengths【55†L442-L447】.  _Priority: Critical. Source: OpenAI GPT-5.5 release notes【32†L53-L58】, Anthropic Opus 4.7 release【55†L442-L447】._

- **Prompt Caching:** Aggressively cache the static system prompt and AGENTS.md prefix. OpenAI advises placing all static instructions at prompt start to maximize cache hits【28†L685-L693】. Use the `prompt_cache_key` and extended 24h retention (default for GPT-5.5) so repeated calls reuse the prefix【28†L731-L739】【28†L769-L774】. Structure prompts as *[Static instructions][Dynamic query]*. For example: `System: “<AGENTS.md contents>” + User: “<task-specific details>”`. The diagram below shows how identical prefix text enables cache hits (green) but changes cause misses (orange)【28†L685-L693】:  

  【50†embed_image】 *Figure: Prompt caching hits when the initial prefix is identical【28†L685-L693】.*  

  _Priority: High. Source: OpenAI API docs【28†L685-L693】【28†L731-L739】._  

- **GPT-5.5 Features:** Reference GPT-5.5’s multi-modal and tool use improvements where relevant. For example, note its improved web-search and coding tools support【32†L53-L58】【29†L13-L19】. Emphasize GPT-5.5’s large 1,000,000-token context window and efficiency (per-token latency same as 5.4, half the cost in codex tasks)【32†L64-L67】【33†L49-L52】. In AGENTS.md sections like *Quality Gates* or *Execution Mode*, you can remove workarounds for context limits now that GPT-5.5 handles 1M tokens【33†L49-L52】. Where GPT-5.5 outperforms older models (e.g. reasoning through failures, carrying context, fewer retries), highlight these gains in the *Execution Mode* or *Roles* descriptions【32†L253-L258】.  _Priority: Medium. Source: GPT-5.5 launch【32†L64-L67】【33†L49-L52】._  

## Part 2: Claude Opus 4.7 Optimization

- **New `xhigh` Effort Level:** Use `xhigh` for tasks demanding maximum reasoning. For *PLANNING* and critical *VERIFICATION* steps, default to `xhigh` (Claude Code now defaults here)【55†L442-L447】. For routine coding steps, use `high`. Update any mentions of effort in AGENTS.md (e.g. replace “high” with “xhigh” where deeper analysis is needed). For instance, in **Priority Hierarchy** add: “Use **xhigh** effort for deep planning or complex refactors”【55†L442-L447】.  _Priority: High. Source: Anthropic release (default `xhigh` for coding)【55†L442-L447】._

- **Context Compression & Tokenizer:** Opus 4.7’s new tokenizer expands token count by ~1.0–1.35×【55†L462-L468】【57†L317-L324】. To prevent context overfill, lower the compression threshold by ~30% (e.g. compress context at ~70% of the old limit). In **Context Compression Rules** (or wherever we trigger summarization), adjust thresholds accordingly. Likewise, in **Verbosity Tiers**, allow for slightly more concise output, since the model generates more tokens at high effort【55†L462-L468】. The migration guide suggests increasing any `max_tokens` headroom and compaction triggers【57†L317-L324】. Add a note: “*Context tokens now expand more densely – compress context earlier*” or similar.  _Priority: Medium. Source: Opus 4.7 docs【55†L462-L468】【57†L317-L324】._  

- **Enhanced Vision Testing:** Exploit Opus 4.7’s higher-resolution vision. In **Testing Requirements**, add steps for image-based verification: e.g. “*Take screenshots of UI changes and ask the agent to compare differences*” or “*Provide design mockups as input and verify rendered output*.” Use charts or slides in tests and instruct the agent to analyze them (since Opus now self-checks .pptx slides and .docx redlining【57†L339-L347】). For example, under *Quality Gates* include: “Use visual diff tool to compare UI screenshots, or use Opus’s vision API to list layout differences.” This leverages “improved vision, high-res support” for UI and chart verification【57†L339-L347】【53†L28-L33】.  _Priority: Medium. Source: Claude 4.7 release (better image/chart analysis)【57†L339-L347】【53†L28-L33】._

- **Task Budgets (β):** Introduce `task_budget` to scope long tasks. In **Execution Mode** or *MEU Workflow*, add: “Set `task_budget` (e.g. 50k–100k) for well-defined tasks to limit token use. For open-ended tasks (P1), omit the budget to allow thorough completion【57†L236-L243】.” Explain that `task_budget` is advisory across the full agent loop (unlike a hard max_tokens)【57†L245-L250】. E.g.: “*Use task budgets when you want the agent to self-moderate output length【57†L236-L243】【57†L245-L250】*.” In the migration checklist, note enabling the `task-budgets` beta flag.  _Priority: Medium. Source: Claude 4.7 API docs【57†L236-L243】【57†L245-L250】._

- **Literal Instruction Refinement:** Claude 4.7 follows instructions **more literally**【57†L375-L383】. Ensure every required subtask is explicitly stated. For instance, if *Windows Shell* section says “run build and tests,” add “(e.g. `dotnet build`, `npm test`)” to avoid ambiguity. Remove any implicit instructions (“don’t do X” can leave out doing X). Revise vague directives in **Quality Gates** or **Roles** to be explicit (e.g. instead of “ensure docs are accurate,” say “verify function docstrings match code behavior”). Remove any scaffolding that tells the model to self-check (the model now auto-verifies slides/charts【57†L339-L347】). Similarly, the release notes advise removing “double-check slide layouts” prompts, since the model does this inherently【57†L342-L350】.  _Priority: High. Source: Claude 4.7 behavior changes【57†L375-L383】【57†L342-L350】._

## Part 3: Cross-Model Architecture

- **Model-Specific Instructions:** Maintain separate context sections per model. E.g., use `CLAUDE.md` (or AGENTS.md) for Claude-specific policies, and a distinct file or system prompt for GPT-5.5 instructions. Mixing formats can cause “context chaos”【49†L715-L723】. For multi-model teams, the 2026 consensus is to namespace or scope rules by tool: Claude uses CLAUDE.md/AGENTS.md, Cursor uses `.mdc` files, Copilot uses its `.md` instructions【49†L715-L723】【49†L829-L834】. In practice, you can tag AGENTS.md sections like `[Claude]` and `[GPT]`, or simply create two files. The goal is that each agent only loads relevant rules. For example, a **“GPT-5.5 Notes”** section (or separate file) could specify “As GPT-5.5 is goal-oriented, skip step-by-step scaffolding.”  _Priority: Medium. Source: Packmind context-ops guide【49†L715-L723】【49†L829-L834】._

- **Context Engineering Best Practices:** Adopt 2026 standards for agentic teams. Structure AGENTS.md as a high-level context file (like a CLAUDE.md): start with project overview and tech stack, then coding conventions, testing strategy, build/test commands, followed by anti-patterns【49†L829-L834】. Use `.mdc`-style scoping if supported (e.g. separate “rules” per directory). Reference coding examples rather than prose where possible【49†L797-L805】【49†L773-L780】. For instance, in **Code Quality** rules, use small code snippets to illustrate style. Regularly update and slim AGENTS.md: drop lines that the model can infer from code【44†L327-L336】. This follows the best practice of keeping instructions concise and test-driven【49†L797-L805】.  _Priority: High. Source: Packmind (2026) context engineering【49†L829-L834】【49†L797-L805】._  

- **Anti-Patterns:** Add a dedicated section (or end-of-file list) of known pitfalls. For example, Claude’s guidelines suggest listing “avoid these habits”【49†L829-L834】. New anti-patterns in 2026 include: *over-relying on a single model*, *ignoring token budgets*, *allowing context drift*, and *neglecting to review or version-control instruction changes*. Incorporate the recommended anti-pattern format from [49] (CLAUDE.md anti-patterns at the end) and update the **Anti-Slop Checklist** with cases like “the agent performing actions outside allowed tools” or “disregarding new guardrail rules.”  _Priority: Medium. Source: Best-practices manuals【49†L829-L834】._

- **Industry Examples:** Many production systems use lightweight, scoped instruction files. Claude Code’s CLAUDE.md focuses on team standards (not exhaustive docs)【44†L327-L336】【49†L829-L834】. Cursor breaks context into multiple `.mdc` rules by file type【49†L744-L753】. GitHub Copilot’s instructions emphasize code examples and top-priority rules【49†L797-L805】. You can mimic these: e.g. split AGENTS.md into topical sections or separate files (one for global rules, one per agent). Use `@filename` references or copy key snippets (as Claude Code’s CLAUDE.md uses) for concreteness【44†L270-L278】. Highlight in **Code Quality** or **Quick Commands** that examples outrank descriptions【49†L797-L805】.  _Priority: Low. Source: Claude Code docs【44†L270-L278】【44†L327-L335】; Packmind 2026 guide【49†L797-L805】【49†L829-L834】._

## Summary of Recommendations

| Change / Section                           | Priority  | Source(s)                                  |
|--------------------------------------------|-----------|--------------------------------------------|
| Update “Reviewer model” to GPT-5.5 (Dual-Agent)| Critical  | GPT-5.5 launch【32†L53-L58】; Claude 4.7 docs【55†L442-L447】 |
| Map *Planning*→high/xhigh effort, *Exec*→high, *Verify*→xhigh | High      | Claude 4.7 docs【55†L442-L447】; GPT-5.5 guide【32†L53-L58】 |
| Simplify prescriptive instructions (outcomes) | High      | OpenAI agent best practices【40†L323-L331】; GPT-5.5 intro【32†L53-L58】 |
| Add prompt-caching (prefix static instructions) | High      | OpenAI prompt caching guide【28†L685-L693】【28†L731-L739】 |
| Increase use of GPT-5.5 tool/autonomy features | Medium    | GPT-5.5 intro【32†L53-L58】【32†L253-L258】 |
| Enable Claude `xhigh` by default for coding | High      | Claude 4.7 announcement【55†L442-L447】 |
| Lower context-compression threshold (~30%)   | Medium    | Claude 4.7 migration guide【57†L317-L324】【55†L462-L468】 |
| Add image/chart tests (UI diff, slides)      | Medium    | Claude 4.7 vision improvements【57†L339-L347】【53†L28-L33】 |
| Integrate `task_budget` in execution workflow | Medium    | Claude API docs【57†L236-L243】 |
| Clarify instructions (explicit tasks)        | High      | Claude 4.7 behavior changes【57†L375-L383】【57†L342-L350】 |
| Separate model-specific contexts (CLAUDE.md vs GPT) | Medium   | ContextOps guide【49†L715-L723】【49†L829-L834】 |
| Structure context file (overview, rules, anti-patterns) | High | ContextOps guide【49†L829-L834】 |
| Add or update anti-patterns list             | Medium    | ContextOps guide【49†L829-L834】 |
| Include code examples in rules               | Low       | Copilot/Claude guides【49†L797-L805】【44†L270-L278】 |

## Top 5 Before→After Examples

1. **Dual-Agent Workflow** (Reviewer model):  
   - *Before:* `| **Reviewer model** | **GPT-5.4** (locked as baseline – do not downgrade)`  
   - *After:*  `| **Reviewer model** | **GPT-5.5** (base; GPT-5.5 Pro for final sign-off)【32†L53-L58】【55†L442-L447】`  

2. **Effort Mapping** (instructions under Planning/Execution):  
   - *Before:* `"Use **high** effort for all planning, coding, and reviews."`  
   - *After:*  `"Use **xhigh** effort for deep planning and thorough verification, **high** effort for regular coding tasks【55†L442-L447】."`  

3. **Quick Commands / Pipeline** (over-prescriptive):  
   - *Before:* “To run tests: `pytest tests/` (redirect to file), then `dotnet build`.”  
   - *After:*  “*Outcome:* Build must succeed and all unit tests pass. (Run `pytest` or your language’s test runner; **ensure no failures**.)”  

4. **Prompt Caching Note** (new strategy guidance):  
   - *Before:* – *(no existing instructions)*  
   - *After:*  “**Prompt Caching:** Place this instruction block at the start of each prompt and use a consistent prompt_cache_key to reuse the static context【28†L685-L693】.”  

5. **Task Budgets** (Execution mode):  
   - *Before:* – *(no existing instructions)*  
   - *After:*  “When launching an agentic task, optionally set `task_budget` (20k+ tokens) as an advisory cap. For open-ended tasks where thoroughness matters, leave it unset【57†L236-L243】.”  

## Migration Checklist

1. **Update models:** Change all GPT-5.4 references to GPT-5.5 (and GPT-5.5 Pro where noted) in the *Dual-Agent Workflow* section (Critical).  
2. **Effort mapping:** Revise PLANNING/EXECUTION/VERIFICATION instructions to use *xhigh/high* levels as per above (High).  
3. **Simplify instructions:** Audit sections (e.g. *Quick Commands*, *Validation Pipeline*, *Testing Decision*) to remove step-by-step lists. Rewrite these to state the end goals (High).  
4. **Add caching guidance:** Insert a note under *Context & Docs* or *System Prompt* about static prefix and using `prompt_cache_key` (High).  
5. **Add GPT-5.5 features:** Where applicable, remove references to outdated limits and mention GPT-5.5’s large context and tool use (Medium).  
6. **Configure Claude xhigh:** In Claude-related sections, update effort defaults to `xhigh` (High). Ensure `xhigh` is explained.  
7. **Adjust compression rules:** Reduce compaction threshold (~30% earlier) and note new token multiplier (Medium).  
8. **Vision tests:** Create new tests in *Testing Requirements* for image comparisons, chart analysis, or slide layout checks (Medium).  
9. **Enable task budgets:** In *Execution Mode*, add instructions to use `task_budget` for scoped tasks and explain when to set/omit it (Medium).  
10. **Refine language:** Explicitly enumerate any subtasks (especially conditional logic or edge cases) to match Claude’s literal mode (High). Remove phrases telling the agent to “double-check” things it now does automatically【57†L342-L350】.  
11. **Model-specific context:** If using multiple agents, create separate context files or sections (e.g. a GPT instructions file) and scope rules accordingly (Medium).  
12. **Context structure:** Reorganize AGENTS.md as in best-practice guides: start with project overview, technology, coding conventions, then workflow rules, commands, and an “Anti-Patterns” section at the end【49†L829-L834】.  
13. **Anti-patterns:** Add any new anti-patterns (e.g. “Never assume the agent inferred missing instructions” or “Don’t disable all permissions checks”) as guardrails (Medium).  

## Agentic Workflow Diagram

```mermaid
flowchart LR
    Planning[[PLANNING<br/>(Analyze requirements)]] --> Execution[[EXECUTION<br/>(Write code)]]
    Execution --> Verification[[VERIFICATION<br/>(Run tests)]]
    subgraph Agents
        GPT5["GPT-5.5 (Pro) Agent"]
        Claude["Claude Opus 4.7 Agent"]
    end
    Planning --> GPT5
    Execution --> Claude
    Verification --> GPT5
    style GPT5 fill:#cde9f9,stroke:#036,stroke-width:1px
    style Claude fill:#f9e0d9,stroke:#630,stroke-width:1px
    click GPT5 href "https://openai.com/index/introducing-gpt-5-5/" "GPT-5.5 Intro"
    click Claude href "https://www.anthropic.com/news/claude-opus-4-7" "Opus 4.7 Intro"
```

## Migration Timeline

```mermaid
gantt
    dateFormat  YYYY-MM-DD
    title Update AGENTS.md for GPT-5.5 & Claude 4.7
    section GPT-5.5 Changes
      Map Effort Levels          :done,    des1, 2026-05-01, 3d
      Simplify Instructions      :active,  des2, 2026-05-04, 4d
      Update Dual-Agent Roles    :done,    des3, 2026-05-08, 2d
      Add Prompt-Caching Notes   :todo,    des4, 2026-05-11, 2d
    section Claude 4.7 Changes
      Set xhigh in Workflow      :done,    des5, 2026-05-01, 1d
      Adjust Context Compression :active,  des6, 2026-05-02, 2d
      Add Vision Test Cases      :todo,    des7, 2026-05-04, 2d
      Integrate Task Budgets     :todo,    des8, 2026-05-06, 3d
      Refine Instructions        :todo,    des9, 2026-05-09, 3d
    section Cross-Model Updates
      Create GPT-specific Context:todo,    des10,2026-05-12, 2d
      Organize Context Structure :todo,    des11,2026-05-14, 3d
      Add Anti-Patterns Section  :todo,    des12,2026-05-17, 2d
```

**Sources:** Official release notes and docs from OpenAI and Anthropic (GPT-5.5 and Claude Opus 4.7)【32†L53-L58】【55†L442-L447】【57†L317-L324】【28†L685-L693】, Claude Code best-practices【42†L141-L150】【44†L239-L248】, Cursor blog【38†L100-L107】, and 2026 AI-context engineering guides【49†L715-L723】【49†L829-L834】. Each recommendation is prioritized (Critical/High/Medium/Low) as indicated.
