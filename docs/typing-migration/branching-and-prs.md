# Branching & PR Strategy

## Branch naming
`feature/types-phase-<phase>-<short>` per phase. Example: `feature/types-phase-07-orderdetails`.

## PR slicing
- Contract PR: introduce models/adapters (<200 LOC)
- Usage PR: refactor callers (<500 LOC)
- Maximum 3 open PRs per phase

## CI gates
| Phase | mypy flags | Coverage |
|-------|------------|----------|
|5|`--strict-optional`|>=60%|
|6|`--disallow-any-generics`|>=60%|
|7|`--disallow-untyped-defs`|>=65%|
|8|`--warn-unused-ignores`|>=65%|
|9|`--disallow-any-expr`|>=70%|
|10|`--disallow-any-unimported`|>=70%|
|11|`--no-warn-no-return`|>=75%|
|12|`--warn-redundant-casts`|>=75%|
|13|`--warn-unused-configs`|>=80%|
|14|`--strict` (allow ≤5 errors)|>=80%|
|15|`--strict` (0 errors)|>=85%|

## Release notes & versioning
- CLI or email output changes require minor version bump and changelog entry
- Snapshot diffs must accompany release notes
