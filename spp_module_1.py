import bpy
import bmesh
from mathutils.bvhtree import BVHTree
from mathutils import Vector

# Import utility modules
from .utils.panel_utils import update_stabilizer, update_stabilizer_ui, apply_surface_snap, reduce_mesh_verts, compute_curvature, create_flow_based_quads
from .utils.collections import get_sneaker_panels_collection, get_panel_collection, add_object_to_panel_collection

# Import operators - only for reference, not for registration
from .operators.add_gp_draw import OBJECT_OT_AddGPDraw
from .operators.gp_to_curve import OBJECT_OT_GPToCurve
from .operators.decimate_curve import OBJECT_OT_DecimateCurve
from .operators.convert_to_mesh import OBJECT_OT_ConvertToMesh
from .operators.smooth_vertices import OBJECT_OT_SmoothVertices
from .operators.reduce_verts import OBJECT_OT_ReduceVerts
from .operators.panel_generate import OBJECT_OT_PanelGenerate

# Import properties
from .properties import register_properties, unregister_properties  


# ----------------------------------------------------
# REGISTRATION
# ----------------------------------------------------

# No UI panel registration here - panels are now registered through the ui package
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