import bpy

class OBJECT_PT_SneakerPanelProMain(bpy.types.Panel):
    bl_label = "Sneaker Panel Pro"
    bl_idname = "OBJECT_PT_sneaker_panel_pro_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sneaker Panel'
    
    def draw(self, context):
        layout = self.layout
        
        # Shell UV Generation Section
        box = layout.box()
        row = box.row()
        row.label(text="Generate Shell UV", icon="OUTLINER_OB_LIGHTPROBE")
        
        box.label(text="** First Mark Seams At Heel And Boundary Edges**")
        
        # Unwrap Shell button
        box.operator("object.unwrap_shell", text="Unwrap Shell", icon="MOD_UVPROJECT")
        
        # Define Toe button
        box.operator("object.define_toe", text="Define Toe", icon="CURVE_PATH")
        
        # Orient UV Island button
        box.operator("object.orient_uv_island", text="Orient UV Island", icon="ORIENTATION_LOCAL")
        
        # Panel Settings Section
        box = layout.box()
        box.label(text="Panel Settings", icon="SETTINGS")
        
        row = box.row()
        row.label(text="Panel Number:")
        row.prop(context.scene, "spp_panel_count", text="")
        
        row = box.row()
        row.label(text="Panel Name:")
        row.prop(context.scene, "spp_panel_name", text="")
        
        box.prop_search(context.scene, "spp_shell_object", bpy.data, "objects", text="Shell Object")

        # Common Panel Creation Tools Section
        box = layout.box()
        box.label(text="1. Draw Panel Using Grease Pencil", icon="GREASEPENCIL")
        box.operator("object.add_gp_draw", text="Add Grease Pencil Item", icon='OUTLINER_OB_GREASEPENCIL')
        box.prop(context.scene, "spp_use_stabilizer", text="Use Stabilizer")
        if context.scene.spp_use_stabilizer:
            box.prop(context.scene, "spp_stabilizer_radius", text="Stabilizer Radius")
            box.prop(context.scene, "spp_stabilizer_strength_ui", text="Stabilizer Strength")

        box = layout.box()
        box.label(text="2. Convert Grease Pencil to Curve - Edit", icon='OUTLINER_OB_CURVE')
        box.operator("object.gp_to_curve", text="Create Curve", icon='IPO_BEZIER')
        box.label(text="2a. Optional - Decimate Curve")
        box.prop(context.scene, "spp_decimate_ratio", text="Ratio")
        box.operator("object.decimate_curve", text="Decimate Curve", icon='MOD_DECIM')
     
# Registration
classes = [OBJECT_PT_SneakerPanelProMain]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
