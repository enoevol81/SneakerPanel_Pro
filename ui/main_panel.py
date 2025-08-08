# File: ui/main_panel.py
"""Main panel for the Sneaker Panel Pro addon.

This panel contains only:
- Workflow toggles (Surface Direct [3D] / UV Workflow [2D])
- Compact toggles (Auto UV / Lace Generator)
- Panel Configuration
- Panel Helper Tools
- Thicken Panel (Solidify)
No Step 1/2/3 workflow content lives here; those are in their workflow panels.
"""

import bpy


class OBJECT_PT_SneakerPanelProMain(bpy.types.Panel):
    bl_label = "Sneaker Panel Pro"
    bl_idname = "OBJECT_PT_sneaker_panel_pro_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Sneaker Panel'

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        scn = context.scene

        # === Top: Segmented workflow selector ===
        seg = layout.row(align=True); seg.scale_y = 1.5

        left = seg.row(align=True)
        b = left.operator("wm.context_set_enum",
                          text=" Surface Direct [3D] ",
                          icon='MESH_CUBE',
                          depress=(wm.spp_active_workflow == 'SURFACE_3D'))
        b.data_path = "window_manager.spp_active_workflow"; b.value = 'SURFACE_3D'

        right = seg.row(align=True)
        b = right.operator("wm.context_set_enum",
                           text=" UV Workflow [2D] ",
                           icon='MESH_GRID',
                           depress=(wm.spp_active_workflow == 'UV_2D'))
        b.data_path = "window_manager.spp_active_workflow"; b.value = 'UV_2D'

        layout.separator(factor=0.5)

        # === Compact toggles ===
        toggles = layout.row(align=True)
        t = toggles.operator("wm.context_toggle", text=" Auto UV", icon='UV', depress=wm.spp_show_auto_uv)
        t.data_path = "window_manager.spp_show_auto_uv"
        t = toggles.operator("wm.context_toggle", text=" Lace Generator", icon='CURVE_NCURVE', depress=wm.spp_show_lace_gen)
        t.data_path = "window_manager.spp_show_lace_gen"

        layout.separator()

        # === Panel Configuration ===
        main_box = layout.box()
        header_row = main_box.row()
        header_row.label(text="Panel Configuration", icon="SETTINGS")

        row = main_box.row(align=True)
        row.prop(scn, "spp_panel_count", text="Panel #")
        row.prop(scn, "spp_panel_name", text="Name")

        shell_row = main_box.row(align=True)
        shell_row.prop_search(scn, "spp_shell_object", bpy.data, "objects", text="Shell Object", icon="OUTLINER_OB_MESH")

        # === Panel Helper Tools ===
        tools_box = layout.box()
        tools_header = tools_box.row()
        tools_header.label(text="Panel Helper Tools", icon="TOOL_SETTINGS")

        tools_grid_edgeflow = tools_box.grid_flow(columns=2, align=True); tools_grid_edgeflow.scale_y = 1.1
        tools_grid_edgeflow.operator("mesh.set_edge_flow", text="Set Edge Flow", icon="MOD_SMOOTH")
        tools_grid_edgeflow.operator("mesh.edge_relax", text="Edge Relax", icon="MOD_SMOOTH")

        tools_grid_edgeflow.operator("mesh.select_all", text="Select All", icon="SELECT_SET").action = 'SELECT'
        tools_grid_edgeflow.operator("mesh.loop_multi_select", text="Select Edge Loops", icon="EDGESEL")

        tools_grid_mod = tools_box.grid_flow(columns=2, align=True); tools_grid_mod.scale_y = 1.1
        tools_grid_mod.operator("mesh.mirror_panel", text="Mirror Panel", icon="MOD_MIRROR")
        tools_grid_mod.operator("mesh.apply_shrinkwrap", text="Apply Shrinkwrap", icon="MOD_SHRINKWRAP")

        tools_grid_mod2 = tools_box.grid_flow(columns=1, align=True); tools_grid_mod2.scale_y = 1.1
        tools_grid_mod2.operator("mesh.quick_conform", text="Quick Conform", icon="SNAP_ON")

        # === Thicken Panel (Solidify) ===
        finalize = layout.box()
        finalize.label(text="Thicken Panel", icon='MOD_SOLIDIFY')
        # Only show the button; the full parameters/UI live in finalize_panel.py
        finalize.operator("object.solidify_panel", text="Solidify", icon='MODIFIER')


# Registration
classes = [OBJECT_PT_SneakerPanelProMain]

def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception:
            pass

def unregister():
    for cls in reversed(classes):
        try:
            if hasattr(cls, 'bl_rna'):
                bpy.utils.unregister_class(cls)
        except Exception:
            pass

if __name__ == "__main__":
    register()
