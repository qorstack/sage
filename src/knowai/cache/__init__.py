"""Persistent scan cache — allows cross-repo cognition without all repos cloned."""

from knowai.cache.scan_cache import ScanCache, get_cached_scan, save_scan

__all__ = ["ScanCache", "get_cached_scan", "save_scan"]
