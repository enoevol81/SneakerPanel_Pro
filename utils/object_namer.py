"""Object naming utilities for SneakerPanel Pro addon.

This module provides functions for consistent naming of objects created by the addon,
ensuring proper sequential naming and descriptive prefixes.
"""

import bpy


def get_unique_name(base_name, panel_number):
    """Generate a unique name for an object with panel number suffix.
    
    Args:
        base_name (str): Base name for the object (e.g., 'GPDraw', 'Curve', 'PanelMesh')
        panel_number (int): Panel number to append as suffix
        
    Returns:
        str: Unique name with panel number suffix
    """
    return f"{base_name}_{panel_number}"


def rename_object(obj, base_name, panel_number):
    """Rename an object with consistent naming convention.
    
    Args:
        obj (bpy.types.Object): Object to rename
        base_name (str): Base name for the object
        panel_number (int): Panel number to append as suffix
        
    Returns:
        str: The new name assigned to the object
    """
    new_name = get_unique_name(base_name, panel_number)
    obj.name = new_name
    if obj.data:
        obj.data.name = new_name
    return new_name
