import bpy

def update_active_surface_resolution(self, context):
    """Update the resolution of the active NURBS surface.
    
    Args:
        self: The property owner.
        context: The Blender context.
    """
    obj = context.active_object
    if obj and obj.type == 'SURFACE':
        obj.data.resolution_u = context.scene.spp_resolution_u
        obj.data.resolution_v = context.scene.spp_resolution_v

class OBJECT_PT_SurfaceWorkflow(bpy.types.Panel):
    """Surface Workflow Panel.
    
    This panel nests the Bezier to NURBS Surface and Boundary Mesh to Grid Fill workflows:
    1. Bezier to NURBS Surface
    2. Boundary Mesh Surface
    """
    bl_label = "Surface Direct Workflow"
    bl_idname = "OBJECT_PT_surface_workflow"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sneaker Panel'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Bezier to NURBS Surface Workflow
        box_bezier = layout.box()
        row_bezier = box_bezier.row()
        # Custom operator to handle both toggling this workflow and closing the other
        op_bezier = row_bezier.operator("wm.context_toggle_workflow", text="", 
                        icon="TRIA_DOWN" if scene.spp_bezier_workflow_expanded else "TRIA_RIGHT",
                        emboss=True)
        op_bezier.toggle_prop = "spp_bezier_workflow_expanded"
        op_bezier.other_prop = "spp_boundary_workflow_expanded"
        row_bezier.label(text="Bezier to NURBS Surface", icon='SURFACE_NSURFACE')
        
        if scene.spp_bezier_workflow_expanded:
            self.draw_bezier_workflow(box_bezier, context)

        # Boundary Mesh to Grid Fill Workflow
        box_boundary = layout.box()
        row_boundary = box_boundary.row()
        # Custom operator to handle both toggling this workflow and closing the other
        op_boundary = row_boundary.operator("wm.context_toggle_workflow", text="", 
                          icon="TRIA_DOWN" if scene.spp_boundary_workflow_expanded else "TRIA_RIGHT",
                          emboss=True)
        op_boundary.toggle_prop = "spp_boundary_workflow_expanded"
        op_boundary.other_prop = "spp_bezier_workflow_expanded"
        row_boundary.label(text="Boundary Mesh to Surface", icon='MESH_GRID')
        
        if scene.spp_boundary_workflow_expanded:
            self.draw_boundary_workflow(box_boundary, context)

    def draw_bezier_workflow(self, layout, context):
        scene = context.scene
        
        # Surface Generation Section
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

    def draw_boundary_workflow(self, layout, context):
        # Mesh Edit Section
        box = layout.box()
        box.label(text="3. Convert Curve to Boundary Mesh", icon='OUTLINER_OB_MESH')
        box.operator("object.convert_to_mesh", text="Create Mesh", icon='MESH_DATA')
        
        # Show vertex count if we have a mesh
        obj = context.active_object
        vert_count = 0  # Initialize with default value
        if obj and obj.type == 'MESH':
            vert_count = len(obj.data.vertices)
        box.label(text="Mesh Edit")
        box.prop(context.scene, "spp_smooth_factor", text="Smooth Factor")
        box.operator("object.smooth_vertices", text="Apply Smoothing", icon='MOD_SMOOTH')
        box.label(text="Reduce Vertices")
        box.label(text=f"Current Vertex Count: {vert_count}", icon='VERTEXSEL')
        box.prop(context.scene, "spp_reduce_verts", text="Reduce Verts")
        if context.scene.spp_reduce_verts and obj and obj.type == 'MESH':
            row = box.row(align=True)
            op1 = row.operator("object.reduce_verts", text=f"20% ({int(vert_count * 0.8)} verts)")
            op1.factor = 0.2
            op2 = row.operator("object.reduce_verts", text=f"40% ({int(vert_count * 0.6)} verts)")
            op2.factor = 0.4
            row = box.row(align=True)
            op3 = row.operator("object.reduce_verts", text=f"60% ({int(vert_count * 0.4)} verts)")
            op3.factor = 0.6
            op4 = row.operator("object.reduce_verts", text=f"80% ({int(vert_count * 0.2)} verts)")
            op4.factor = 0.8

        # Grid Fill Section
        box = layout.box()
        box.label(text="4. Generate Grid Fill Mesh", icon='MESH_GRID')
        box.prop(context.scene, "spp_grid_fill_span", text="Grid Fill Span")
        box.operator("object.panel_generate", text="Generate Panel", icon='MOD_MESHDEFORM')

