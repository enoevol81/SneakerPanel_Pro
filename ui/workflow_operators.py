"""Shared operators for workflow panels in the Sneaker Panel Pro addon.

This module contains operators that are used by multiple UI panels
to provide consistent behavior across the addon.
"""

import bpy

# Custom operator to toggle one workflow and close the other
class WM_OT_context_toggle_workflow(bpy.types.Operator):
    """Toggle a workflow property and close another workflow if needed"""
    bl_idname = "wm.context_toggle_workflow"
    bl_label = "Toggle Workflow"
    bl_options = {'INTERNAL'}
    
    toggle_prop: bpy.props.StringProperty(
        name="Toggle Property",
        description="The property to toggle"
    )
    
    other_prop: bpy.props.StringProperty(
        name="Other Property",
        description="The other property to set to False when this one is toggled on"
    )
    
    def execute(self, context):
        # Get the current value of the property to toggle
        current_value = getattr(context.scene, self.toggle_prop)
        
        # Toggle the property
        setattr(context.scene, self.toggle_prop, not current_value)
        
        # If we're turning this one on, turn the other one off
        if not current_value:  # We're toggling from False to True
            setattr(context.scene, self.other_prop, False)
            
        return {'FINISHED'}

# Registration
classes = [WM_OT_context_toggle_workflow]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
