"""
Services folder reorganization utility.

This script moves files in the_alchemiser/services into a cleaner
DDD-aligned structure and creates any missing __init__.py files.

It is idempotent and safe to re-run; it will skip moves when the
destination already exists with the same content.

Usage (ALWAYS via Poetry):
  poetry run python scripts/perform_services_reorg.py --apply

Options:
  --apply     Perform the moves. Without this flag, the script prints the plan.
  --verbose   Print extra details.
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
SERVICES_ROOT = REPO_ROOT / "the_alchemiser" / "services"


@dataclass(frozen=True)
class Move:
    src: Path
    dst: Path

    def as_str(self) -> str:
        return f"{self.src.relative_to(REPO_ROOT)} -> {self.dst.relative_to(REPO_ROOT)}"


def ensure_package(path: Path, verbose: bool = False) -> None:
    path.mkdir(parents=True, exist_ok=True)
    init_file = path / "__init__.py"
    if not init_file.exists():
        init_file.write_text("# auto-created by perform_services_reorg\n")
        if verbose:
            print(f"created: {init_file.relative_to(REPO_ROOT)}")


def planned_moves() -> list[Move]:
    """Return the list of intended file moves."""
    # Target subpackages
    account = SERVICES_ROOT / "account"
    market_data = SERVICES_ROOT / "market_data"
    trading = SERVICES_ROOT / "trading"
    shared = SERVICES_ROOT / "shared"
    errors = SERVICES_ROOT / "errors"
    repository = SERVICES_ROOT / "repository"

    # Map of current -> destination
    mapping: dict[Path, Path] = {
        # enhanced (new architecture)
        SERVICES_ROOT / "enhanced" / "account_service.py": account / "account_service.py",
        SERVICES_ROOT
        / "enhanced"
        / "market_data_service.py": market_data
        / "market_data_service.py",
        SERVICES_ROOT / "enhanced" / "order_service.py": trading / "order_service.py",
        SERVICES_ROOT / "enhanced" / "position_service.py": trading / "position_service.py",
        SERVICES_ROOT
        / "enhanced"
        / "trading_service_manager.py": trading
        / "trading_service_manager.py",
        # legacy/root services
        SERVICES_ROOT / "account_service.py": account / "legacy_account_service.py",
        SERVICES_ROOT / "account_utils.py": account / "account_utils.py",
        SERVICES_ROOT / "market_data_client.py": market_data / "market_data_client.py",
        SERVICES_ROOT / "price_service.py": market_data / "price_service.py",
        SERVICES_ROOT / "price_utils.py": market_data / "price_utils.py",
        SERVICES_ROOT / "price_fetching_utils.py": market_data / "price_fetching_utils.py",
        SERVICES_ROOT / "streaming_service.py": market_data / "streaming_service.py",
        SERVICES_ROOT / "trading_client_service.py": trading / "trading_client_service.py",
        SERVICES_ROOT / "position_manager.py": trading / "position_manager.py",
        SERVICES_ROOT / "cache_manager.py": shared / "cache_manager.py",
        SERVICES_ROOT / "config_service.py": shared / "config_service.py",
        SERVICES_ROOT / "retry_decorator.py": shared / "retry_decorator.py",
        SERVICES_ROOT / "secrets_service.py": shared / "secrets_service.py",
        SERVICES_ROOT / "service_factory.py": shared / "service_factory.py",
        SERVICES_ROOT / "alpaca_manager.py": repository / "alpaca_manager.py",
        # errors
        SERVICES_ROOT / "exceptions.py": errors / "exceptions.py",
        SERVICES_ROOT / "error_handler.py": errors / "error_handler.py",
        SERVICES_ROOT / "error_handling.py": errors / "error_handling.py",
        SERVICES_ROOT / "error_monitoring.py": errors / "error_monitoring.py",
        SERVICES_ROOT / "error_recovery.py": errors / "error_recovery.py",
        SERVICES_ROOT / "error_reporter.py": errors / "error_reporter.py",
    }

    return [Move(src=k, dst=v) for k, v in mapping.items()]


def create_target_packages(moves: Iterable[Move], verbose: bool = False) -> None:
    pkgs: set[Path] = set()
    for mv in moves:
        pkgs.add(mv.dst.parent)
    for pkg in sorted(pkgs):
        ensure_package(pkg, verbose=verbose)


def files_equal(a: Path, b: Path) -> bool:
    try:
        return filecmp.cmp(a, b, shallow=False)
    except Exception:
        return False


def do_moves(moves: Iterable[Move], apply: bool, verbose: bool = False) -> int:
    pending = 0
    for mv in moves:
        if not mv.src.exists():
            # Already moved or missing
            if verbose:
                print(f"skip (missing): {mv.as_str()}")
            continue
        if mv.dst.exists() and files_equal(mv.src, mv.dst):
            if verbose:
                print(f"skip (exists same): {mv.as_str()}")
            continue

        pending += 1
        if apply:
            mv.dst.parent.mkdir(parents=True, exist_ok=True)
            # Use shutil.move to handle cross-filesystem moves
            shutil.move(str(mv.src), str(mv.dst))
            if verbose:
                print(f"moved: {mv.as_str()}")
        else:
            print(f"PLAN: move {mv.as_str()}")
    return pending


def cleanup_empty_dirs(verbose: bool = False) -> None:
    # Remove empty 'enhanced' folder and any now-empty service subfolders created previously
    candidates = [
        SERVICES_ROOT / "enhanced",
        SERVICES_ROOT / "market_data",
        SERVICES_ROOT / "shared",
        SERVICES_ROOT / "trading",
    ]
    # Add any other immediate subdirectories
    candidates.extend(p for p in SERVICES_ROOT.iterdir() if p.is_dir())

    for d in sorted(set(candidates)):
        try:
            if d.exists() and d.is_dir() and not any(d.iterdir()):
                d.rmdir()
                if verbose:
                    print(f"removed empty dir: {d.relative_to(REPO_ROOT)}")
        except Exception:
            # Directory not empty or cannot remove
            pass


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Reorganize services folder")
    parser.add_argument("--apply", action="store_true", help="Perform the moves")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args(argv)

    if not SERVICES_ROOT.exists():
        print(f"ERROR: services root not found at {SERVICES_ROOT}", file=sys.stderr)
        return 2

    moves = planned_moves()
    create_target_packages(moves, verbose=args.verbose)
    pending = do_moves(moves, apply=args.apply, verbose=args.verbose)

    if args.apply:
        cleanup_empty_dirs(verbose=args.verbose)
        print(f"Applied {pending} move(s).")
    else:
        print(f"Planned {pending} move(s). Re-run with --apply to execute.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
