# Documentation Migration Plan

This document outlines the migration of existing documentation into the new structured framework.

## Current Documentation Status

### ✅ Completed - New Documentation Framework

**Core Structure Created:**
- `docs/README.md` - Main documentation index
- `docs/getting-started/quickstart.md` - Quick start guide
- `docs/getting-started/installation.md` - Installation guide
- `docs/architecture/overview.md` - System architecture
- `docs/trading/smart-orders.md` - Smart order execution
- `docs/strategies/nuclear.md` - Nuclear strategy guide
- `docs/user-guide/cli-commands.md` - CLI reference
- `docs/development/testing.md` - Testing framework

### 📋 Files to Migrate

**Implementation Documentation (High Priority):**
1. `INTELLIGENT_SELL_ORDERS_IMPLEMENTATION.md` → `docs/trading/intelligent-sell-orders.md`
2. `PROGRESSIVE_LIMIT_ORDER_STRATEGY.md` → `docs/trading/progressive-orders.md`
3. `REAL_TIME_PRICING_SUMMARY.md` → `docs/trading/real-time-pricing.md`
4. `PORTFOLIO_PNL_IMPLEMENTATION.md` → `docs/trading/portfolio-pnl.md`
5. `WEBSOCKET_ANALYSIS.md` → `docs/trading/websocket-implementation.md`
6. `WEBSOCKET_URL_VERIFICATION.md` → `docs/trading/websocket-configuration.md`

**Process Documentation (Medium Priority):**
7. `end to end process.md` → `docs/architecture/data-flow.md`
8. `tests/test-fails.md` → `docs/development/test-analysis.md`
9. `tests/tests to make.md` → `docs/development/test-plan.md`
10. `tests/test.md` → `docs/development/test-gaps.md`

**Execution Documentation (Low Priority - Reference):**
11. `the_alchemiser/execution/README.md` → Merge into architecture docs

**Refactoring Plans (Archive):**
12. `refactoring_plans/*.md` → `docs/development/archive/`

## Migration Tasks

### Phase 1: Core Trading Features (Priority 1)

Move and restructure trading-focused documentation:

```bash
# Smart Order Documentation
mv INTELLIGENT_SELL_ORDERS_IMPLEMENTATION.md docs/trading/intelligent-sell-orders.md
mv PROGRESSIVE_LIMIT_ORDER_STRATEGY.md docs/trading/progressive-orders.md

# Real-time Features  
mv REAL_TIME_PRICING_SUMMARY.md docs/trading/real-time-pricing.md
mv WEBSOCKET_ANALYSIS.md docs/trading/websocket-implementation.md
mv WEBSOCKET_URL_VERIFICATION.md docs/trading/websocket-configuration.md

# Portfolio Management
mv PORTFOLIO_PNL_IMPLEMENTATION.md docs/trading/portfolio-pnl.md
```

### Phase 2: Architecture and Process (Priority 2)

Reorganize system and process documentation:

```bash
# Architecture
mv "end to end process.md" docs/architecture/data-flow.md

# Development
mv tests/test-fails.md docs/development/test-analysis.md
mv "tests/tests to make.md" docs/development/test-plan.md
mv tests/test.md docs/development/test-gaps.md
```

### Phase 3: Archive and Cleanup (Priority 3)

Archive outdated and reference materials:

```bash
# Create archive directory
mkdir -p docs/development/archive

# Move refactoring plans
mv refactoring_plans/ docs/development/archive/

# Archive execution readme
mv the_alchemiser/execution/README.md docs/development/archive/execution-readme.md
```

## Content Updates Required

### 1. Smart Orders Documentation

**Consolidate overlapping content:**
- `INTELLIGENT_SELL_ORDERS_IMPLEMENTATION.md` - Sell order specifics
- `PROGRESSIVE_LIMIT_ORDER_STRATEGY.md` - General progressive strategy
- Existing `docs/trading/smart-orders.md` - Overview

**New structure:**
```
docs/trading/
├── smart-orders.md (overview - already created)
├── progressive-orders.md (detailed implementation)
├── intelligent-sell-orders.md (sell-specific logic)
└── order-execution-examples.md (practical examples)
```

### 2. WebSocket Documentation

**Combine WebSocket files:**
- `WEBSOCKET_ANALYSIS.md` - Implementation analysis
- `WEBSOCKET_URL_VERIFICATION.md` - Configuration verification
- `REAL_TIME_PRICING_SUMMARY.md` - Pricing integration

**New structure:**
```
docs/trading/
├── real-time-pricing.md (user guide)
├── websocket-implementation.md (technical details)
└── websocket-configuration.md (setup guide)
```

### 3. Testing Documentation

