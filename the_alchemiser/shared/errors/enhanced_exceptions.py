#!/usr/bin/env python3#!/usr/bin/env python3

"""Business Unit: shared | Status: current."""Business Unit: shared | Status: current.



Enhanced exception classes with context tracking.Enhanced exception classes with context tracking.



This module provides simplified enhanced exception classes for backwardThis module provides simplified enhanced exception classes for backward

compatibility with code that imports EnhancedAlchemiserError and EnhancedDataError.compatibility with code that imports EnhancedAlchemiserError and EnhancedDataError.

""""""



from __future__ import annotationsfrom __future__ import annotations



from typing import Anyfrom typing import Any



# Import base exception from the canonical location# Import base exception from the canonical location

try:try:

    from the_alchemiser.shared.types.exceptions import (    from the_alchemiser.shared.types.exceptions import (

        AlchemiserError,        AlchemiserError,

        DataProviderError,        DataProviderError,

    )    )

except ImportError:except ImportError:



    class AlchemiserError(Exception):  # type: ignore[no-redef]    class AlchemiserError(Exception):  # type: ignore[no-redef]

        """Fallback AlchemiserError."""        """Fallback AlchemiserError."""



    class DataProviderError(AlchemiserError):  # type: ignore[no-redef]    class DataProviderError(AlchemiserError):  # type: ignore[no-redef]

        """Fallback DataProviderError."""        """Fallback DataProviderError."""





class EnhancedAlchemiserError(AlchemiserError):class EnhancedAlchemiserError(AlchemiserError):

    """Enhanced base exception with context support.    """Enhanced base exception with context support.



    This is a simplified version that maintains backward compatibility    This is a simplified version that maintains backward compatibility

    with code expecting enhanced error features while using the standard    with code expecting enhanced error features while using the standard

    AlchemiserError as the base.    AlchemiserError as the base.



    Args:    Args:

        message: Error message        message: Error message

        context: Optional error context dictionary        context: Optional error context dictionary

        **kwargs: Additional keyword arguments (for compatibility)        **kwargs: Additional keyword arguments (for compatibility)



    Examples:    Examples:

        >>> error = EnhancedAlchemiserError(        >>> error = EnhancedAlchemiserError(

        ...     "Operation failed",        ...     "Operation failed",

        ...     context={"module": "test", "correlation_id": "123"}        ...     context={"module": "test", "correlation_id": "123"}

        ... )        ... )

        >>> str(error)        >>> str(error)

        'Operation failed'        'Operation failed'



    """    """



    def __init__(    def __init__(

        self,        self,

        message: str,        message: str,

        context: dict[str, Any] | None = None,        context: dict[str, Any] | None = None,

        **kwargs: str | int | float | bool | None,        **kwargs: str | int | float | bool | None,

    ) -> None:    ) -> None:

        """Initialize enhanced error with optional context."""

        super().__init__(message)    """

        self.context = context or {}

        self.original_message = message    def __init__(

        # Store any additional kwargs for compatibility        self,

        for key, value in kwargs.items():        message: str,

            setattr(self, key, value)        context: dict[str, Any] | None = None,

        **kwargs: Any,

    ) -> None:

class EnhancedDataError(DataProviderError):        """Initialize enhanced error with optional context."""

    """Enhanced data error with data source context.        super().__init__(message)

        self.context = context or {}

    This is a specialized error for data-related failures with additional        self.original_message = message

    context about the data source, type, and recoverability.        # Store any additional kwargs for compatibility

        for key, value in kwargs.items():

    Args:            setattr(self, key, value)

        message: Error message

        data_source: Optional data source identifier

        data_type: Optional data type identifierclass EnhancedDataError(DataProviderError):

        recoverable: Whether the error is recoverable (default: False)    """Enhanced data error with data source context.

        **kwargs: Additional keyword arguments

    This is a specialized error for data-related failures with additional

    Examples:    context about the data source, type, and recoverability.

        >>> error = EnhancedDataError(

        ...     "Failed to parse timestamp",    Args:

        ...     data_source="timezone_utils",        message: Error message

        ...     data_type="timestamp",        data_source: Optional data source identifier

        ...     recoverable=False        data_type: Optional data type identifier

        ... )        recoverable: Whether the error is recoverable (default: False)

        >>> error.data_source        **kwargs: Additional keyword arguments

        'timezone_utils'

    Examples:

    """        >>> error = EnhancedDataError(

        ...     "Failed to parse timestamp",

    def __init__(        ...     data_source="timezone_utils",

        self,        ...     data_type="timestamp",

        message: str,        ...     recoverable=False

        data_source: str | None = None,        ... )

        data_type: str | None = None,        >>> error.data_source

        *,        'timezone_utils'

        recoverable: bool = False,

        **kwargs: str | int | float | bool | None,    """

    ) -> None:

        """Initialize data error with source context."""    def __init__(

        super().__init__(message)        self,

        self.data_source = data_source        message: str,

        self.data_type = data_type        data_source: str | None = None,

        self.recoverable = recoverable        data_type: str | None = None,

        self.original_message = message        *,

        # Store any additional kwargs for compatibility        recoverable: bool = False,

        for key, value in kwargs.items():        **kwargs: str | int | float | bool | None,

            setattr(self, key, value)    ) -> None:



    """

class EnhancedTradingError(EnhancedAlchemiserError):

    """Enhanced trading error (alias for backward compatibility)."""    def __init__(

        self,

    def __init__(        message: str,

        self,        data_source: str | None = None,

        message: str,        data_type: str | None = None,

        symbol: str | None = None,        recoverable: bool = False,

        order_id: str | None = None,        **kwargs: Any,

        quantity: float | None = None,    ) -> None:

        price: float | None = None,        """Initialize data error with source context."""

        **kwargs: str | int | float | bool | None,        super().__init__(message)

    ) -> None:        self.data_source = data_source

        """Initialize trading error with trading context."""        self.data_type = data_type

        super().__init__(message, **kwargs)        self.recoverable = recoverable

        self.symbol = symbol        self.original_message = message

        self.order_id = order_id        # Store any additional kwargs for compatibility

        self.quantity = quantity        for key, value in kwargs.items():

        self.price = price            setattr(self, key, value)



# Alias for backward compatibility (some code may import this)
class EnhancedTradingError(EnhancedAlchemiserError):
    """Enhanced trading error (alias for backward compatibility)."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        order_id: str | None = None,
        quantity: float | None = None,
        price: float | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize trading error with trading context."""
        super().__init__(message, **kwargs)
        self.symbol = symbol
        self.order_id = order_id
        self.quantity = quantity
        self.price = price
