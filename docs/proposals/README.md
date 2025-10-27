# Proposals

Proposed changes and improvements.

## 📁 Contents

### [Active](active/)
Current proposals under consideration.

### [Implemented](implemented/)
Completed proposals organized by date.
- [2025-01](implemented/2025-01/)
- [2025-10](implemented/2025-10/)

## 📋 Active Proposals

See [active/](active/) for proposals currently under review.

## ✅ Implemented Proposals

### October 2025
See [implemented/2025-10/](implemented/2025-10/)

### January 2025
See [implemented/2025-01/](implemented/2025-01/)

## 📝 Proposal Naming Convention

Proposal documents should use descriptive lowercase-with-hyphens:
```
descriptive-proposal-name.md
```

Example: `limit-order-pricing.md`

## 📝 Creating New Proposals

When creating a new proposal:
1. Create file in `proposals/active/`
2. Use descriptive naming
3. Include:
   - Problem statement
   - Proposed solution
   - Alternatives considered
   - Implementation plan
   - Impact analysis
   - Testing strategy
4. Add frontmatter

### Frontmatter Template
```markdown
---
title: Proposal Title
date: YYYY-MM-DD
status: proposed|under-review|accepted|rejected|implemented
type: proposal
module: affected modules
impact: low|medium|high
related:
  - path/to/related/doc.md
---
```

## 📊 Proposal Lifecycle

1. **Proposed**: Create in `active/` folder
2. **Under Review**: Update status, gather feedback
3. **Accepted**: Begin implementation
4. **Implemented**: Move to `implemented/YYYY-MM/` with date
5. **Rejected**: Archive with rationale

## 🎯 Finding Proposals

### By Status
- **Active** → [active/](active/)
- **Implemented** → [implemented/](implemented/)

### By Date
Navigate to appropriate year-month in [implemented/](implemented/)

---

**Last Updated**: 2025-10-27
