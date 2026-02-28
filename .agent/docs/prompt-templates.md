# Prompt Templates for Agentic Build Plan Execution

> Copy, fill in the blanks, and paste into your AI agent IDE.

---

## Start a New MEU

```
Read SOUL.md, AGENTS.md, and GEMINI.md.
Read .agent/context/meu-registry.md and locate MEU-{N} ({slug}).
Read the build plan section at docs/build-plan/{XX}-{section}.md §{X.X}.

Use /tdd-implementation workflow to implement MEU-{N}.
```

---

## Validate a Completed MEU (Codex)

```
Read AGENTS.md.
Read the handoff at .agent/context/handoffs/{date}-meu-{N}-{slug}.md.
Read ALL changed files listed in the handoff.

Use /validation-review workflow to validate MEU-{N}.
```

---

## Resume Interrupted Work

```
Search pomera_notes for "Zorivest" to find my last session state.
Read .agent/context/current-focus.md.
Read .agent/context/known-issues.md.

Resume work on {brief description of what was in progress}.
```

---

## Plan a Multi-MEU Phase

```
Read .agent/context/meu-registry.md for the full MEU list.
Read docs/build-plan/{XX}-{section}.md for Phase {N} scope.

Create an implementation plan for MEUs {N} through {M}.
Order by dependency. Flag any blockers.
```

---

## Research Before Building

```
Use /pre-build-research workflow.
Topic: {what you need to understand before coding}.
Focus on: {specific patterns, libraries, or constraints}.
Save findings to pomera_notes with title "Memory/Research/{topic}-{date}".
```

---

## Tips

- **Be specific about which MEU.** Don't say "implement the domain layer" — say "implement MEU-1 calculator".
- **Reference the workflow.** The `/tdd-implementation` and `/validation-review` slash commands trigger the full step-by-step process.
- **One MEU per session.** If you need multiple MEUs, start a new conversation for each.
- **Always read context first.** The agent performs better when it reads `current-focus.md` and `known-issues.md` before coding.
