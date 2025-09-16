# Typing Architecture Audit Report

## Summary

- **Total Violations:** 170
- **Files Affected:** 36

### Violations by Severity

- 🟢 **LOW:** 0
- 🟡 **MEDIUM:** 159
- 🟠 **HIGH:** 11
- 🔴 **CRITICAL:** 0

### Violations by Rule Type

- **Ann401 Violation:** 168
- **Layer Type Violation:** 2
- **Conversion Point Violation:** 0
- **Naming Convention Violation:** 0
- **Protocol Typing Violation:** 0

## 🟠 HIGH Priority Violations

### execution_v2/core/smart_execution_strategy.py:221

**Issue:** Function '_calculate_simple_inside_spread_price' returns 'Any' type

**Suggested Fix:** Return specific DTO instead of Any

---

### execution_v2/core/smart_execution_strategy.py:266

**Issue:** Function 'calculate_liquidity_aware_price' returns 'Any' type

**Suggested Fix:** Return specific DTO instead of Any

---

### strategy_v2/engines/nuclear/engine.py:179

**Issue:** Function '_calculate_indicators' returns 'Any' type

**Suggested Fix:** Return specific DTO instead of Any

---

### strategy_v2/engines/nuclear/engine.py:179

**Issue:** Business logic function '_calculate_indicators' returns dict[str, Any] instead of DTO

**Suggested Fix:** Return specific DTO type instead of dict[str, Any]

---

### strategy_v2/engines/nuclear/engine.py:321

**Issue:** Parameter 'market_data' uses 'Any' type annotation

**Suggested Fix:** Use specific DTO or Union of known types instead of Any

---

### strategy_v2/engines/tecl/engine.py:121

**Issue:** Parameter 'market_data' uses 'Any' type annotation

**Suggested Fix:** Use specific DTO or Union of known types instead of Any

---

### strategy_v2/engines/tecl/engine.py:121

**Issue:** Function 'calculate_indicators' returns 'Any' type

**Suggested Fix:** Return specific DTO instead of Any

---

### strategy_v2/engines/tecl/engine.py:121

**Issue:** Business logic function 'calculate_indicators' returns dict[str, Any] instead of DTO

**Suggested Fix:** Return specific DTO type instead of dict[str, Any]

---

### strategy_v2/engines/tecl/engine.py:424

**Issue:** Parameter 'indicators' uses 'Any' type annotation

**Suggested Fix:** Replace Any with specific type or Union for parameter

---

### strategy_v2/engines/tecl/engine.py:462

**Issue:** Parameter 'indicators' uses 'Any' type annotation

**Suggested Fix:** Replace Any with specific type or Union for parameter

---

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

