# ADR Index

## Active ADRs

- [ADR-001: Circular Import Dependencies in AlpacaManager](./ADR-001-circular-imports.md) (2025-10-13)
  - **Status**: Accepted
  - **Topic**: Import architecture, circular dependencies
  - **Decision**: Accept circular imports in AlpacaManager as intentional design trade-off for singleton facade pattern
  - **Impact**: Development practice, code review guidelines

## How to Use This Directory

Architecture Decision Records (ADRs) document significant architectural choices made in the project. Each ADR:

1. **Documents a specific decision** with context, alternatives, and consequences
2. **Is immutable** - once accepted, ADRs are not modified (superseded by new ADRs if needed)
3. **Provides rationale** for future developers to understand why decisions were made

### ADR Template

When creating a new ADR, use this structure:

```markdown
# ADR-NNN: [Title]

## Status
[Proposed | Accepted | Deprecated | Superseded]

## Context
[What is the issue we're addressing?]

## Decision
[What is the change we're making?]

## Consequences
[What becomes easier or more difficult to do because of this change?]

## Alternatives Considered
[What other options were evaluated?]

## References
[Links to related docs, code, issues]
```

### Numbering

ADRs are numbered sequentially (ADR-001, ADR-002, etc.) in the order they are created.

### Lifecycle

- **Proposed**: Under discussion, not yet accepted
- **Accepted**: Approved and should be followed
- **Deprecated**: No longer recommended, but not actively harmful
- **Superseded**: Replaced by a newer ADR (reference the superseding ADR)

---

For more information on ADRs, see: https://adr.github.io/
