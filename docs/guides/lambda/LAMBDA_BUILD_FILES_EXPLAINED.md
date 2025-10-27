# Lambda Build Files - What's Needed vs Not Needed

## Files Lambda DOES NOT Need at Runtime

### pyproject.toml
**Purpose:** Poetry project configuration file
**Used For:**
- Defining project metadata (name, version, description)
- Specifying dependencies and their versions
- Configuration for development tools (mypy, ruff, pytest)
- Build system configuration

**Why Lambda Doesn't Need It:**
- Dependencies are pre-installed in the Lambda Layer from `dependencies/requirements.txt`
- No package installation happens at runtime
- Lambda runtime doesn't use Poetry

### poetry.lock
**Purpose:** Lockfile with exact dependency versions
**Used For:**
- Ensuring reproducible builds
- Pinning exact versions of all dependencies (direct and transitive)
- Local development consistency

**Why Lambda Doesn't Need It:**
- Dependencies are already resolved and installed in the Layer
- Lambda runtime doesn't install packages
- The Layer is built once with locked dependencies

### setup.py / setup.cfg
**Purpose:** Alternative Python packaging configuration
**Used For:**
- Traditional setuptools-based package definition
- Similar to pyproject.toml but older standard

**Why Lambda Doesn't Need It:**
- Not used by this project (we use Poetry)
- Even if present, Lambda doesn't build/install packages at runtime

## Files Lambda DOES Need at Runtime

### Python Application Code
**Location:** `the_alchemiser/` directory
**Includes:**
- `*.py` files - All Python modules
- `*.clj` files - Strategy DSL files
- `config/*.json` - Configuration files

**Why Lambda Needs It:**
- This is the actual application code that runs
- Imported and executed by the Lambda handler

### Dependencies (Pre-installed in Layer)
**Location:** Lambda Layer (built from `dependencies/requirements.txt`)
**Includes:**
- alpaca-py, pandas, numpy, etc.
- All production dependencies

**Why Lambda Needs It:**
- Application imports these at runtime
- Pre-installed in `/opt/python/` (Lambda Layer mount point)

## Build Process Flow

### Development (Local)
```
1. Developer runs: poetry install
   ├─→ Reads: pyproject.toml
   ├─→ Reads: poetry.lock
   └─→ Installs dependencies to .venv/

2. Developer writes code in the_alchemiser/

3. Developer runs: poetry run python -m the_alchemiser
   └─→ Uses installed dependencies from .venv/
```

### Deployment (Lambda)
```
1. Deployment script runs: poetry export --only=main -o dependencies/requirements.txt
   ├─→ Reads: pyproject.toml (to get main dependencies)
   ├─→ Reads: poetry.lock (for exact versions)
   └─→ Writes: dependencies/requirements.txt

2. SAM builds Lambda Layer:
   ├─→ Reads: dependencies/requirements.txt
   ├─→ Runs: pip install -r requirements.txt -t layer/
   └─→ Creates: DependenciesLayer.zip

3. SAM builds Lambda Function:
   ├─→ Reads: template.yaml (CodeUri: the_alchemiser/)
   ├─→ Copies: the_alchemiser/** to function package
   └─→ Creates: TradingSystemFunction.zip

4. Lambda deployment:
   ├─→ Uploads: DependenciesLayer.zip → /opt/python/
   ├─→ Uploads: TradingSystemFunction.zip → /var/task/
   └─→ Lambda runtime imports from both locations
```

## Runtime (Lambda Execution)

```
Lambda Container Start
  │
  ├─→ Mount Layer: /opt/python/ (dependencies)
  │   └─→ Contains: alpaca-py, pandas, numpy, etc.
  │
  ├─→ Extract Function: /var/task/ (application code)
  │   └─→ Contains: lambda_handler.py, config/, strategy_v2/, etc.
  │
  ├─→ Set PYTHONPATH: /var/task:/opt/python
  │
  └─→ Execute: lambda_handler.lambda_handler()
      ├─→ Imports work because:
      │   - Application code in /var/task
      │   - Dependencies in /opt/python
      └─→ NO BUILD/INSTALL happens at runtime
```

## Key Insight

**Build-time files (pyproject.toml, poetry.lock) are NOT needed at runtime because:**
1. Dependencies are already installed in the Layer
2. Lambda doesn't install packages at runtime
3. Application code is already packaged

**This is why:**
- CodeUri points to `the_alchemiser/` (application code only)
- Dependencies are in a separate Layer
- Build files (pyproject.toml, poetry.lock) stay in repository root
- Lambda never sees or needs the build files

## Analogy

Think of it like a compiled application:
- **Build time:** Compiler needs source files, build configs, dependencies
- **Runtime:** Executable only needs runtime libraries, not build tools

For Lambda:
- **Build time:** SAM needs pyproject.toml, poetry, pip to build Layer
- **Runtime:** Lambda only needs pre-built Layer + application code

---

**In Summary:**
- ✅ Lambda needs: Application code (`the_alchemiser/`) + Dependencies (Layer)
- ❌ Lambda does NOT need: pyproject.toml, poetry.lock, build tools
- ✅ Build files stay in repository root (outside `the_alchemiser/`)
- ✅ This separation is correct and follows AWS Lambda best practices
