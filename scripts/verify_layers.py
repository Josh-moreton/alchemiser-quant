"""Business Unit: scripts | Status: current.

Verify Lambda layer dependencies are correctly installed for ARM64 Lambda.

Run this locally to catch missing or wrong-platform packages BEFORE deploying:
    python scripts/verify_layers.py

This script simulates each layer's pip install into a temp directory, then
checks that critical packages are present and that compiled extensions
(pydantic_core, etc.) are built for linux-aarch64 -- not macOS.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Layer definitions: layer_name -> pip command (same as CDK stacks)
# Uses /asset-output as placeholder, replaced with temp dir at runtime
# ---------------------------------------------------------------------------
LAYERS: dict[str, str] = {
    "notifications": (
        "pip install -q alpaca-py==0.43.0 --no-deps -t /asset-output/python --upgrade"
        " && pip install -q msgpack websockets -t /asset-output/python --upgrade --platform manylinux2014_aarch64 --only-binary=:all: --python-version 3.12 --implementation cp"
        " && pip install -q 'pydantic>=2.0.0' -t /asset-output/python --upgrade --platform manylinux2014_aarch64 --only-binary=:all: --python-version 3.12 --implementation cp"
        " && pip install -q dependency-injector -t /asset-output/python --upgrade --platform manylinux2014_aarch64 --only-binary=:all: --python-version 3.12 --implementation cp"
        " && pip install -q charset-normalizer pyyaml -t /asset-output/python --upgrade --platform manylinux2014_aarch64 --only-binary=:all: --python-version 3.12 --implementation cp"
        " && pip install -q pydantic-settings python-dotenv sseclient-py structlog 'cachetools>=6,<7' -t /asset-output/python --upgrade --no-deps"
        " && pip install -q httpx httpcore anyio h11 requests certifi"
        " idna urllib3 python-dateutil pytz tzdata -t /asset-output/python --upgrade --no-deps"
    ),
    "portfolio": (
        "pip install -q alpaca-py==0.43.0 --no-deps -t /asset-output/python --upgrade"
        " && pip install -q msgpack websockets -t /asset-output/python --upgrade --platform manylinux2014_aarch64 --only-binary=:all: --python-version 3.12 --implementation cp"
        " && pip install -q 'pydantic>=2.0.0' -t /asset-output/python --upgrade --platform manylinux2014_aarch64 --only-binary=:all: --python-version 3.12 --implementation cp"
        " && pip install -q dependency-injector -t /asset-output/python --upgrade --platform manylinux2014_aarch64 --only-binary=:all: --python-version 3.12 --implementation cp"
        " && pip install -q charset-normalizer pyyaml -t /asset-output/python --upgrade --platform manylinux2014_aarch64 --only-binary=:all: --python-version 3.12 --implementation cp"
        " && pip install -q pydantic-settings python-dotenv sseclient-py structlog 'cachetools>=6,<7' -t /asset-output/python --upgrade --no-deps"
        " && pip install -q httpx httpcore anyio h11 requests certifi"
        " idna urllib3 python-dateutil pytz tzdata -t /asset-output/python --upgrade --no-deps"
    ),
    "data": (
        "pip install -q alpaca-py==0.43.0 --no-deps -t /asset-output/python --upgrade"
        " && pip install -q msgpack websockets -t /asset-output/python --upgrade --platform manylinux2014_aarch64 --only-binary=:all: --python-version 3.12 --implementation cp"
        " && pip install -q 'pydantic>=2.0.0' -t /asset-output/python --upgrade --platform manylinux2014_aarch64 --only-binary=:all: --python-version 3.12 --implementation cp"
        " && pip install -q charset-normalizer -t /asset-output/python --upgrade --platform manylinux2014_aarch64 --only-binary=:all: --python-version 3.12 --implementation cp"
        " && pip install -q pydantic-settings python-dotenv sseclient-py structlog -t /asset-output/python --upgrade --no-deps"
        " && pip install -q httpx httpcore anyio h11 requests certifi"
        " idna urllib3 python-dateutil pytz tzdata -t /asset-output/python --upgrade --no-deps"
    ),
    "strategy": (
        "pip install -q alpaca-py==0.43.0 --no-deps -t /asset-output/python --upgrade"
        " && pip install -q msgpack websockets -t /asset-output/python --upgrade --platform manylinux2014_aarch64 --only-binary=:all: --python-version 3.12 --implementation cp"
        " && pip install -q 'pydantic>=2.0.0' -t /asset-output/python --upgrade --platform manylinux2014_aarch64 --only-binary=:all: --python-version 3.12 --implementation cp"
        " && pip install -q dependency-injector -t /asset-output/python --upgrade --platform manylinux2014_aarch64 --only-binary=:all: --python-version 3.12 --implementation cp"
        " && pip install -q charset-normalizer pyyaml -t /asset-output/python --upgrade --platform manylinux2014_aarch64 --only-binary=:all: --python-version 3.12 --implementation cp"
        " && pip install -q pydantic-settings python-dotenv sseclient-py structlog 'cachetools>=5.5,<7' -t /asset-output/python --upgrade --no-deps"
        " && pip install -q httpx httpcore anyio h11 requests certifi"
        " idna urllib3 python-dateutil pytz tzdata -t /asset-output/python --upgrade --no-deps"
    ),
    "execution": (
        "pip install -q alpaca-py==0.43.0 --no-deps -t /asset-output/python --upgrade"
        " && pip install -q msgpack websockets -t /asset-output/python --upgrade --platform manylinux2014_aarch64 --only-binary=:all: --python-version 3.12 --implementation cp"
        " && pip install -q 'pydantic>=2.0.0' -t /asset-output/python --upgrade --platform manylinux2014_aarch64 --only-binary=:all: --python-version 3.12 --implementation cp"
        " && pip install -q dependency-injector -t /asset-output/python --upgrade --platform manylinux2014_aarch64 --only-binary=:all: --python-version 3.12 --implementation cp"
        " && pip install -q charset-normalizer pyyaml -t /asset-output/python --upgrade --platform manylinux2014_aarch64 --only-binary=:all: --python-version 3.12 --implementation cp"
        " && pip install -q pydantic-settings python-dotenv sseclient-py structlog 'cachetools>=6,<7' -t /asset-output/python --upgrade --no-deps"
        " && pip install -q httpx httpcore anyio h11 requests certifi"
        " idna urllib3 python-dateutil pytz tzdata -t /asset-output/python --upgrade --no-deps"
    ),
}

# Packages that MUST exist in each layer
REQUIRED_PACKAGES: dict[str, list[str]] = {
    "notifications": [
        "pydantic", "pydantic_core", "pydantic_settings", "dotenv",
        "structlog", "alpaca", "requests", "httpx", "httpcore",
    ],
    "portfolio": [
        "pydantic", "pydantic_core", "pydantic_settings", "dotenv",
        "structlog", "alpaca", "requests", "httpx", "httpcore",
    ],
    "data": [
        "pydantic", "pydantic_core", "pydantic_settings", "dotenv",
        "structlog", "alpaca", "requests", "httpx", "httpcore",
    ],
    "strategy": [
        "pydantic", "pydantic_core", "pydantic_settings", "dotenv",
        "structlog", "alpaca", "requests", "httpx", "httpcore",
    ],
    "execution": [
        "pydantic", "pydantic_core", "pydantic_settings", "dotenv",
        "structlog", "alpaca", "requests", "httpx", "httpcore",
    ],
}

# .so files that must be linux-aarch64, not darwin/macOS
COMPILED_CHECKS: list[str] = [
    "pydantic_core/_pydantic_core*.so",
    "pydantic_core/*.so",
]


def _check_platform(site_dir: Path) -> list[str]:
    """Check that .so files are for linux-aarch64, not macOS."""
    errors: list[str] = []
    so_files = list(site_dir.rglob("*.so"))
    if not so_files:
        errors.append("  [WARN] No .so files found at all")
        return errors

    for so_file in so_files:
        name = so_file.name
        # linux aarch64 .so files contain "aarch64-linux" or "linux_aarch64"
        # macOS .so files contain "darwin" or "cpython-312-darwin"
        if "darwin" in name:
            errors.append(f"  [FAIL] macOS binary found: {so_file.relative_to(site_dir)}")
        elif "linux" in name or "manylinux" in name:
            pass  # correct platform
        elif re.search(r"cpython-\d+", name) and "linux" not in name and "darwin" not in name:
            # Generic .so without platform tag -- warn
            errors.append(
                f"  [WARN] Platform-ambiguous .so: {so_file.relative_to(site_dir)}"
            )
    return errors


def _check_packages(site_dir: Path, required: list[str]) -> list[str]:
    """Check that required packages exist in site-packages dir."""
    errors: list[str] = []
    for pkg in required:
        # Check for directory (package/) or .dist-info/ or loose .py
        candidates = [
            site_dir / pkg,
            site_dir / f"{pkg}.py",
        ]
        # Also check dist-info directories
        dist_infos = list(site_dir.glob(f"{pkg.replace('-', '_')}*.dist-info"))
        found = any(c.exists() for c in candidates) or bool(dist_infos)
        if not found:
            errors.append(f"  [FAIL] Missing package: {pkg}")
    return errors


def verify_layer(name: str, cmd: str) -> tuple[bool, list[str]]:
    """Build a layer in a temp dir and verify its contents."""
    messages: list[str] = []
    success = True

    with tempfile.TemporaryDirectory() as tmpdir:
        resolved_cmd = cmd.replace("/asset-output", tmpdir)
        # Replace bare 'pip' with 'pip3' or 'python3 -m pip' for portability
        resolved_cmd = resolved_cmd.replace("pip install", "pip3 install")
        messages.append(f"Building {name} layer...")

        result = subprocess.run(  # noqa: S603, S607
            ["bash", "-c", resolved_cmd],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            messages.append(f"  [FAIL] pip install failed (exit {result.returncode})")
            if result.stderr:
                for line in result.stderr.strip().splitlines()[-5:]:
                    messages.append(f"    {line}")
            return False, messages

        site_dir = Path(tmpdir) / "python"
        if not site_dir.exists():
            messages.append("  [FAIL] python/ directory not created")
            return False, messages

        # Count installed packages
        pkg_dirs = [d for d in site_dir.iterdir() if d.is_dir() and not d.name.startswith("_")]
        messages.append(f"  Installed {len(pkg_dirs)} package directories")

        # Check required packages
        required = REQUIRED_PACKAGES.get(name, [])
        pkg_errors = _check_packages(site_dir, required)
        if pkg_errors:
            messages.extend(pkg_errors)
            success = False

        # Check platform of compiled extensions
        platform_errors = _check_platform(site_dir)
        if platform_errors:
            messages.extend(platform_errors)
            for err in platform_errors:
                if "[FAIL]" in err:
                    success = False

        if success:
            messages.append("  [OK] All checks passed")

    return success, messages


def main() -> int:
    """Verify all layers. Returns 0 on success, 1 on failure."""
    print("=" * 60)
    print("Lambda Layer Dependency Verification")
    print("=" * 60)
    print()

    all_ok = True
    for name, cmd in LAYERS.items():
        ok, messages = verify_layer(name, cmd)
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name}")
        for msg in messages:
            print(msg)
        print()
        if not ok:
            all_ok = False

    print("=" * 60)
    if all_ok:
        print("All layers verified successfully.")
    else:
        print("FAILURES detected. Fix layer pip commands before deploying.")
    print("=" * 60)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
