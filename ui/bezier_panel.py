import bpy

class OBJECT_PT_BezierToPanel(bpy.types.Panel):
    bl_label = "Bezier to Panel"
    bl_idname = "OBJECT_PT_bezier_to_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sneaker Panel'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        self.draw_grease_pencil_section(layout, context)
        self.draw_conversion_section(layout, context)


    def draw_grease_pencil_section(self, layout, context):
        box = layout.box()
        box.label(text="1. Draw Panel Using Grease Pencil", icon="GREASEPENCIL")

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
        box = layout.box()
        box.label(text="3. Convert Bezier to Surface - Edit", icon='OUTLINER_OB_CURVE')
        box.operator("curvetools.convert_bezier_to_surface", text="Convert Bezier to Surface", icon='SURFACE_DATA')


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
