"""Boundary Mesh to Grid Fill workflow UI panel for the Sneaker Panel Pro addon.

This module defines the panel that provides tools for converting boundary meshes to grid-filled panels,
including mesh editing operations and grid fill generation.
"""

import bpy


class OBJECT_PT_BoundaryMeshToGridFill(bpy.types.Panel):
    """Boundary Mesh to Grid Fill workflow panel.
    
    This panel provides tools for converting boundary meshes to grid-filled panels:
    1. Converting curves to meshes
    2. Optional mesh smoothing and vertex reduction
    3. Generating grid-filled panels with configurable span settings
    """
    bl_label = "Boundary Mesh To Grid Based Fill"
    bl_idname = "OBJECT_PT_boundary_mesh_to_grid_fill"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sneaker Panel'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        self.draw_mesh_edit_section(layout, context)
        self.draw_grid_fill_section(layout, context)

    def draw_mesh_edit_section(self, layout, context):
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

    def draw_grid_fill_section(self, layout, context):
        box = layout.box()
        box.label(text="4. Generate Grid Fill Mesh", icon='MESH_GRID')
        box.prop(context.scene, "spp_grid_fill_span", text="Grid Fill Span")
        box.operator("object.panel_generate", text="Generate Panel", icon='MOD_MESHDEFORM')

# Registration
classes = [OBJECT_PT_BoundaryMeshToGridFill]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
