"""File utility functions for The Alchemiser.

Business Unit: shared
Status: current
"""
from pathlib import Path


def read_file(file_path: str | Path, encoding: str = "utf-8") -> str:
    """Read contents from a file.
    
    Args:
        file_path: Absolute or relative path to the file to read.
        encoding: Text encoding to use when reading the file (default: utf-8).
        
    Returns:
        The complete file contents as a string.
        
    Raises:
        FileNotFoundError: If the specified file does not exist.
        PermissionError: If read access to the file is denied.
        UnicodeDecodeError: If the file cannot be decoded with the specified encoding.

    """
    path = Path(file_path)
    with path.open(encoding=encoding) as file:
        return file.read()


def write_file(file_path: str | Path, content: str, encoding: str = "utf-8") -> None:
    """Write content to a file, creating or overwriting as needed.
    
    Args:
        file_path: Absolute or relative path to the file to write.
        content: String content to write to the file.
        encoding: Text encoding to use when writing the file (default: utf-8).
        
    Raises:
        PermissionError: If write access to the file location is denied.
        FileNotFoundError: If the parent directory does not exist.
        UnicodeEncodeError: If the content cannot be encoded with the specified encoding.

    """
    path = Path(file_path)
    with path.open("w", encoding=encoding) as file:
        file.write(content)


def append_file(file_path: str | Path, content: str, encoding: str = "utf-8") -> None:
    """Append content to an existing file or create a new file if it doesn't exist.
    
    Args:
        file_path: Absolute or relative path to the file to append to.
        content: String content to append to the file.
        encoding: Text encoding to use when writing the file (default: utf-8).
        
    Raises:
        PermissionError: If write access to the file location is denied.
        FileNotFoundError: If the parent directory does not exist.
        UnicodeEncodeError: If the content cannot be encoded with the specified encoding.

    """
    path = Path(file_path)
    with path.open("a", encoding=encoding) as file:
        file.write(content)


def delete_file(file_path: str | Path) -> bool:
    """Delete a file if it exists.
    
    Args:
        file_path: Absolute or relative path to the file to delete.
        
    Returns:
        True if the file was successfully deleted, False if the file did not exist.
        
    Raises:
        PermissionError: If delete access to the file is denied.
        IsADirectoryError: If the path points to a directory instead of a file.

    """
    path = Path(file_path)
    try:
        path.unlink()
        return True
    except FileNotFoundError:
        return False


def file_exists(file_path: str | Path) -> bool:
    """Check if a file exists at the specified path.
    
    Args:
        file_path: Absolute or relative path to check for file existence.
        
    Returns:
        True if a file exists at the specified path, False otherwise.
        Note: Returns False for directories, only True for actual files.

    """
    path = Path(file_path)
    return path.is_file()