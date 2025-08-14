"""UV Workflow UI panel (streamlined)"""

import bpy
from bpy.types import Panel


# Properties used by this panel
def register_properties():
    S = bpy.types.Scene

    def add(name, prop):
        if not hasattr(S, name):
            setattr(S, name, prop)

    # Only two actions now
    add(
        "spp_uv_boundary_action",
        bpy.props.EnumProperty(
            name="Boundary Action",
            description="What to do with boundary violations",
            items=[
                ("CHECK", "Check Only", "Highlight violations for inspection"),
                ("FIX", "Fix Vertices", "Push violators inside with safe padding"),
            ],
            default="CHECK",
        ),
    )

    # Single exposed control: Padding (UV)
    add(
        "spp_uv_padding_uv",
        bpy.props.FloatProperty(
            name="Padding (UV)",
            description="Minimum inward offset from UV boundary (0..1). Smart scaling is applied automatically.",
            default=0.005,
            min=0.0,
            max=0.05,
            step=0.001,
            precision=4,
        ),
    )

    add(
        "spp_uv_boundary_status",
        bpy.props.EnumProperty(
            name="Boundary Status",
            description="Status of the last UV boundary check",
            items=[
                ("NONE", "Not Checked", "No boundary check has been performed"),
                ("PASS", "Pass", "No boundary violations found"),
                ("VIOLATIONS", "Violations Found", "Boundary violations detected"),
                ("ERROR", "Error", "Error occurred during boundary check"),
            ],
            default="NONE",
        ),
    )


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
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Sneaker Panel"
    bl_order = 2

    @classmethod
    def poll(cls, context):
        return context.window_manager.spp_active_workflow == "UV_2D"

    def draw(self, context):
        layout = self.layout
        S = context.scene

        uv_box = layout.box()
        uv_header = uv_box.row(align=True)
        uv_header.label(text="UV Workflow [2D]", icon="MOD_UVPROJECT")
        tooltip_icon = (
            "LIGHT_SUN" if context.scene.spp_show_uv_workflow_tooltip else "INFO"
        )
        uv_header.prop(
            context.scene,
            "spp_show_uv_workflow_tooltip",
            text="",
            icon=tooltip_icon,
            emboss=False,
        )

        if context.scene.spp_show_uv_workflow_tooltip:
            tip_box = uv_box.box()
            tip_box.alert = True
            tip_col = tip_box.column(align=True)
            tip_col.scale_y = 0.9
            tip_col.label(text="UV Workflow Tips:", icon="HELP")
            tip_col.label(text="• Use Stabilizer for pencil control")
            tip_col.operator(
                "wm.url_open", text="View UV Workflow Tutorial", icon="URL"
            ).url = "https://example.com/uv-workflow-tutorial"

        # Step 1
        box = uv_box.box()
        box.label(text="Step 1. UV to Mesh (Auto Add Grease Pencil)", icon="UV")
        row = box.row()
        row.operator("object.uv_to_mesh", icon="MESH_DATA")

        # Step 2
        curve_box = uv_box.box()
        curve_box.label(text="Step 2: Create & Edit Curve", icon="OUTLINER_OB_CURVE")
        col = curve_box.column(align=True)
        col.scale_y = 1.1
        col.operator("object.gp_to_curve", text="Convert to Curve", icon="IPO_BEZIER")

        tools = curve_box.box()
        tools.label(text="Curve Editing Tools", icon="TOOL_SETTINGS")
        dec = tools.column(align=True)
        dec.label(text="Decimate Curve:", icon="MOD_DECIM")
        r = dec.row(align=True)
        r.prop(S, "spp_decimate_ratio", text="Ratio")
        r.operator("object.decimate_curve", text="Apply", icon="CHECKMARK")
        opts = tools.column(align=True)
        opts.label(text="Curve Options:", icon="CURVE_DATA")
        cyclic = opts.row()
        cyclic.prop(S, "spp_curve_cyclic", text="")
        cyclic.label(text="Cyclic Curve")
        mir = tools.column(align=True)
        mh = mir.row(align=True)
        mh.label(text="Mirror Tools (Edit Mode):", icon="MOD_MIRROR")
        mir.operator(
            "curve.mirror_selected_points_at_cursor",
            text="Mirror at Cursor",
            icon="CURVE_BEZCIRCLE",
        )

        # Step 3
        box_sample = uv_box.box()
        box_sample.label(text="Step 3: Sample Curve to Polyline", icon="CURVE_DATA")
        if hasattr(S, "spp_sampler_fidelity"):
            col_sample = box_sample.column(align=True)
            col_sample.prop(S, "spp_sampler_fidelity", text="Boundary Samples")
        row = box_sample.row(align=True)
        row.scale_y = 1.2
        row.operator(
            "curve.sample_to_polyline",
            text="Sample Curve to Polyline",
            icon="CURVE_BEZCURVE",
        )

        # Step 4 — Boundary Check
        box_boundary = uv_box.box()
        boundary_header = box_boundary.row()
        boundary_header.label(text="Step 4: Boundary Check", icon="CHECKMARK")

        action_row = box_boundary.row(align=True)
        action_row.prop(S, "spp_uv_boundary_action", text="Action")

        # Padding (UV) slider
        pad_row = box_boundary.row(align=True)
        pad_row.prop(S, "spp_uv_padding_uv")

        boundary_op_row = box_boundary.row(align=True)
        boundary_op_row.scale_y = 1.2
        boundary_op_row.operator(
            "mesh.check_uv_boundary",
            text="Check / Fix UV Boundary",
            icon="ZOOM_SELECTED",
        )

        help_col = box_boundary.column(align=True)
        help_col.scale_y = 0.8
        help_col.label(text="Checks for out-of-bounds & near-boundary verts")
        help_col.label(
            text="FIX: pushes violators safely inside (min = Padding (UV), plus smart scaling)"
        )

        status_row = box_boundary.row(align=True)
        status_row.scale_y = 0.9
        status = getattr(S, "spp_uv_boundary_status", "NONE")
        if status == "PASS":
            status_row.label(text="Status: PASS - No Violations", icon="CHECKMARK")
        elif status == "VIOLATIONS":
            status_row.alert = True
            status_row.label(text="Status: VIOLATIONS - Found Issues", icon="ERROR")
        elif status == "ERROR":
            status_row.alert = True
            status_row.label(text="Status: ERROR - Check Failed", icon="CANCEL")
        else:
            status_row.enabled = False
            status_row.label(text="Status: NONE - Not Checked", icon="QUESTION")

        # Re-select button (only if violation VG exists)
        if context.active_object and context.active_object.type == "MESH":
            has_vg = any(
                vg.name == "UV_Violations" for vg in context.active_object.vertex_groups
            )
            if has_vg:
                reselect_row = box_boundary.row(align=True)
                reselect_row.operator(
                    "mesh.reselect_uv_violations",
                    text="Re-select Violations",
                    icon="RESTRICT_SELECT_OFF",
                )

        # Step 5
        box_fill = uv_box.box()
        box_fill.label(text="Step 5: Fill Border with Grid", icon="GRID")
        fill_row = box_fill.row(align=True)
        fill_row.scale_y = 1.2
        fill_row.operator(
            "mesh.simple_grid_fill", text="Fill Panel Border", icon="MOD_TRIANGULATE"
        )
        smooth_row = box_fill.row(align=True)
        smooth_row.operator(
            "mesh.smooth_mesh", text="Smooth Mesh (Optional)", icon="MOD_SMOOTH"
        )
        help_col = box_fill.column(align=True)
        help_col.scale_y = 0.8
        help_col.label(
            text="Fill Panel Border: Auto-closes edges, creates quads, includes smoothing"
        )
        help_col.label(
            text="Smooth Mesh: Additional smoothing with boundary preservation"
        )

        # Step 6
        box_proj = uv_box.box()
        box_proj.label(text="Step 6:  Project To Surface", icon="OUTLINER_OB_MESH")
        proj_row = box_proj.row(align=True)
        proj_row.scale_y = 1.2
        proj_row.operator(
            "mesh.overlay_panel_onto_shell",
            text="Project 2D Panel to 3D Shell",
            icon="UV_DATA",
        )


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
