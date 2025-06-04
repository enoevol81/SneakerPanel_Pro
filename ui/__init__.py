import bpy
from . import main_panel
from . import gpencil_panel
from . import bezier_panel
from . import shell_uv_panel
from . import finalize_panel

modules = [
    main_panel,
    gpencil_panel,
    bezier_panel,
    shell_uv_panel,
    finalize_panel,
]

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()

if __name__ == "__main__":
    register()
