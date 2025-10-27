# Code Reviews

Detailed file-by-file code reviews organized by date and module.

## 📁 Contents

### [2025-10](2025-10/)
October 2025 code reviews organized by module:
- [strategy_v2](2025-10/strategy_v2/)
- [portfolio_v2](2025-10/portfolio_v2/)
- [execution_v2](2025-10/execution_v2/)
- [shared](2025-10/shared/)
- [orchestration](2025-10/orchestration/)

## 🔍 Finding Code Reviews

### By Module
Navigate directly to the module folder:
- **strategy_v2** → [2025-10/strategy_v2/](2025-10/strategy_v2/)
- **portfolio_v2** → [2025-10/portfolio_v2/](2025-10/portfolio_v2/)
- **execution_v2** → [2025-10/execution_v2/](2025-10/execution_v2/)
- **shared** → [2025-10/shared/](2025-10/shared/)
- **orchestration** → [2025-10/orchestration/](2025-10/orchestration/)

### By Date
Navigate to the year-month folder (e.g., [2025-10/](2025-10/))

### By File
See [index-by-file.md](index-by-file.md) for an alphabetical listing of all reviewed files.

## 📝 Code Review Naming Convention

Code review documents should follow this pattern:
```
YYYY-MM-DD_filename.md
```

Example: `2025-10-09_signal_generation_handler.md`

## 🎯 Review Types

Code reviews include:
- **FILE_REVIEW**: Detailed file analysis
- **COMPLETION_SUMMARY**: Review completion summary
- **AUDIT**: Code audit findings
- **REVIEW_SUMMARY**: High-level review summary

## 📝 Adding New Code Reviews

When documenting a new code review:
1. Create file in `code-reviews/YYYY-MM/module/`
2. Use naming: `YYYY-MM-DD_filename.md`
3. Include:
   - File path and purpose
   - Code quality assessment
   - Issues found
   - Recommendations
   - Related files/reviews
4. Add frontmatter

### Frontmatter Template
```markdown
---
title: Filename Review
date: YYYY-MM-DD
status: active|archived
module: strategy_v2|portfolio_v2|execution_v2|shared|orchestration
type: review
file: path/to/reviewed/file.py
related:
  - path/to/related/review.md
---
```

## 📊 Statistics

As of 2025-10-27:
- **Total reviews**: 324+
- **Active month**: 2025-10
- **Modules covered**: 5 (strategy_v2, portfolio_v2, execution_v2, shared, orchestration)

---

**Last Updated**: 2025-10-27
