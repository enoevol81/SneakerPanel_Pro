"""UV Workflow UI panel for the Sneaker Panel Pro addon.

This module defines the panel that provides tools for generating 2D panels from UV space,
including UV to mesh conversion and shell UV to panel projection workflows.
"""

import bpy
from bpy.types import Panel


# Properties for collapsible sections and tooltips
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
    bpy.types.Scene.spp_show_workflow_a_tooltip = bpy.props.BoolProperty(
        name="Show Workflow A Tooltip",
        description="Show or hide the tooltip for Workflow A",
        default=False
    )
    bpy.types.Scene.spp_show_workflow_b_tooltip = bpy.props.BoolProperty(
        name="Show Workflow B Tooltip",
        description="Show or hide the tooltip for Workflow B",
        default=False
    )
    
    # UV Boundary Checker properties
    bpy.types.Scene.spp_uv_boundary_action = bpy.props.EnumProperty(
        name="Boundary Action",
        description="What to do with boundary violations",
        items=[
            ('CHECK', "Check Only", "Highlight violations for inspection"),
            ('FIX', "Fix Vertices", "Fix vertex violations only (preserves topology)"),
            ('INTERACTIVE', "Select for Manual Fix", "Select violations for manual editing (recommended for edges)")
        ],
        default='CHECK'
    )
    
    bpy.types.Scene.spp_uv_boundary_samples = bpy.props.IntProperty(
        name="Raycast Samples",
        description="Number of samples per edge for boundary checking",
        default=10,
        min=3,
        max=50
    )
    
    bpy.types.Scene.spp_uv_boundary_margin = bpy.props.FloatProperty(
        name="Boundary Margin",
        description="Safety margin from UV boundary (0.0-1.0)",
        default=0.01,
        min=0.0,
        max=0.1
    )
    
    bpy.types.Scene.spp_uv_boundary_status = bpy.props.EnumProperty(
        name="Boundary Status",
        description="Status of the last UV boundary check",
        items=[
            ('NONE', "Not Checked", "No boundary check has been performed"),
            ('PASS', "Pass", "No boundary violations found"),
            ('VIOLATIONS', "Violations Found", "Boundary violations detected"),
            ('ERROR', "Error", "Error occurred during boundary check")
        ],
        default='NONE'
    )

def unregister_properties():
    del bpy.types.Scene.spp_workflow_a_expanded
    del bpy.types.Scene.spp_workflow_b_expanded
    del bpy.types.Scene.spp_show_workflow_a_tooltip
    del bpy.types.Scene.spp_show_workflow_b_tooltip
    del bpy.types.Scene.spp_uv_boundary_action
    del bpy.types.Scene.spp_uv_boundary_samples
    del bpy.types.Scene.spp_uv_boundary_margin
    del bpy.types.Scene.spp_uv_boundary_status

