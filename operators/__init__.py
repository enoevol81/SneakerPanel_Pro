
bl_info = {
    "name": "SneakerPanel Pro Operators",
    "description": "Modular operators for SneakerPanel Pro addon",
    "author": "SneakerPanel Pro Team",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D",
    "category": "Object",
}

from . import (
    add_gp_draw,
    add_subsurf,
    apply_shrinkwrap,
    boundary_edges,
    convert_bezier_to_surface,
    convert_to_mesh,
    create_quad_panel_from_outline,
    decimate_curve,
    define_toe,
    edge_flow,
    edge_relax,
    fill_border_grid,
    fill_quad_border,
    gp_to_curve,
    lace_from_curves,
    mirror_curve_points,
    mirror_panel,
    orient_uv_island,
    overlay_panel_onto_shell,
    panel_generate,
    panel_generator,
    quick_conform,
    reduce_verts,
    ref_image_gen,
    sample_curve_to_polyline,
    set_edge_linear,
    shell_uv_to_panel,
    simple_grid_fill,
    smooth_mesh,
    smooth_vertices,
    solidify_panel,
    surface_resolution,
    unwrap_shell,
    uv_boundary_checker,
    uv_to_mesh,
)


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
    simple_grid_fill.register()
    smooth_mesh.register()
    overlay_panel_onto_shell.register()
    uv_boundary_checker.register()
    lace_from_curves.register()
    edge_flow.register()
    mirror_panel.register()
    edge_relax.register()
    apply_shrinkwrap.register()
    quick_conform.register()
    boundary_edges.register()
    add_subsurf.register()
    set_edge_linear.register()
    ref_image_gen.register()


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
    simple_grid_fill.unregister()
    smooth_mesh.unregister()
    overlay_panel_onto_shell.unregister()
    uv_boundary_checker.unregister()
    lace_from_curves.unregister()
    edge_flow.unregister()
    mirror_panel.unregister()
    edge_relax.unregister()
    apply_shrinkwrap.unregister()
    quick_conform.unregister()
    boundary_edges.unregister()
    add_subsurf.unregister()
    set_edge_linear.unregister()
    ref_image_gen.unregister()
