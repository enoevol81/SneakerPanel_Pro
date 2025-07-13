"""Lace Generator panel for the Sneaker Panel Pro addon.

This module defines the panel that appears in the 3D View sidebar under the 'Sneaker Panel' category
for applying the shoelace nodegroup to curve objects.
"""

import bpy


class OBJECT_PT_SneakerPanelLace(bpy.types.Panel):
    """Lace Generator panel for Sneaker Panel Pro addon.
    
    This panel provides a button to apply the lace geometry node group to selected curve objects.
    """
    bl_label = "Lace Generator"
    bl_idname = "OBJECT_PT_sneaker_panel_pro_lace"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sneaker Panel'
    
    def draw(self, context):
        layout = self.layout
        
        # Only show button if a curve is selected
        if context.active_object and context.active_object.type == 'CURVE':
            layout.operator("object.apply_lace_nodegroup", text="Apply Lace Geometry")
        else:
            layout.label(text="Select a curve object")
            layout.label(text="to apply lace geometry")

# Registration
classes = [OBJECT_PT_SneakerPanelLace]

def register():
    # Register the panel class
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    # Unregister the panel class
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
