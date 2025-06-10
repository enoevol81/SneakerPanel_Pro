# File: SneakerPanel_Pro/ui/shell_pattern_panel.py
# This panel guides the user through the new multi-step quad panel creation process.

import bpy
from bpy.types import Panel

class OBJECT_PT_ShellPatternToOverlay(Panel):
    bl_label = "2D Panel Generation"
    bl_idname = "OBJECT_PT_shell_pattern_to_overlay"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sneaker Panel' # Your custom category
    bl_order = 2 

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # --- Instructions Box ---
        box_workflow = layout.box()
        col = box_workflow.column(align=True)
        col.label(text="Workflow:", icon='INFO')
        col.label(text="1. With Curve active, 'Sample to Polyline'.")
        col.label(text="2. With Outline active, 'Create Quad Border'.")
        col.label(text="3. With Border active, 'Fill Panel Border'.")
        col.label(text="4. (Next) Project final panel to 3D shell.")


        # --- Step 1: Sample Curve to Polyline ---
        box_sample = layout.box()
        box_sample.label(text="Step 1: Sample Curve to Polyline", icon='CURVE_DATA')
        
        # This section uses the 'spp_sampler_fidelity' scene property
        if hasattr(scene, "spp_sampler_fidelity"):
            col_sample = box_sample.column(align=True)
            col_sample.prop(scene, "spp_sampler_fidelity", text="Boundary Samples")
            # This calls the operator from sample_curve_to_polyline.py
            col_sample.operator("curve.sample_to_polyline", text="Sample Curve to Polyline")
        else:
            box_sample.label(text="Error: spp_sampler_fidelity not registered.", icon='ERROR')

        # --- Step 2: Create Quad Panel Border from Outline ---
        box_create_border = layout.box()
        box_create_border.label(text="Step 2: Create Quad Panel Border", icon='MESH_GRID')
        
        # This calls the operator from create_quad_border.py
        op_quad_border = box_create_border.operator("mesh.create_quad_panel_from_outline", text="Create Quad Border from Outline")
        props_col_border = box_create_border.column(align=True)
        props_col_border.prop(op_quad_border, "inset_thickness")
        props_col_border.prop(op_quad_border, "keep_original_outline")
        
        # --- Step 3: Fill Panel Border ---
        box_fill = layout.box()
        box_fill.label(text="Step 3: Fill Panel Border", icon='FILE_NEW')
        
        # This calls the operator from fill_quad_border.py
        op_fill = box_fill.operator("mesh.fill_quad_panel_border", text="Fill Panel Border")
        props_col_fill = box_fill.column(align=True)
        props_col_fill.prop(op_fill, "grid_fill_span")
        props_col_fill.prop(op_fill, "keep_original_border")

        # --- Step 4: Project to 3D Shell ---
        box_project = layout.box()
        box_project.label(text="Step 4: Project Panel to 3D Shell", icon='MOD_SHRINKWRAP')
        box_project.label(text="(Operator for this step to be built)")


# Registration
classes = [OBJECT_PT_ShellPatternToOverlay]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

