import bpy
from . import main_panel
from . import finalize_panel
from . import workflow_operators
from . import uv_workflow_panel
from . import surface_workflow_panel
from . import lace_panel
from . import autu_uv

modules = [
    main_panel,
    finalize_panel,
    workflow_operators,
    uv_workflow_panel,
    surface_workflow_panel,
    lace_panel,
    autu_uv,
    ]

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()

if __name__ == "__main__":
    register()
