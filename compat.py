# -------------------------------------------------------------------------
# Blender compatibility helpers for 4.4.3 → 4.5+
# -------------------------------------------------------------------------
import bpy

BL_VER = bpy.app.version  # e.g., (4, 4, 3)


def is_45_or_newer():
    return BL_VER >= (4, 5)


def enable_gp_surface_constraint(
    context: bpy.types.Context, enable: bool = True
) -> None:
    ts = context.scene.tool_settings
    try:
        ts.gpencil_stroke_placement_view3d = "SURFACE" if enable else "VIEW"
    except Exception:
        pass


def enable_gp_automerge(context: bpy.types.Context, enable: bool = True) -> None:
    ts = context.scene.tool_settings
    try:
        ts.use_gpencil_automerge_strokes = bool(enable)
    except Exception:
        pass
