# Alchemiser Documentation

Welcome to the Alchemiser project documentation. This guide will help you find what you need quickly.

## 📚 Documentation Structure

### 🏗️ [Architecture](architecture/)
System design, architectural decisions, and core component documentation.
- [Alpaca Integration](architecture/alpaca/) - Alpaca API integration and compliance
- [Event-Driven Architecture](architecture/event-driven/) - Event workflow and state management
- [WebSocket Architecture](architecture/websocket/) - Real-time data streaming
- [Architecture Decision Records (ADR)](adr/) - Historical design decisions

### 📖 [Guides](guides/)
How-to guides, references, and development documentation.
- [Deployment](guides/deployment/) - Deployment workflows and ephemeral environments
- [Development](guides/development/) - Development guides and best practices
- [Lambda](guides/lambda/) - AWS Lambda build and deployment
- [Quick References](guides/quick-references/) - Quick lookup guides

### 🐛 [Bug Fixes](bug-fixes/)
Historical bug documentation organized by date.
- [2025-01](bug-fixes/2025-01/) - January 2025 bug fixes
- [2025-10](bug-fixes/2025-10/) - October 2025 bug fixes
- [Archived](bug-fixes/archived/) - Pre-2025 bug fixes

### 🔍 [Investigations](investigations/)
Active and completed investigations into system behavior.
- [2025-01](investigations/2025-01/) - January 2025 investigations
- [Archived](investigations/archived/) - Completed investigations

### ✅ [Audits](audits/)
Code audits and reviews organized by date.
- [2025-01](audits/2025-01/) - January 2025 audits
- [2025-10](audits/2025-10/) - October 2025 audits
- [Archive](audits/archive/) - Historical audits

### 📝 [Code Reviews](code-reviews/)
Detailed file-by-file code reviews organized by date and module.
- [2025-10](code-reviews/2025-10/) - October 2025 reviews
  - [strategy_v2](code-reviews/2025-10/strategy_v2/)
  - [portfolio_v2](code-reviews/2025-10/portfolio_v2/)
  - [execution_v2](code-reviews/2025-10/execution_v2/)
  - [shared](code-reviews/2025-10/shared/)
  - [orchestration](code-reviews/2025-10/orchestration/)

### 📊 [Analysis](analysis/)
System analysis, reports, and technical findings.
- [Exceptions](analysis/exceptions/) - Exception handling analysis
- [Performance](analysis/performance/) - Performance analysis and P&L reports
- [Strategy](analysis/strategy/) - Strategy overlap and analysis
- [Technical Debt](analysis/technical-debt/) - Technical debt tracking

### ⚠️ [Deprecations](deprecations/)
Deprecation notices and migration guides.

### 🔧 [Issue Resolutions](issue-resolutions/)
Resolved issues and their solutions, organized by date.
- [2025-01](issue-resolutions/2025-01/)
- [2025-10](issue-resolutions/2025-10/)

### 💡 [Proposals](proposals/)
Proposed changes and improvements.
- [Active](proposals/active/) - Current proposals under consideration
- [Implemented](proposals/implemented/) - Completed proposals

### 🔄 [CI/CD](ci-cd/)
Continuous integration and deployment documentation.

### 📦 [Archive](archive/)
Obsolete or superseded documentation.

## 🔍 Finding Documentation

### By Type
- **Architecture overview?** → [architecture/](architecture/)
- **How-to guide?** → [guides/](guides/)
- **Bug fix history?** → [bug-fixes/](bug-fixes/)
- **Code review?** → [code-reviews/](code-reviews/)
- **System analysis?** → [analysis/](analysis/)
- **Order attribution?** → [ORDER_ATTRIBUTION_SUMMARY.md](ORDER_ATTRIBUTION_SUMMARY.md)

### By Module
- **strategy_v2** → [code-reviews/2025-10/strategy_v2/](code-reviews/2025-10/strategy_v2/)
- **portfolio_v2** → [code-reviews/2025-10/portfolio_v2/](code-reviews/2025-10/portfolio_v2/)
- **execution_v2** → [code-reviews/2025-10/execution_v2/](code-reviews/2025-10/execution_v2/)
- **shared** → [code-reviews/2025-10/shared/](code-reviews/2025-10/shared/)
- **orchestration** → [code-reviews/2025-10/orchestration/](code-reviews/2025-10/orchestration/)

### By Date
Most documentation is organized chronologically within categories:
- [2025-10](bug-fixes/2025-10/) - Most recent month
- [2025-01](bug-fixes/2025-01/) - January 2025

## 📝 Contributing Documentation

### Naming Conventions
- **Dated documents**: `YYYY-MM-DD_descriptive_name.md` (bug fixes, audits, reviews)
- **Living documents**: `DESCRIPTIVE_NAME.md` (guides, architecture, references)
- **ADRs**: `ADR-NNN-short-title.md`

### Document Frontmatter
Include this at the top of new documents:
```markdown
---
title: Descriptive Title
date: YYYY-MM-DD
status: active|archived|superseded
module: strategy_v2|portfolio_v2|execution_v2|shared|orchestration
type: guide|bug-fix|audit|review|analysis|proposal
related:
  - path/to/related/doc.md
---
```

### Where to Place Documents
- **New architecture doc** → `architecture/`
- **New how-to guide** → `guides/`
- **Bug fix documentation** → `bug-fixes/YYYY-MM/`
- **Code review** → `code-reviews/YYYY-MM/module/`
- **Investigation** → `investigations/YYYY-MM/`
- **System analysis** → `analysis/category/`

## 🗺️ Quick Links

### Most Referenced
- [Alpaca Architecture](architecture/alpaca/ALPACA_ARCHITECTURE.md)
- [Order Tracking Guide](guides/development/ORDER_TRACKING_GUIDE.md)
- [Deployment Workflow](guides/deployment/DEPLOYMENT_WORKFLOW.md)
- [Exception Quick Reference](guides/quick-references/EXCEPTIONS_QUICK_REFERENCE.md)

### Order Attribution Analysis (December 2025)
- [Executive Summary](ORDER_ATTRIBUTION_SUMMARY.md) - Quick overview with diagrams
- [Detailed Analysis](ORDER_ATTRIBUTION_ANALYSIS.md) - Technical deep-dive
- [Implementation Checklist](ORDER_ATTRIBUTION_CHECKLIST.md) - Actionable tasks

### Recent Updates
- [October 2025 Bug Fixes](bug-fixes/2025-10/)
- [October 2025 Code Reviews](code-reviews/2025-10/)
- [October 2025 Audits](audits/2025-10/)

---

**Last Updated**: 2025-12-13  
**Total Documents**: 395+  
**Maintained By**: Alchemiser Development Team
