import bpy

class OBJECT_PT_SurfaceWorkflow(bpy.types.Panel):
    """Surface Workflow Panel.
    
    This panel nests the Bezier to NURBS Surface and Boundary Mesh to Grid Fill workflows:
    1. Bezier to NURBS Surface
    2. Boundary Mesh to Grid Fill
    """
    bl_label = "Surface Workflow"
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
        row_bezier.prop(scene, "spp_bezier_workflow_expanded", 
                        icon="TRIA_DOWN" if scene.spp_bezier_workflow_expanded else "TRIA_RIGHT",
                        icon_only=True, emboss=True)
        row_bezier.label(text="Bezier to NURBS Surface", icon='SURFACE_NSURFACE')
        
        if scene.spp_bezier_workflow_expanded:
            self.draw_bezier_workflow(box_bezier, context)

        # Boundary Mesh to Grid Fill Workflow
        box_boundary = layout.box()
        row_boundary = box_boundary.row()
        row_boundary.prop(scene, "spp_boundary_workflow_expanded", 
                          icon="TRIA_DOWN" if scene.spp_boundary_workflow_expanded else "TRIA_RIGHT",
                          icon_only=True, emboss=True)
        row_boundary.label(text="Boundary Mesh to Grid Fill", icon='MESH_GRID')
        
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
        box.label(text="3. Convert Curve to Mesh - Edit", icon='OUTLINER_OB_MESH')
        box.operator("object.convert_to_mesh", text="Convert to Mesh", icon='MESH_DATA')
        
        # Show vertex count if we have a mesh
        obj = context.active_object
        vert_count = 0  # Initialize with default value
        if obj and obj.type == 'MESH':
            vert_count = len(obj.data.vertices)
        box.label(text="3a. Optional - Smooth")
        box.prop(context.scene, "spp_smooth_factor", text="Smooth Factor")
        box.operator("object.smooth_vertices", text="Apply Smoothing", icon='MOD_SMOOTH')
        box.label(text="3b. Optional - Reduce Verts")
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
    
    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class
    
    # Unregister scene properties
    del bpy.types.Scene.spp_bezier_workflow_expanded
    del bpy.types.Scene.spp_boundary_workflow_expanded
    
    for cls in classes:
        unregister_class(cls)

if __name__ == "__main__":
    register()