class OBJECT_PT_UVWorkflow(Panel):
    """UV Workflow panel.
    
    This panel provides tools for generating 2D panels from UV space with two workflow options:
    - Workflow A: UV to mesh, Grease Pencil drawing, curve conversion, and shell UV to panel projection
    - Workflow B: UV to mesh, Grease Pencil drawing, curve conversion, sampling to polyline, and quad border creation
    
    Both workflows support panel refinement options including grid fill span and subdivision.
    """
    bl_label = "UV Workflow [2D]"
    bl_idname = "OBJECT_PT_uv_workflow"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sneaker Panel' 
    bl_order = 2 

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box = layout.box()
        box.label(text="UV to Mesh (Auto Add Grease Pencil Object):", icon='UV')
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
        row.label(text="UV Curve to Panel - Quick & Dirty", icon='UV_VERTEXSEL')
        
        # Only show content if expanded
        if scene.spp_workflow_a_expanded:
            intro_box = box_workflow_a.box()
            
            # Header row with info icon and light bulb toggle
            header_row = intro_box.row()
            header_row.label(text="Workflow Overview:", icon='INFO')
            
            # Add light bulb icon that toggles tooltip visibility
            tooltip_icon = 'LIGHT_SUN' if scene.spp_show_workflow_a_tooltip else 'LIGHT'
            header_row.prop(scene, "spp_show_workflow_a_tooltip", text="", icon=tooltip_icon, emboss=False)
            
            # Standard workflow steps
            col = intro_box.column(align=True)
            col.label(text="Step 2: Use Grease Pencil to draw your design outline")            
            col.label(text="Step 3: Convert to Curve")
            col.label(text="Step 4: Refine in Edit Mode")
            
            # Show tooltip box if enabled
            if scene.spp_show_workflow_a_tooltip:
                tip_box = intro_box.box()
                tip_box.alert = True  # Makes the box stand out with a different color
                tip_col = tip_box.column(align=True)
                tip_col.scale_y = 0.9  # Slightly smaller text
                tip_col.label(text="Quick & Dirty Workflow Tips:", icon='HELP')
                tip_col.label(text="• Draw your design directly on the UV mesh")
                tip_col.label(text="• Keep curves simple with minimal control points")
                tip_col.label(text="• Add more detail in high-curvature areas")
                tip_col.label(text="• This method works best for simple panel shapes")
                tip_col.label(text="• Use subdivision for smoother results")
                tip_col.operator("wm.url_open", text="View Tutorial", icon='URL').url = "https://example.com/tutorial"
            
            # Add UV Boundary Checker before projection
            box_boundary = box_workflow_a.box()
            boundary_header = box_boundary.row()
            boundary_header.label(text="UV Boundary Check (Recommended):", icon='CHECKMARK')
            
            # Action selection
            action_row = box_boundary.row(align=True)
            action_row.prop(context.scene, "spp_uv_boundary_action", text="Action")
            
            # Main operator button
            boundary_op_row = box_boundary.row(align=True)
            boundary_op_row.scale_y = 1.2
            boundary_op_row.operator("mesh.check_uv_boundary", text="Check UV Boundary", icon='ZOOM_SELECTED')
            
            # Help text
            help_col = box_boundary.column(align=True)
            help_col.scale_y = 0.8
            help_col.label(text="Prevents misprojections by detecting boundary violations")
            help_col.label(text="FIX mode snaps vertices directly to boundary (no padding)")
            help_col.label(text="Simple and reliable approach that actually works")
            
            # Status indicator
            status_row = box_boundary.row(align=True)
            status_row.scale_y = 0.9
            
            try:
                status = context.scene.spp_uv_boundary_status
            except AttributeError:
                # Property doesn't exist, initialize it
                context.scene.spp_uv_boundary_status = 'NONE'
                status = 'NONE'
            
            if status == 'PASS':
                status_row.label(text="Status: PASS - No Violations", icon='CHECKMARK')
            elif status == 'VIOLATIONS':
                status_row.alert = True
                status_row.label(text="Status: VIOLATIONS - Found Issues", icon='ERROR')
            elif status == 'ERROR':
                status_row.alert = True
                status_row.label(text="Status: ERROR - Check Failed", icon='CANCEL')
            else:  # NONE
                status_row.enabled = False
                status_row.label(text="Status: NONE - Not Checked", icon='QUESTION')
            
            # Re-select button (only show if violation vertex groups exist)
            if context.active_object and context.active_object.type == 'MESH':
                has_violations = any(vg.name.startswith("UV_Violation_") for vg in context.active_object.vertex_groups)
                if has_violations:
                    reselect_row = box_boundary.row(align=True)
                    reselect_row.scale_y = 1.0
                    reselect_row.operator("mesh.reselect_uv_violations", text="Re-select Violations", icon='RESTRICT_SELECT_OFF')
            
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

        # Workflow B - Collapsible section with enhanced styling
        box_workflow_b = layout.box()
        header_row = box_workflow_b.row(align=True)
        # Custom operator to handle both toggling this workflow and closing the other
        op_workflow_b = header_row.operator("wm.context_toggle_workflow", text="", 
                 icon="TRIA_DOWN" if scene.spp_workflow_b_expanded else "TRIA_RIGHT",
                 emboss=True)
        op_workflow_b.toggle_prop = "spp_workflow_b_expanded"
        op_workflow_b.other_prop = "spp_workflow_a_expanded"
        header_row.label(text="2D Quad Mesh to Panel - Advanced", icon='MOD_LATTICE')
        
        # Only show content if expanded
        if scene.spp_workflow_b_expanded:
            intro_box = box_workflow_b.box()
            
            # Header row with info icon and light bulb toggle
            header_row = intro_box.row()
            header_row.label(text="Workflow Overview:", icon='INFO')
            
            # Add light bulb icon that toggles tooltip visibility
            tooltip_icon = 'LIGHT_SUN' if scene.spp_show_workflow_b_tooltip else 'LIGHT'
            header_row.prop(scene, "spp_show_workflow_b_tooltip", text="", icon=tooltip_icon, emboss=False)
            
            # Standard workflow steps
            col = intro_box.column(align=True)
            col.label(text="Step 2: Use Grease Pencil to draw your design outline")            
            col.label(text="Step 3: Convert to Curve")
            col.label(text="Step 4: Refine in Edit Mode")
            
            # Show tooltip box if enabled
            if scene.spp_show_workflow_b_tooltip:
                tip_box = intro_box.box()
                tip_box.alert = True  # Makes the box stand out with a different color
                tip_col = tip_box.column(align=True)
                tip_col.scale_y = 0.9  # Slightly smaller text
                tip_col.label(text="Advanced Workflow Tips:", icon='HELP')
                tip_col.label(text="• This method gives more precise control over topology")
                tip_col.label(text="• Sample curve with appropriate density for your design")
                tip_col.label(text="• Create quad border first, then fill with grid")
                tip_col.label(text="• Select edge loops to create flow lines")
                tip_col.label(text="• Best for complex panels requiring precise edge flow")
                tip_col.operator("wm.url_open", text="View Advanced Tutorial", icon='URL').url = "https://example.com/advanced-tutorial"

            # Step 5 with enhanced styling
            box_sample = box_workflow_b.box()
            sample_header = box_sample.row()
            sample_header.label(text="Step 5: Sample Curve to Polyline", icon='CURVE_DATA')
            if hasattr(scene, "spp_sampler_fidelity"):
                col_sample = box_sample.column(align=True)
                col_sample.prop(scene, "spp_sampler_fidelity", text="Boundary Samples")
                sample_row = col_sample.row(align=True)
                sample_row.scale_y = 1.2
                sample_row.operator("curve.sample_to_polyline", text="Sample Curve to Polyline", icon='CURVE_BEZCURVE')

            # Step 6 with enhanced styling
            box_create_border = box_workflow_b.box()
            border_header = box_create_border.row()
            border_header.label(text="Step 6: Create Quad Panel Border", icon='MESH_GRID')
            border_row = box_create_border.row(align=True)
            border_row.scale_y = 1.2
            border_row.operator("mesh.create_quad_panel_from_outline", text="Create Quad Border from Outline", icon='OUTLINER_OB_MESH')
            
            # Step 7 with enhanced styling
            box_fill = box_workflow_b.box()
            fill_header = box_fill.row()
            fill_header.label(text="Step 7: Fill Border with Grid", icon='GRID')            
            fill_row = box_fill.row(align=True)
            fill_row.scale_y = 1.2
            fill_row.operator("mesh.fill_border_grid", text="Fill Panel Border", icon='MOD_TRIANGULATE')
            
            # Add grid fill options if needed
            if hasattr(scene, "spp_grid_fill_density"):
                grid_options = box_fill.column(align=True)
                grid_options.prop(scene, "spp_grid_fill_density", text="Grid Density")
                grid_options.prop(scene, "spp_grid_fill_smooth", text="Smooth Grid")
                
            # New Step 8 for edge loop selection
            box_edge_loop = box_workflow_b.box()
            edge_loop_header = box_edge_loop.row()
            edge_loop_header.label(text="Step 8: Select Edge Loops", icon='EDGESEL')
            
            # Tips for edge loop selection
            tips_col = box_edge_loop.column(align=True)
            tips_col.label(text="Tip: Alt+Click on edges to select loops")
            tips_col.label(text="Shift+Alt+Click to select multiple loops")
            
            # Add UV Boundary Checker before projection
            box_boundary = box_workflow_b.box()
            boundary_header = box_boundary.row()
            boundary_header.label(text="UV Boundary Check (Recommended):", icon='CHECKMARK')
            
            # Action selection
            action_row = box_boundary.row(align=True)
            action_row.prop(context.scene, "spp_uv_boundary_action", text="Action")
            
            # Main operator button
            boundary_op_row = box_boundary.row(align=True)
            boundary_op_row.scale_y = 1.2
            boundary_op_row.operator("mesh.check_uv_boundary", text="Check UV Boundary", icon='ZOOM_SELECTED')
            
            # Help text
            help_col = box_boundary.column(align=True)
            help_col.scale_y = 0.8
            help_col.label(text="Prevents misprojections by detecting boundary violations")
            help_col.label(text="FIX mode snaps vertices directly to boundary (no padding)")
            help_col.label(text="Simple and reliable approach that actually works")
            
            # Status indicator
            status_row = box_boundary.row(align=True)
            status_row.scale_y = 0.9
            
            try:
                status = context.scene.spp_uv_boundary_status
            except AttributeError:
                # Property doesn't exist, initialize it
                context.scene.spp_uv_boundary_status = 'NONE'
                status = 'NONE'
            
            if status == 'PASS':
                status_row.label(text="Status: PASS - No Violations", icon='CHECKMARK')
            elif status == 'VIOLATIONS':
                status_row.alert = True
                status_row.label(text="Status: VIOLATIONS - Found Issues", icon='ERROR')
            elif status == 'ERROR':
                status_row.alert = True
                status_row.label(text="Status: ERROR - Check Failed", icon='CANCEL')
            else:  # NONE
                status_row.enabled = False
                status_row.label(text="Status: NONE - Not Checked", icon='QUESTION')
            
            # Re-select button (only show if violation vertex groups exist)
            if context.active_object and context.active_object.type == 'MESH':
                has_violations = any(vg.name.startswith("UV_Violation_") for vg in context.active_object.vertex_groups)
                if has_violations:
                    reselect_row = box_boundary.row(align=True)
                    reselect_row.scale_y = 1.0
                    reselect_row.operator("mesh.reselect_uv_violations", text="Re-select Violations", icon='RESTRICT_SELECT_OFF')
            
            # Rename the relax step to Step 9
            box_relax = box_workflow_b.box()
            relax_header = box_relax.row()
            relax_header.label(text="Step 9: Relax Loops & Project", icon='MOD_SMOOTH')
            row_proj = box_relax.row(align=True)
            row_proj.scale_y = 1.2
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
