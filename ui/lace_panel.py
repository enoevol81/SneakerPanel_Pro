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

    @classmethod
    def poll(cls, context):
        return bool(context.window_manager.spp_show_lace_gen)
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        obj = context.active_object
        
        # Check if object has a lace modifier
        has_lace_modifier = False
        for mod in obj.modifiers:
            if mod.type == 'NODES' and mod.name.startswith('Lace'):
                has_lace_modifier = True
                break
        
        # Main box
        main_box = layout.box()
        main_box.label(text="Lace Generator", icon='CURVE_DATA')
        
        if not has_lace_modifier:
            # Show apply button if no lace modifier exists
            main_box.operator("object.apply_lace_nodegroup", text="Apply Lace Geometry")
            return
        
        # Parameters section - only shown if the modifier exists
        # Profile type selection
        row = main_box.row()
        row.prop(scene, "spp_lace_profile", text="Profile")
        
        # Scale control
        row = main_box.row()
        row.prop(scene, "spp_lace_scale", text="Scale")
        
        # Resolution control
        row = main_box.row()
        row.prop(scene, "spp_lace_resample", text="Resolution")
        
        # Tilt control
        row = main_box.row()
        row.prop(scene, "spp_lace_tilt", text="Tilt")
        
        # Normal mode selection
        row = main_box.row()
        row.prop(scene, "spp_lace_normal_mode", text="Normal Mode")
        
        # Custom profile object - only show if profile type is Custom
        if scene.spp_lace_profile == '2':
            row = main_box.row()
            row.prop(scene, "spp_lace_custom_profile", text="Custom Profile")
        
        # Material assignment
        row = main_box.row()
        row.prop(scene, "spp_lace_material", text="Material")
        
        # Shade smooth toggle
        row = main_box.row()
        row.prop(scene, "spp_lace_shade_smooth", text="Shade Smooth")

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
