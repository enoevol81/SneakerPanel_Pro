"""Finalize panel UI for the Sneaker Panel Pro addon.

This module defines the panel that provides tools for finalizing panels,
including solidification and other finishing operations.
"""

import bpy


class OBJECT_PT_SolidifyPanel(bpy.types.Panel):
    """Finalize panel for solidifying and finishing panels.
    
    This panel provides tools for finalizing panels with solidify operations:
    1. Adding solidify modifiers to panels
    2. Configuring solidify parameters (thickness, offset, etc.)
    3. Applying solidify modifiers
    """
    bl_label = "Thicken"
    bl_idname = "OBJECT_PT_solidify_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sneaker Panel'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        # Solidify button if no modifier exists
        solidify = obj.modifiers.get('Solidify')
        if not solidify:
            layout.operator("object.solidify_panel", text="Solidify", icon='MODIFIER')
            return

        # Parameters box
        box = layout.box()
        box.label(text="Solidify Parameters:", icon='MODIFIER')
        
        # Thickness
        row = box.row()
        row.prop(solidify, "thickness", text="Thickness")

        # Offset
        row = box.row()
        row.prop(solidify, "offset", text="Offset")

        # Additional useful parameters
        row = box.row()
        row.prop(solidify, "use_even_offset", text="Even Thickness")
        
        row = box.row()
        row.prop(solidify, "use_rim", text="Fill Rim")

        # Apply button
        layout.operator("object.apply_solidify", text="Finalize", icon='CHECKMARK')

# Registration
classes = [OBJECT_PT_SolidifyPanel]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
