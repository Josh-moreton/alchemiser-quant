# Phase 7 Cleanup Tools - Usage Guide

This document provides comprehensive guidance for using the Phase 7 cleanup tools to systematically remove backward compatibility artifacts from the alchemiser-quant codebase.

## Overview

The Phase 7 cleanup toolkit consists of three main tools:

1. **Scanner** (`phase7_cleanup_scanner.py`) - Discovery and inventory
2. **Remover** (`phase7_cleanup_remover.py`) - Controlled removal with testing
3. **Orchestrator** (`phase7_cleanup_orchestrator.py`) - Complete workflow automation

## Quick Start

### 1. Full Automated Cleanup (Recommended)

For a complete cleanup workflow with safety checks:

```bash
# Dry run first to preview changes
python scripts/phase7_cleanup_orchestrator.py --dry-run --risk-levels low medium

# Execute cleanup of low-risk items
python scripts/phase7_cleanup_orchestrator.py --risk-levels low --max-artifacts 10

# Execute cleanup of medium-risk items (with confirmation)
python scripts/phase7_cleanup_orchestrator.py --risk-levels medium --max-artifacts 5
```

### 2. Scanner Only

To generate reports without making changes:

```bash
# Generate comprehensive scan report
python scripts/phase7_cleanup_scanner.py --root the_alchemiser --format markdown --output cleanup_report.md

# Filter by risk level
python scripts/phase7_cleanup_scanner.py --root the_alchemiser --filter-risk high --format json
```

### 3. Manual Removal

For fine-grained control over specific artifacts:

```bash
# Use pre-generated scan data
python scripts/phase7_cleanup_remover.py --scan-file artifacts.json --dry-run --max-artifacts 3

# Interactive removal with confirmation
python scripts/phase7_cleanup_remover.py --root the_alchemiser --risk-levels low
```

## Tool Details

### Scanner (`phase7_cleanup_scanner.py`)

**Purpose**: Discovers and categorizes backward compatibility artifacts

**Key Features**:
- Scans Python files, documentation, and configuration
- AST analysis for code patterns
- Risk level assessment (high/medium/low)
- Multiple output formats (JSON, Markdown, Text)

**Usage Examples**:
```bash
# Basic scan
python scripts/phase7_cleanup_scanner.py

# Detailed options
python scripts/phase7_cleanup_scanner.py \
  --root the_alchemiser \
  --format markdown \
  --output /tmp/scan_report.md \
  --filter-risk medium
```

**Output**: 
- Detailed reports with file locations and line numbers
- Risk categorization and removal notes
- Summary statistics by type and risk level

### Remover (`phase7_cleanup_remover.py`)

**Purpose**: Safely removes artifacts with testing and rollback

**Key Features**:
- Individual artifact processing with confirmation
- Automatic backup creation before changes
- Smoke test execution after each removal
- Automatic rollback on test failures
- Comprehensive session reporting

**Usage Examples**:
```bash
# Dry run mode (preview only)
python scripts/phase7_cleanup_remover.py --dry-run --max-artifacts 5

# Remove low-risk items
python scripts/phase7_cleanup_remover.py --risk-levels low --max-artifacts 10

# Use pre-scanned data
python scripts/phase7_cleanup_remover.py --scan-file artifacts.json
```

**Safety Features**:
- Backups stored in `/tmp/phase7_cleanup_backups/`
- Test failures trigger automatic rollback
- High-risk items require explicit confirmation
- Session logs track all changes

### Orchestrator (`phase7_cleanup_orchestrator.py`)

**Purpose**: Complete workflow automation with comprehensive reporting

**Key Features**:
- End-to-end cleanup workflow
- Risk-based filtering and processing
- Interactive confirmation for high-risk items
- Documentation update suggestions
- Final verification and reporting

**Usage Examples**:
```bash
# Complete cleanup workflow
python scripts/phase7_cleanup_orchestrator.py --risk-levels low medium

# Non-interactive mode
python scripts/phase7_cleanup_orchestrator.py \
  --risk-levels low \
  --max-artifacts 20 \
  --non-interactive

# Dry run preview
python scripts/phase7_cleanup_orchestrator.py --dry-run
```

**Workflow Phases**:
1. **Discovery**: Scans codebase for artifacts
2. **Assessment**: Categorizes and analyzes findings
3. **Removal**: Safely removes artifacts with testing
4. **Documentation**: Identifies docs needing updates
5. **Verification**: Final testing and remaining artifact scan

## Risk Level Guidelines

### Low Risk (Safe for Automated Removal)
- Comment-only removals
- Private function deprecation notes
- Internal TODO items
- Development-only annotations

**Example**: `# TODO: remove after migration`

### Medium Risk (Review Recommended)
- Public API compatibility functions
- Import redirections
- Legacy aliases in use
- Conditional compatibility logic

