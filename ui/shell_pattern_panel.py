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

        box_workflow = layout.box()
        col = box_workflow.column(align=True)
        col.label(text="Workflow:", icon='INFO')
        col.label(text="1. Create a 2D Curve for your design.")
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
        else:
            box_sample.label(text="Error: spp_sampler_fidelity not registered.", icon='ERROR')

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
