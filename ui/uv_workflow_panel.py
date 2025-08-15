# -------------------------------------------------------------------------
# UV Workflow Panel UI
# -------------------------------------------------------------------------

import bpy
from bpy.types import Panel


# UV Workflow Properties
def register_properties():
    S = bpy.types.Scene

    def add(name, prop):
        if not hasattr(S, name):
            setattr(S, name, prop)

    # Boundary action options
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

    # UV padding control
    add(
        "spp_uv_padding_uv",
        bpy.props.FloatProperty(
            name="Padding (UV)",
            description="Minimum inward offset from UV boundary (0..1). Smart scaling is applied automatically",
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

        # Tooltip toggle
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

        # Tooltip content
        if context.scene.spp_show_uv_workflow_tooltip:
            uv_box.separator(factor=0.3)
            tip_box = uv_box.box()
            tip_box.alert = True
            tip_col = tip_box.column(align=True)
            tip_col.scale_y = 0.9
            tip_col.label(text="UV Workflow Tips:", icon="HELP")
            tip_col.label(text="• Use Stabilizer for pencil control")
            tip_col.operator(
                "wm.url_open", text="View UV Workflow Tutorial", icon="URL"
            ).url = "https://example.com/uv-workflow-tutorial"

        # Step 1: UV to Mesh
        uv_box.separator(factor=0.5)
        step1_box = uv_box.box()
        step1_box.label(text="Step 1: UV to Mesh (Auto Add Grease Pencil)", icon="UV")

        step1_box.separator(factor=0.3)
        step1_row = step1_box.row(align=True)
        step1_row.scale_y = 1.0
        step1_row.operator("object.uv_to_mesh", icon="MESH_DATA")

        # Step 2: Create & Edit Curve (collapsible)
        step2_header = uv_box.row(align=True)
        step2_header.prop(
            context.window_manager,
            "spp_show_uv_step_2",
            text="",
            icon="TRIA_DOWN" if context.window_manager.spp_show_uv_step_2 else "TRIA_RIGHT",
            emboss=False,
        )
        step2_header.label(text="Step 2: Create & Edit Curve", icon="OUTLINER_OB_CURVE")
        
        if context.window_manager.spp_show_uv_step_2:
            # Check requirements
            obj = context.active_object
            if not obj or obj.type not in {"GPENCIL", "CURVE"}:
                req_box = uv_box.box()
                req_box.alert = True
                req_box.label(text="Requires: Select a Grease Pencil stroke or Curve", icon="INFO")
            else:
                curve_box = uv_box.box()

                curve_box.separator(factor=0.3)
                col = curve_box.column(align=True)
                col.scale_y = 1.0
                col.operator("object.gp_to_curve", text="Convert to Curve", icon="IPO_BEZIER")

                # Curve editing tools
                curve_box.separator(factor=0.3)
                tools = curve_box.box()
                tools.label(text="Curve Editing Tools", icon="TOOL_SETTINGS")
                
                # Decimate curve
                tools.separator(factor=0.2)
                dec = tools.column(align=True)
                dec.label(text="Decimate Curve", icon="MOD_DECIM")
                dec_row = dec.row(align=True)
                dec_row.prop(S, "spp_decimate_ratio", text="Ratio")
                dec_row.operator("object.decimate_curve", text="Apply", icon="CHECKMARK")

                # Curve options
                tools.separator(factor=0.2)
                opts = tools.column(align=True)
                opts.label(text="Curve Options", icon="CURVE_DATA")
                cyclic_row = opts.row(align=True)
                cyclic_row.prop(S, "spp_curve_cyclic", text="")
                cyclic_row.label(text="Cyclic Curve")

                # Mirror tools
                tools.separator(factor=0.2)
                mir = tools.column(align=True)
                mir.label(text="Mirror Tools (Edit Mode)", icon="MOD_MIRROR")
                mir.operator(
                    "curve.mirror_selected_points_at_cursor",
                    text="Mirror at Cursor",
                    icon="CURVE_BEZCIRCLE",
                )

        # Step 3: Sample Curve to Polyline
        sample_box = uv_box.box()
        sample_box.label(text="Step 3: Sample Curve to Polyline", icon="CURVE_DATA")

        if hasattr(S, "spp_sampler_fidelity"):
            sample_box.separator(factor=0.3)
            sample_box.prop(S, "spp_sampler_fidelity", text="Boundary Samples")

        sample_box.separator(factor=0.3)
        sample_row = sample_box.row(align=True)
        sample_row.scale_y = 1.0
        sample_row.operator(
            "curve.sample_to_polyline",
            text="Sample Curve to Polyline",
            icon="CURVE_BEZCURVE",
        )

        # Step 4: Boundary Check (collapsible)
        step4_header = uv_box.row(align=True)
        step4_header.prop(
            context.window_manager,
            "spp_show_uv_step_4",
            text="",
            icon="TRIA_DOWN" if context.window_manager.spp_show_uv_step_4 else "TRIA_RIGHT",
            emboss=False,
        )
        step4_header.label(text="Step 4: Boundary Check", icon="CHECKMARK")
        
        if context.window_manager.spp_show_uv_step_4:
            # Check requirements
            obj = context.active_object
            if not obj or obj.type != "MESH":
                req_box = uv_box.box()
                req_box.alert = True
                req_box.label(text="Requires: Select a Mesh", icon="INFO")
            else:
                boundary_box = uv_box.box()

                boundary_box.separator(factor=0.3)
                action_row = boundary_box.row(align=True)
                action_row.prop(S, "spp_uv_boundary_action", text="Action")

                boundary_box.separator(factor=0.2)
                boundary_box.prop(S, "spp_uv_padding_uv")

                boundary_box.separator(factor=0.3)
                boundary_op_row = boundary_box.row(align=True)
                boundary_op_row.scale_y = 1.0
                boundary_op_row.operator(
                    "mesh.check_uv_boundary",
                    text="Check / Fix UV Boundary",
                    icon="ZOOM_SELECTED",
                )

                # Help text
                boundary_box.separator(factor=0.2)
                help_col = boundary_box.column(align=True)
                help_col.scale_y = 0.8
                help_col.enabled = False
                help_col.label(text="Checks for out-of-bounds & near-boundary verts")
                help_col.label(
                    text="FIX: pushes violators safely inside (min = Padding (UV), plus smart scaling)"
                )

                # Status indicator
                boundary_box.separator(factor=0.2)
                status_row = boundary_box.row(align=True)
                status_row.scale_y = 0.9

                status = getattr(S, "spp_uv_boundary_status", "NONE")
                if status == "PASS":
                    status_row.label(text="✓ No Violations Found", icon="CHECKMARK")
                elif status == "VIOLATIONS":
                    status_row.alert = True
                    status_row.label(text="⚠ Violations Detected", icon="ERROR")
                elif status == "ERROR":
                    status_row.alert = True
                    status_row.label(text="✗ Check Failed", icon="CANCEL")
                else:
                    status_row.enabled = False
                    status_row.label(text="? Not Checked", icon="QUESTION")

                # Re-select violations button
                if context.active_object and context.active_object.type == "MESH":
                    has_vg = any(
                        vg.name == "UV_Violations" for vg in context.active_object.vertex_groups
                    )
                    if has_vg:
                        boundary_box.separator(factor=0.2)
                        reselect_row = boundary_box.row(align=True)
                        reselect_row.scale_y = 0.9
                        reselect_row.operator(
                            "mesh.reselect_uv_violations",
                            text="Re-select Violations",
                            icon="RESTRICT_SELECT_OFF",
                        )

        # Step 5: Fill Border with Grid (collapsible)
        step5_header = uv_box.row(align=True)
        step5_header.prop(
            context.window_manager,
            "spp_show_uv_step_5",
            text="",
            icon="TRIA_DOWN" if context.window_manager.spp_show_uv_step_5 else "TRIA_RIGHT",
            emboss=False,
        )
        step5_header.label(text="Step 5: Fill Border with Grid", icon="GRID")
        
        if context.window_manager.spp_show_uv_step_5:
            # Check requirements
            obj = context.active_object
            if not obj or obj.type != "MESH":
                req_box = uv_box.box()
                req_box.alert = True
                req_box.label(text="Requires: Select a Mesh", icon="INFO")
            else:
                fill_box = uv_box.box()

                fill_box.separator(factor=0.3)
                fill_row = fill_box.row(align=True)
                fill_row.scale_y = 1.0
                fill_row.operator(
                    "mesh.simple_grid_fill", text="Fill Panel Border", icon="MOD_TRIANGULATE"
                )

                fill_box.separator(factor=0.2)
                smooth_row = fill_box.row(align=True)
                smooth_row.scale_y = 0.9
                smooth_row.operator(
                    "mesh.smooth_mesh", text="Smooth Mesh (Optional)", icon="MOD_SMOOTH"
                )

                # Help text
                fill_box.separator(factor=0.2)
                help_col = fill_box.column(align=True)
                help_col.scale_y = 0.8
                help_col.enabled = False
                help_col.label(
                    text="Fill Panel Border: Auto-closes edges, creates quads, includes smoothing"
                )
                help_col.label(
                    text="Smooth Mesh: Additional smoothing with boundary preservation"
                )

        # Step 6: Project To Surface (collapsible)
        step6_header = uv_box.row(align=True)
        step6_header.prop(
            context.window_manager,
            "spp_show_uv_step_6",
            text="",
            icon="TRIA_DOWN" if context.window_manager.spp_show_uv_step_6 else "TRIA_RIGHT",
            emboss=False,
        )
        step6_header.label(text="Step 6: Project To Surface", icon="OUTLINER_OB_MESH")
        
        if context.window_manager.spp_show_uv_step_6:
            # Check requirements
            obj = context.active_object
            if not obj or obj.type != "MESH":
                req_box = uv_box.box()
                req_box.alert = True
                req_box.label(text="Requires: Select a Mesh", icon="INFO")
            else:
                proj_box = uv_box.box()

                proj_box.separator(factor=0.3)
                proj_row = proj_box.row(align=True)
                proj_row.scale_y = 1.0
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
