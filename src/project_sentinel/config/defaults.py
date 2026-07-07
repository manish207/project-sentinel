"""
Default configuration values.
"""

from pathlib import Path

PROJECT_NAME = "Project Sentinel"
VERSION = "0.1.0"

ROOT_DIR = Path.cwd()

DEFAULT_CONFIG_DIR = ROOT_DIR / "config"

DEFAULT_DATA_DIR = ROOT_DIR / "data"

DEFAULT_LOG_DIR = ROOT_DIR / "logs"

DEFAULT_PLUGIN_DIR = ROOT_DIR / "plugins"

DEFAULT_HOST = "127.0.0.1"

DEFAULT_PORT = 8080

DEFAULT_LOG_LEVEL = "INFO"

DEFAULT_OLLAMA_URL = "http://localhost:11434"

DEFAULT_DATABASE_URL = "sqlite+aiosqlite:///sentinel.db"
