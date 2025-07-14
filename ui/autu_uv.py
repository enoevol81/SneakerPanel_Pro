import bpy


class OBJECT_PT_autu_uv(bpy.types.Panel):
    """Lace Generator panel for Sneaker Panel Pro addon.
    
    This panel provides a button to apply the lace geometry node group to selected curve objects.
    """
    bl_label = "Auto UV"
    bl_idname = "OBJECT_PT_sneaker_panel_pro_autu_uv"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sneaker Panel'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        obj = context.active_object
        
        uv_box = layout.box()
        uv_header = uv_box.row(align=True)
        
        # Panel header
        uv_header.label(text="Shell UV Generation", icon="OUTLINER_OB_LIGHTPROBE")
        
        # Add light bulb icon for tooltip
        tooltip_icon = 'LIGHT_SUN' if context.scene.spp_show_uv_gen_tooltip else 'LIGHT'
        uv_header.prop(context.scene, "spp_show_uv_gen_tooltip", text="", icon=tooltip_icon, emboss=False)
        
        # Show tooltip if enabled
        if context.scene.spp_show_uv_gen_tooltip:
            tip_box = uv_box.box()
            tip_box.alert = True  # Makes the box stand out with a different color
            tip_col = tip_box.column(align=True)
            tip_col.scale_y = 0.9  # Slightly smaller text
            tip_col.label(text="Shell UV Generation Tips:", icon='HELP')
            tip_col.label(text="• Mark seams at heel counter and toe areas")
            tip_col.label(text="• Use the Smart UV Project first if needed")
            tip_col.label(text="• Proper orientation ensures accurate panel creation")
            tip_col.label(text="• The toe definition helps with panel alignment")
            tip_col.label(text="• Orient UV island for consistent panel direction")
            tip_col.operator("wm.url_open", text="View UV Setup Tutorial", icon='URL').url = "https://example.com/uv-setup-tutorial"
        
        # Important note with better formatting
        note_col = uv_box.column(align=True)
        note_col.label(text="Before Starting: Mark Seams at Heel and Boundary Edges", icon="INFO")
        
        # Steps with better visual flow
        steps_col = uv_box.column(align=True)
        steps_col.scale_y = 1.1
        steps_col.operator("object.unwrap_shell", text="1. Unwrap Shell", icon="MOD_UVPROJECT")
        steps_col.operator("object.define_toe", text="2. Define Toe", icon="CURVE_PATH")
        steps_col.operator("object.orient_uv_island", text="3. Orient UV Island", icon="ORIENTATION_LOCAL")
        
        
        
# Registration
classes = [OBJECT_PT_autu_uv]

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
