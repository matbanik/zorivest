# Agent Skills — Progressive Disclosure

Skills are domain-specific instruction sets loaded on demand, not at session start.
This prevents context window bloat as the project scales.

## When to Create a Skill

Create a SKILL.md when:
- A workflow involves domain-specific patterns not in AGENTS.md (e.g., SQLCipher encryption, Electron IPC)
- Instructions exceed 20 lines and apply to only one layer (core, infra, api, ui, mcp)
- A task requires specialized tool usage (e.g., database migration, audio generation)

## Skill Format

```yaml
---
name: {skill-name}
description: {one-line description}
applies_to: [packages/core, packages/infrastructure, etc.]
---

{Markdown instructions, examples, and patterns}
```

## Loading Strategy

- Agents read AGENTS.md at session start (always)
- Skills are loaded only when the task touches the skill's `applies_to` packages
- The orchestrator role determines which skills to load during PLANNING mode

## Planned Skills (populate as codebase grows)

| Skill | Applies To | Content |
|-------|-----------| --------|
| `sqlcipher-patterns.md` | packages/infrastructure | Encryption key management, migration patterns |
| `electron-ipc.md` | ui/ | Main↔renderer IPC protocol, preload scripts |
| `fastapi-patterns.md` | packages/api | Dependency injection, middleware, error responses |
| `mcp-tool-patterns.md` | mcp-server/ | Tool registration, schema validation, response format |
