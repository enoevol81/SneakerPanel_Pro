"""UV Workflow UI panel for the Sneaker Panel Pro addon.

This module defines the panel that provides tools for generating 2D panels from UV space,
including UV to mesh conversion and shell UV to panel projection workflows.
"""

import bpy
from bpy.types import Panel


# Properties for collapsible sections
def register_properties():
    bpy.types.Scene.spp_workflow_a_expanded = bpy.props.BoolProperty(
        name="Expand Workflow A",
        description="Expand or collapse Workflow A section",
        default=True
    )
    bpy.types.Scene.spp_workflow_b_expanded = bpy.props.BoolProperty(
        name="Expand Workflow B",
        description="Expand or collapse Workflow B section",
        default=True
    )

def unregister_properties():
    del bpy.types.Scene.spp_workflow_a_expanded
    del bpy.types.Scene.spp_workflow_b_expanded

class OBJECT_PT_UVWorkflow(Panel):
    """UV Workflow panel.
    
    This panel provides tools for generating 2D panels from UV space with two workflow options:
    - Workflow A: UV to mesh, Grease Pencil drawing, curve conversion, and shell UV to panel projection
    - Workflow B: UV to mesh, Grease Pencil drawing, curve conversion, sampling to polyline, and quad border creation
    
    Both workflows support panel refinement options including grid fill span and subdivision.
    """
    bl_label = "UV Workflow"
    bl_idname = "OBJECT_PT_uv_workflow"
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

        # Workflow A - Collapsible section
        box_workflow_a = layout.box()
        row = box_workflow_a.row()
        # Custom operator to handle both toggling this workflow and closing the other
        op_workflow_a = row.operator("wm.context_toggle_workflow", text="", 
                 icon="TRIA_DOWN" if scene.spp_workflow_a_expanded else "TRIA_RIGHT",
                 emboss=True)
        op_workflow_a.toggle_prop = "spp_workflow_a_expanded"
        op_workflow_a.other_prop = "spp_workflow_b_expanded"
        row.label(text="Workflow A", icon='INFO')
        
        # Only show content if expanded
        if scene.spp_workflow_a_expanded:
            col = box_workflow_a.column(align=True)
            col.label(text="2. Use Grease Pencil Item to draw your design.")
            col.label(text="3. Convert to Curve / Decimate (Fewer Control Points Preferred)")
            col.label(text="4. Refine Curve (Edit Mode) - Subdivide Spans in Regions of Higher Tension.")
            
            box = box_workflow_a.box()
            box.label(text=" Step 5. Shell UV to Panel:", icon='MODIFIER')
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

        # Workflow B - Collapsible section
        box_workflow_b = layout.box()
        row = box_workflow_b.row()
        # Custom operator to handle both toggling this workflow and closing the other
        op_workflow_b = row.operator("wm.context_toggle_workflow", text="", 
                 icon="TRIA_DOWN" if scene.spp_workflow_b_expanded else "TRIA_RIGHT",
                 emboss=True)
        op_workflow_b.toggle_prop = "spp_workflow_b_expanded"
        op_workflow_b.other_prop = "spp_workflow_a_expanded"
        row.label(text="Workflow B", icon='INFO')
        
        # Only show content if expanded
        if scene.spp_workflow_b_expanded:
            col = box_workflow_b.column(align=True)
            col.label(text="2. Use Grease Pencil Item to draw your design.")
            col.label(text="3. Convert to Curve - Decimate (Fewer Control Points Preferred)")
            col.label(text="4. Refine Curve (Edit Mode).")

            box_sample = box_workflow_b.box()
            box_sample.label(text="Step 5: Sample Curve to Polyline", icon='CURVE_DATA')
            if hasattr(scene, "spp_sampler_fidelity"):
                col_sample = box_sample.column(align=True)
                col_sample.prop(scene, "spp_sampler_fidelity", text="Boundary Samples")
                col_sample.operator("curve.sample_to_polyline", text="Sample Curve to Polyline")

            box_create_border = box_workflow_b.box()
            box_create_border.label(text="Step 6: Create Quad Panel Border", icon='MESH_GRID')
            op_quad_border = box_create_border.operator("mesh.create_quad_panel_from_outline", text="Create Quad Border from Outline")
            props_col_border = box_create_border.column(align=True)
            
        
            box_fill = box_workflow_b.box()
            box_fill.label(text="Step 7: Fill Border with Grid", icon='FILE_NEW')            
            op_fill = box_fill.operator("mesh.fill_border_grid", text="Fill Panel Border")
            props_col_fill = box_fill.column(align=True)
            
            box_relax = box_workflow_b.box()
            box_relax.label(text="Step 8: Relax Loops & Project", icon='MOD_SMOOTH')
            row_proj = box_relax.row()
            row_proj.operator("mesh.overlay_panel_onto_shell", text="Project 2D Panel to 3D Shell", icon='UV_DATA')


# Import the shared operator from workflow_operators
from . import workflow_operators

# Registration
classes = [OBJECT_PT_UVWorkflow]
def register():
    register_properties()
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    unregister_properties()
