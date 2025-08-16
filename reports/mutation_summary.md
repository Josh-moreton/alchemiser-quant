# Mutation Testing Summary

`mutmut run` could not execute successfully due to import path issues when copying test modules into the mutation workspace. The tool reported:

```
ModuleNotFoundError: No module named 'the_alchemiser.application.execution'
```

Next steps:
- Configure `paths_to_mutate` in project configuration and ensure the package is discoverable when tests are executed from the `mutants/` directory.
- Once configured, enforce a minimum mutation score of 60% with `make mutate` and `make mutate-report`.
