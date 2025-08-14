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
    # guard deletions so reloads don’t crash
    if hasattr(bpy.types.WindowManager, "spp_active_workflow"):
        del bpy.types.WindowManager.spp_active_workflow
    if hasattr(bpy.types.WindowManager, "spp_show_auto_uv"):
        del bpy.types.WindowManager.spp_show_auto_uv
    if hasattr(bpy.types.WindowManager, "spp_show_lace_gen"):
        del bpy.types.WindowManager.spp_show_lace_gen
    if hasattr(bpy.types.Scene, "spp_nurbs_qd_active"):
        del bpy.types.Scene.spp_nurbs_qd_active
