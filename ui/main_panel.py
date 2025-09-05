
import bpy
from bpy.props import EnumProperty
from bpy.types import Operator

from ..utils import icons


class WM_OT_SPP_ToggleWorkflow(Operator):
    bl_idname = "wm.spp_toggle_workflow"
    bl_label = "Toggle Workflow"
    bl_description = "Enable/disable a workflow. Clicking the active button toggles workflow off (None)."
    bl_options = {"INTERNAL"}

    mode: EnumProperty(
        name="Mode",
        items=[("SURFACE_3D", "Surface 3D", ""), ("UV_2D", "UV 2D", "")],
    )

    def execute(self, context):
        wm = context.window_manager
        current = getattr(wm, "spp_active_workflow", "NONE")
        wm.spp_active_workflow = "NONE" if current == self.mode else self.mode
        return {"FINISHED"}


class OBJECT_PT_SneakerPanelProMain(bpy.types.Panel):
    bl_label = " Sneaker Panel Pro"
    bl_idname = "OBJECT_PT_sneaker_panel_pro_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Sneaker Panel"

    def draw_header(self, context):
        """Draw custom header with icon."""
        layout = self.layout
        # Get the custom icon ID
        icon_id = icons.get_icon("logo")
        layout.label(text="", icon_value=icon_id)

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        scn = context.scene

        # === Workflow Controls ===
        workflow_box = layout.box()

        # === Top: Segmented workflow selector ===
        seg = workflow_box.row()
        seg.scale_y = 1.75

        left = seg.row()
        b = left.operator(
            "wm.spp_toggle_workflow",
            text=" Surface Direct [3D] ",
            icon_value=icons.get_icon("3d"),
            depress=(wm.spp_active_workflow == "SURFACE_3D"),
        )
        b.mode = "SURFACE_3D"

        right = seg.row()
        b = right.operator(
            "wm.spp_toggle_workflow",
            text=" UV Workflow [2D] ",
            icon_value=icons.get_icon("2d"),
            depress=(wm.spp_active_workflow == "UV_2D"),
        )
        b.mode = "UV_2D"

        # === Compact toggles ===
        toggles = workflow_box.row()
        toggles.scale_y = 1.3
        t = toggles.operator(
            "wm.context_toggle", text=" Auto UV", icon_value=icons.get_icon("auto_uv"), depress=wm.spp_show_auto_uv
        )
        t.data_path = "window_manager.spp_show_auto_uv"
        t = toggles.operator(
            "wm.context_toggle",
            text=" Lace Generator",
            icon_value=icons.get_icon("laces"),
            depress=wm.spp_show_lace_gen,
        )
        t.data_path = "window_manager.spp_show_lace_gen"
        t = toggles.operator(
            "wm.context_toggle",
            text=" Profile Projection",
            icon_value=icons.get_icon("ref_image"),
            depress=wm.spp_show_profile_projection,
        )
        t.data_path = "window_manager.spp_show_profile_projection"

        # === Panel Configuration ===
        main_box = layout.box()
        header_row = main_box.row()
        icon_id = icons.get_icon("edit")
        if icon_id:
            header_row.label(text="Panel Configuration", icon_value=icon_id)
        else:
            header_row.label(text="Panel Configuration")

        row = main_box.row()
        row.prop(scn, "spp_panel_count", text="Panel #")
        row.prop(scn, "spp_panel_name", text=" Name")

        shell_row = main_box.row()
        shell_row.prop_search(
            scn,
            "spp_shell_object",
            bpy.data,
            "objects",
            text="Shell Object",
            icon="OUTLINER_OB_MESH",
        )

        # === Panel Helper Tools ===
        tools_box = layout.box()
        tools_header = tools_box.row()
        icon_id = icons.get_icon("tools")
        if icon_id:
            tools_header.label(text="Panel Helper Tools", icon_value=icon_id)
            icon = 'LIGHT_SUN' if context.window_manager.spp_show_helper_tooltip else 'INFO'
            tools_header.prop(context.window_manager, "spp_show_helper_tooltip", text="", toggle=True, icon=icon)

        # When toggled on, show compact tips
        if context.window_manager.spp_show_helper_tooltip:
            tip_box = tools_box.box()
            tip_box.alert = True
            col = tip_box.column(align=True)
            col.label(text="• Smooth Mesh — relaxes interior quads after fill")
            col.label(text="• Merge by Distance — collapses tiny edges/verts")
            col.label(text="• Checker Dissolve — halves interior density quickly")
            col.label(text="• Edge Flow/Relax — evens spacing without shrinking border")
            col.operator(
                "wm.url_open", text="View Helper Tooltips Tutorial", icon="URL"
            ).url = "https://example.com/helper-tooltips-tutorial"
            
        # Edge & Loop Refinement (collapsible)
        refinement_box = tools_box.box()
        refinement_header = refinement_box.row(align=True)
        refinement_header.prop(scn, "spp_show_edge_refinement", toggle=True, text="Edge & Loop Refinement", icon="TRIA_DOWN" if getattr(scn, "spp_show_edge_refinement", False) else "TRIA_RIGHT")
        
        if getattr(scn, "spp_show_edge_refinement", False):
            # Selection tools
            refinement_box.label(text="Selection:", icon="SELECT_SET")
            sel_grid = refinement_box.grid_flow(columns=2, align=True)
            sel_grid.scale_y = 1.3
            sel_grid.operator(
                "mesh.select_all", text="Select All", icon="SELECT_SET"
            ).action = "SELECT"
            sel_grid.operator(
                "mesh.loop_multi_select", text="Select Edge Loops", icon="EDGESEL"
            )
            sel_grid.operator(
                "mesh.deselect_boundary_edges", text="Deselect Boundary", icon="EDGESEL"
            )
            sel_grid.operator(
                "mesh.select_boundary_edges", text="Select Boundary", icon="EDGESEL"
            )
            
            # Flow tools
            refinement_box.label(text="Edge Flow:", icon="FORCE_FORCE")
            flow_grid = refinement_box.grid_flow(columns=3, align=True)
            flow_grid.scale_y = 1.3
            flow_grid.operator("mesh.set_edge_linear", text="Straighten", icon="IPO_LINEAR")
            flow_grid.operator("mesh.edge_relax", text="Relax", icon="MOD_SMOOTH")
            flow_grid.operator("mesh.set_edge_flow", text="Set Flow", icon="FORCE_FORCE")

        # Mesh Object Tools (collapsible)
        panel_box = tools_box.box()
        panel_header = panel_box.row(align=True)
        panel_header.prop(scn, "spp_show_mesh_object", toggle=True, text="Mesh Object", icon="TRIA_DOWN" if getattr(scn, "spp_show_mesh_object", False) else "TRIA_RIGHT")
        
        if getattr(scn, "spp_show_mesh_object", False):
            # Shading controls
            obj = context.active_object
            shading_row = panel_box.row()

            # Check current shading mode
            is_smooth = False
            if obj and obj.type == "MESH" and obj.data.polygons:
                # Check if any face is smooth (if any face is smooth, consider object as smooth)
                is_smooth = any(poly.use_smooth for poly in obj.data.polygons)

            shading_row.operator(
                "object.shade_smooth",
                text="Shade Smooth",
                icon="SHADING_RENDERED",
                depress=is_smooth,
            )
            shading_row.operator(
                "object.shade_flat",
                text="Shade Flat",
                icon="SHADING_SOLID",
                depress=not is_smooth,
            )

            # Object tools
            panel_grid = panel_box.grid_flow(columns=3, align=True)
            panel_grid.scale_y = 1.2    
            panel_grid.operator("mesh.add_subsurf", text="SubD", icon="MOD_SUBSURF")
            panel_grid.operator("mesh.mirror_panel", text="Mirror", icon="MOD_MIRROR")
            panel_grid.operator(
                "mesh.apply_shrinkwrap", text="Shrinkwrap", icon="MOD_SHRINKWRAP"
            )

            fitment_row = panel_box.row(align=True)
            fitment_row.operator("mesh.quick_conform", text="Quick Conform", icon="SNAP_ON")
            fitment_row.operator("mesh.smooth_mesh", text="Smooth Mesh", icon="MOD_SMOOTH")

            # Thicken Panel (Solidify) section
            panel_box.label(text="Thicken Panel:", icon="MOD_SOLIDIFY")

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
                add = buttons.operator(
                    "object.solidify_panel", text="Add Solidify", icon="MODIFIER"
                )
                add.thickness = scn.spp_solidify_thickness

                # Show parameters and Finalize only when a Solidify modifier exists
                if mod:
                    panel_box.separator(factor=0.4)
                    # Parameter controls (live update via property callbacks)
                    panel_box.prop(scn, "spp_solidify_thickness", text="Thickness")
                    row = panel_box.row(align=True)
                    row.prop(scn, "spp_solidify_offset", text="Offset")
                    toggles = panel_box.row(align=True)
                    toggles.prop(scn, "spp_solidify_even_thickness", text="Even")
                    toggles.prop(scn, "spp_solidify_rim", text="Fill Rim")
                    toggles.prop(scn, "spp_solidify_rim_only", text="Only Rim")

                    # Finalize (Apply) button
                    apply_row = panel_box.row(align=True)
                    apply_row.operator(
                        "object.apply_solidify", text="Finalize", icon="CHECKMARK"
                    )
            else:
                panel_box.label(
                    text="Select a mesh object to enable solidify controls.", icon="INFO"
                )
                
        # Retopology section (only visible in edit mode)
        if context.mode == 'EDIT_MESH':
            retopo_box = tools_box.box()
            retopo_header = retopo_box.row(align=True)
            retopo_header.prop(scn, "spp_show_retopology", toggle=True, text="Retopology ViewPort Context", icon="TRIA_DOWN" if getattr(scn, "spp_show_retopology", False) else "TRIA_RIGHT")
            
            if getattr(scn, "spp_show_retopology", False):
                retopo_content = retopo_box.column(align=True)
                
                # Enable/disable retopology overlay
                overlay = context.space_data.overlay
                retopo_content.prop(overlay, "show_retopology", text="Show Retopology")
                
                if overlay.show_retopology:
                    # Retopology opacity slider
                    retopo_content.prop(overlay, "retopology_offset", text="Offset", slider=True)


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