**Example**: `def _legacy_function(): # Backward compatibility`

### High Risk (Manual Review Required)
- Global configuration changes
- Public interface modifications
- Core system compatibility layers
- External API changes

**Example**: `# Global instance for backward compatibility`

## Best Practices

### 1. Start Small
```bash
# Begin with a small number of low-risk items
python scripts/phase7_cleanup_orchestrator.py --risk-levels low --max-artifacts 5
```

### 2. Always Test First
```bash
# Use dry-run mode to preview changes
python scripts/phase7_cleanup_orchestrator.py --dry-run --risk-levels medium
```

### 3. Monitor Progress
```bash
# Check remaining artifacts after cleanup
python scripts/phase7_cleanup_scanner.py --format markdown > remaining_artifacts.md
```

### 4. Backup Strategy
- Tool automatically creates backups in `/tmp/phase7_cleanup_backups/`
- Git state is preserved for larger rollbacks
- Session reports track all changes

### 5. Incremental Approach
1. Clean up all low-risk items first
2. Review and clean medium-risk items in batches
3. Manually address high-risk items with care
4. Run full verification after each major cleanup

## Reports and Outputs

### Generated Reports
- **Scan Report**: Complete inventory of artifacts
- **Session Report**: Detailed log of removal operations
- **Final Report**: Comprehensive cleanup summary
- **Remaining Artifacts**: Updated scan after cleanup

### Report Locations
All reports are generated in `/tmp/phase7_reports/` with session timestamps.

### Key Metrics Tracked
- Total artifacts found/remaining
- Successful/failed removals
- Test results and rollbacks
- Risk level distribution
- Artifact type breakdown

## Common Workflows

### Daily Cleanup Routine
```bash
# 1. Quick scan to check current state
python scripts/phase7_cleanup_scanner.py --filter-risk low | head -20

# 2. Clean up 10 low-risk items
python scripts/phase7_cleanup_orchestrator.py --risk-levels low --max-artifacts 10 --non-interactive

# 3. Verify stability
./scripts/smoke_tests.sh
```

### Comprehensive Cleanup Session
```bash
# 1. Generate full baseline report
python scripts/phase7_cleanup_scanner.py --format markdown --output baseline_scan.md

# 2. Clean all low-risk items
python scripts/phase7_cleanup_orchestrator.py --risk-levels low --non-interactive

# 3. Review and clean medium-risk items interactively
python scripts/phase7_cleanup_orchestrator.py --risk-levels medium --max-artifacts 20

# 4. Generate final report
python scripts/phase7_cleanup_scanner.py --format markdown --output final_scan.md
```

### Recovery from Issues
```bash
# Check recent backups
ls -la /tmp/phase7_cleanup_backups/

# Manually restore a file if needed
cp /tmp/phase7_cleanup_backups/session_file_line.backup path/to/original/file

# Or use git to revert broader changes
git checkout HEAD~1 -- the_alchemiser/path/to/file
```

## Troubleshooting

### Common Issues

1. **Test Failures After Removal**
   - Tool automatically rolls back the change
   - Check session report for details
   - May indicate the artifact is still in use

2. **Scanner Missing Items**
   - Adjust search patterns in scanner code
   - Check for non-standard comment formats
   - Verify file types are included in scan

3. **Path Issues**
   - Ensure running from repository root
   - Check that `scripts/smoke_tests.sh` exists and is executable
   - Verify Python import paths

### Debugging Tips

```bash
# Verbose output during removal
python scripts/phase7_cleanup_remover.py --risk-levels low --max-artifacts 1

# Check specific file changes
git diff the_alchemiser/path/to/file

# Review session logs
cat /tmp/phase7_reports/phase7_cleanup_*/session_report.md
```

## Integration with Development Workflow

### Pre-commit Checks
Add to your development routine:
```bash
# Quick check for new backward compatibility items
python scripts/phase7_cleanup_scanner.py --filter-risk high | wc -l
```

### CI/CD Integration
Consider adding to automated checks:
```bash
# Fail build if high-risk artifacts increase
ARTIFACT_COUNT=$(python scripts/phase7_cleanup_scanner.py --filter-risk high | wc -l)
if [ "$ARTIFACT_COUNT" -gt 10 ]; then
  echo "Too many high-risk backward compatibility artifacts: $ARTIFACT_COUNT"
  exit 1
fi
```

## Next Steps

After using these tools to clean up backward compatibility artifacts:

1. **Update Documentation**: Review and update any documentation references
2. **Code Review**: Have team members review significant changes
3. **Extended Testing**: Run full test suite including integration tests
4. **Monitor Metrics**: Track reduction in compatibility artifacts over time
5. **Share Knowledge**: Document any patterns found for future migrations

The Phase 7 cleanup tools provide a safe, systematic approach to achieving a clean, maintainable modular codebase without legacy cruft.