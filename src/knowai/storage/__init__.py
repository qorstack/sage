"""Storage primitives — file locking + atomic write for safe concurrent access."""

from knowai.storage.atomic import atomic_write_text, file_lock, read_modify_write

__all__ = ["atomic_write_text", "file_lock", "read_modify_write"]
