# Code Quality Standards

> Referenced from `AGENTS.md`. Contains detailed examples and forbidden patterns.

## Tiered Quality Model

### Maximum Tier (core, infrastructure, api, mcp-server)

- Read the ENTIRE file before modifying it
- NEVER use "// rest of implementation here" or "// ... existing code ..."
- Handle ALL error states explicitly — no silent failures
- Every function must have input validation
- Write the COMPLETE implementation, not a skeleton
- No `TODO` comments — implement it or create an issue
- No `any` type in TypeScript — use proper types
- No empty `catch {}` — handle or re-throw with context
- No `console.log` — use structured logging (`structlog`)
- Docstrings on every exported function/class

### Balanced Tier (ui/)

- No placeholders or skeleton code
- Basic error handling required (no empty catch)
- `TODO` allowed ONLY if referencing a tracked issue (e.g., `// TODO(#42): add animation`)
- `console.warn` allowed for development debugging
- Docstrings only on complex/non-obvious components

## Forbidden Patterns

### Python

```python
# ❌ NEVER
except Exception:
    pass

# ✅ ALWAYS
except SpecificError as e:
    logger.error("operation_failed", error=str(e), context=ctx)
    raise
```

### TypeScript

```typescript
// ❌ NEVER
catch (e) {}

// ✅ ALWAYS
catch (e: unknown) {
  logger.error('Operation failed', { error: e instanceof Error ? e.message : String(e) });
  throw;
}
```
