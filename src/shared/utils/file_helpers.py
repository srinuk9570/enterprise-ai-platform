"""
File system utility functions.
"""
import os
import shutil
import tempfile
import hashlib
from pathlib import Path
from typing import Optional, List, BinaryIO, Union
import mimetypes


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path
    
    Returns:
        Path object for the directory
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_filename(filename: str) -> str:
    """
    Convert a string to a safe filename.
    
    Args:
        filename: Original filename
    
    Returns:
        Safe filename
    """
    import re
    
    # Remove path separators
    filename = filename.replace("/", "_").replace("\\", "_")
    
    # Remove non-alphanumeric characters
    filename = re.sub(r"[^\w\s.-]", "", filename)
    
    # Replace spaces with underscores
    filename = re.sub(r"\s+", "_", filename)
    
    # Remove consecutive dots and dashes
    filename = re.sub(r"\.+", ".", filename)
    filename = re.sub(r"\-+", "-", filename)
    
    # Trim
    filename = filename.strip("._-")
    
    # Ensure non-empty
    if not filename:
        filename = "unnamed"
    
    return filename


def get_file_extension(filename: str) -> str:
    """
    Get file extension with dot.
    
    Args:
        filename: File name
    
    Returns:
        Lowercase extension with dot (e.g., '.txt')
    """
    return Path(filename).suffix.lower()


def get_mime_type(filename: str) -> str:
    """
    Get MIME type from filename.
    
    Args:
        filename: File name
    
    Returns:
        MIME type string
    """
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"


def read_file(filepath: Union[str, Path], mode: str = "r", encoding: str = "utf-8") -> str:
    """
    Read file contents as string.
    
    Args:
        filepath: Path to file
        mode: Read mode
        encoding: File encoding
    
    Returns:
        File contents
    """
    with open(filepath, mode, encoding=encoding) as f:
        return f.read()


def read_file_bytes(filepath: Union[str, Path]) -> bytes:
    """
    Read file contents as bytes.
    
    Args:
        filepath: Path to file
    
    Returns:
        File contents as bytes
    """
    with open(filepath, "rb") as f:
        return f.read()


def write_file(
    filepath: Union[str, Path],
    content: Union[str, bytes],
    mode: str = "w",
    encoding: str = "utf-8",
) -> Path:
    """
    Write content to file.
    
    Args:
        filepath: Path to file
        content: Content to write
        mode: Write mode
        encoding: File encoding
    
    Returns:
        Path to written file
    """
    filepath = Path(filepath)
    ensure_directory(filepath.parent)
    
    if isinstance(content, bytes):
        with open(filepath, "wb") as f:
            f.write(content)
    else:
        with open(filepath, mode, encoding=encoding) as f:
            f.write(content)
    
    return filepath


def delete_file(filepath: Union[str, Path]) -> bool:
    """
    Delete a file.
    
    Args:
        filepath: Path to file
    
    Returns:
        True if deleted, False if not found
    """
    filepath = Path(filepath)
    
    if filepath.exists():
        filepath.unlink()
        return True
    
    return False


def copy_file(
    src: Union[str, Path],
    dst: Union[str, Path],
    overwrite: bool = True,
) -> Path:
    """
    Copy a file.
    
    Args:
        src: Source path
        dst: Destination path
        overwrite: Whether to overwrite existing file
    
    Returns:
        Destination path
    """
    src = Path(src)
    dst = Path(dst)
    
    ensure_directory(dst.parent)
    
    if dst.exists() and not overwrite:
        raise FileExistsError(f"Destination file already exists: {dst}")
    
    shutil.copy2(src, dst)
    return dst


def move_file(
    src: Union[str, Path],
    dst: Union[str, Path],
    overwrite: bool = True,
) -> Path:
    """
    Move/rename a file.
    
    Args:
        src: Source path
        dst: Destination path
        overwrite: Whether to overwrite existing file
    
    Returns:
        Destination path
    """
    src = Path(src)
    dst = Path(dst)
    
    ensure_directory(dst.parent)
    
    if dst.exists() and not overwrite:
        raise FileExistsError(f"Destination file already exists: {dst}")
    
    shutil.move(str(src), str(dst))
    return dst


def get_file_size(filepath: Union[str, Path]) -> int:
    """
    Get file size in bytes.
    
    Args:
        filepath: Path to file
    
    Returns:
        File size in bytes, 0 if not found
    """
    filepath = Path(filepath)
    
    if filepath.exists():
        return filepath.stat().st_size
    
    return 0


def get_file_hash(filepath: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Get file hash.
    
    Args:
        filepath: Path to file
        algorithm: Hash algorithm (md5, sha1, sha256)
    
    Returns:
        Hex digest string
    """
    hasher = hashlib.new(algorithm)
    
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    
    return hasher.hexdigest()


def list_files(
    directory: Union[str, Path],
    pattern: str = "*",
    recursive: bool = False,
) -> List[Path]:
    """
    List files in a directory.
    
    Args:
        directory: Directory path
        pattern: Glob pattern
        recursive: Whether to search recursively
    
    Returns:
        List of file paths
    """
    directory = Path(directory)
    
    if recursive:
        return list(directory.rglob(pattern))
    else:
        return list(directory.glob(pattern))


def create_temp_file(
    content: Optional[Union[str, bytes]] = None,
    suffix: Optional[str] = None,
    prefix: Optional[str] = None,
) -> Path:
    """
    Create a temporary file.
    
    Args:
        content: Optional content to write
        suffix: File suffix (extension)
        prefix: File prefix
    
    Returns:
        Path to temporary file
    """
    with tempfile.NamedTemporaryFile(
        mode="wb" if isinstance(content, bytes) else "w",
        suffix=suffix or "",
        prefix=prefix or "",
        delete=False,
    ) as f:
        filepath = Path(f.name)
        if content:
            f.write(content)
    
    return filepath


def cleanup_temp_files(max_age_hours: int = 24) -> int:
    """
    Clean up old temporary files.
    
    Args:
        max_age_hours: Maximum age in hours
    
    Returns:
        Number of files deleted
    """
    import time
    
    temp_dir = Path(tempfile.gettempdir())
    cutoff_time = time.time() - (max_age_hours * 3600)
    deleted_count = 0
    
    for filepath in temp_dir.glob("tmp*"):
        try:
            if filepath.stat().st_mtime < cutoff_time:
                filepath.unlink()
                deleted_count += 1
        except Exception:
            pass
    
    return deleted_count


def get_directory_size(directory: Union[str, Path]) -> int:
    """
    Get total size of a directory.
    
    Args:
        directory: Directory path
    
    Returns:
        Total size in bytes
    """
    directory = Path(directory)
    total_size = 0
    
    for filepath in directory.rglob("*"):
        if filepath.is_file():
            total_size += filepath.stat().st_size
    
    return total_size


def is_file_empty(filepath: Union[str, Path]) -> bool:
    """
    Check if a file is empty.
    
    Args:
        filepath: Path to file
    
    Returns:
        True if file is empty or doesn't exist
    """
    return get_file_size(filepath) == 0