"""Collection management utilities for SneakerPanel Pro addon.

This module provides functions for managing Blender collections for the SneakerPanel Pro addon,
including creating and organizing collections for panels and adding objects to them.
"""

import bpy

def get_sneaker_panels_collection():
    """
    Get or create the main 'Sneaker Panels' collection
    
    Returns:
        bpy.types.Collection: The main Sneaker Panels collection
    """
    # Check if collection already exists
    if "Sneaker Panels" in bpy.data.collections:
        return bpy.data.collections["Sneaker Panels"]
    
    # Create new collection
    main_collection = bpy.data.collections.new("Sneaker Panels")
    bpy.context.scene.collection.children.link(main_collection)
    return main_collection

def get_panel_collection(panel_number, panel_name=None):
    """
    Get or create a collection for a specific panel number with optional descriptive name
    
    Args:
        panel_number (int): The panel number
        panel_name (str, optional): Descriptive name for the panel
        
    Returns:
        bpy.types.Collection: The panel-specific collection
    """
    # Get main collection
    main_collection = get_sneaker_panels_collection()
    
    # Determine collection name
    if panel_name and panel_name.strip():
        # Use descriptive name with number suffix for uniqueness
        panel_collection_name = f"{panel_name}_{panel_number}"
    else:
        # Fallback to just number if no name provided
        panel_collection_name = f"Panel_{panel_number}"
    
    # Check if panel collection already exists
    if panel_collection_name in bpy.data.collections:
        return bpy.data.collections[panel_collection_name]
    
    # Create new panel collection
    panel_collection = bpy.data.collections.new(panel_collection_name)
    main_collection.children.link(panel_collection)
    return panel_collection

def add_object_to_panel_collection(obj, panel_number, panel_name=None):
    """
    Add an object to the appropriate panel collection
    
    Args:
        obj (bpy.types.Object): The object to add to the collection
        panel_number (int): The panel number
        panel_name (str, optional): Descriptive name for the panel
    """
    # Get panel collection
    panel_collection = get_panel_collection(panel_number, panel_name)
    
    # Remove from current collections
    for col in obj.users_collection:
        col.objects.unlink(obj)
    
    # Add to panel collection
    panel_collection.objects.link(obj)
