"""
Compatibility shim for Sneaker Panel Pro.

This module keeps the legacy import path `sneaker_panel_pro.operators.panel_generator`
working while delegating the implementation to `panel_generate.py`.

It also exposes no-op register()/unregister() so add-on loaders that iterate
modules and call `register()` won't fail.
"""

from .panel_generate import generate_panel  # re-export for legacy imports


def register():
    """No-op: kept for add-on loader compatibility."""
    # Nothing to register here; operator classes live in panel_generate.py
    return None


def unregister():
    """No-op: kept for add-on loader compatibility."""
    return None
