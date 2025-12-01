#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$ROOT_DIR/dist/services"
REQUIREMENTS_FILE="$ROOT_DIR/dependencies/requirements.txt"

if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo "❌ dependencies/requirements.txt not found. Run scripts/deploy.sh to generate it first." >&2
    exit 1
fi

mkdir -p "$DIST_DIR"
SERVICES=("strategy_v2" "portfolio_v2" "execution_v2")

function package_service() {
    local service=$1
    local target_dir="$DIST_DIR/$service"
    echo "📦 Packaging $service into $target_dir"
    rm -rf "$target_dir" "$target_dir.zip"
    mkdir -p "$target_dir/the_alchemiser"

    rsync -a "$ROOT_DIR/the_alchemiser/$service" "$target_dir/the_alchemiser/"
    rsync -a "$ROOT_DIR/the_alchemiser/shared" "$target_dir/the_alchemiser/"
    cp "$ROOT_DIR/the_alchemiser/__init__.py" "$target_dir/the_alchemiser/__init__.py"
    cp "$ROOT_DIR/the_alchemiser/py.typed" "$target_dir/the_alchemiser/py.typed"

    python -m pip install --upgrade pip >/dev/null
    python -m pip install -r "$REQUIREMENTS_FILE" --target "$target_dir" >/dev/null

    (cd "$target_dir" && zip -qr "$DIST_DIR/${service}.zip" .)
    echo "✅ Created $DIST_DIR/${service}.zip"
}

for service in "${SERVICES[@]}"; do
    package_service "$service"
done
