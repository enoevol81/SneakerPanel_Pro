# File: SneakerPanel_Pro/ui/shell_pattern_panel.py

import bpy
from bpy.types import Panel

class OBJECT_PT_ShellPatternToOverlay(Panel):
    bl_label = "2D Panel Generation"
    bl_idname = "OBJECT_PT_shell_pattern_to_overlay"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sneaker Panel' 
    bl_order = 2 

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box = layout.box()
        box.label(text="1. UV to Mesh(Auto Add GpDraw):", icon='UV')
        row = box.row()
        row.operator("object.uv_to_mesh", icon='MESH_DATA')


        box_workflow_a = layout.box()
        col = box_workflow_a.column(align=True)
        col.label(text="Workflow A:", icon='INFO')
        col.label(text="1. Use Grease Pencil Item to draw your design.")
        col.label(text="2. Convert to Curve (Decimate_Less Control Points Easier to Edit)")
        col.label(text="3. With Border active, run 'Fill Border with Grid'.")
        col.label(text="4. (Next) Relax loops and project to shell.")

        box = box_workflow_a.box()
        box.label(text="2. Shell UV to Panel:", icon='MODIFIER')
        row = box.row()
        row.operator("object.shell_uv_to_panel", icon='MOD_SOLIDIFY')

        box_postprocess = box_workflow_a.box()
        box_postprocess.label(text="Panel Refinement Options:")
        box_postprocess.prop(context.scene, "spp_grid_fill_span", text="Initial Grid Fill Span")

        row = box_postprocess.row()
        row.prop(context.scene, "spp_panel_add_subdivision", text="Add Subdivision")
        row_sub = box_postprocess.row(align=True)
        row_sub.enabled = context.scene.spp_panel_add_subdivision
        row_sub.prop(context.scene, "spp_panel_subdivision_levels", text="Levels")
        row_sub.prop(context.scene, "spp_panel_conform_after_subdivision", text="Re-Conform")
        box_postprocess.prop(context.scene, "spp_panel_shade_smooth", text="Shade Smooth")

        box_workflow_b = layout.box()
        col = box_workflow_b.column(align=True)
        col.label(text="Workflow B:", icon='INFO')
        col.label(text="1. Add Grease Pencil Item and draw your design.")
        col.label(text="1. Use Grease Pencil Item to draw your design.")
        col.label(text="2. Convert to Curve (Decimate_Less Control Points Easier to Edit)")
        col.label(text="3. With Border active, run 'Fill Border with Grid'.")
        col.label(text="4. (Next) Relax loops and project to shell.")
        col.label(text="2. With Curve active, 'Sample to Polyline'.")
        col.label(text="3. With Outline active, 'Create Quad Border'.")
        col.label(text="4. With Border active, run 'Fill Border with Grid'.")
        col.label(text="5. (Next) Relax loops and project to shell.")

        box_sample = layout.box()
        box_sample.label(text="Step 1: Sample Curve to Polyline", icon='CURVE_DATA')
        if hasattr(scene, "spp_sampler_fidelity"):
            col_sample = box_sample.column(align=True)
            col_sample.prop(scene, "spp_sampler_fidelity", text="Boundary Samples")
            col_sample.operator("curve.sample_to_polyline", text="Sample Curve to Polyline")

        box_create_border = layout.box()
        box_create_border.label(text="Step 2: Create Quad Panel Border", icon='MESH_GRID')
        op_quad_border = box_create_border.operator("mesh.create_quad_panel_from_outline", text="Create Quad Border from Outline")
        props_col_border = box_create_border.column(align=True)
        props_col_border.prop(op_quad_border, "inset_thickness")
        props_col_border.prop(op_quad_border, "keep_original_outline")
        
        box_fill = layout.box()
        box_fill.label(text="Step 3: Fill Border with Grid", icon='FILE_NEW')
        
        op_fill = box_fill.operator("mesh.fill_border_grid", text="Fill Panel Border")
        props_col_fill = box_fill.column(align=True)

        box_relax = layout.box()
        box_relax.label(text="Step 4: Relax Loops & Project", icon='MOD_SMOOTH')
        box_relax.label(text="(Operators for these steps to be built)")


# Registration
classes = [OBJECT_PT_ShellPatternToOverlay]
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
