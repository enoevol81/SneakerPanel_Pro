import bpy

class OBJECT_PT_BezierToPanel(bpy.types.Panel):
    bl_label = "Module 1 - Bezier to Panel"
    bl_idname = "OBJECT_PT_bezier_to_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sneaker Panel'
    bl_parent_id = "OBJECT_PT_sneaker_panel_pro_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        self.draw_grease_pencil_section(layout, context)
        self.draw_conversion_section(layout, context)
        self.draw_mesh_edit_section(layout, context)
        self.draw_flatten_section(layout, context)
        self.draw_projection_section(layout, context)
        self.draw_finalize_section(layout)

    def draw_grease_pencil_section(self, layout, context):
        box = layout.box()
        box.label(text="1. Draw Panel Using Grease Pencil", icon="GREASEPENCIL")
        box.prop_search(context.scene, "spp_shell_object", bpy.data, "objects", text="Shell Object")
        
        # Panel number and name
        row = box.row()
        row.label(text="Panel Number:")
        row.prop(context.scene, "spp_panel_count", text="")
        
        row = box.row()
        row.label(text="Panel Name:")
        row.prop(context.scene, "spp_panel_name", text="")
        
        box.operator("object.add_gp_draw", text="Add Grease Pencil Item", icon='GREASEPENCIL')
        box.prop(context.scene, "spp_use_stabilizer", text="Use Stabilizer")
        if context.scene.spp_use_stabilizer:
            box.prop(context.scene, "spp_stabilizer_radius", text="Stabilizer Radius")
            box.prop(context.scene, "spp_stabilizer_factor", text="Stabilizer Factor")

    def draw_conversion_section(self, layout, context):
        box = layout.box()
        box.label(text="2. Convert Grease Pencil to Curve - Edit", icon='OUTLINER_OB_CURVE')
        box.operator("object.gp_to_curve", text="Create Curve", icon='OUTLINER_OB_CURVE')
        box.label(text="-- 2a. Optional - Decimate Curve --")
        box.prop(context.scene, "spp_decimate_ratio", text="Ratio")
        box.operator("object.decimate_curve", text="Decimate Curve", icon='MOD_DECIM')
        box.separator()
        box.label(text="2b. Bezier to Surface:")
        box.operator("curvetools.convert_bezier_to_surface", text="Convert Bezier to Surface", icon='SURFACE_DATA')

    def draw_mesh_edit_section(self, layout, context):
        box = layout.box()
        box.label(text="3. Mesh Editing", icon='MESH_DATA')
        box.operator("object.convert_to_mesh", text="Convert to Mesh", icon='MESH_DATA')
        box.operator("object.smooth_vertices", text="Smooth Vertices", icon='MOD_SMOOTH')
        box.prop(context.scene, "spp_dissolve_angle", text="Dissolve Angle")
        box.operator("object.reduce_verts", text="Reduce Vertices", icon='MOD_DECIM')

    def draw_flatten_section(self, layout, context):
        box = layout.box()
        box.label(text="4. Flatten Panel", icon='MOD_UVPROJECT')
        box.operator("object.bezier_to_panel", text="Flatten Panel (WIP)", icon='MOD_UVPROJECT')

    def draw_projection_section(self, layout, context):
        box = layout.box()
        box.label(text="5. Project Back to Surface", icon='MOD_SHRINKWRAP')
        # Placeholder for future projection operators

    def draw_finalize_section(self, layout):
        box = layout.box()
        box.label(text="6. Finalize Panel", icon='CHECKMARK')
        # Placeholder for future finalization operators

# Registration
classes = [OBJECT_PT_BezierToPanel]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
