import bpy
import bmesh
from mathutils import Vector

# Import utility modules
from .utils.panel_utils import apply_surface_snap
from .utils.collections import get_sneaker_panels_collection, get_panel_collection, add_object_to_panel_collection

# Import operators - only for reference, not for registration
from .operators.uv_to_mesh import OBJECT_OT_UVToMesh
from .operators.shell_uv_to_panel import OBJECT_OT_ShellUVCrvPanel

# ----------------------------------------------------
# REGISTRATION
# ----------------------------------------------------

def register():
    # No direct class registration here - operators are registered through the operators package
    pass

def unregister():
    # No direct class unregistration here - operators are unregistered through the operators package
    pass

if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()