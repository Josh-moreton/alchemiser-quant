# Bug Fixes Documentation

Historical bug documentation organized chronologically.

## 📁 Contents

### [2025-10](2025-10/)
October 2025 bug fixes.

### [2025-01](2025-01/)
January 2025 bug fixes.

### [Archived](archived/)
Pre-2025 bug fixes.

## 🐛 Bug Fixes by Month

### October 2025
See [2025-10/](2025-10/) for:
- Average fill price race condition
- Correlation ID propagation
- Crossed market pricing
- EDZ fractional liquidation
- S3 parameter capitalization
- Trade result factory field mismatch
- Trade result validation

### January 2025
See [2025-01/](2025-01/) for:
- Email notification data

## 📝 Bug Fix Naming Convention

Bug fix documents should follow this naming pattern:
```
YYYY-MM-DD_component_brief_description.md
```

Example: `2025-10-15_trade_result_validation.md`

## 🎯 Finding Bug Fixes

### By Date
Navigate to the appropriate year-month folder (e.g., [2025-10/](2025-10/))

### By Component
Use your editor's search or see the module-specific code review sections in [../code-reviews/](../code-reviews/)

## 📝 Adding Bug Fix Documentation

When documenting a new bug fix:
1. Create file in current month folder (e.g., `bug-fixes/2025-10/`)
2. Use naming convention: `YYYY-MM-DD_component_description.md`
3. Include:
   - Problem description
   - Root cause analysis
   - Solution implemented
   - Testing performed
   - Related PRs/issues
4. Add frontmatter with date, module, and type

### Frontmatter Template
```markdown
---
title: Brief Description
date: YYYY-MM-DD
status: fixed
module: strategy_v2|portfolio_v2|execution_v2|shared|orchestration
type: bug-fix
related:
  - path/to/related/doc.md
---
```

---

**Last Updated**: 2025-10-27  
**Total Bug Fixes Documented**: 8+
