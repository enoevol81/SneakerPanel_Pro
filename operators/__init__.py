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
from . import convert_bezier_to_surface
from . import convert_to_mesh
from . import surface_resolution
from . import smooth_vertices
from . import reduce_verts
from . import panel_generate
from . import panel_generator
from . import shell_uv_to_panel
from . import solidify_panel
from . import uv_to_mesh
from . import unwrap_shell
from . import define_toe
from . import orient_uv_island
from . import mirror_curve_points
from . import sample_curve_to_polyline
from . import create_quad_panel_from_outline
from . import fill_quad_border
from . import fill_border_grid

# Register/unregister functions
def register():
    add_gp_draw.register()
    gp_to_curve.register()
    decimate_curve.register()
    convert_bezier_to_surface.register()
    convert_to_mesh.register()
    surface_resolution.register()
    smooth_vertices.register()
    reduce_verts.register()
    panel_generate.register()
    panel_generator.register()
    shell_uv_to_panel.register()
    solidify_panel.register()
    uv_to_mesh.register()
    unwrap_shell.register()
    define_toe.register()
    orient_uv_island.register()
    mirror_curve_points.register()
    sample_curve_to_polyline.register()
    create_quad_panel_from_outline.register()
    fill_quad_border.register()
    fill_border_grid.register()

def unregister():
    orient_uv_island.unregister()
    define_toe.unregister()
    unwrap_shell.unregister()
    uv_to_mesh.unregister()
    solidify_panel.unregister()
    shell_uv_to_panel.unregister()
    panel_generator.unregister()
    panel_generate.unregister()
    reduce_verts.unregister()
    smooth_vertices.unregister()
    surface_resolution.unregister()
    convert_to_mesh.unregister()
    convert_bezier_to_surface.unregister()
    decimate_curve.unregister()
    gp_to_curve.unregister()
    add_gp_draw.unregister()
    mirror_curve_points.unregister()
    sample_curve_to_polyline.unregister()       
    create_quad_panel_from_outline.unregister()
    fill_quad_border.unregister()
    fill_border_grid.unregister()

