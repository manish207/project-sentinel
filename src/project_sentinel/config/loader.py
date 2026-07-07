"""
Configuration loader.
"""

from functools import lru_cache

from project_sentinel.config.settings import Settings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return cached settings object.
    """
    return Settings()
