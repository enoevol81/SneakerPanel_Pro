import bpy

from . import (
    auto_uv,
    lace_panel,
    main_panel,
    panel_nurbs_qd,
    profile_projection_panel,
    surface_workflow_panel,
    uv_workflow_panel,
    workflow_operators,
)

modules = [
    main_panel,
    workflow_operators,
    uv_workflow_panel,
    surface_workflow_panel,
    lace_panel,
    auto_uv,
    panel_nurbs_qd,
    profile_projection_panel,
]


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()


if __name__ == "__main__":
    register()
