# Deprecations

Deprecation notices and migration guides.

## 📁 Contents

Documentation for deprecated features and their replacements.

## 📄 Deprecation Notices

- **DEPRECATION_TimeInForce.md** - TimeInForce enum deprecation

## 📝 Deprecation Process

When deprecating a feature:

1. **Announce**: Create deprecation notice in this directory
2. **Document**: Include:
   - What's being deprecated
   - Why it's being deprecated
   - Replacement/migration path
   - Timeline
   - Migration examples
3. **Communicate**: Update relevant guides and documentation
4. **Track**: Add to issue tracker with deprecation label

## 📋 Deprecation Template

```markdown
---
title: Component Deprecation
date: YYYY-MM-DD
status: announced|deprecated|removed
type: deprecation
module: affected modules
deprecated_version: X.Y.Z
removal_version: X.Y.Z
replacement: path or description
---

# Deprecation: [Component Name]

## What's Being Deprecated
[Description]

## Why
[Rationale]

## Replacement
[What to use instead]

## Migration Guide
[Step-by-step migration instructions]

## Timeline
- **Announced**: YYYY-MM-DD
- **Deprecated**: YYYY-MM-DD (version X.Y.Z)
- **Removed**: YYYY-MM-DD (planned version X.Y.Z)

## Examples
[Before and after code examples]
```

---

**Last Updated**: 2025-10-27
