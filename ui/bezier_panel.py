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

        box.operator("object.add_gp_draw", text="Add Grease Pencil Item", icon='OUTLINER_OB_GREASEPENCIL')
        box.prop(context.scene, "spp_use_stabilizer", text="Use Stabilizer")
        if context.scene.spp_use_stabilizer:
            box.prop(context.scene, "spp_stabilizer_radius", text="Stabilizer Radius")
            box.prop(context.scene, "spp_stabilizer_factor", text="Stabilizer Factor")

    def draw_conversion_section(self, layout, context):
        box = layout.box()
        box.label(text="2.Grease Pencil to Bezier Curve", icon='OUTLINER_OB_CURVE')
        box.operator("object.gp_to_curve", text="Create Curve", icon='IPO_BEZIER')
        
        box.label(text="-- 2a. Optional - Decimate Curve --")
        box.prop(context.scene, "spp_decimate_ratio", text="Ratio")
        box.operator("object.decimate_curve", text="Decimate Curve", icon='MOD_DECIM')
        
        box = layout.box()
        box.label(text="3. Convert Bezier to Surface - Edit", icon='OUTLINER_OB_SURFACE')
        
        # Bezier to Surface conversion options
        row = box.row()
        row.prop(context.scene, "spp_bezier_center", text="Center")
        
        row = box.row(align=True)
        row.prop(context.scene, "spp_resolution_u", text="Resolution U")
        row.prop(context.scene, "spp_resolution_v", text="Resolution V")
        
        # Bezier to Surface conversion button
        box.operator("spp.convert_bezier_to_surface", text="Convert Bezier to Surface", icon='SURFACE_DATA')
        
        # Surface to Mesh conversion section
        box = layout.box()
        box.label(text="4. Convert Surface to Mesh", icon='MESH_DATA')
        
        # Surface to Mesh conversion options
        box.prop(context.scene, "spp_preserve_surface", text="Preserve Surface")
        box.prop(context.scene, "spp_shade_smooth", text="Smooth Shading")
        
        # Surface to Mesh conversion button
        box.operator("object.convert", text="Convert Surface to Mesh", icon='MESH_GRID').target = 'MESH'


# Registration
classes = [OBJECT_PT_BezierToPanel]

def register():
    # Register scene properties for operator settings
    bpy.types.Scene.spp_bezier_center = bpy.props.BoolProperty(
        name="Center",
        description="Consider center points when creating the surface",
        default=False
    )
    
    bpy.types.Scene.spp_resolution_u = bpy.props.IntProperty(
        name="Resolution U",
        description="Surface resolution in the U direction",
        default=4,
        min=1,
        soft_max=64
    )
    
    bpy.types.Scene.spp_resolution_v = bpy.props.IntProperty(
        name="Resolution V",
        description="Surface resolution in the V direction",
        default=4,
        min=1,
        soft_max=64
    )
    
    bpy.types.Scene.spp_preserve_surface = bpy.props.BoolProperty(
        name="Preserve Surface",
        description="Keep the original NURBS surface after conversion",
        default=True
    )
    
    bpy.types.Scene.spp_shade_smooth = bpy.props.BoolProperty(
        name="Smooth Shading",
        description="Apply smooth shading to the resulting mesh",
        default=True
    )
    
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    # Unregister scene properties
    del bpy.types.Scene.spp_bezier_center
    del bpy.types.Scene.spp_resolution_u
    del bpy.types.Scene.spp_resolution_v
    del bpy.types.Scene.spp_preserve_surface
    del bpy.types.Scene.spp_shade_smooth
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
