# Wiki Documentation

This folder contains documentation that should be moved to the `alchemiser-quant.wiki` repository when it becomes available.

## Contents

- **Trading-Engine-Decomposition.md**: Comprehensive architecture documentation for the Trading Engine refactoring

## Instructions for Wiki Migration

When the `alchemiser-quant.wiki` repository is available:

1. Clone the wiki repository:
   ```bash
   git clone https://github.com/Josh-moreton/alchemiser-quant.wiki.git
   ```

2. Move the documentation:
   ```bash
   cp docs/wiki/Trading-Engine-Decomposition.md alchemiser-quant.wiki/
   ```

3. Update any relative links to work in the wiki context

4. Commit and push to the wiki repository:
   ```bash
   cd alchemiser-quant.wiki
   git add Trading-Engine-Decomposition.md
   git commit -m "Add Trading Engine Decomposition documentation"
   git push origin master
   ```

## Documentation Standards

All wiki documentation follows these standards:
- Uses exact terminology from the codebase (value objects, facades, orchestrators)
- Includes comprehensive code references with file paths
- Provides sequence diagrams for complex flows
- Links to existing documentation where appropriate
- Maintains consistency with the project's DDD architecture principles