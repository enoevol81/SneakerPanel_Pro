"""Bezier to Panel workflow UI panel for the Sneaker Panel Pro addon.

This module defines the panel that provides a workflow for creating panels
from Bezier curves, including conversion to NURBS surfaces and mesh generation.
"""

import bpy
from ..operators.surface_resolution import update_active_surface_resolution


class OBJECT_PT_BezierToPanel(bpy.types.Panel):
    """Bezier to Panel workflow panel.
    
    This panel provides a step-by-step workflow for creating panels from Bezier curves:
    1. Drawing with Grease Pencil (with optional stabilizer settings)
    2. Converting Grease Pencil to Bezier curves (with optional decimation)
    3. Converting Bezier curves to NURBS surfaces with configurable resolution
    4. Converting surfaces to mesh with optional settings
    """
    bl_label = "Bezier to Panel"
    bl_idname = "OBJECT_PT_bezier_to_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sneaker Panel'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        self.draw_grease_pencil_section(layout, scene)
        self.draw_conversion_section(layout, scene)

    def draw_grease_pencil_section(self, layout, scene):
        box = layout.box()
        box.label(text="1. Draw Panel Using Grease Pencil", icon="GREASEPENCIL")
        box.operator("object.add_gp_draw", text="Add Grease Pencil", icon='ADD')
        box.prop(scene, "spp_use_stabilizer", text="Use Stabilizer")
        if scene.spp_use_stabilizer:
            box.prop(scene, "spp_stabilizer_radius", text="Stabilizer Radius")
            box.prop(scene, "spp_stabilizer_factor", text="Stabilizer Factor")

    def draw_conversion_section(self, layout, scene):
        box = layout.box()
        box.label(text="2.Grease Pencil to Bezier Curve", icon='OUTLINER_OB_CURVE')
        box.operator("object.gp_to_curve", text="Create Curve", icon='IPO_BEZIER')
        
        box = layout.box()
        box.label(text="-- 2a. Optional - Decimate Curve --")
        box.prop(scene, "spp_decimate_ratio", text="Ratio")
        box.operator("object.decimate_curve", text="Decimate Curve", icon='MOD_DECIM')
        
        box = layout.box()
        box.label(text="3. Bezier to NURBS Surface", icon='SURFACE_NSURFACE')
        
        # Operator properties for the Bezier to Surface conversion
        op_bs = box.operator("spp.convert_bezier_to_surface", text="Convert Bezier to Surface", icon='SURFACE_DATA')
        op_bs.center = scene.spp_bezier_center 
        op_bs.Resolution_U = scene.spp_resolution_u
        op_bs.Resolution_V = scene.spp_resolution_v
        
        # Live Surface Editing Section
        live_edit_box = box.box() 
        live_edit_box.label(text="Live Surface Editing:")
        live_edit_box.prop(scene, "spp_show_surface_resolution_controls", text="Advanced: Edit Resolution")

        if scene.spp_show_surface_resolution_controls:
            res_controls_box = live_edit_box.box() 
            row = res_controls_box.row(align=True)
            row.prop(scene, "spp_resolution_u", text="Resolution U")
            row.prop(scene, "spp_resolution_v", text="Resolution V")
        
        # Surface to Mesh conversion section
        box = layout.box()
        box.label(text="4. Surface to Mesh", icon='MESH_GRID')
        box.prop(scene, "spp_preserve_surface", text="Preserve Surface")
        box.prop(scene, "spp_shade_smooth", text="Smooth Shading")
        box.operator("object.convert", text="Convert Surface to Mesh", icon='MESH_GRID').target = 'MESH'

# Registration
classes = [OBJECT_PT_BezierToPanel]

def register():
    # Register scene properties
    bpy.types.Scene.spp_bezier_center = bpy.props.BoolProperty(
        name="Center",
        description="Consider center points when creating the surface",
        default=False
    )
    
    bpy.types.Scene.spp_resolution_u = bpy.props.IntProperty(
        name="Resolution U",
        description="Live-edit surface resolution in the U direction. Also used as initial U-resolution for new surfaces.",
        default=4,
        min=1,
        soft_max=64,
        update=update_active_surface_resolution
    )
    
    bpy.types.Scene.spp_resolution_v = bpy.props.IntProperty(
        name="Resolution V",
        description="Live-edit surface resolution in the V direction. Also used as initial V-resolution for new surfaces.",
        default=4,
        min=1,
        soft_max=64,
        update=update_active_surface_resolution
    )
    
    bpy.types.Scene.spp_show_surface_resolution_controls = bpy.props.BoolProperty(
        name="Edit Surface Resolution",
        description="Show controls to edit the resolution of the active NURBS surface",
        default=False 
    )
    
    bpy.types.Scene.spp_preserve_surface = bpy.props.BoolProperty(
        name="Preserve Surface",
        description="Keep the NURBS surface after converting to mesh",
        default=True
    )
    
    bpy.types.Scene.spp_shade_smooth = bpy.props.BoolProperty(
        name="Smooth Shading",
        description="Apply smooth shading to the converted mesh",
        default=True
    )
    
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    # Unregister scene properties
    del bpy.types.Scene.spp_bezier_center
    del bpy.types.Scene.spp_resolution_u
    del bpy.types.Scene.spp_resolution_v
    del bpy.types.Scene.spp_show_surface_resolution_controls
    del bpy.types.Scene.spp_preserve_surface
    del bpy.types.Scene.spp_shade_smooth
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()