# Import the shared operator from workflow_operators
from . import workflow_operators

# Registration
classes = [OBJECT_PT_SurfaceWorkflow]

def register():
    from bpy.utils import register_class
    
    # Register scene properties for workflow expansion
    bpy.types.Scene.spp_bezier_workflow_expanded = bpy.props.BoolProperty(
        name="Bezier Workflow Expanded",
        description="Toggle to expand/collapse the Bezier to NURBS Surface workflow",
        default=False
    )
    
    bpy.types.Scene.spp_boundary_workflow_expanded = bpy.props.BoolProperty(
        name="Boundary Workflow Expanded",
        description="Toggle to expand/collapse the Boundary Mesh to Grid Fill workflow",
        default=False
    )
    
    # Register Bezier to Surface properties
    bpy.types.Scene.spp_bezier_center = bpy.props.BoolProperty(
        name="Center",
        description="Center the surface at the origin",
        default=True
    )
    
    bpy.types.Scene.spp_resolution_u = bpy.props.IntProperty(
        name="Resolution U",
        description="Resolution in the U direction",
        default=12,
        min=2,
        max=64,
        update=update_active_surface_resolution
    )
    
    bpy.types.Scene.spp_resolution_v = bpy.props.IntProperty(
        name="Resolution V",
        description="Resolution in the V direction",
        default=12,
        min=2,
        max=64,
        update=update_active_surface_resolution
    )
    
    bpy.types.Scene.spp_show_surface_resolution_controls = bpy.props.BoolProperty(
        name="Show Surface Resolution Controls",
        description="Show or hide the surface resolution controls",
        default=False
    )
    
    bpy.types.Scene.spp_preserve_surface = bpy.props.BoolProperty(
        name="Preserve Surface",
        description="Keep the original surface after conversion to mesh",
        default=True
    )
    
    bpy.types.Scene.spp_shade_smooth = bpy.props.BoolProperty(
        name="Smooth Shading",
        description="Apply smooth shading to the converted mesh",
        default=True
    )
    
    # Register Boundary Mesh properties
    bpy.types.Scene.spp_smooth_factor = bpy.props.FloatProperty(
        name="Smooth Factor",
        description="Smoothing factor for vertices",
        default=0.5,
        min=0.0,
        max=1.0
    )
    
    bpy.types.Scene.spp_reduce_verts = bpy.props.BoolProperty(
        name="Reduce Vertices",
        description="Enable vertex reduction options",
        default=False
    )
    
    bpy.types.Scene.spp_grid_fill_span = bpy.props.IntProperty(
        name="Grid Fill Span",
        description="Number of segments for grid fill",
        default=12,
        min=2,
        max=100
    )
    
    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class
    
    # Unregister scene properties
    del bpy.types.Scene.spp_bezier_workflow_expanded
    del bpy.types.Scene.spp_boundary_workflow_expanded
    
    # Unregister Bezier to Surface properties
    del bpy.types.Scene.spp_bezier_center
    del bpy.types.Scene.spp_resolution_u
    del bpy.types.Scene.spp_resolution_v
    del bpy.types.Scene.spp_show_surface_resolution_controls
    del bpy.types.Scene.spp_preserve_surface
    del bpy.types.Scene.spp_shade_smooth
    
    # Unregister Boundary Mesh properties
    del bpy.types.Scene.spp_smooth_factor
    del bpy.types.Scene.spp_reduce_verts
    del bpy.types.Scene.spp_grid_fill_span
    
    for cls in classes:
        unregister_class(cls)

if __name__ == "__main__":
    register()