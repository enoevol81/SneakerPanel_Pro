"""Icon management for Sneaker Panel Pro addon.

This module handles loading and managing custom icons using Blender's previews system.
"""

import os
import bpy
import bpy.utils.previews

# Global variable to store icon previews
preview_collections = {}

def load_icons():
    """Load custom icons for the addon."""
    # Create a new preview collection
    pcoll = bpy.utils.previews.new()
    
    # Path to the icons directory
    icons_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "operators", "icons")
    
    # Load the UV checker icon
    uv_checker_path = os.path.join(icons_dir, "uv_checker_32.png")
    if os.path.exists(uv_checker_path):
        pcoll.load("uv_checker", uv_checker_path, 'IMAGE')
    else:
        print(f"Warning: Icon not found at {uv_checker_path}")
    
    # Store the preview collection
    preview_collections["main"] = pcoll

def get_icon(icon_name):
    """Get an icon from the preview collection.
    
    Args:
        icon_name (str): Name of the icon to retrieve
        
    Returns:
        int: Icon ID for use in UI layouts, or 0 if not found
    """
    pcoll = preview_collections.get("main")
    if pcoll and icon_name in pcoll:
        return pcoll[icon_name].icon_id
    return 0

def unload_icons():
    """Unload all icon preview collections."""
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
