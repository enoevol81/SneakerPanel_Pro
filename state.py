# sneaker_panel_pro/state.py
import bpy
from bpy.props import EnumProperty, BoolProperty


def register():
    WM = bpy.types.WindowManager
    SC = bpy.types.Scene

    # -------------------------------------------------------------------------
    # Active workflow (already present; keep as-is)
    # -------------------------------------------------------------------------
    if not hasattr(WM, "spp_active_workflow"):
        WM.spp_active_workflow = EnumProperty(
            name="Active Workflow",
            items=[
                ('SURFACE_3D', 'Surface 3D', ''),
                ('UV_2D', 'UV 2D', ''),
                ('NONE', 'None', 'Hide all workflow panels'),
            ],
            default='SURFACE_3D'
        )

    # -------------------------------------------------------------------------
    # Independent toggles (keep your existing)
    # -------------------------------------------------------------------------
    if not hasattr(WM, "spp_show_auto_uv"):
        WM.spp_show_auto_uv = BoolProperty(name="Show Auto UV", default=False)
    if not hasattr(WM, "spp_show_lace_gen"):
        WM.spp_show_lace_gen = BoolProperty(name="Show Lace Generator", default=False)

    # -------------------------------------------------------------------------
    # NEW: Helper Tooltips toggle for "Panel Helper Tools"
    # -------------------------------------------------------------------------
    if not hasattr(WM, "spp_show_helper_tooltip"):
        WM.spp_show_helper_tooltip = BoolProperty(
            name="Show Helper Tooltip",
            default=False,
            description="Show/hide Helper Tools tips in the main panel"
        )

    # -------------------------------------------------------------------------
    # NEW: Collapsible step toggles — Surface (3D)
    # -------------------------------------------------------------------------
    if not hasattr(WM, "spp_show_surface_step_1"):
        WM.spp_show_surface_step_1 = BoolProperty(
            name="Show Surface Step 1", default=True,
            description="Toggle visibility of Surface Step 1"
        )
    if not hasattr(WM, "spp_show_surface_step_2"):
        WM.spp_show_surface_step_2 = BoolProperty(
            name="Show Surface Step 2", default=True,
            description="Toggle visibility of Surface Step 2"
        )
    if not hasattr(WM, "spp_show_surface_step_3"):
        WM.spp_show_surface_step_3 = BoolProperty(
            name="Show Surface Step 3", default=True,
            description="Toggle visibility of Surface Step 3"
        )
    if not hasattr(WM, "spp_show_surface_step_4"):
        WM.spp_show_surface_step_4 = BoolProperty(
            name="Show Surface Step 4", default=True,
            description="Toggle visibility of Surface Step 4"
        )

    # -------------------------------------------------------------------------
    # NEW: Collapsible step toggles — UV (2D)
    # -------------------------------------------------------------------------
    
    if not hasattr(WM, "spp_show_uv_step_1"):
        WM.spp_show_uv_step_1 = BoolProperty(
            name="Show UV Step 1", default=True,
            description="Toggle visibility of UV Step 1"
        )
    if not hasattr(WM, "spp_show_uv_step_2"):
        WM.spp_show_uv_step_2 = BoolProperty(
            name="Show UV Step 2", default=True,
            description="Toggle visibility of UV Step 2"
        )
    if not hasattr(WM, "spp_show_uv_step_3"):
        WM.spp_show_uv_step_3 = BoolProperty(
            name="Show UV Step 3", default=True,
            description="Toggle visibility of UV Step 3"
        )
    if not hasattr(WM, "spp_show_uv_step_4"):
        WM.spp_show_uv_step_4 = BoolProperty(
            name="Show UV Step 4", default=True,
            description="Toggle visibility of UV Step 4"
        )
    if not hasattr(WM, "spp_show_uv_step_5"):
        WM.spp_show_uv_step_5 = BoolProperty(
            name="Show UV Step 5", default=True,
            description="Toggle visibility of UV Step 5"
        )
    if not hasattr(WM, "spp_show_uv_step_6"):
        WM.spp_show_uv_step_6 = BoolProperty(
            name="Show UV Step 6", default=True,
            description="Toggle visibility of UV Step 6"
        )

    # -------------------------------------------------------------------------
    # Experimental panel internal radio (keep yours)
    # -------------------------------------------------------------------------
    if not hasattr(SC, "spp_nurbs_qd_active"):
        SC.spp_nurbs_qd_active = EnumProperty(
            name="NURBS QD Active",
            items=[('QD_UV_CURVE', 'UV Curve Q&D', ''), ('QD_BEZIER', 'Bezier Q&D', '')],
            default='QD_UV_CURVE'
        )


def unregister():
    # guard deletions so reloads don’t crash
    rmW = getattr(bpy.types, "WindowManager", None)
    rmS = getattr(bpy.types, "Scene", None)

    if rmW and hasattr(rmW, "spp_active_workflow"):
        delattr(rmW, "spp_active_workflow")
    if rmW and hasattr(rmW, "spp_show_auto_uv"):
        delattr(rmW, "spp_show_auto_uv")
    if rmW and hasattr(rmW, "spp_show_lace_gen"):
        delattr(rmW, "spp_show_lace_gen")

    # NEW
    for name in (
        "spp_show_helper_tooltip",
        "spp_show_surface_step_1", "spp_show_surface_step_2", "spp_show_surface_step_3", "spp_show_surface_step_4",
        "spp_show_uv_step_1", "spp_show_uv_step_2", "spp_show_uv_step_3", "spp_show_uv_step_4", "spp_show_uv_step_5", "spp_show_uv_step_6",
    ):
        if rmW and hasattr(rmW, name):
            delattr(rmW, name)

    if rmS and hasattr(rmS, "spp_nurbs_qd_active"):
        delattr(rmS, "spp_nurbs_qd_active")
