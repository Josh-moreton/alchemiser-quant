# Typing Architecture Audit Report

## Summary

- **Total Violations:** 159
- **Files Affected:** 35

### Violations by Severity

- 🟢 **LOW:** 0
- 🟡 **MEDIUM:** 159
- 🟠 **HIGH:** 0
- 🔴 **CRITICAL:** 0

### Violations by Rule Type

- **Ann401 Violation:** 159
- **Layer Type Violation:** 0
- **Conversion Point Violation:** 0
- **Naming Convention Violation:** 0
- **Protocol Typing Violation:** 0

## 🟡 MEDIUM Priority Violations

### orchestration/event_driven_orchestrator.py:314

**Issue:** Function 'get_workflow_status' returns 'Any' type

**Suggested Fix:** Return specific DTO instead of Any

---

### orchestration/signal_orchestrator.py:190

**Issue:** Parameter 'strategy_signals' uses 'Any' type annotation

**Suggested Fix:** Use StrategySignalDTO for signal parameters

---

### orchestration/signal_orchestrator.py:232

**Issue:** Parameter 'strategy_signals' uses 'Any' type annotation

**Suggested Fix:** Use StrategySignalDTO for signal parameters

---

### orchestration/signal_orchestrator.py:355

**Issue:** Parameter 'strategy_signals' uses 'Any' type annotation

**Suggested Fix:** Use StrategySignalDTO for signal parameters

---

### orchestration/signal_orchestrator.py:420

**Issue:** Parameter 'strategy_signals' uses 'Any' type annotation

**Suggested Fix:** Use StrategySignalDTO for signal parameters

---

### orchestration/signal_orchestrator.py:444

**Issue:** Parameter 'strategy_signals' uses 'Any' type annotation

**Suggested Fix:** Use StrategySignalDTO for signal parameters

---

### orchestration/signal_orchestrator.py:455

**Issue:** Parameter 'signal' uses 'Any' type annotation

**Suggested Fix:** Use StrategySignalDTO for signal parameters

---

### orchestration/signal_orchestrator.py:488

**Issue:** Parameter 'strategy_signals' uses 'Any' type annotation

**Suggested Fix:** Use StrategySignalDTO for signal parameters

---

### orchestration/strategy_orchestrator.py:294

**Issue:** Function '_create_conflict_record' returns 'Any' type

**Suggested Fix:** Return specific DTO instead of Any

---

### orchestration/trading_orchestrator.py:291

**Issue:** Parameter 'result' uses 'Any' type annotation

**Suggested Fix:** Replace Any with specific type or Union for parameter

---

