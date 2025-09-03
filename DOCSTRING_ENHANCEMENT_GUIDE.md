# Docstring Enhancement Guide

This guide provides a systematic approach to enhancing docstrings across The Alchemiser codebase.

## Quick Start

1. **Run the analysis framework**:
   ```bash
   python docstring_enhancement_framework.py
   ```

2. **Review the generated report**:
   ```bash
   less docstring_enhancement_report.md
   ```

3. **Focus on high-priority files** (5+ missing docstrings first)

## Business Unit Standards

Every module must start with a business unit docstring:

```python
"""Business Unit: {strategy|portfolio|execution|shared} | Status: current.

Brief description of module responsibility.

Detailed description explaining the module's role in the system.
"""
```

### Business Unit Mapping
- **strategy**: Signal generation, indicators, ML models
- **portfolio**: Portfolio state, sizing, rebalancing logic
- **execution**: Broker API integrations, order placement, error handling
- **shared**: DTOs, utilities, logging, cross-cutting concerns

## Google Style Format

### Module Docstring
```python
"""Business Unit: shared | Status: current.

Short description of the module.

Detailed description explaining what the module does,
its dependencies, and how it fits into the system.
"""
```

### Class Docstring
```python
class ExampleClass:
    """Short description of the class.

    Detailed description explaining the purpose, responsibilities,
    and how this class fits into the overall system.

    Attributes:
        attribute_name: Description of the attribute.
        another_attr: Description of another attribute.

    Example:
        >>> instance = ExampleClass(param1, param2)
        >>> result = instance.method_name()
        >>> print(result)
    """
```

### Function Docstring
```python
def example_function(param1: str, param2: int = 10) -> bool:
    """Short description of what the function does.

    Detailed description explaining the purpose, algorithm,
    and any important implementation details.

    Args:
        param1: Description of first parameter.
        param2: Description of second parameter. Defaults to 10.

    Returns:
        True if successful, False otherwise.

    Raises:
        ValueError: When input validation fails.
        TypeError: When wrong type is provided.

    Example:
        >>> result = example_function("test", 5)
        >>> print(result)
        True
    """
```

## Quality Checklist

- [ ] Module has business unit docstring
- [ ] All public classes have docstrings
- [ ] All public functions have docstrings
- [ ] Docstrings use Google style format
- [ ] Args section documents all parameters
- [ ] Returns section describes return value
- [ ] Raises section lists relevant exceptions
- [ ] Examples provided where helpful
- [ ] First line ends with period
- [ ] Blank line after summary if multi-line

## Validation

Run docstring validation:
```bash
# Check all docstring rules
poetry run ruff check --select D the_alchemiser/

# Check specific violations
poetry run ruff check --select D100,D101,D102 the_alchemiser/

# Auto-fix formatting issues
poetry run ruff check --fix --select D the_alchemiser/
```

## Priority Files (Current)

Based on the latest analysis, focus on these files first:

1. `shared/utils/error_recovery.py` (15 missing)
2. `shared/value_objects/core_types.py` (11 missing)
3. `shared/utils/error_monitoring.py` (7 missing)
4. `shared/utils/error_handling.py` (6 missing)

## Implementation Tips

### TypedDict Classes
```python
class ExampleTypeDict(TypedDict):
    """Description of the typed dictionary.
    
    Contains structured data for specific use cases.
    Used throughout the system for type safety.
    
    Attributes:
        field1: Description of first field.
        field2: Description of second field.
    """
    field1: str
    field2: int
```

### Value Objects
```python
@dataclass(frozen=True)
class ValueObject:
    """Immutable value object description.
    
    Represents domain concept with validation and behavior.
    
    Attributes:
        value: The core value being represented.
        
    Raises:
        ValueError: When validation fails.
        
    Example:
        >>> obj = ValueObject(valid_value)
        >>> print(obj.value)
    """
```

### Abstract Base Classes
```python
class AbstractBase(ABC):
    """Abstract base class description.
    
    Defines interface for implementing classes.
    
    Subclasses must implement all abstract methods.
    """
    
    @abstractmethod
    def required_method(self) -> None:
        """Description of required method.
        
        Must be implemented by subclasses.
        """
```

## Common Patterns

### Error Handling Classes
- Document error conditions clearly
- Include recovery strategies
- Specify when exceptions are raised

### Repository Interfaces
- Document data source interactions
- Specify expected data formats
- Include error handling approaches

### Strategy Classes
- Document signal generation logic
- Include examples of usage
- Specify confidence levels and reasoning

## Automation Tools

The `docstring_enhancement_framework.py` script provides:
- Priority file identification
- Template generation
- Validation helpers
- Progress tracking

Run it regularly to identify areas needing attention.