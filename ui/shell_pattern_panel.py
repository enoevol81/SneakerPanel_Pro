import bpy

class OBJECT_PT_ShellPatternToOverlay(bpy.types.Panel):
    bl_label = "Shell Pattern To Overlay"
    bl_idname = "OBJECT_PT_shell_pattern_to_overlay"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sneaker Panel'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        
        # UV to Mesh section
        box = layout.box()
        box.label(text="1. UV to Mesh:", icon='UV')
        row = box.row()
        op = row.operator("object.uv_to_mesh", icon='MESH_DATA')
        
        # Shell UV to Panel section
        box = layout.box()
        box.label(text="2. Shell UV to Panel:", icon='MODIFIER')
        row = box.row()
        row.operator("object.shell_uv_to_panel", icon='MOD_SOLIDIFY')

        # In shell_pattern_panel.py, inside the draw method:
        # ... after row.operator("object.shell_uv_to_panel"...)

        box_postprocess = layout.box()
        box_postprocess.label(text="Panel Refinement Options:")
        box_postprocess.prop(context.scene, "spp_grid_fill_span", text="Initial Grid Fill Span") # Already exists, good to have here too

        row = box_postprocess.row()
        row.prop(context.scene, "spp_panel_add_subdivision", text="Add Subdivision")
        row_sub = box_postprocess.row(align=True)
        row_sub.enabled = context.scene.spp_panel_add_subdivision
        row_sub.prop(context.scene, "spp_panel_subdivision_levels", text="Levels")
        row_sub.prop(context.scene, "spp_panel_conform_after_subdivision", text="Re-Conform")
        box_postprocess.prop(context.scene, "spp_panel_shade_smooth", text="Shade Smooth")

# Registration
classes = [OBJECT_PT_ShellPatternToOverlay]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
