# File: SneakerPanel_Pro/ui/shell_pattern_panel.py
# This panel guides the user through the new two-step quad panel creation process.

import bpy
from bpy.types import Panel

class OBJECT_PT_ShellPatternToOverlay(Panel):
    bl_label = "Shell Pattern To Overlay"
    bl_idname = "OBJECT_PT_shell_pattern_to_overlay"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sneaker Panel' # Your custom category
    bl_order = 2 

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # --- Instructions Box ---
        info_box = layout.box()
        info_box.label(text="Workflow:", icon='INFO')
        info_box.label(text="1. Run 'Generate UV Flat'.")
        info_box.label(text="2. Draw design with GP, convert to Curve.")
        info_box.label(text="3. With Curve selected, run 'Sample Curve'.")
        info_box.label(text="4. With outline selected, run 'Create Quad Panel'.")

        # --- Section 1: Get UVs as a 2D Mesh (from original shell) ---
        box_uv_to_mesh = layout.box()
        box_uv_to_mesh.label(text="Step 1: Generate UV Flat & Prep Draw", icon='UV')
        col_uv = box_uv_to_mesh.column(align=True)
        # This operator creates the flat UV mesh and a Grease Pencil layer for drawing.
        op_uv_mesh = col_uv.operator("object.uv_to_mesh", text="Generate UV Flat", icon='MESH_PLANE')

        # --- Section 2: Sample Curve to Polyline ---
        box_sample = layout.box()
        box_sample.label(text="Step 2: Sample Curve to Polyline", icon='CURVE_DATA')
        
        # Check if the required property exists before drawing it
        if hasattr(scene, "spp_sampler_fidelity"):
            col_sample = box_sample.column(align=True)
            col_sample.prop(scene, "spp_sampler_fidelity", text="Boundary Samples")
            # This calls the operator from sample_curve_to_polyline.py
            col_sample.operator("curve.sample_to_polyline", text="Sample Curve to Polyline", icon='MESH_CIRCLE')
        else:
            box_sample.label(text="Error: spp_sampler_fidelity not registered.", icon='ERROR')

        # --- Section 3: Create Panel from Outline ---
        box_create = layout.box()
        box_create.label(text="Step 3: Create Quad Panel from Outline", icon='MESH_GRID')
        
        # This calls the operator from create_quad_panel_from_outline.py
        op_quad_panel = box_create.operator("mesh.create_quad_panel_from_outline", text="Create Quad Panel", icon='FILE_NEW')
        
        # Expose properties for the Create Quad Panel operator
        props_col = box_create.column(align=True)
        props_col.separator()
        props_col.prop(op_quad_panel, "inset_thickness")
        props_col.separator()
        props_col.label(text="Center Fill (Tris to Quads):")
        props_col.prop(op_quad_panel, "face_angle_limit")
        props_col.prop(op_quad_panel, "shape_angle_limit")
        props_col.separator()
        props_col.prop(op_quad_panel, "keep_original_outline")
        
        # --- Section 4: Project 2D Panel to 3D Shell ---
        box_project = layout.box()
        box_project.label(text="Step 4: Project Panel to 3D Shell", icon='MOD_SHRINKWRAP')
        box_project.label(text="(Operator for this step to be built)")
        # This is where the operator that takes the 2D quad panel and reprojects it would go.
        # Example: op_project = box_project.operator("object.project_2d_panel_to_shell")


# Registration
classes = [OBJECT_PT_ShellPatternToOverlay]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    # The spp_sampler_fidelity property should be registered in your properties.py file.

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    # The spp_sampler_fidelity property should be unregistered in your properties.py file.
