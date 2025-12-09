"""
Backward compatibility shim.

This module re-exports from app.config.settings for backward compatibility.
New code should import from app.config.settings directly.
"""
from app.config.settings import Settings, settings, get_settings

__all__ = ["Settings", "settings", "get_settings"]
