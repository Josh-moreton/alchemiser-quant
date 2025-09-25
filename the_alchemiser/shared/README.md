# Shared Module

**Business Unit:** shared  
**Status:** current (under construction)

## Purpose

The shared module provides schemas, utilities, and cross-cutting concerns. This module contains:

- **Schemas**: Data models for inter-module communication
- **Types**: Common value objects (Money, Symbol classes)
- **Utils**: Utility functions and helpers
- **Config**: Configuration management
- **Logging**: Logging setup and utilities

## Current Status

⚠️ **No logic here yet** - This module is part of Phase 1 scaffolding for the modular architecture migration. Business logic will be moved here in Phase 2.

## Dependencies

- ✅ Leaf module: No dependencies on other modules
- ❌ Forbidden: Cannot import from `strategy/`, `portfolio/`, `execution/`

## Architecture Notes

This module provides common types and utilities used across modules. It should have no dependencies on other modules and keep minimal and focused on truly shared concerns. All modules may import from shared/ only.