import bpy
from . import bezier_panel
from . import shell_uv_panel
from . import solidify_panel

modules = [
    bezier_panel,
    shell_uv_panel,
    solidify_panel,
]

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()

if __name__ == "__main__":
    register()
