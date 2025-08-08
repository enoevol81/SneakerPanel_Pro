"""
SneakerPanel Pro - Blender Addon for Sneaker Panel Design

This addon provides tools for creating, editing, and projecting 2D panels
onto 3D shoe models. It includes utilities for drawing with Grease Pencil,
converting to curves and meshes, and projecting panels onto 3D surfaces.

Usage:
    1. Install the addon through Blender's addon preferences
    2. Access tools in the 3D View sidebar under "Sneaker Panel"
    3. Follow the workflow from drawing to projection
"""

bl_info = {
    "name": "Sneaker Panel Pro",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (4, 4, 0),
    "location": "View3D > Sidebar > Sneaker Panel",
    "description": "Modular plugin for drawing and projecting sneaker panels",
    "category": "Object",
    "doc_url": "",  # Add documentation URL when available
    "tracker_url": "",  # Add issue tracker URL when available
    "warning": "",  # Add any compatibility warnings if needed
}

import bpy
from . import properties
from . import operators
from . import ui
from . import prefs  # Import preferences module
from . import state  # Import state module

# List of all classes for registration
classes = []

def register():
    """Register all addon components."""
    try:
        # Register preferences first
        prefs.register()
        
        # Register state
        state.register()
        
        # Register properties
        properties.register()
        
        # Register operators
        operators.register()
        
        # Register UI components
        ui.register()
        
        # Register any classes defined directly in this file
        for cls in classes:
            bpy.utils.register_class(cls)
            
        print(f"SneakerPanel Pro: Successfully registered addon")
    except Exception as e:
        print(f"SneakerPanel Pro: Error during registration: {e}")
        raise

def unregister():
    """Unregister all addon components."""
    try:
        # Unregister any classes defined directly in this file
        for cls in reversed(classes):
            bpy.utils.unregister_class(cls)
            
        # Unregister UI components
        ui.unregister()
        
        # Unregister operators
        operators.unregister()
        
        # Unregister properties
        properties.unregister()

        # Unregister state
        state.unregister()
        
        # Unregister preferences last
        prefs.unregister()
        
        
        print(f"SneakerPanel Pro: Successfully unregistered addon")
    except Exception as e:
        print(f"SneakerPanel Pro: Error during unregistration: {e}")
        raise

# This allows running the script directly from Blender's text editor
if __name__ == "__main__":
    register()
