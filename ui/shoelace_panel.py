"""
Shoelace Panel UI module for SneakerPanel Pro addon.

This module provides the UI panel for generating and editing shoelaces
using bezier curves with customizable profiles and materials.
"""

import bpy
from bpy.types import Panel


class OBJECT_PT_ShoelacePanel(Panel):
    """Panel for shoelace generation and editing"""
    bl_label = "Shoelace Generator"
    bl_idname = "OBJECT_PT_shoelace_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sneaker Panel'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        
        # Shoelace Generation
        box = layout.box()
        row = box.row()
        row.scale_y = 1.2
        row.operator("spp.create_shoelace_geonodes", icon='CURVE_PATH')
        
        # Help and info
        info_box = layout.box()
        col = info_box.column(align=True)
        col.label(text="How to use:", icon='INFO')
        col.label(text="1. Select or create a bezier curve")
        col.label(text="2. Click 'Create Shoelace'")
        col.label(text="3. Adjust parameters as needed")
        
        # Material editing for existing shoelaces
        if context.active_object and context.active_object.type == 'MESH':
            obj = context.active_object
            if len(obj.modifiers) > 0 and any(mod.type == 'NODES' and 'Shoelace' in mod.name for mod in obj.modifiers):
                box = layout.box()
                box.label(text="Edit Shoelace", icon='MATERIAL')
                row = box.row()
                row.operator("spp.update_shoelace_material", icon='MATERIAL')
        
        # Quick curve tips
        tips_box = layout.box()
        tips_box.label(text="Tips:", icon='LIGHT_DATA')
        col = tips_box.column(align=True)
        col.label(text="• Use smooth bezier curves for best results")
        col.label(text="• Adjust curve tilt for custom orientation")
        col.label(text="• Try different profile shapes for variety")


# Registration
classes = (
    OBJECT_PT_ShoelacePanel,
)

def register():
    """Register the UI classes."""
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    """Unregister the UI classes."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
