"""
Addon Preferences for SneakerPanel Pro.

This module defines the addon preferences class and related utility functions
for accessing preferences throughout the addon.
"""

import bpy


class SPPrefs(bpy.types.AddonPreferences):
    """Addon Preferences for SneakerPanel Pro.
    
    Stores global settings that persist across Blender sessions.
    """
    bl_idname = __package__
    
    # Global preference properties
    # Note: AddonPreferences doesn't support PointerProperty for data-blocks
    # Using StringProperty to store object name instead
    shell_object_name: bpy.props.StringProperty(
        name="Shell Object",
        description="Default shell object name to use for panel projection",
        default=""
    )

    def draw(self, context):
        """Draw the preferences panel UI.
        
        Args:
            context: Blender context
        """
        layout = self.layout
        layout.label(text="Global Settings")
        
        # Create a row for the shell object selection
        row = layout.row(align=True)
        row.prop_search(self, "shell_object_name", context.scene, "objects", text="Shell (Target Mesh)")
        
        # Add a button to set the current active object as shell
        if context.active_object and context.active_object.type == 'MESH':
            op = row.operator("wm.context_set_string", text="", icon='EYEDROPPER')
            op.data_path = "preferences.addons['" + __package__ + "'].preferences.shell_object_name"
            op.value = context.active_object.name


def get_shell_object():
    """Get the shell object from addon preferences.
    
    Returns:
        bpy.types.Object or None: The shell object if set, None otherwise
    """
    try:
        prefs = bpy.context.preferences.addons[__package__].preferences
        if prefs.shell_object_name:
            return bpy.data.objects.get(prefs.shell_object_name)
        return None
    except (KeyError, AttributeError):
        # Handle case where preferences aren't loaded or addon isn't registered
        return None


def register():
    """Register the addon preferences class."""
    bpy.utils.register_class(SPPrefs)


def unregister():
    """Unregister the addon preferences class."""
    bpy.utils.unregister_class(SPPrefs)


if __name__ == "__main__":
    register()
