# Deployment Workflow

## Overview

The Alchemiser uses a tag-based deployment workflow that separates development and production releases:

- **Dev Deployments**: Triggered by beta tags (e.g., `v2.23.1-beta.1`)
- **Prod Deployments**: Triggered by release tags (e.g., `v2.23.1`)
- **No automatic deploys on main pushes** - all deployments are tag-based

## Deployment Commands

### Development/Beta Deployment

Deploy to the **dev** environment:

```bash
# Create beta tag and trigger dev deployment
make deploy-dev
# or
make release-beta
```

This will:
1. Read current version from `pyproject.toml` (e.g., `2.23.1`)
2. Auto-increment beta number (e.g., `v2.23.1-beta.1`, `v2.23.1-beta.2`, etc.)
3. Create and push the beta tag
4. Trigger GitHub Actions CD workflow → deploys to **dev** environment

### Production Deployment

Deploy to the **prod** environment:

```bash
# Create release tag and trigger prod deployment
make deploy-prod
```

This will:
1. Read current version from `pyproject.toml` (e.g., `2.23.1`)
2. Create release tag (e.g., `v2.23.1`)
3. Ask for confirmation (⚠️ production deployment!)
4. Create and push the release tag
5. Trigger GitHub Actions CD workflow → deploys to **prod** environment

### Manual Deployment

You can still manually trigger deployments via GitHub Actions workflow_dispatch:
1. Go to Actions → CD workflow
2. Click "Run workflow"
3. Select environment (dev or prod)

## Version Management Workflow

### Standard Development Cycle

1. **Make changes and commit:**
   ```bash
   git add <files>
   git commit -m "Your changes"
   ```

2. **Bump version (following semantic versioning):**
   ```bash
   make bump-patch   # Bug fixes (2.23.1 → 2.23.2)
   make bump-minor   # New features (2.23.1 → 2.24.0)
   make bump-major   # Breaking changes (2.23.1 → 3.0.0)
   ```

3. **Deploy to dev for testing:**
   ```bash
   make deploy-dev
   ```
   Creates tag like `v2.23.2-beta.1` and deploys to dev

4. **Test in dev environment**

5. **Deploy to production when ready:**
   ```bash
   make deploy-prod
   ```
   Creates tag like `v2.23.2` and deploys to prod

### Multiple Dev Iterations

You can deploy multiple beta versions before going to prod:

```bash
# First dev deployment
make deploy-dev  # Creates v2.23.2-beta.1

# More changes...
git commit -m "Fix something"
make deploy-dev  # Creates v2.23.2-beta.2

# More changes...
git commit -m "Fix another thing"
make deploy-dev  # Creates v2.23.2-beta.3

# Finally ready for prod
make deploy-prod # Creates v2.23.2
```

## Tag Patterns

### Beta Tags (Dev Environment)
- Pattern: `v{major}.{minor}.{patch}-beta.{number}`
- Examples: `v2.23.1-beta.1`, `v2.23.1-beta.2`, `v3.0.0-beta.1`
- Triggers: Dev deployment
- Auto-increments beta number

### Release Tags (Prod Environment)
- Pattern: `v{major}.{minor}.{patch}`
- Examples: `v2.23.1`, `v2.24.0`, `v3.0.0`
- Triggers: Prod deployment
- Requires confirmation before push

## GitHub Actions Workflow

The CD workflow (`.github/workflows/cd.yml`) triggers on:

```yaml
on:
  push:
    tags:
      - 'v[0-9]+.[0-9]+.[0-9]+'              # Prod: v2.23.1
      - 'v[0-9]+.[0-9]+.[0-9]+-beta.[0-9]+'  # Dev: v2.23.1-beta.1
  workflow_dispatch:                          # Manual trigger
```

### Environment Detection

The workflow automatically determines the target environment:

- **Contains "beta"** → Deploy to **dev**
- **No "beta"** → Deploy to **prod**
- **workflow_dispatch** → User selects environment

## Best Practices

### 1. Semantic Versioning

Follow [Semantic Versioning](https://semver.org/):
- **PATCH** (`x.y.Z`): Bug fixes, minor refactoring, documentation
- **MINOR** (`x.Y.0`): New features, backward-compatible changes
- **MAJOR** (`X.0.0`): Breaking changes, major architectural changes

### 2. Development Workflow

Always test in dev before deploying to prod:
```bash
# 1. Make changes
git add . && git commit -m "Feature X"

# 2. Bump version
make bump-minor

# 3. Deploy to dev
make deploy-dev

# 4. Test in dev
# ... testing ...

# 5. Deploy to prod only when dev is stable
make deploy-prod
```

### 3. Version Bumping Strategy

As per Copilot instructions, **AI agents MUST update version numbers** for every code change:

```bash
# After making changes
git add <changed-files>

# Choose appropriate bump
make bump-patch  # For bug fixes, tests, docs
make bump-minor  # For new features
make bump-major  # For breaking changes
```

The bump command will:
1. Check for unstaged changes (warn if any)
2. Update `pyproject.toml`
3. Stage `pyproject.toml`
4. Commit with message: `"Bump version to X.Y.Z"`

### 4. Emergency Hotfixes

For urgent production fixes:

```bash
# 1. Fix the issue
git add . && git commit -m "Hotfix: Critical bug"

# 2. Bump patch version
make bump-patch

# 3. Optional: Test in dev first
make deploy-dev

# 4. Deploy to prod
make deploy-prod
```

### 5. Rollback Strategy

If a deployment fails or has issues:

```bash
# Find previous stable tag
git tag -l "v*" | tail -5

# Delete bad tag locally and remotely
git tag -d v2.23.2
git push origin :refs/tags/v2.23.2

# Re-deploy previous version
git checkout v2.23.1
make bump-patch  # Bumps to 2.23.2 again or next available
make deploy-prod
```

## CI/CD Pipeline

### CI (Continuous Integration)
- Runs on: PRs and pushes to any branch
- Checks: format, lint, type-check, tests
- Does NOT deploy

### CD (Continuous Deployment)
- Runs on: Tag pushes matching patterns
- Triggers: Automatic deployment to dev or prod based on tag
- Environments: Uses GitHub environment secrets/vars

## Monitoring Deployments

### GitHub Actions
1. Go to: https://github.com/Josh-moreton/alchemiser-quant/actions
2. Click on "CD" workflow
3. View running/completed deployments

### AWS Lambda
- Dev: Check AWS Lambda console for dev environment
- Prod: Check AWS Lambda console for prod environment

## Troubleshooting

### Tag Already Exists
```bash
❌ Tag v2.23.1 already exists!
```
**Solution**: Bump version again or delete the tag:
```bash
git tag -d v2.23.1
git push origin :refs/tags/v2.23.1
```

### Uncommitted Changes
```bash
❌ You have uncommitted changes!
```
**Solution**: Commit or stash changes:
```bash
git add . && git commit -m "Your changes"
# or
git stash
```

### Branch Protection Blocks Force Push
If you need to force-push to main:
1. Temporarily disable branch protection
2. Push changes
3. Re-enable branch protection

### Deployment Failed
Check GitHub Actions logs:
1. Go to Actions tab
2. Click failed workflow
3. Check logs for specific error
4. Common issues:
   - AWS credentials expired
   - SAM build failed
   - Environment variables missing

## Migration Notes

### Old Workflow (Deprecated)
- ❌ Automatic deploys on main pushes
- ❌ Manual `make deploy` script
- ❌ GitHub releases for prod

### New Workflow (Current)
- ✅ Tag-based deployments
- ✅ Separate dev/prod via beta tags
- ✅ Manual control over deploys
- ✅ Clear separation of environments
