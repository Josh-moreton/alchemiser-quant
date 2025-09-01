# Migration Rollback Procedures

## Emergency Rollback

If the migration causes critical issues, use these commands to immediately revert to the baseline state.

### Quick Rollback to Baseline

```bash
# 1. Reset to baseline commit (DESTRUCTIVE - loses all changes)
git reset --hard 13842739f83524852173460f7790ba90c178ea5e

# 2. Force push to update remote (if on migration branch)
git push --force-with-lease origin migration/modular-split

# 3. Verify rollback success
git log --oneline -1
# Should show: 1384273 (HEAD -> migration/modular-split) Initial plan
```

### Safe Rollback (Preserves Work)

```bash
# 1. Create a backup branch of current work
git checkout -b migration/backup-$(date +%Y%m%d-%H%M%S)
git push origin migration/backup-$(date +%Y%m%d-%H%M%S)

# 2. Return to migration branch and reset
git checkout migration/modular-split
git reset --hard 13842739f83524852173460f7790ba90c178ea5e

# 3. Verify rollback
make lint  # Should show 679 errors (baseline state)
poetry run alchemiser --help  # Should work normally
```

### Rollback Specific Phases

#### Phase 0 Rollback
```bash
# Remove migration artifacts only
rm -rf migration/
git checkout scripts/smoke_tests.sh  # If it existed before
git checkout .github/ISSUE_TEMPLATE/migration-pr.md  # If template was modified
git commit -m "Rollback Phase 0 preparation"
```

#### Phase 1 Rollback (Directory Structure)
```bash
# Remove new module directories
rm -rf the_alchemiser/strategy/
rm -rf the_alchemiser/portfolio/
rm -rf the_alchemiser/execution/
rm -rf the_alchemiser/shared/

# Restore original structure (if moved)
git checkout the_alchemiser/  # Restore all original files
git commit -m "Rollback Phase 1 directory structure"
```

#### Phase 2 Rollback (Content Migration)
```bash
# Reset import changes
git checkout pyproject.toml  # Restore original dependencies
git checkout the_alchemiser/  # Restore all source files

# Rebuild environment
poetry install --with dev
make format
make lint

git commit -m "Rollback Phase 2 content migration"
```

### Verification Commands

After any rollback, verify the system is in working order:

```bash
# 1. Check baseline commit
git log --oneline -1
# Expected: 1384273 (HEAD) Initial plan

# 2. Verify dependencies
poetry install --with dev
poetry check

# 3. Run baseline smoke tests
scripts/smoke_tests.sh
# Expected: All tests should pass with exit code 0

# 4. Check CLI functionality
poetry run alchemiser --help
poetry run alchemiser signal --help
poetry run alchemiser status --help

# 5. Verify linting baseline
make lint 2>&1 | grep "Found .* errors" | tail -1
# Expected: "Found 679 errors." (baseline state)

# 6. Test basic mypy compliance (should work on baseline)
poetry run mypy --version
```

### Recovery from Corrupted State

If the repository is in an inconsistent state:

```bash
# 1. Clean workspace completely
git clean -fdx
git reset --hard HEAD

# 2. Rebuild environment from scratch  
rm -rf .venv/
poetry install --with dev

# 3. If still broken, reclone from baseline
cd ..
git clone https://github.com/Josh-moreton/alchemiser-quant.git alchemiser-quant-recovery
cd alchemiser-quant-recovery
git checkout copilot/fix-443
git reset --hard 13842739f83524852173460f7790ba90c178ea5e
```

### Baseline State Characteristics

The baseline commit `13842739f83524852173460f7790ba90c178ea5e` should have:

- **Linting:** 679 ruff errors (acceptable baseline)
- **CLI:** All commands functional (signal, trade, status, etc.)
- **Dependencies:** Poetry environment installs successfully
- **Architecture:** Current DDD layered structure
- **MyPy:** Type checking works with configured ignores

### Emergency Contacts

If rollback procedures fail:

1. **Check Git History:** `git reflog` to find commit states
2. **Backup Recovery:** Look for `migration/backup-*` branches
3. **Fresh Clone:** Last resort - reclone repository from known good state

### Testing Rollback Procedures

These rollback commands should be tested periodically:

```bash
# Test in separate clone (safe)
cd /tmp
git clone https://github.com/Josh-moreton/alchemiser-quant.git rollback-test
cd rollback-test
git checkout copilot/fix-443

# Simulate changes
echo "test" > test-file.txt
git add test-file.txt
git commit -m "Test change"

# Test rollback
git reset --hard 13842739f83524852173460f7790ba90c178ea5e

# Verify
ls test-file.txt  # Should fail (file should be gone)
git log --oneline -1  # Should show baseline commit

# Cleanup
cd .. && rm -rf rollback-test
```

**⚠️ WARNING:** The destructive rollback commands will permanently lose uncommitted changes. Always backup important work before executing rollback procedures.