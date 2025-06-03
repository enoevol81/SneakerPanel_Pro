# File: __init__.py

bl_info = {
    "name": "Sneaker Panel Pro",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (4, 4, 0),
    "location": "View3D > Sidebar > Sneaker Panel",
    "description": "Modular plugin for drawing and projecting sneaker panels",
    "category": "Object",
}

import bpy
from . import properties
from . import operators
from . import ui

def register():
    # Register properties first
    properties.register()
    
    # Register operators
    operators.register()
    
    # Register UI components
    ui.register()

def unregister():
    # Unregister UI components
    ui.unregister()
    
    # Unregister operators
    operators.unregister()
    
    # Unregister properties last
    properties.unregister()
