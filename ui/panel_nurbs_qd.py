import bpy
from bpy.types import Panel

from ..prefs import get_prefs

CATEGORY = "Sneaker Panel"


def ensure_scene_props():
    S = bpy.types.Scene
    if not hasattr(S, "spp_nurbs_qd_active"):
        S.spp_nurbs_qd_active = bpy.props.EnumProperty(
            name="Active Q&D Stack",
            description="Choose which Quick & Dirty stack to show",
            items=[
                ("QD_BEZIER", "QD Bezier", "Quick & Dirty Bezier → Surface stack"),
                ("QD_UV_CURVE", "QD UV Curve", "Quick & Dirty UV Curve → Panel stack"),
            ],
            default="QD_UV_CURVE",
        )


class SPP_PT_NurbsToSurface(Panel):
    bl_label = "Experimental — Nurbs To Surface"
    bl_idname = "SPP_PT_nurbs_qd"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = CATEGORY
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        try:
            return bool(get_prefs(context).enable_experimental_qd)
        except Exception:
            return False

    def draw(self, context):
        sc = context.scene
        layout = self.layout

        # mini radio to switch between the two Q&D stacks
        row = layout.row(align=True)
        b = row.operator(
            "wm.context_set_enum",
            text="Bezier Q&D",
            depress=(sc.spp_nurbs_qd_active == "QD_BEZIER"),
            icon="CURVE_BEZCURVE",
        )
        b.data_path = "scene.spp_nurbs_qd_active"
        b.value = "QD_BEZIER"
        b = row.operator(
            "wm.context_set_enum",
            text="UV Curve Q&D",
            depress=(sc.spp_nurbs_qd_active == "QD_UV_CURVE"),
            icon="CURVE_NCURVE",
        )
        b.data_path = "scene.spp_nurbs_qd_active"
        b.value = "QD_UV_CURVE"

        layout.separator()

        if sc.spp_nurbs_qd_active == "QD_BEZIER":
            box = layout.box()
            box.label(text="Bezier → Surface (Q&D)", icon="SURFACE_DATA")
            self.draw_qd_bezier(layout, context)
        else:
            self.draw_qd_uvcurve(layout, context)

    # ---------- Q&D: Bezier → Surface ----------
    def draw_qd_bezier(self, layout, context):
        sc = context.scene

        # Step 1: Create Grease Pencil
        gp_box = layout.box()
        gp_header = gp_box.row()
        gp_header.label(
            text="Step 1: Create Grease Pencil - Bezier Q&D", icon="GREASEPENCIL"
        )
        gp_col = gp_box.column(align=True)
        gp_col.scale_y = 1.1
        gp_col.operator(
            "object.add_gp_draw",
            text="Create Grease Pencil",
            icon="OUTLINER_OB_GREASEPENCIL",
        )

        # Stabilizer (optional)
        stab_box = gp_box.box()
        stab_row = stab_box.row()
        stab_row.prop(sc, "spp_use_stabilizer", text="")
        stab_row.label(text="Stabilizer Settings")
        if getattr(sc, "spp_use_stabilizer", False):
            stab_col = stab_box.column(align=True)
            stab_col.prop(sc, "spp_stabilizer_radius", text="Radius")
            stab_col.prop(sc, "spp_stabilizer_strength_ui", text="Strength")

        # Step 2: Convert & Edit Curve
        curve_box = layout.box()
        curve_box.label(text="Step 2: Convert & Edit Curve", icon="OUTLINER_OB_CURVE")
        curve_col = curve_box.column(align=True)
        curve_col.scale_y = 1.1
        curve_col.operator(
            "object.gp_to_curve", text="Convert to Curve", icon="IPO_BEZIER"
        )

        curve_tools_box = curve_box.box()
        curve_tools_box.label(text="Curve Editing Tools", icon="TOOL_SETTINGS")

        decimate_col = curve_tools_box.column(align=True)
        decimate_col.label(text="Decimate Curve:", icon="MOD_DECIM")
        row = decimate_col.row(align=True)
        row.prop(sc, "spp_decimate_ratio", text="Ratio")
        row.operator("object.decimate_curve", text="Apply", icon="CHECKMARK")

        opts = curve_tools_box.column(align=True)
        opts.label(text="Curve Options:", icon="CURVE_DATA")
        cyclic = opts.row()
        cyclic.prop(sc, "spp_curve_cyclic", text="")
        cyclic.label(text="Cyclic Curve")

        mirror = curve_tools_box.column(align=True)
        mrow = mirror.row(align=True)
        mrow.label(text="Mirror Tools (Edit Mode):", icon="MOD_MIRROR")
        mirror.operator(
            "curve.mirror_selected_points_at_cursor",
            text="Mirror at Cursor",
            icon="CURVE_BEZCIRCLE",
        )

        # Step 3: Generate NURBS Surface (Q&D)
        surf_box = layout.box()
        surf_box.label(
            text="Step 3: Generate NURBS Surface (Q&D)", icon="SURFACE_NSURFACE"
        )
        op_bs = surf_box.operator(
            "spp.convert_bezier_to_surface",
            text="Convert Bezier to Surface",
            icon="SURFACE_DATA",
        )
        # These properties are shared with the main SD panel
        op_bs.center = getattr(sc, "spp_bezier_center", True)
        op_bs.Resolution_U = getattr(sc, "spp_resolution_u", 12)
        op_bs.Resolution_V = getattr(sc, "spp_resolution_v", 12)

        # Step 4: Surface → Mesh
        mesh_box = layout.box()
        mesh_box.label(text="Step 4: Surface to Mesh", icon="MESH_GRID")
        mesh_box.prop(sc, "spp_preserve_surface", text="Preserve Surface")
        mesh_box.prop(sc, "spp_shade_smooth", text="Smooth Shading")
        mesh_box.operator(
            "object.convert", text="Convert to Mesh Object", icon="MESH_GRID"
        ).target = "MESH"

    # ---------- Q&D: UV Curve → Panel ----------
    def draw_qd_uvcurve(self, layout, context):
        sc = context.scene

        # Step 1: UV to Mesh
        box = layout.box()
        box.label(text="Step 1. UV to Mesh (Auto Add Grease Pencil)", icon="UV")
        row = box.row()
        row.operator("object.uv_to_mesh", icon="MESH_DATA")

        # Step 2: Convert & Edit Curve
        curve_box = layout.box()
        curve_box.label(text="Step 2: Create & Edit Curve", icon="OUTLINER_OB_CURVE")

        curve_col = curve_box.column(align=True)
        curve_col.scale_y = 1.1
        curve_col.operator(
            "object.gp_to_curve", text="Convert to Curve", icon="IPO_BEZIER"
        )

        tools = curve_box.box()
        tools.label(text="Curve Editing Tools", icon="TOOL_SETTINGS")

        decimate_col = tools.column(align=True)
        decimate_col.label(text="Decimate Curve:", icon="MOD_DECIM")
        r = decimate_col.row(align=True)
        r.prop(sc, "spp_decimate_ratio", text="Ratio")
        r.operator("object.decimate_curve", text="Apply", icon="CHECKMARK")

        opts = tools.column(align=True)
        opts.label(text="Curve Options:", icon="CURVE_DATA")
        cyclic = opts.row()
        cyclic.prop(sc, "spp_curve_cyclic", text="")
        cyclic.label(text="Cyclic Curve")

        mirror = tools.column(align=True)
        mh = mirror.row(align=True)
        mh.label(text="Mirror Tools (Edit Mode):", icon="MOD_MIRROR")
        mirror.operator(
            "curve.mirror_selected_points_at_cursor",
            text="Mirror at Cursor",
            icon="CURVE_BEZCIRCLE",
        )

        # Boundary Check
        box_boundary = layout.box()
        boundary_header = box_boundary.row()
        boundary_header.label(text="Step 2a: Boundary Check", icon="CHECKMARK")

        action_row = box_boundary.row(align=True)
        action_row.prop(sc, "spp_uv_boundary_action", text="Action")

        boundary_op_row = box_boundary.row(align=True)
        boundary_op_row.scale_y = 1.2
        boundary_op_row.operator(
            "mesh.check_uv_boundary", text="Check UV Boundary", icon="ZOOM_SELECTED"
        )

        help_col = box_boundary.column(align=True)
        help_col.scale_y = 0.8
        help_col.label(text="Detects boundary violations before projection")
        help_col.label(
            text="FIX mode intelligently snaps vertices (smart padding), preserves topology"
        )

        status_row = box_boundary.row(align=True)
        status_row.scale_y = 0.9
        status = getattr(sc, "spp_uv_boundary_status", "NONE")
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

        if context.active_object and context.active_object.type == "MESH":
            has_violations = any(
                vg.name.startswith("UV_Violation_")
                for vg in context.active_object.vertex_groups
            )
            if has_violations:
                reselect_row = box_boundary.row(align=True)
                reselect_row.scale_y = 1.0
                reselect_row.operator(
                    "mesh.reselect_uv_violations",
                    text="Step 2a: UV Boundary Check - Re-select Violations",
                    icon="RESTRICT_SELECT_OFF",
                )

        # Shell UV → Panel
        box = layout.box()
        box.label(text="Step 3: Shell UV to Panel", icon="MODIFIER")
        row = box.row()
        row.operator("object.shell_uv_to_panel", icon="MOD_SOLIDIFY")

        # Refinement
        post = layout.box()
        post.label(text="Panel Refinement Options:")
        post.prop(sc, "spp_grid_fill_span", text="Initial Grid Fill Span")

        row = post.row()
        row.prop(sc, "spp_panel_add_subdivision", text="Add Subdivision")
        row_sub = post.row(align=True)
        row_sub.enabled = getattr(sc, "spp_panel_add_subdivision", False)
        row_sub.prop(sc, "spp_panel_subdivision_levels", text="Levels")
        row_sub.prop(sc, "spp_panel_conform_after_subdivision", text="Re-Conform")
        post.prop(sc, "spp_panel_shade_smooth", text="Shade Smooth")


classes = [SPP_PT_NurbsToSurface]


def register():
    ensure_scene_props()
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
