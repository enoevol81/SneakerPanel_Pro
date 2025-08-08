"""UV Workflow UI panel for the Sneaker Panel Pro addon.

Core UV workflow arranged linearly with no collapsible sections.
Quick & Dirty lives in the Experimental panel (panel_nurbs_qd.py).
"""

import bpy
from bpy.types import Panel


# Properties used by this panel
def register_properties():
    S = bpy.types.Scene

    def add(name, prop):
        if not hasattr(S, name):
            setattr(S, name, prop)

    # UV Boundary Checker props (shared with Experimental panel)
    add("spp_uv_boundary_action", bpy.props.EnumProperty(
        name="Boundary Action",
        description="What to do with boundary violations",
        items=[
            ('CHECK', "Check Only", "Highlight violations for inspection"),
            ('FIX', "Fix Vertices", "Fix vertex violations only (preserves topology)"),
            ('INTERACTIVE', "Select for Manual Fix", "Select violations for manual editing (recommended for edges)"),
        ],
        default='CHECK'
    ))
    add("spp_uv_boundary_samples", bpy.props.IntProperty(
        name="Raycast Samples",
        description="Number of samples per edge for boundary checking",
        default=10, min=3, max=50
    ))
    add("spp_uv_boundary_margin", bpy.props.FloatProperty(
        name="Boundary Margin",
        description="Safety margin from UV boundary (0.0-1.0)",
        default=0.01, min=0.0, max=0.1
    ))
    add("spp_uv_boundary_status", bpy.props.EnumProperty(
        name="Boundary Status",
        description="Status of the last UV boundary check",
        items=[
            ('NONE', "Not Checked", "No boundary check has been performed"),
            ('PASS', "Pass", "No boundary violations found"),
            ('VIOLATIONS', "Violations Found", "Boundary violations detected"),
            ('ERROR', "Error", "Error occurred during boundary check"),
        ],
        default='NONE'
    ))


def unregister_properties():
    S = bpy.types.Scene
    for name in (
        "spp_uv_boundary_action",
        "spp_uv_boundary_samples",
        "spp_uv_boundary_margin",
        "spp_uv_boundary_status",
    ):
        if hasattr(S, name):
            delattr(S, name)


