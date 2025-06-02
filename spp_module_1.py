import bpy
import bmesh
from mathutils.bvhtree import BVHTree
from mathutils import Vector

# Import utility modules
from .utils.panel_utils import update_stabilizer, update_stabilizer_ui, apply_surface_snap, reduce_mesh_verts, compute_curvature, create_flow_based_quads
from .utils.collections import get_sneaker_panels_collection, get_panel_collection, add_object_to_panel_collection

# Import operators - only for reference, not for registration
from .operators.add_gp_draw import OBJECT_OT_AddGPDraw
from .operators.gp_to_curve import OBJECT_OT_GPToCurve
from .operators.decimate_curve import OBJECT_OT_DecimateCurve
from .operators.convert_to_mesh import OBJECT_OT_ConvertToMesh
from .operators.smooth_vertices import OBJECT_OT_SmoothVertices
from .operators.reduce_verts import OBJECT_OT_ReduceVerts
from .operators.panel_generate import OBJECT_OT_PanelGenerate

# Import properties
from .properties import register_properties, unregister_properties


# ----------------------------------------------------
# PANELS
# ----------------------------------------------------

class OBJECT_PT_GPToPanelModule(bpy.types.Panel):
    bl_label = "Sneaker Panel Pro"
    bl_idname = "OBJECT_PT_gp_to_panel_module"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sneaker Panel'

    def draw(self, context):
        layout = self.layout
        self.draw_grease_pencil_section(layout, context)
        self.draw_conversion_section(layout, context)
        self.draw_mesh_edit_section(layout, context)
        self.draw_overlay_section(layout, context)

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
            box.prop(context.scene, "spp_stabilizer_strength_ui", text="Stabilizer Strength")

    def draw_conversion_section(self, layout, context):
        box = layout.box()
        box.label(text="2. Convert Grease Pencil to Curve - Edit", icon='OUTLINER_OB_CURVE')
        box.operator("object.gp_to_curve", text="Create Curve", icon='OUTLINER_OB_CURVE')
        box.label(text="-- 2a. Optional - Decimate Curve --")
        box.prop(context.scene, "spp_decimate_ratio", text="Ratio")
        box.operator("object.decimate_curve", text="Decimate Curve", icon='MOD_DECIM')

    def draw_mesh_edit_section(self, layout, context):
        box = layout.box()
        box.label(text="3. Convert Curve to Mesh - Edit", icon='OUTLINER_OB_MESH')
        box.operator("object.convert_to_mesh", text="Convert to Mesh", icon='OUTLINER_OB_MESH')
        
        # Show vertex count if we have a mesh
        obj = context.active_object
        vert_count = 0  # Initialize with default value
        if obj and obj.type == 'MESH':
            vert_count = len(obj.data.vertices)
        box.label(text="-- 3a. Optional - Smooth --")
        box.prop(context.scene, "spp_smooth_factor", text="Smooth Factor")
        box.operator("object.smooth_vertices", text="Apply Smoothing", icon='MOD_SMOOTH')
        box.label(text="-- 3b. Optional - Reduce Verts --")
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

    def draw_overlay_section(self, layout, context):
        box = layout.box()
        box.label(text="4. Select Divisions - Create Mesh", icon='MESH_GRID')
        box.prop(context.scene, "spp_grid_fill_span", text="Grid Fill Span")
        box.operator("object.flatten_panel_uv", text="Generate Overlay", icon='MOD_MESHDEFORM')



# ----------------------------------------------------
# REGISTRATION
# ----------------------------------------------------

# Only register the UI panel, not the operators (they're registered in their own modules)
classes = (
    OBJECT_PT_GPToPanelModule,
)


def register():
    # Only register the UI panel, properties are now handled in properties.py
    for cls in classes:
        bpy.utils.register_class(cls)



def unregister():
    # Only unregister the UI panel, properties are now handled in properties.py
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()