**Consolidate test files:**
- `tests/test-fails.md` - Test failure analysis
- `tests/tests to make.md` - Test planning
- `tests/test.md` - Test gaps analysis
- Existing `docs/development/testing.md` - Framework guide

**New structure:**
```
docs/development/
├── testing.md (framework guide - already created)
├── test-analysis.md (failure analysis)
├── test-plan.md (comprehensive test plan)
└── test-gaps.md (coverage gaps)
```

## File-by-File Migration Plan

### High Priority Migrations

#### 1. INTELLIGENT_SELL_ORDERS_IMPLEMENTATION.md

**Target**: `docs/trading/intelligent-sell-orders.md`

**Content Updates:**
- Add overview section explaining sell vs buy differences
- Update code examples with current class names
- Add links to related documentation
- Include performance metrics from real trading

#### 2. PROGRESSIVE_LIMIT_ORDER_STRATEGY.md

**Target**: `docs/trading/progressive-orders.md`

**Content Updates:**
- Expand with more detailed examples
- Add configuration options
- Include troubleshooting section
- Cross-reference with smart-orders.md

#### 3. REAL_TIME_PRICING_SUMMARY.md

**Target**: `docs/trading/real-time-pricing.md`

**Content Updates:**
- Convert to user-focused guide
- Add setup instructions
- Include monitoring and debugging
- Reference WebSocket implementation details

### Medium Priority Migrations

#### 4. end to end process.md

**Target**: `docs/architecture/data-flow.md`

**Content Updates:**
- Update class names (bot → engine terminology)
- Add sequence diagrams
- Include error handling flows
- Reference API documentation

#### 5. Test Documentation Files

**Targets**: Various `docs/development/` files

**Content Updates:**
- Consolidate duplicated information
- Update test examples with current codebase
- Add new test categories discovered
- Include CI/CD integration examples

## Documentation Standards

### Format Guidelines

All migrated documentation should follow:

**Headers:**
```markdown
# Page Title

Brief description of the content and its purpose.

## Section Headers

Use consistent heading hierarchy.
```

**Code Blocks:**
```markdown
# Always specify language
```python
def example_function():
    pass
```

**Cross-References:**
```markdown
See [Related Topic](./related-topic.md) for details.
```

**Admonitions:**
```markdown
> **Warning**: Important safety information

> **Note**: Additional context or tips
```

### Content Organization

**Each document should include:**
1. **Overview** - What this covers
2. **Prerequisites** - What you need to know first
3. **Main Content** - Detailed information
4. **Examples** - Practical usage
5. **Configuration** - Settings and options
6. **Troubleshooting** - Common issues
7. **Next Steps** - Related documentation

### Link Structure

**Internal Links:**
- Use relative paths: `./filename.md`
- Include section anchors: `./filename.md#section-name`

**External Links:**
- Always include description
- Verify links are still valid

## Timeline

### Week 1: High Priority (Trading Features)
- [ ] Migrate smart order documentation
- [ ] Consolidate WebSocket documentation  
- [ ] Update real-time pricing guide
- [ ] Test all internal links

### Week 2: Medium Priority (Architecture)
- [ ] Migrate process documentation
- [ ] Update architecture diagrams
- [ ] Consolidate test documentation
- [ ] Review cross-references

### Week 3: Cleanup and Polish
- [ ] Archive old documentation
- [ ] Update main README links
- [ ] Verify all documentation builds
- [ ] Create documentation index

### Week 4: Validation
- [ ] User testing of new structure
- [ ] Fix any broken links
- [ ] Update search/navigation
- [ ] Final review and approval

## Success Criteria

✅ **Complete Migration:**
- All existing documentation moved to new structure
- No broken internal links
- Consistent formatting and style

✅ **Improved Organization:**
- Logical grouping by user journey
- Clear navigation paths
- Reduced duplication

✅ **Enhanced Content:**
- Updated examples and code
- Current terminology throughout
- Comprehensive cross-references

✅ **User Validation:**
- New users can follow getting started
- Developers can find technical details
- Traders can understand strategies

## Maintenance Plan

**Regular Reviews:**
- Monthly documentation updates
- Quarterly structure review
- Annual major reorganization if needed

**Quality Checks:**
- Automated link checking in CI
- Documentation builds verification
- User feedback integration

**Content Updates:**
- Keep examples current with codebase
- Update performance metrics
- Add new features documentation

## Next Steps

1. **Start Phase 1 Migration**: Move high-priority trading documentation
2. **Update Navigation**: Ensure all new docs are linked properly  
3. **Content Review**: Update examples and remove outdated information
4. **User Testing**: Get feedback on new structure from team members

---

This migration will transform our scattered documentation into a comprehensive, well-organized resource that serves both new users and experienced developers effectively.
