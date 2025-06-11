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
        row_bezier.label(text="Bezier to NURBS Surface", icon='SURFACE_NURBS')
        
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
        # Include UI elements from bezier_surface_panel.py
        pass  # Placeholder for actual UI elements

    def draw_boundary_workflow(self, layout, context):
        # Include UI elements from boundary_mesh_panel.py
        pass  # Placeholder for actual UI elements

# Registration
classes = [OBJECT_PT_SurfaceWorkflow]

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)

if __name__ == "__main__":
    register()