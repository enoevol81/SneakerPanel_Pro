"""
Surface resolution utility for SneakerPanel Pro.

This module provides functionality to update the resolution of NURBS surfaces
and curves in the 3D viewport. It contains a callback function that is triggered
when the resolution properties in the UI are changed.
"""

import bpy


def update_active_surface_resolution(scene_self, context):
    """Update resolution of active NURBS surface when UI values change.

    This function is called as a callback when the spp_resolution_u or
    spp_resolution_v properties are changed in the UI. It updates the
    resolution of the active NURBS surface or curve object accordingly.

    Args:
        scene_self: The scene containing the properties
        context: The current Blender context

    Returns:
        None
    """
    try:
        # Get the new resolution values from the scene properties
        new_resolution_u = getattr(scene_self, "spp_resolution_u", 12)
        new_resolution_v = getattr(scene_self, "spp_resolution_v", 12)

        # Get the active object
        active_obj = context.active_object
        if not active_obj:
            return

        # Check if the active object is a curve or surface with resolution properties
        if active_obj.type in {"CURVE", "SURFACE"} and hasattr(
            active_obj.data, "resolution_u"
        ):
            # Update the resolution
            curve_data = active_obj.data
            curve_data.resolution_u = new_resolution_u
            curve_data.resolution_v = new_resolution_v
            curve_data.update()
    except Exception as e:
        print(f"Error updating surface resolution: {str(e)}")


# --- Registration ---
def register():
    """Register the module.

    This function is called when the module is registered.
    Currently, it doesn't register any classes or properties.
    """
    pass


def unregister():
    """Unregister the module.

    This function is called when the module is unregistered.
    Currently, it doesn't unregister any classes or properties.
    """
    pass


if __name__ == "__main__":
    register()
