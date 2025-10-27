# GitHub Issue: Enhance Success Email Template with Contextual Decision Path Explanations

## Issue Title
Enhance success email template to display contextual decision path explanations in strategy signal sections

## Labels
- `enhancement`
- `notifications`
- `user-experience`
- `strategy-v2`

## Priority
**Medium** - Improves user understanding of trading decisions but doesn't block functionality

## Problem Statement

Following PR #2622 which added runtime decision path capture to DSL strategies, the system now generates rich contextual explanations of **why** strategies made specific trading decisions. However, the success email template (multi-strategy execution report) is not fully utilizing these decision paths to provide users with maximum insight.

### Current State

The `build_signal_summary()` function in PR #2622 was enhanced to display basic decision reasoning:

```python
# Current implementation shows:
Nuclear: BUY TQQQ
  → Nuclear: ✓ 5 > 3 → ✓ TQQQ RSI(10) < 81 → 75.0% allocation
```

However, several email template sections could benefit from enhanced decision path context:

1. **Strategy Signals Neutral** (`build_strategy_signals_neutral()`) - Summary table with basic reason truncation
2. **Detailed Strategy Signals** (`build_detailed_strategy_signals()`) - Full signal cards with reasoning boxes
3. **Signal Summary** (`build_signal_summary()`) - Already enhanced in PR #2622 ✅

### What's Missing

