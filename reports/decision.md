strategy: Hybrid
why: |
  The codebase defines 11 Pydantic models focused on configuration and order validation, while 28 dataclasses hold core domain state. ValidatedOrder uses Pydantic validators, yet domain packages rely on simple dataclasses without runtime validation. The presence of Pydantic is confined to boundary modules such as infrastructure/config and application/orders, indicating minimal coupling to Pydantic in the core domain.
scope:
  pydantic_use: boundaries
  domain_models: dataclasses
  migration_risk: medium
next_prs:
  - "Add slots and kw_only to core domain dataclasses"
  - "Upgrade order validation module to Pydantic v2"
  - "Introduce DTO layer separating Pydantic models from domain"

---

# Decision

## Recommendation
Use **Hybrid** modeling: frozen, slotted dataclasses in the domain with Pydantic v2 reserved for IO boundaries (config, API, persistence). This approach keeps domain logic lightweight while retaining robust parsing at external interfaces.

## Evidence
- `ValidatedOrder` demonstrates boundary validation via Pydantic with multiple validators for symbol, price fields, and filled quantity【F:the_alchemiser/application/orders/order_validation.py†L40-L158】
- Domain models such as `AccountModel` are plain dataclasses lacking slots or kw-only parameters, indicating internal state handling without framework coupling【F:the_alchemiser/domain/models/account.py†L3-L56】
- Configuration settings rely on Pydantic `BaseModel` and `BaseSettings`, highlighting Pydantic’s existing role at configuration boundaries【F:the_alchemiser/infrastructure/config/config.py†L5-L78】

## Rationale
- Domain logic is better served by lightweight dataclasses with explicit constructors and invariants.
- Pydantic remains ideal for parsing configuration and validating external input like orders.
- Migrating domain models to dataclasses with `frozen=True, slots=True, kw_only=True` improves performance and clarity.

## Risks
- Medium migration effort: existing domain dataclasses need refactoring and additional tests.
- Team must be comfortable with both dataclasses and Pydantic v2 idioms.
- Maintaining DTO/domain mapping introduces slight boilerplate but isolates concerns.

