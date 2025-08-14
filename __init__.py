
bl_info = {
    "name": "Sneaker Panel Pro",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (4, 4, 0),
    "location": "View3D > Sidebar > Sneaker Panel",
    "description": "Modular plugin for drawing and projecting sneaker panels",
    "category": "Object",
    "doc_url": "",  
    "tracker_url": "", 
    "warning": "", 
}

import bpy

from . import prefs  
from . import state  
from . import operators, properties, ui
from .utils import icons  

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

        # Load custom icons
        icons.load_icons()

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

        # Unload custom icons
        icons.unload_icons()

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
