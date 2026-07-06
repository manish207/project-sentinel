"""
Configuration package for Project Sentinel.
"""

from .loader import get_settings
from .settings import Settings

__all__ = ["Settings", "get_settings"]