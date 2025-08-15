# sneaker_panel_pro/state.py
import bpy
from bpy.props import BoolProperty, EnumProperty


def register():
    WM = bpy.types.WindowManager
    SC = bpy.types.Scene

    # Workflow radio (exactly one; supports 'NONE' to hide all workflows)
    if not hasattr(WM, "spp_active_workflow"):
        WM.spp_active_workflow = EnumProperty(
            name="Active Workflow",
            items=[
                ("SURFACE_3D", "Surface 3D", ""),
                ("UV_2D", "UV 2D", ""),
                ("NONE", "None", "Hide all workflow panels"),
            ],
            default="SURFACE_3D",
        )

    # Independent toggles
    if not hasattr(WM, "spp_show_auto_uv"):
        WM.spp_show_auto_uv = BoolProperty(name="Show Auto UV", default=False)
    if not hasattr(WM, "spp_show_lace_gen"):
        WM.spp_show_lace_gen = BoolProperty(name="Show Lace Generator", default=False)

    # Surface workflow step toggles
    if not hasattr(WM, "spp_show_surface_step_2"):
        WM.spp_show_surface_step_2 = BoolProperty(name="Show Surface Step 2", default=True)
    if not hasattr(WM, "spp_show_surface_step_3"):
        WM.spp_show_surface_step_3 = BoolProperty(name="Show Surface Step 3", default=True)
    if not hasattr(WM, "spp_show_surface_step_4"):
        WM.spp_show_surface_step_4 = BoolProperty(name="Show Surface Step 4", default=True)

    # UV workflow step toggles
    if not hasattr(WM, "spp_show_uv_step_2"):
        WM.spp_show_uv_step_2 = BoolProperty(name="Show UV Step 2", default=True)
    if not hasattr(WM, "spp_show_uv_step_4"):
        WM.spp_show_uv_step_4 = BoolProperty(name="Show UV Step 4", default=True)
    if not hasattr(WM, "spp_show_uv_step_5"):
        WM.spp_show_uv_step_5 = BoolProperty(name="Show UV Step 5", default=True)
    if not hasattr(WM, "spp_show_uv_step_6"):
        WM.spp_show_uv_step_6 = BoolProperty(name="Show UV Step 6", default=True)

    # Experimental panel internal radio
    if not hasattr(SC, "spp_nurbs_qd_active"):
        SC.spp_nurbs_qd_active = EnumProperty(
            name="NURBS QD Active",
            items=[
                ("QD_UV_CURVE", "UV Curve Q&D", ""),
                ("QD_BEZIER", "Bezier Q&D", ""),
            ],
            default="QD_UV_CURVE",
        )


def unregister():
    # guard deletions so reloads don't crash
    if hasattr(bpy.types.WindowManager, "spp_active_workflow"):
        del bpy.types.WindowManager.spp_active_workflow
    if hasattr(bpy.types.WindowManager, "spp_show_auto_uv"):
        del bpy.types.WindowManager.spp_show_auto_uv
    if hasattr(bpy.types.WindowManager, "spp_show_lace_gen"):
        del bpy.types.WindowManager.spp_show_lace_gen

    # Surface workflow step toggles cleanup
    if hasattr(bpy.types.WindowManager, "spp_show_surface_step_2"):
        del bpy.types.WindowManager.spp_show_surface_step_2
    if hasattr(bpy.types.WindowManager, "spp_show_surface_step_3"):
        del bpy.types.WindowManager.spp_show_surface_step_3
    if hasattr(bpy.types.WindowManager, "spp_show_surface_step_4"):
        del bpy.types.WindowManager.spp_show_surface_step_4

    # UV workflow step toggles cleanup
    if hasattr(bpy.types.WindowManager, "spp_show_uv_step_2"):
        del bpy.types.WindowManager.spp_show_uv_step_2
    if hasattr(bpy.types.WindowManager, "spp_show_uv_step_4"):
        del bpy.types.WindowManager.spp_show_uv_step_4
    if hasattr(bpy.types.WindowManager, "spp_show_uv_step_5"):
        del bpy.types.WindowManager.spp_show_uv_step_5
    if hasattr(bpy.types.WindowManager, "spp_show_uv_step_6"):
        del bpy.types.WindowManager.spp_show_uv_step_6

    if hasattr(bpy.types.Scene, "spp_nurbs_qd_active"):
        del bpy.types.Scene.spp_nurbs_qd_active
