# File: SneakerPanel_Pro/ui/shell_pattern_panel.py

import bpy

class OBJECT_PT_ShellPatternToOverlay(bpy.types.Panel):
    bl_label = "Shell Pattern To Overlay"
    bl_idname = "OBJECT_PT_shell_pattern_to_overlay"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sneaker Panel' 
    bl_order = 2 

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        info_box = layout.box()
        info_box.label(text="Workflow:", icon='INFO')
        info_box.label(text="1. Run 'Generate UV Flat'.")
        info_box.label(text="2. Draw design with GP, convert to Curve.")
        info_box.label(text="3. With Curve active, 'Sample Curve to Polyline'.")
        info_box.label(text="4. With outline active, 'Create Quad Panel Border'.")
        info_box.label(text="5. (Next) Fill border and project to shell.")

        box_uv_to_mesh = layout.box()
        box_uv_to_mesh.label(text="Step 1: Generate UV Flat", icon='UV')
        box_uv_to_mesh.operator("object.uv_to_mesh", text="Generate UV Flat & Prep Draw", icon='MESH_PLANE')

        box_sample = layout.box()
        box_sample.label(text="Step 2: Sample Curve to Polyline", icon='CURVE_DATA')
        
        if hasattr(scene, "spp_sampler_fidelity"):
            col_sample = box_sample.column(align=True)
            col_sample.prop(scene, "spp_sampler_fidelity", text="Boundary Samples")
            col_sample.operator("curve.sample_to_polyline", text="Sample Curve to Polyline")
        else:
            box_sample.label(text="Error: spp_sampler_fidelity not registered.", icon='ERROR')

        box_create_border = layout.box()
        box_create_border.label(text="Step 3: Create Quad Panel Border", icon='MESH_GRID')
        
        op_quad_border = box_create_border.operator("mesh.create_quad_panel_from_outline", text="Create Quad Border from Outline")
        props_col = box_create_border.column(align=True)
        props_col.prop(op_quad_border, "inset_thickness")
        props_col.prop(op_quad_border, "keep_original_outline")
        
        box_project = layout.box()
        box_project.label(text="Step 4 & 5: Fill and Project", icon='MOD_SHRINKWRAP')
        box_project.label(text="(Operators for these steps to be built)")

classes = [OBJECT_PT_ShellPatternToOverlay]
def register():
    for cls in classes: bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
