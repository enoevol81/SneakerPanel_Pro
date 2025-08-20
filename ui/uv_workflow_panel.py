"""UV Workflow UI panel (collapsible steps, no selection gating)"""

import bpy
from bpy.types import Panel
from ..utils import icons


# Keep (or create) the Scene properties this panel uses
def register_properties():
    S = bpy.types.Scene

    def add(name, prop):
        if not hasattr(S, name):
            setattr(S, name, prop)

    add("spp_uv_boundary_action", bpy.props.EnumProperty(
        name="Boundary Action",
        description="What to do with boundary violations",
        items=[
            ('CHECK', "Check Only", "Highlight violations for inspection"),
            ('FIX',   "Fix Vertices", "Push violators inside with safe padding"),
        ],
        default='CHECK'
    ))

    add("spp_uv_padding_uv", bpy.props.FloatProperty(
        name="Padding (UV)",
        description="Minimum inward offset from UV boundary (0..1). Smart scaling is applied automatically.",
        default=0.005, min=0.0, max=0.05, step=0.001, precision=4
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
        "spp_uv_padding_uv",
        "spp_uv_boundary_status",
    ):
        if hasattr(S, name):
            delattr(S, name)


class OBJECT_PT_UVWorkflow(Panel):
    bl_label = "UV Workflow [2D]"
    bl_idname = "OBJECT_PT_uv_workflow"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sneaker Panel'
    bl_order = 2

    def draw_header(self, context):
        layout = self.layout
        icon_id = icons.get_icon("2d")
        layout.label(text="", icon_value=icon_id)

    @classmethod
    def poll(cls, context):
        return getattr(context.window_manager, "spp_active_workflow", 'UV_2D') == 'UV_2D'

    def draw(self, context):
        layout = self.layout
        S = context.scene
        W = context.window_manager

        uv_box = layout.box()
        uv_header = uv_box.row(align=True)
        uv_header.label(text="Draw Direct To UV",icon_value=icons.get_icon("2d"))

        # Optional workflow tooltip (pattern used elsewhere in your UI)
        tooltip_icon = 'LIGHT_SUN' if getattr(context.scene, "spp_show_uv_workflow_tooltip", False) else 'INFO'
        if hasattr(context.scene, "spp_show_uv_workflow_tooltip"):
            uv_header.prop(context.scene, "spp_show_uv_workflow_tooltip", text="", icon=tooltip_icon, emboss=False)

        if getattr(context.scene, "spp_show_uv_workflow_tooltip", False):
            tip_box = uv_box.box(); tip_box.alert = True
            tip_col = tip_box.column(align=True); tip_col.scale_y = 0.9
            tip_col.label(text="UV Workflow Tips:", icon='HELP')
            tip_col.label(text="• Use Stabilizer for pencil control")
            tip_col.operator("wm.url_open", text="View UV Workflow Tutorial", icon='URL').url = "https://example.com/uv-workflow-tutorial"

        # -----------------------------
        # Step 1 (collapsible)
        # -----------------------------
        step1 = uv_box.box()
        hdr1 = step1.row(align=True)
        hdr1.prop(W, "spp_show_uv_step_1", toggle=True,
                  text="Step 1: UV to Mesh (Auto Add Grease Pencil)", icon='UV')

        if W.spp_show_uv_step_1:
            step1.row().operator("object.uv_to_mesh", icon='MESH_DATA')

        # -----------------------------
        # Step 2 (collapsible, always-on)
        # -----------------------------
        step2 = uv_box.box()
        hdr2 = step2.row(align=True)
        hdr2.prop(W, "spp_show_uv_step_2", toggle=True,
                  text="Step 2: Create & Edit Curve", icon='OUTLINER_OB_CURVE')

        if W.spp_show_uv_step_2:
            col = step2.column(align=True); col.scale_y = 1.1
            col.operator("object.gp_to_curve", text="Convert to Curve", icon='IPO_BEZIER')

            tools = step2.box(); tools.label(text="Curve Editing Tools", icon="TOOL_SETTINGS")
            dec = tools.column(align=True); dec.label(text="Decimate Curve:", icon="MOD_DECIM")
            r = dec.row(align=True); r.prop(S, "spp_decimate_ratio", text="Ratio"); r.operator("object.decimate_curve", text="Apply", icon='CHECKMARK')
            # Curve options + mirror tooltip
            opts = tools.column(align=True)
            rr = opts.row(align=True)

            left_split = rr.split(factor=0.7, align=True)
            left_row = left_split.row(align=True)
            if hasattr(S, "spp_curve_cyclic"):
                left_row.prop(S, "spp_curve_cyclic", text="")
            left_row.label(text="Cyclic Curve")

            right_split = left_split.row(align=True)
            right_split.alignment = 'RIGHT'
            icon = 'LIGHT_SUN' if getattr(context.scene, "spp_show_mirror_tooltip", False) else 'INFO'
            if hasattr(context.scene, "spp_show_mirror_tooltip"):
                right_split.prop(context.scene, "spp_show_mirror_tooltip", text="", toggle=True, icon=icon)

            if getattr(context.scene, "spp_show_mirror_tooltip", False):
                tip_box = tools.box(); tip_box.alert = True
                tip_col = tip_box.column(align=True); tip_col.scale_y = 0.9
                tip_col.label(text="Mirror Curve Tips:", icon="HELP")
                tip_col.label(text="• Mirror curve in edit mode")
                tip_col.label(text="• Mirror curve in object mode")
                tip_col.operator("wm.url_open", text="View Mirror Curve Tutorial", icon="URL").url = "https://example.com/mirror_curve-tutorial"

            # Step 2b – Mirror (Edit Mode)
            mir = tools.column(align=True)
            mir.operator("curve.mirror_selected_points_at_cursor", text="Mirror Curve", icon="MOD_MIRROR")

        # -----------------------------
        # Step 3 (collapsible)
        # -----------------------------
        step3 = uv_box.box()
        hdr3 = step3.row(align=True)
        hdr3.prop(W, "spp_show_uv_step_3", toggle=True,
                  text="Step 3: Sample Curve to Polyline", icon='CURVE_DATA')

        if W.spp_show_uv_step_3:
            if hasattr(S, "spp_sampler_fidelity"):
                step3.column(align=True).prop(S, "spp_sampler_fidelity", text="Boundary Samples")
            row = step3.row(align=True); row.scale_y = 1.2
            row.operator("curve.sample_to_polyline", text="Sample Curve to Polyline", icon='CURVE_BEZCURVE')

        # -----------------------------
        # Step 4 (collapsible, always-on)
        # -----------------------------
        step4 = uv_box.box()
        hdr4 = step4.row(align=True)
        hdr4.prop(W, "spp_show_uv_step_4", toggle=True,
                  text="Step 4: Boundary Check", icon='CHECKMARK')

        if W.spp_show_uv_step_4:
            action_row = step4.row(align=True)
            action_row.prop(S, "spp_uv_boundary_action", text="Action")

            pad_row = step4.row(align=True)
            pad_row.prop(S, "spp_uv_padding_uv")

            boundary_op_row = step4.row(align=True); boundary_op_row.scale_y = 1.2
            boundary_op_row.operator("mesh.check_uv_boundary", text="Check / Fix UV Boundary", icon='ZOOM_SELECTED')

            help_col = step4.column(align=True); help_col.scale_y = 0.8
            help_col.label(text="Checks for out-of-bounds & near-boundary verts")
            help_col.label(text="FIX: pushes violators safely inside (min = Padding (UV), plus smart scaling)")

            status_row = step4.row(align=True); status_row.scale_y = 0.9
            status = getattr(S, "spp_uv_boundary_status", 'NONE')
            if status == 'PASS':
                status_row.label(text="Status: PASS - No Violations", icon='CHECKMARK')
            elif status == 'VIOLATIONS':
                status_row.alert = True; status_row.label(text="Status: VIOLATIONS - Found Issues", icon='ERROR')
            elif status == 'ERROR':
                status_row.alert = True; status_row.label(text="Status: ERROR - Check Failed", icon='CANCEL')
            else:
                status_row.enabled = False; status_row.label(text="Status: NONE - Not Checked", icon='QUESTION')

            # Optional convenience button only when it makes sense
            if context.active_object and context.active_object.type == 'MESH':
                has_vg = any(vg.name == "UV_Violations" for vg in context.active_object.vertex_groups)
                if has_vg:
                    reselect_row = step4.row(align=True)
                    reselect_row.operator("mesh.reselect_uv_violations",
                                          text="Re-select Violations",
                                          icon='RESTRICT_SELECT_OFF')

        # -----------------------------
        # Step 5 (collapsible, always-on)
        # -----------------------------
        step5 = uv_box.box()
        hdr5 = step5.row(align=True)
        hdr5.prop(W, "spp_show_uv_step_5", toggle=True,
                  text="Step 5: Fill Border with Grid", icon='GRID')

        if W.spp_show_uv_step_5:
            fill_row = step5.row(align=True); fill_row.scale_y = 1.2
            fill_row.operator("mesh.simple_grid_fill", text="Fill Panel Border", icon='MOD_TRIANGULATE')
            smooth_row = step5.row(align=True)
            smooth_row.operator("mesh.smooth_mesh", text="Smooth Mesh (Optional)", icon='MOD_SMOOTH')

        # -----------------------------
        # Step 6 (collapsible, always-on)
        # -----------------------------
        step6 = uv_box.box()
        hdr6 = step6.row(align=True)
        hdr6.prop(W, "spp_show_uv_step_6", toggle=True,
                  text="Step 6: Project To Surface", icon='OUTLINER_OB_MESH')

        if W.spp_show_uv_step_6:
            proj_row = step6.row(align=True); proj_row.scale_y = 1.2
            proj_row.operator("mesh.overlay_panel_onto_shell",
                              text="Project 2D Panel to 3D Shell",
                              icon='UV_DATA')


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
