# Type Adoption Scorecard

## Baseline (Week 0)
- Public functions returning `Any`: 22
- mypy errors (`poetry run mypy the_alchemiser`): 0
- Typed cache entries: ~20%
- TODOs remaining: 96

## Targets
| Phase | `Any` in signatures | mypy errors | Typed cache | TODOs remaining |
|-------|---------------------|-------------|-------------|-----------------|
|5|20|0|25%|95|
|6|18|0|30%|85|
|7|15|0|40%|80|
|8|10|0|50%|59|
|9|8|0|65%|46|
|10|5|0|80%|35|
|11|3|0|90%|29|
|12|1|0|95%|24|
|13|1|0|98%|5|
|14|0|≤5|100%|0|
|15|0|0|100%|0|
