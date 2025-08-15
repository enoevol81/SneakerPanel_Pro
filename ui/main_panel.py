import bpy
from bpy.props import EnumProperty
from bpy.types import Operator

from ..utils import icons


class WM_OT_SPP_ToggleWorkflow(Operator):
    bl_idname = "wm.spp_toggle_workflow"
    bl_label = "Toggle Workflow"
    bl_description = "Enable/disable a workflow. Clicking the active button toggles workflow off (None)"
    bl_options = {"INTERNAL"}

    mode: EnumProperty(
        name="Mode",
        description="Workflow mode to toggle",
        items=[
            ("SURFACE_3D", "Surface 3D", "3D surface workflow"),
            ("UV_2D", "UV 2D", "2D UV workflow"),
        ],
    )

    def execute(self, context):
        wm = context.window_manager
        current = getattr(wm, "spp_active_workflow", "NONE")
        wm.spp_active_workflow = "NONE" if current == self.mode else self.mode
        return {"FINISHED"}


class OBJECT_PT_SneakerPanelProMain(bpy.types.Panel):
    bl_label = "Sneaker Panel Pro"
    bl_idname = "OBJECT_PT_sneaker_panel_pro_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Sneaker Panel"

    def draw_header(self, context):
        """Draw custom header with icon."""
        layout = self.layout
        # Get the custom icon ID
        icon_id = icons.get_icon("uv_checker")
        if icon_id:
            layout.label(text="", icon_value=icon_id)

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        scn = context.scene

        # Workflow Controls
        workflow_box = layout.box()

        # Segmented workflow selector
        seg = workflow_box.row(align=True)
        seg.scale_y = 1.4

        b = seg.operator(
            "wm.spp_toggle_workflow",
            text="Surface Direct [3D]",
            icon="MESH_CUBE",
            depress=(wm.spp_active_workflow == "SURFACE_3D"),
        )
        b.mode = "SURFACE_3D"

        b = seg.operator(
            "wm.spp_toggle_workflow",
            text="UV Workflow [2D]",
            icon="MESH_GRID",
            depress=(wm.spp_active_workflow == "UV_2D"),
        )
        b.mode = "UV_2D"

        # Feature toggles
        workflow_box.separator(factor=0.5)
        toggles = workflow_box.row(align=True)
        toggles.scale_y = 1.1

        t = toggles.operator(
            "wm.context_toggle", text="Auto UV", icon="UV", depress=wm.spp_show_auto_uv
        )
        t.data_path = "window_manager.spp_show_auto_uv"

        t = toggles.operator(
            "wm.context_toggle",
            text="Lace Generator",
            icon="CURVE_NCURVE",
            depress=wm.spp_show_lace_gen,
        )
        t.data_path = "window_manager.spp_show_lace_gen"

        # Panel Configuration
        layout.separator(factor=0.8)
        main_box = layout.box()
        header_row = main_box.row()
        header_row.label(text="Panel Configuration", icon="COLLECTION_COLOR_05")

        main_box.separator(factor=0.3)
        config_row = main_box.row(align=True)
        config_row.prop(scn, "spp_panel_count", text="Panel")
        config_row.prop(scn, "spp_panel_name", text="Name")

        main_box.separator(factor=0.3)
        shell_row = main_box.row()
        shell_row.prop_search(
            scn,
            "spp_shell_object",
            bpy.data,
            "objects",
            text="Shell Object",
            icon="OUTLINER_OB_MESH",
        )

        # Panel Helper Tools
        layout.separator(factor=0.8)
        tools_box = layout.box()
        tools_header = tools_box.row()
        tools_header.label(text="Panel Helper Tools", icon="TOOL_SETTINGS")

        # Edge Select
        tools_box.separator(factor=0.3)
        select_box = tools_box.box()
        select_box.label(text="Edge Select", icon="UV_EDGESEL")
        sel_grid = select_box.grid_flow(columns=2, align=True)
        sel_grid.scale_y = 1.0

        sel_grid.operator(
            "mesh.select_all", text="Select All", icon="SELECT_SET"
        ).action = "SELECT"
        sel_grid.operator("mesh.loop_multi_select", text="Edge Loops", icon="EDGESEL")
        sel_grid.operator(
            "mesh.deselect_boundary_edges",
            text="Deselect Boundary",
            icon="RESTRICT_SELECT_ON",
        )
        sel_grid.operator(
            "mesh.select_boundary_edges",
            text="Select Boundary",
            icon="RESTRICT_SELECT_OFF",
        )

        # Edge Flow
        flow_box = tools_box.box()
        flow_box.label(text="Edge Flow", icon="VIEW_PERSPECTIVE")
        flow_grid = flow_box.grid_flow(columns=3, align=True)
        flow_grid.scale_y = 1.0

        flow_grid.operator("mesh.set_edge_linear", text="Straighten", icon="IPO_LINEAR")
        flow_grid.operator("mesh.edge_relax", text="Relax", icon="MOD_SMOOTH")
        flow_grid.operator("mesh.set_edge_flow", text="Set Flow", icon="FORCE_FORCE")

        # Mesh Object Tools
        panel_box = tools_box.box()
        panel_box.label(text="Mesh Object", icon="OUTLINER_OB_MESH")

        # Shading controls
        obj = context.active_object
        shading_row = panel_box.row(align=True)
        shading_row.scale_y = 0.9

        # Check current shading mode
        is_smooth = False
        if obj and obj.type == "MESH" and obj.data.polygons:
            is_smooth = any(poly.use_smooth for poly in obj.data.polygons)

        shading_row.operator(
            "object.shade_smooth",
            text="Smooth",
            icon="SHADING_RENDERED",
            depress=is_smooth,
        )
        shading_row.operator(
            "object.shade_flat",
            text="Flat",
            icon="SHADING_SOLID",
            depress=not is_smooth,
        )

        # Object tools
        panel_box.separator(factor=0.3)
        panel_grid = panel_box.grid_flow(columns=3, align=True)
        panel_grid.scale_y = 1.0

        panel_grid.operator("mesh.add_subsurf", text="SubD", icon="MOD_SUBSURF")
        panel_grid.operator("mesh.mirror_panel", text="Mirror", icon="MOD_MIRROR")
        panel_grid.operator(
            "mesh.apply_shrinkwrap", text="Shrinkwrap", icon="MOD_SHRINKWRAP"
        )

        panel_box.separator(factor=0.3)
        fitment_row = panel_box.row(align=True)
        fitment_row.scale_y = 1.0
        fitment_row.operator("mesh.quick_conform", text="Quick Conform", icon="SNAP_ON")
        fitment_row.operator("mesh.smooth_mesh", text="Smooth Mesh", icon="MOD_SMOOTH")

        # Thicken Panel (Solidify) section
        panel_box.separator(factor=0.5)
        panel_box.label(text="Thicken Panel", icon="MOD_SOLIDIFY")

        obj = context.active_object
        if obj and obj.type == "MESH":
            # Get existing Solidify modifier and sync scene props if present
            mod = obj.modifiers.get("Solidify")
            if mod:
                try:
                    if (
                        hasattr(scn, "spp_solidify_thickness")
                        and getattr(mod, "thickness", None) is not None
                        and scn.spp_solidify_thickness != mod.thickness
                    ):
                        scn.spp_solidify_thickness = mod.thickness
                    if (
                        hasattr(scn, "spp_solidify_offset")
                        and hasattr(mod, "offset")
                        and scn.spp_solidify_offset != mod.offset
                    ):
                        scn.spp_solidify_offset = mod.offset
                    if (
                        hasattr(scn, "spp_solidify_even_thickness")
                        and hasattr(mod, "use_even_offset")
                        and scn.spp_solidify_even_thickness != mod.use_even_offset
                    ):
                        scn.spp_solidify_even_thickness = mod.use_even_offset
                    if (
                        hasattr(scn, "spp_solidify_rim")
                        and hasattr(mod, "use_rim")
                        and scn.spp_solidify_rim != mod.use_rim
                    ):
                        scn.spp_solidify_rim = mod.use_rim
                    if (
                        hasattr(scn, "spp_solidify_rim_only")
                        and hasattr(mod, "use_rim_only")
                        and scn.spp_solidify_rim_only != mod.use_rim_only
                    ):
                        scn.spp_solidify_rim_only = mod.use_rim_only
                except Exception:
                    pass

            # Always show Add Solidify button when a mesh is selected
            buttons = panel_box.row(align=True)
            buttons.scale_y = 1.0
            add = buttons.operator(
                "object.solidify_panel", text="Add Solidify", icon="MODIFIER"
            )
            add.thickness = scn.spp_solidify_thickness

            # Show parameters and Finalize only when a Solidify modifier exists
            if mod:
                panel_box.separator(factor=0.4)
                # Parameter controls (live update via property callbacks)
                panel_box.separator(factor=0.3)
                panel_box.prop(scn, "spp_solidify_thickness", text="Thickness")
                panel_box.prop(scn, "spp_solidify_offset", text="Offset")

                toggles = panel_box.row(align=True)
                toggles.scale_y = 0.9
                toggles.prop(scn, "spp_solidify_even_thickness", text="Even")
                toggles.prop(scn, "spp_solidify_rim", text="Fill Rim")
                toggles.prop(scn, "spp_solidify_rim_only", text="Only Rim")

                # Finalize (Apply) button
                panel_box.separator(factor=0.3)
                apply_row = panel_box.row(align=True)
                apply_row.scale_y = 1.0
                apply_row.operator(
                    "object.apply_solidify", text="Finalize", icon="CHECKMARK"
                )
        else:
            panel_box.separator(factor=0.3)
            info_row = panel_box.row()
            info_row.enabled = False
            info_row.label(
                text="Select a mesh object to enable solidify controls", icon="INFO"
            )


# Registration
classes = [WM_OT_SPP_ToggleWorkflow, OBJECT_PT_SneakerPanelProMain]


def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception:
            pass


def unregister():
    for cls in reversed(classes):
        try:
            if hasattr(cls, "bl_rna"):
                bpy.utils.unregister_class(cls)
        except Exception:
            pass


if __name__ == "__main__":
    register()
