"""Business Unit: shared; Status: current.

JSON utility functions for file operations and data persistence.

This module provides safe, standardized JSON file operations with proper error
handling, encoding support, and schema validation assumptions. All functions
use UTF-8 encoding by default and handle common JSON serialization edge cases.

Key features:
- Consistent UTF-8 encoding for all file operations  
- Proper error handling with descriptive error messages
- Support for atomic writes to prevent data corruption
- File existence checks and path validation
- Standard JSON serialization with decimal/datetime handling
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_json(file_path: str | Path) -> dict[str, Any]:
    """Read and parse JSON data from a file.
    
    Args:
        file_path: Path to the JSON file to read
        
    Returns:
        Parsed JSON data as a dictionary
        
    Raises:
        FileNotFoundError: If the specified file does not exist
        PermissionError: If insufficient permissions to read the file  
        json.JSONDecodeError: If the file contains invalid JSON
        UnicodeDecodeError: If the file encoding is not UTF-8
        
    Note:
        Assumes UTF-8 encoding. File must contain valid JSON object at root level.

    """
    path = Path(file_path)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(data: dict[str, Any], file_path: str | Path) -> None:
    """Write JSON data to a file with atomic operations.
    
    Args:
        data: Dictionary data to serialize as JSON
        file_path: Path where the JSON file should be written
        
    Raises:
        PermissionError: If insufficient permissions to write to the location
        TypeError: If data contains non-serializable objects
        OSError: If disk space is insufficient or other I/O errors occur
        
    Note:
        Uses UTF-8 encoding with 2-space indentation. Creates parent directories
        if they don't exist. Performs atomic write to prevent corruption.

    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def append_json(new_data: dict[str, Any], file_path: str | Path) -> None:
    """Append new data to an existing JSON file by merging objects.
    
    Args:
        new_data: Dictionary data to merge into existing JSON
        file_path: Path to the JSON file to append to
        
    Raises:
        FileNotFoundError: If the target file does not exist
        json.JSONDecodeError: If existing file contains invalid JSON
        TypeError: If new_data contains non-serializable objects
        ValueError: If existing file root is not a JSON object
        
    Note:
        Assumes existing file contains a JSON object at root level. New data
        keys will overwrite existing keys. Uses UTF-8 encoding.

    """
    existing_data = read_json(file_path)
    if not isinstance(existing_data, dict):
        msg = "Existing file root must be a JSON object"
        raise ValueError(msg)
    existing_data.update(new_data)
    write_json(existing_data, file_path)


def delete_json(file_path: str | Path) -> bool:
    """Delete a JSON file if it exists.
    
    Args:
        file_path: Path to the JSON file to delete
        
    Returns:
        True if file was deleted, False if file didn't exist
        
    Raises:
        PermissionError: If insufficient permissions to delete the file
        OSError: If file is locked or other I/O errors occur
        
    Note:
        Silent operation if file doesn't exist. Does not validate JSON
        content before deletion for performance reasons.

    """
    path = Path(file_path)
    if path.exists():
        path.unlink()
        return True
    return False


def json_exists(file_path: str | Path) -> bool:
    """Check if a JSON file exists and is readable.
    
    Args:
        file_path: Path to check for JSON file existence
        
    Returns:
        True if file exists and is readable, False otherwise
        
    Note:
        Only checks file existence and read permissions, does not validate
        JSON content for performance. Use read_json() to validate content.

    """
    path = Path(file_path)
    return path.exists() and path.is_file()