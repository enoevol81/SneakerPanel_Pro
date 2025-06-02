# SneakerPanel Pro - Operators Package
#
# This package contains modular operators for the SneakerPanel Pro addon

bl_info = {
    "name": "SneakerPanel Pro Operators",
    "description": "Modular operators for SneakerPanel Pro addon",
    "author": "SneakerPanel Pro Team",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D",
    "category": "Object"
}

# Import all operator modules
from . import add_gp_draw
from . import gp_to_curve
from . import decimate_curve
from . import convert_to_mesh
from . import smooth_vertices
from . import reduce_verts
from . import panel_generate
from . import panel_generator
from . import convert_bezier_to_surface
from . import bezier_to_panel
from . import shell_uv_to_panel
from . import solidify_panel
from . import flatten_panel_uv

# Register/unregister functions
def register():
    add_gp_draw.register()
    gp_to_curve.register()
    decimate_curve.register()
    convert_to_mesh.register()
    smooth_vertices.register()
    reduce_verts.register()
    panel_generate.register()
    convert_bezier_to_surface.register()
    bezier_to_panel.register()
    shell_uv_to_panel.register()
    solidify_panel.register()
    flatten_panel_uv.register()
    
    # Import and register uv_to_mesh separately to avoid circular imports
    from . import uv_to_mesh
    uv_to_mesh.register()

def unregister():
    # Import and unregister uv_to_mesh first
    try:
        from . import uv_to_mesh
        uv_to_mesh.unregister()
    except:
        pass
        
    # Unregister other operators
    flatten_panel_uv.unregister()
    solidify_panel.unregister()
    shell_uv_to_panel.unregister()
    bezier_to_panel.unregister()
    convert_bezier_to_surface.unregister()
    panel_generate.unregister()
    panel_generator.unregister()
    reduce_verts.unregister()
    smooth_vertices.unregister()
    convert_to_mesh.unregister()
    decimate_curve.unregister()
    gp_to_curve.unregister()
    add_gp_draw.unregister()