Users receiving success emails currently see:
- ✅ **Signal Summary**: Shows condensed decision paths (added in PR #2622)
- ⚠️ **Strategy Signals Table**: Shows truncated generic reasoning without decision path formatting
- ⚠️ **Detailed Signal Cards**: Shows full reasoning but could benefit from better visual hierarchy
- ❌ **No decision tree visualization**: Complex multi-condition decisions are shown as flat text

### Desired State

Success emails should provide:
1. **Visual hierarchy** for decision paths (checkmarks, arrows, indentation)
2. **Expandable decision trees** for complex multi-branch logic
3. **Indicator value highlights** showing actual values that triggered decisions
4. **Consistent formatting** across all signal display sections

## Proposed Solution

### Phase 1: Enhance Existing Signal Sections (High Priority)

#### 1.1 Update `build_strategy_signals_neutral()`
**Location**: `the_alchemiser/shared/notifications/templates/signals.py:663-771`

**Current Implementation**:
```python
# Truncate reason for summary display
display_reason = SignalsBuilder._truncate_reason(reason, MAX_REASON_LENGTH_SUMMARY)

signal_rows.append(
    f"""
    <td style="...">
        {display_reason}
    </td>
    """
)
```

**Enhanced Implementation**:
```python
# Format decision path for table display
display_reason = SignalsBuilder._format_decision_path_for_table(
    reason, 
    max_length=MAX_REASON_LENGTH_SUMMARY,
    show_icons=True  # Include ✓ and → symbols
)

signal_rows.append(
    f"""
    <td style="font-family: monospace; color: #4B5563; font-size: 13px; line-height: 1.6;">
        {display_reason}
    </td>
    """
)
```

**Helper Function** (new):
```python
@staticmethod
def _format_decision_path_for_table(
    reasoning: str,
    max_length: int,
    show_icons: bool = True
) -> str:
    """Format decision path reasoning for table display.
    
    Preserves decision path symbols (✓, →) and applies smart truncation
    that keeps the most important decision nodes visible.
    
    Args:
        reasoning: Raw reasoning string from StrategySignal
        max_length: Maximum display length before truncation
        show_icons: Whether to preserve checkmark and arrow symbols
        
    Returns:
        HTML-safe formatted reasoning string with preserved structure
    """
    # Implementation details...
```

#### 1.2 Enhance `build_detailed_strategy_signals()`
**Location**: `the_alchemiser/shared/notifications/templates/signals.py:323-418`

**Current Implementation**:
```python
<div style="background-color: #F8FAFC; padding: 16px; border-radius: 8px;">
    <h5 style="...">Strategy Reasoning:</h5>
    <div style="color: #4B5563; font-size: 14px; line-height: 1.5;">
        {formatted_reason}
    </div>
</div>
```

**Enhanced Implementation**:
```python
<div style="background-color: #F8FAFC; padding: 16px; border-radius: 8px;">
    <h5 style="...">Decision Path:</h5>
    {SignalsBuilder._render_decision_tree(formatted_reason)}
</div>
```

**Helper Function** (new):
```python
@staticmethod
def _render_decision_tree(reasoning: str) -> str:
    """Render decision path as a hierarchical tree structure.
    
    Parses decision path reasoning and renders it with visual hierarchy:
    - Decision nodes with checkmarks (✓)
    - Arrows (→) for flow
    - Indentation for nested conditions
    - Color coding for true/false branches
    
    Args:
        reasoning: Decision path reasoning string
        
    Returns:
        HTML string with hierarchical decision tree visualization
    """
    # Parse decision nodes
    # Split on → symbols
    # Render as indented list with visual styling
```

### Phase 2: Add Advanced Features (Medium Priority)

#### 2.1 Indicator Value Highlighting

Extract indicator values from decision paths and highlight them:

```
SPY RSI(10) > 79
       ↓
SPY RSI(10): 82.5 > 79  [highlighted in color]
```

#### 2.2 Expandable Decision Trees (HTML details/summary)

For complex multi-branch decisions, use HTML `<details>` tags:

```html
<details style="...">
    <summary style="...">Decision Path Summary (3 nodes)</summary>
    <div style="...">
        ✓ SPY RSI(10) > 79 → True (82.5)
        ✓ TQQQ RSI(10) < 81 → True (75.2)
        ✓ Market regime check → Bullish
    </div>
</details>
```

#### 2.3 Decision Path Metrics Box

Add a summary box showing:
- Total decision nodes evaluated
- True branches taken
- False branches taken
- Key indicators referenced

### Phase 3: Testing & Validation (Required)

#### 3.1 Unit Tests
- Test `_format_decision_path_for_table()` with various decision path formats
- Test `_render_decision_tree()` with single and multi-node paths
- Test truncation behavior preserves important information

#### 3.2 Integration Tests
- Verify email HTML renders correctly in major email clients
- Test with long decision paths (>1000 chars)
- Test with no decision path (fallback to generic reasoning)

#### 3.3 Visual Testing
- Generate sample emails with real strategy data
- Verify mobile responsiveness
- Check dark mode compatibility (if applicable)

## Technical Considerations

### 1. Backward Compatibility
- Must handle signals without decision paths (fallback to existing behavior)
- Must support both old-style `reason` strings and new decision path format
- No breaking changes to `SignalsBuilder` public API

### 2. Performance
- Decision path parsing should be O(n) where n = reasoning length
- No regex processing in hot loops
- Pre-compute formatted strings where possible

### 3. HTML Email Constraints
- Limited CSS support in email clients
- Must use inline styles exclusively
- No JavaScript (static HTML only)
- Table-based layouts for maximum compatibility

### 4. Type Safety
- Maintain strict typing (`mypy --strict`)
- Use TypedDicts for structured decision node data
- Proper error handling for malformed decision paths

## Implementation Checklist

### Phase 1: Core Enhancement
- [ ] Create `_format_decision_path_for_table()` helper function
- [ ] Create `_render_decision_tree()` helper function
- [ ] Update `build_strategy_signals_neutral()` to use formatted paths
- [ ] Update `build_detailed_strategy_signals()` to use decision tree rendering
- [ ] Add docstrings and type hints to new functions
- [ ] Write unit tests for new helper functions
- [ ] Manual testing with sample decision paths

### Phase 2: Advanced Features (Optional)
- [ ] Implement indicator value highlighting
- [ ] Add expandable decision tree support (`<details>` tags)
- [ ] Create decision path metrics summary box
- [ ] Test email client compatibility

### Phase 3: Quality Assurance
- [ ] Run `make type-check` (mypy --strict)
- [ ] Run `make format` (ruff formatting)
- [ ] Integration tests with real strategy execution
- [ ] Visual regression testing for email templates
- [ ] Update version (MINOR bump: new features)

## Acceptance Criteria

### Must Have (Phase 1)
1. ✅ Decision paths formatted with checkmarks (✓) and arrows (→) in neutral signal table
2. ✅ Detailed signal cards render decision paths with visual hierarchy
3. ✅ Smart truncation preserves most important decision nodes
4. ✅ Backward compatible with non-decision-path signals
5. ✅ All tests pass (unit + integration)
6. ✅ Type checking passes (mypy --strict)
7. ✅ No HTML rendering issues in Gmail, Outlook, Apple Mail

### Nice to Have (Phase 2)
- ⭐ Indicator values highlighted in decision paths
- ⭐ Expandable decision trees for complex logic
- ⭐ Decision path metrics summary
- ⭐ Mobile-optimized responsive layout

### Quality Gates
- **Test Coverage**: ≥90% for new helper functions
- **Performance**: Email generation time < 100ms for typical signals
- **Accessibility**: Proper semantic HTML for screen readers
- **Compatibility**: Renders correctly in top 3 email clients

## Files to Modify

### Primary Changes
1. **`the_alchemiser/shared/notifications/templates/signals.py`**
   - Add `_format_decision_path_for_table()` helper
   - Add `_render_decision_tree()` helper
   - Update `build_strategy_signals_neutral()` (lines 663-771)
   - Update `build_detailed_strategy_signals()` (lines 323-418)

### Test Files
2. **`tests/shared/notifications/templates/test_signals.py`**
   - Add tests for `_format_decision_path_for_table()`
   - Add tests for `_render_decision_tree()`
   - Add integration tests with decision path data

### Documentation
3. **`docs/DECISION_PATH_EMAIL_ENHANCEMENT.md`** (new)
   - Document decision path formatting rules
   - Provide examples of enhanced email sections
   - Email client compatibility matrix

## Related Issues & PRs

- **PR #2622**: Add contextual decision path explanations to strategy signals (prerequisite)
- **Issue #2591**: Original feature request for decision path capture (closed by PR #2622)

## Estimated Effort

- **Phase 1 (Core)**: 4-6 hours
  - Helper functions: 2 hours
  - Template updates: 1 hour
  - Testing: 2-3 hours
  
- **Phase 2 (Advanced)**: 4-6 hours
  - Indicator highlighting: 2 hours
  - Expandable trees: 2 hours
  - Metrics box: 1-2 hours
  
- **Phase 3 (QA)**: 2-3 hours
  - Email client testing: 1-2 hours
  - Visual regression: 1 hour

**Total**: 10-15 hours for complete implementation

## Success Metrics

- [ ] Users can understand decision logic at a glance from email
- [ ] Decision path visualization reduces time to understand trades by 50%
- [ ] No increase in email rendering time (performance neutral)
- [ ] Zero reports of broken email layouts in production

## Additional Context

This enhancement builds on the foundation laid by PR #2622, which implemented the decision path capture mechanism. The goal is to make that captured data maximally useful for end users by presenting it in clear, visually hierarchical formats within success emails.

The enhancement aligns with the project's goal of transparency and explainability in algorithmic trading decisions, helping users build trust in the automated strategy execution.

## Example: Before vs After

### Before (Current)
```
Strategy Signals
┌──────────────────────────────────────────────────┐
│ NUCLEAR     │ BUY    │ TQQQ │ Nuclear allocation: 75.0%    │
│ QUANTUM     │ BUY    │ RGTI │ Quantum allocation: 25.0%    │
└──────────────────────────────────────────────────┘
```

### After (Enhanced)
```
Strategy Signals
┌────────────────────────────────────────────────────────────────────┐
│ NUCLEAR  │ BUY │ TQQQ │ ✓ SPY RSI(10)>79 → ✓ TQQQ RSI(10)<81 → ... │
│ QUANTUM  │ BUY │ RGTI │ ✓ Custom exposures → 25.0% allocation       │
└────────────────────────────────────────────────────────────────────┘

Detailed Signal Card:
╔═══════════════════════════════════════════════════╗
║ Nuclear Strategy                                   ║
║ Target: TQQQ | Allocation: 75.0%                  ║
║                                                    ║
║ Decision Path:                                     ║
║   ✓ SPY RSI(10) > 79 (actual: 82.5)              ║
║     → Market overbought condition detected        ║
║   ✓ TQQQ RSI(10) < 81 (actual: 75.2)             ║
║     → Tech leverage position available            ║
║   → Aggressive allocation: 75.0%                  ║
╚═══════════════════════════════════════════════════╝
```

---

**Prepared by**: Copilot AI Assistant  
**Date**: 2025-10-17  
**Based on**: PR #2622 implementation and project requirements
