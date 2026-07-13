# Design Decisions

## Principles
1. **Local First**: Keep all information under user control by default.
2. **API First**: Core business logic must be fully exposed via clear APIs (internal Python services, REST, and CLI).
3. **Clean Architecture**: Decouple domain layer from database/framework implementations.

## Design Patterns
- **Repository Pattern**: Abstract away persistence using Protocals.
- **Dependency Injection**: Services receive repositories in construction.
- **Separation of Concerns**: CLI only manages formatting and interaction, business logic belongs to Services and Domain.
