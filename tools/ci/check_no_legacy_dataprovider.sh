#!/usr/bin/env bash
set -euo pipefail

if grep -R "the_alchemiser\.infrastructure\.data_providers\.data_provider" -n \
    --exclude="swap_to_facade.py" \
    --exclude="test_data_provider_parity.py" \
    --exclude="data_provider.py" \
    --exclude-dir="__pycache__" .; then
    echo "legacy data_provider import detected" >&2
    exit 1
fi
