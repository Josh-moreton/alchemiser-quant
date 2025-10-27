# Architecture Documentation

System design, architectural decisions, and core component documentation.

## 📁 Contents

### [Alpaca Integration](alpaca/)
Documentation related to Alpaca API integration, compliance, and trading.
- Architecture overview
- Compliance reports
- Quick reference guides

### [Event-Driven Architecture](event-driven/)
Event workflow, state management, and orchestration.
- Workflow state management
- Event-driven patterns

### [WebSocket Architecture](websocket/)
Real-time data streaming and connection management.
- WebSocket architecture
- Connection management
- Bug fixes and improvements

### [Architecture Decision Records (ADR)](../adr/)
Historical design decisions and their rationale.
- [ADR-001: Circular Imports](../adr/ADR-001-circular-imports.md)

## 🎯 Finding Architecture Documents

### By Component
- **Alpaca/Trading** → [alpaca/](alpaca/)
- **Events/Orchestration** → [event-driven/](event-driven/)
- **Data Streaming** → [websocket/](websocket/)
- **Design Decisions** → [../adr/](../adr/)

### Living Documents
All architecture documents are living documents (no dates in filenames) that are kept current through updates.

## 📝 Adding Architecture Documentation

New architecture documentation should:
1. Go in the appropriate subdirectory (alpaca/, event-driven/, websocket/)
2. Use descriptive UPPER_CASE names (e.g., `COMPONENT_ARCHITECTURE.md`)
3. Include frontmatter with status, module, and type
4. Link to related documents

For architectural decisions, use the ADR process in [../adr/](../adr/).

---

**Last Updated**: 2025-10-27
