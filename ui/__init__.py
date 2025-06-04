import bpy
from . import main_panel
from . import boundary_mesh_panel
from . import bezier_surface_panel
from . import shell_pattern_panel
from . import finalize_panel

modules = [
    main_panel,
    boundary_mesh_panel,
    bezier_surface_panel,
    shell_pattern_panel,
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
