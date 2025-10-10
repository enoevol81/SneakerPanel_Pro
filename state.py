# sneaker_panel_pro/state.py
import bpy
from bpy.props import EnumProperty, BoolProperty


def update_surface_step_1(self, context):
    """Ensure only one surface step is open at a time"""
    if self.spp_show_surface_step_1:
        self.spp_show_surface_step_2 = False
        self.spp_show_surface_step_3 = False
        self.spp_show_surface_step_4 = False


def update_surface_step_2(self, context):
    """Ensure only one surface step is open at a time"""
    if self.spp_show_surface_step_2:
        self.spp_show_surface_step_1 = False
        self.spp_show_surface_step_3 = False
        self.spp_show_surface_step_4 = False


def update_surface_step_4(self, context):
    """Ensure only one surface step is open at a time"""
    if self.spp_show_surface_step_4:
        self.spp_show_surface_step_1 = False
        self.spp_show_surface_step_2 = False
        self.spp_show_surface_step_3 = False


def update_uv_step_1(self, context):
    """Ensure only one UV step is open at a time"""
    if self.spp_show_uv_step_1:
        self.spp_show_uv_step_2 = False
        self.spp_show_uv_step_3 = False
        self.spp_show_uv_step_4 = False
        self.spp_show_uv_step_5 = False
        self.spp_show_uv_step_6 = False


def update_uv_step_2(self, context):
    """Ensure only one UV step is open at a time"""
    if self.spp_show_uv_step_2:
        self.spp_show_uv_step_1 = False
        self.spp_show_uv_step_3 = False
        self.spp_show_uv_step_4 = False
        self.spp_show_uv_step_5 = False
        self.spp_show_uv_step_6 = False


def update_uv_step_4(self, context):
    """Ensure only one UV step is open at a time"""
    if self.spp_show_uv_step_4:
        self.spp_show_uv_step_1 = False
        self.spp_show_uv_step_2 = False
        self.spp_show_uv_step_3 = False
        self.spp_show_uv_step_5 = False
        self.spp_show_uv_step_6 = False


def update_uv_step_5(self, context):
    """Ensure only one UV step is open at a time"""
    if self.spp_show_uv_step_5:
        self.spp_show_uv_step_1 = False
        self.spp_show_uv_step_2 = False
        self.spp_show_uv_step_3 = False
        self.spp_show_uv_step_4 = False
        self.spp_show_uv_step_6 = False


def update_uv_step_6(self, context):
    """Ensure only one UV step is open at a time"""
    if self.spp_show_uv_step_6:
        self.spp_show_uv_step_1 = False
        self.spp_show_uv_step_2 = False
        self.spp_show_uv_step_3 = False
        self.spp_show_uv_step_4 = False
        self.spp_show_uv_step_5 = False


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
                ("SURFACE_3D", "Surface 3D", ""),
                ("UV_2D", "UV 2D", ""),
                ("NONE", "None", "Hide all workflow panels"),
            ],
            default="SURFACE_3D",
        )

    # -------------------------------------------------------------------------
    # Independent toggles (keep your existing)
    # -------------------------------------------------------------------------
    if not hasattr(WM, "spp_show_auto_uv"):
        WM.spp_show_auto_uv = BoolProperty(name="Show Auto UV", default=False)
    if not hasattr(WM, "spp_show_lace_gen"):
        WM.spp_show_lace_gen = BoolProperty(name="Show Lace Generator", default=False)
    if not hasattr(WM, "spp_show_profile_projection"):
        WM.spp_show_profile_projection = BoolProperty(
            name="Show Profile Projection", default=False
        )

    # -------------------------------------------------------------------------
    # NEW: Helper Tooltips toggle for "Panel Helper Tools"
    # -------------------------------------------------------------------------
    if not hasattr(WM, "spp_show_helper_tooltip"):
        WM.spp_show_helper_tooltip = BoolProperty(
            name="Show Helper Tooltip",
            default=False,
            description="Show/hide Helper Tools tips in the main panel",
        )

    # -------------------------------------------------------------------------
    # NEW: Collapsible step toggles — Surface (3D)
    # -------------------------------------------------------------------------
    if not hasattr(WM, "spp_show_surface_step_1"):
        WM.spp_show_surface_step_1 = BoolProperty(
            name="Show Surface Step 1",
            default=True,
            description="Toggle visibility of Surface Step 1",
            update=update_surface_step_1,
        )
    if not hasattr(WM, "spp_show_surface_step_2"):
        WM.spp_show_surface_step_2 = BoolProperty(
            name="Show Surface Step 2",
            default=False,
            description="Toggle visibility of Surface Step 2",
            update=update_surface_step_2,
        )
    if not hasattr(WM, "spp_show_surface_step_3"):
        WM.spp_show_surface_step_3 = BoolProperty(
            name="Show Surface Step 3",
            default=False,
            description="Toggle visibility of Surface Step 3",
        )
    if not hasattr(WM, "spp_show_surface_step_4"):
        WM.spp_show_surface_step_4 = BoolProperty(
            name="Show Surface Step 4",
            default=False,
            description="Toggle visibility of Surface Step 4",
            update=update_surface_step_4,
        )

    # -------------------------------------------------------------------------
    # NEW: Collapsible step toggles — UV (2D)
    # -------------------------------------------------------------------------

    if not hasattr(WM, "spp_show_uv_step_1"):
        WM.spp_show_uv_step_1 = BoolProperty(
            name="Show UV Step 1",
            default=True,
            description="Toggle visibility of UV Step 1",
            update=update_uv_step_1,
        )
    if not hasattr(WM, "spp_show_uv_step_2"):
        WM.spp_show_uv_step_2 = BoolProperty(
            name="Show UV Step 2",
            default=False,
            description="Toggle visibility of UV Step 2",
            update=update_uv_step_2,
        )
    if not hasattr(WM, "spp_show_uv_step_3"):
        WM.spp_show_uv_step_3 = BoolProperty(
            name="Show UV Step 3",
            default=False,
            description="Toggle visibility of UV Step 3",
        )
    if not hasattr(WM, "spp_show_uv_step_4"):
        WM.spp_show_uv_step_4 = BoolProperty(
            name="Show UV Step 4",
            default=False,
            description="Toggle visibility of UV Step 4",
            update=update_uv_step_4,
        )
    if not hasattr(WM, "spp_show_uv_step_5"):
        WM.spp_show_uv_step_5 = BoolProperty(
            name="Show UV Step 5",
            default=False,
            description="Toggle visibility of UV Step 5",
            update=update_uv_step_5,
        )
    if not hasattr(WM, "spp_show_uv_step_6"):
        WM.spp_show_uv_step_6 = BoolProperty(
            name="Show UV Step 6",
            default=False,
            description="Toggle visibility of UV Step 6",
            update=update_uv_step_6,
        )

    # -------------------------------------------------------------------------
    # Experimental panel internal radio (keep yours)
    # -------------------------------------------------------------------------
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
        "spp_show_surface_step_1",
        "spp_show_surface_step_2",
        "spp_show_surface_step_3",
        "spp_show_surface_step_4",
        "spp_show_uv_step_1",
        "spp_show_uv_step_2",
        "spp_show_uv_step_3",
        "spp_show_uv_step_4",
        "spp_show_uv_step_5",
        "spp_show_uv_step_6",
        "spp_show_profile_projection",
    ):
        if rmW and hasattr(rmW, name):
            delattr(rmW, name)

    if rmS and hasattr(rmS, "spp_nurbs_qd_active"):
        delattr(rmS, "spp_nurbs_qd_active")