class OBJECT_PT_UVWorkflow(Panel):
    """UV Workflow panel (core, non-experimental)."""
    bl_label = "UV Workflow [2D]"
    bl_idname = "OBJECT_PT_uv_workflow"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sneaker Panel'
    bl_order = 2

    @classmethod
    def poll(cls, context):
        return context.window_manager.spp_active_workflow == 'UV_2D'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # --- Step 1: UV to Mesh ---
        box = layout.box()
        box.label(text="Step 1. UV to Mesh (Auto Add Grease Pencil)", icon='UV')
        row = box.row()
        row.operator("object.uv_to_mesh", icon='MESH_DATA')

        # --- Step 2: Create & Edit Curve ---
        curve_box = layout.box()
        curve_box.label(text="Step 2: Create & Edit Curve", icon='OUTLINER_OB_CURVE')

        col = curve_box.column(align=True); col.scale_y = 1.1
        col.operator("object.gp_to_curve", text="Convert to Curve", icon='IPO_BEZIER')

        tools = curve_box.box()
        tools.label(text="Curve Editing Tools", icon="TOOL_SETTINGS")

        # Step 2a: Decimate
        dec = tools.column(align=True)
        dec.label(text="Decimate Curve:", icon="MOD_DECIM")
        r = dec.row(align=True)
        r.prop(scene, "spp_decimate_ratio", text="Ratio")
        r.operator("object.decimate_curve", text="Apply", icon='CHECKMARK')

        # Curve Options
        opts = tools.column(align=True)
        opts.label(text="Curve Options:", icon="CURVE_DATA")
        cyclic = opts.row()
        cyclic.prop(scene, "spp_curve_cyclic", text="")
        cyclic.label(text="Cyclic Curve")

        # Step 2b: Mirror tools
        mir = tools.column(align=True)
        mh = mir.row(align=True)
        mh.label(text="Mirror Tools (Edit Mode):", icon="MOD_MIRROR")
        mir.operator("curve.mirror_selected_points_at_cursor",
                     text="Mirror at Cursor", icon="CURVE_BEZCIRCLE")

        # --- Step 3: Sample Curve to Polyline ---
        box_sample = layout.box()
        box_sample.label(text="Step 3: Sample Curve to Polyline", icon='CURVE_DATA')
        if hasattr(scene, "spp_sampler_fidelity"):
            col_sample = box_sample.column(align=True)
            col_sample.prop(scene, "spp_sampler_fidelity", text="Boundary Samples")
        row = box_sample.row(align=True); row.scale_y = 1.2
        row.operator("curve.sample_to_polyline", text="Sample Curve to Polyline", icon='CURVE_BEZCURVE')

        # --- Step 4: Boundary Check ---
        box_boundary = layout.box()
        boundary_header = box_boundary.row()
        boundary_header.label(text="Step 4: Boundary Check", icon='CHECKMARK')

        action_row = box_boundary.row(align=True)
        action_row.prop(scene, "spp_uv_boundary_action", text="Action")

        boundary_op_row = box_boundary.row(align=True); boundary_op_row.scale_y = 1.2
        boundary_op_row.operator("mesh.check_uv_boundary", text="Check UV Boundary", icon='ZOOM_SELECTED')

        help_col = box_boundary.column(align=True); help_col.scale_y = 0.8
        help_col.label(text="Detects boundary violations before projection")
        help_col.label(text="FIX mode intelligently snaps vertices (smart padding), preserves topology")

        status_row = box_boundary.row(align=True); status_row.scale_y = 0.9
        status = getattr(scene, "spp_uv_boundary_status", 'NONE')
        if status == 'PASS':
            status_row.label(text="Status: PASS - No Violations", icon='CHECKMARK')
        elif status == 'VIOLATIONS':
            status_row.alert = True
            status_row.label(text="Status: VIOLATIONS - Found Issues", icon='ERROR')
        elif status == 'ERROR':
            status_row.alert = True
            status_row.label(text="Status: ERROR - Check Failed", icon='CANCEL')
        else:
            status_row.enabled = False
            status_row.label(text="Status: NONE - Not Checked", icon='QUESTION')

        # Re-select button (only if violation VGs exist)
        if context.active_object and context.active_object.type == 'MESH':
            has_violations = any(vg.name.startswith("UV_Violation_")
                                 for vg in context.active_object.vertex_groups)
            if has_violations:
                reselect_row = box_boundary.row(align=True)
                reselect_row.operator("mesh.reselect_uv_violations",
                                      text="Step 4: UV Boundary Check - Re-select Violations",
                                      icon='RESTRICT_SELECT_OFF')

        # --- Step 5: Fill Border with Grid ---
        box_fill = layout.box()
        box_fill.label(text="Step 5: Fill Border with Grid", icon='GRID')
        fill_row = box_fill.row(align=True); fill_row.scale_y = 1.2
        fill_row.operator("mesh.fill_border_grid", text="Fill Panel Border", icon='MOD_TRIANGULATE')

        # --- Step 6: Project To Surface ---
        box_proj = layout.box()
        box_proj.label(text="Step 6:  Project To Surface", icon='OUTLINER_OB_MESH')
        proj_row = box_proj.row(align=True); proj_row.scale_y = 1.2
        proj_row.operator("mesh.overlay_panel_onto_shell",
                          text="Project 2D Panel to 3D Shell",
                          icon='UV_DATA')


# Not used here anymore, but other modules use it; safe to keep import
from . import workflow_operators  # noqa: F401

classes = [OBJECT_PT_UVWorkflow]

def register():
    register_properties()
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception:
            pass

def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
    unregister_properties()
