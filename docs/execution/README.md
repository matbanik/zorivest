# Execution Tracking

> Prompts, plans, and meta-reflections for each build session.

## Structure

```
execution/
├── README.md
├── prompts/
│   ├── 2026-03-06-scaffold-meu-1.md
│   ├── 2026-03-07-enums-logging.md
│   └── ...
├── plans/
│   ├── 2026-03-06-implementation-plan.md   ← copied from Antigravity brain folder
│   ├── 2026-03-06-task.md
│   └── ...
├── reflections/
│   ├── 2026-03-06-reflection.md
│   └── ...
└── metrics.md
```

## Session Lifecycle: Prompt → Plan → Execute → Reflect

1. **Human** creates the prompt in `prompts/{YYYY-MM-DD}-{slug}.md`
2. **Antigravity** (Opus 4.6) enters PLANNING mode → generates `implementation_plan.md` + `task.md` in its brain folder (`~/.gemini/antigravity/brain/{conversation-id}/`)
3. **Human** reviews the plan — tunes if needed, then approves
4. **Antigravity** archives plan to `plans/`, executes the approved plan
5. **Post-execution**: agent writes reflection to `reflections/`, updates `metrics.md`

## Naming Convention

All files use **`{YYYY-MM-DD}-{slug}`** format, consistent with `.agent/context/handoffs/`.

- **Prompts**: `{YYYY-MM-DD}-{slug}.md`
- **Plans**: `{YYYY-MM-DD}-implementation-plan.md` / `{YYYY-MM-DD}-task.md`
- **Reflections**: `{YYYY-MM-DD}-reflection.md`

## Workflow

Invoke `/execution-session` in any AI session.
