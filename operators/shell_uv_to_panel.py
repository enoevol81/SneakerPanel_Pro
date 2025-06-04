import bpy
import bmesh
from mathutils import Vector, geometry
from ..utils.collections import add_object_to_panel_collection
from .panel_generator import generate_panel # Import the utility

def get_3d_point_from_uv(shell_obj, uv_layer_name, uv_coord_target, context):
    """
    Finds the 3D world coordinate on the shell_obj corresponding to a given UV coordinate.
    Returns None if no corresponding point is found.
    """
    if not shell_obj or shell_obj.type != 'MESH':
        # print("Shell object is invalid or not a MESH.")
        return None
    if not shell_obj.data.uv_layers:
        # print("Shell object has no UV layers.")
        return None
    
    uv_layer = shell_obj.data.uv_layers.get(uv_layer_name)
    if not uv_layer:
        uv_layer = shell_obj.data.uv_layers.active # Fallback to active
        if not uv_layer:
            # print(f"UV layer '{uv_layer_name}' not found and no active UV layer on shell.")
            return None

    mesh = shell_obj.data
    
    # Ensure the shell object's dependencies are updated if it has modifiers
    # This gives access to the evaluated mesh (after modifiers)
    depsgraph = context.evaluated_depsgraph_get()
    eval_shell_obj = shell_obj.evaluated_get(depsgraph)
    eval_mesh = eval_shell_obj.to_mesh() # Get evaluated mesh data
    if not eval_mesh:
        # print("Could not get evaluated mesh from shell object.")
        return None

    bm = bmesh.new()
    bm.from_mesh(eval_mesh)
    bm.transform(shell_obj.matrix_world) # Transform bmesh to world space

    uv_layer_bm = bm.loops.layers.uv.get(uv_layer.name) 
    if not uv_layer_bm:
        # print(f"BMesh UV layer '{uv_layer.name}' not found.")
        bm.free()
        eval_shell_obj.to_mesh_clear() # Clear the temporary mesh data
        return None

    found_point_3d = None

    # Iterate over faces to find the one containing the UV coordinate
    for face in bm.faces:
        uvs_poly_face = [loop[uv_layer_bm].uv.copy() for loop in face.loops]
        verts_poly_3d_face = [loop.vert.co.copy() for loop in face.loops]

        if geometry.intersect_point_poly_2d(uv_coord_target, uvs_poly_face):
            if len(verts_poly_3d_face) == 3: # Triangle
                bary_coords = geometry.barycentric_coordinates_tri(uv_coord_target, uvs_poly_face[0], uvs_poly_face[1], uvs_poly_face[2])
                if all(0 <= bc <= 1 + 1e-6 for bc in bary_coords): # Add tolerance for floating point
                    found_point_3d = (bary_coords[0] * verts_poly_3d_face[0] +
                                    bary_coords[1] * verts_poly_3d_face[1] +
                                    bary_coords[2] * verts_poly_3d_face[2])
                    break
            elif len(verts_poly_3d_face) == 4: # Quad
                # Triangulate quad for barycentric coords (0,1,2) and (0,2,3)
                bary_coords_tri1 = geometry.barycentric_coordinates_tri(uv_coord_target, uvs_poly_face[0], uvs_poly_face[1], uvs_poly_face[2])
                if all(0 <= bc <= 1 + 1e-6 for bc in bary_coords_tri1):
                    found_point_3d = (bary_coords_tri1[0] * verts_poly_3d_face[0] +
                                    bary_coords_tri1[1] * verts_poly_3d_face[1] +
                                    bary_coords_tri1[2] * verts_poly_3d_face[2])
                    break
                
                bary_coords_tri2 = geometry.barycentric_coordinates_tri(uv_coord_target, uvs_poly_face[0], uvs_poly_face[2], uvs_poly_face[3])
                if all(0 <= bc <= 1 + 1e-6 for bc in bary_coords_tri2):
                    found_point_3d = (bary_coords_tri2[0] * verts_poly_3d_face[0] +
                                    bary_coords_tri2[1] * verts_poly_3d_face[2] +
                                    bary_coords_tri2[2] * verts_poly_3d_face[3])
                    break
            # Add more complex N-gon handling if necessary, though UVs are often on tris/quads
    
    bm.free()
    eval_shell_obj.to_mesh_clear() # Clear the temporary mesh data
    return found_point_3d


class OBJECT_OT_ShellUVToPanel(bpy.types.Operator):
    bl_idname = "object.shell_uv_to_panel"
    bl_label = "Shell UV Design to 3D Panel"
    bl_description = "Reprojects a 2D design (curve) from UV space onto the 3D shell and creates a panel"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # Expects an active curve object (the 2D design)
        # and a shell object to be defined in scene properties
        active_obj = context.active_object
        return (active_obj and active_obj.type == 'CURVE' and
                context.scene.spp_shell_object and
                context.scene.spp_shell_object.type == 'MESH')

    def find_uv_reference_mesh(self, context, shell_obj_name):
        """Finds the UV mesh created by uv_to_mesh operator for the given shell."""
        for obj in context.scene.objects:
            if obj.type == 'MESH' and "spp_original_3d_mesh_name" in obj:
                if obj["spp_original_3d_mesh_name"] == shell_obj_name:
                    return obj
        return None

    def execute(self, context):
        bpy.ops.ed.undo_push(message="Shell UV to Panel")

        design_obj = context.active_object
        shell_obj = context.scene.spp_shell_object

        if not shell_obj:
            self.report({'ERROR'}, "Scene 'Shell Object' not set.")
            return {'CANCELLED'}

        # Find the corresponding UV flat reference mesh
        uv_mesh_obj = self.find_uv_reference_mesh(context, shell_obj.name)
        if not uv_mesh_obj:
            self.report({'ERROR'}, f"Could not find the UV reference mesh for shell '{shell_obj.name}'. Run 'UV to Mesh' first.")
            return {'CANCELLED'}

        if "spp_applied_scale_factor" not in uv_mesh_obj or \
           "spp_source_uv_map_name" not in uv_mesh_obj:
            self.report({'ERROR'}, "UV reference mesh is missing required custom properties (scale_factor or uv_map_name).")
            return {'CANCELLED'}

        scale_factor = uv_mesh_obj["spp_applied_scale_factor"]
        source_uv_map_name = uv_mesh_obj["spp_source_uv_map_name"]

        if scale_factor == 0:
            self.report({'ERROR'}, "UV reference mesh scale factor is zero.")
            return {'CANCELLED'}

        # Ensure design_obj is a curve
        if design_obj.type != 'CURVE' or not design_obj.data.splines:
            self.report({'ERROR'}, "Active object must be a curve with at least one spline.")
            return {'CANCELLED'}

        reprojected_splines_data = [] # List to store lists of 3D points for each spline

        # --- Step 1: Reproject 2D curve points to 3D on the shell ---
        for spline in design_obj.data.splines:
            if not spline.bezier_points and not spline.points: # Skip if no points
                continue

            points_3d_for_spline = []
            
            # Handle Bezier points or Poly points
            source_points = spline.bezier_points if spline.type == 'BEZIER' else spline.points
            
            for point in source_points:
                # Get world coordinate of the 2D design curve point
                p_world_curve = design_obj.matrix_world @ point.co.xyz
                
                # Transform this world coordinate to the local coordinate system of the uv_mesh_obj
                p_local_uv_mesh = uv_mesh_obj.matrix_world.inverted() @ p_world_curve
                
                # Calculate original UV (0-1 range)
                # The local X,Y of uv_mesh_obj's vertices are directly the scaled UVs
                uv_original_x = p_local_uv_mesh.x / scale_factor
                uv_original_y = p_local_uv_mesh.y / scale_factor
                current_uv = Vector((uv_original_x, uv_original_y))

                point_3d = get_3d_point_from_uv(shell_obj, source_uv_map_name, current_uv, context)
                
                if point_3d:
                    points_3d_for_spline.append(point_3d)
                else:
                    self.report({'WARNING'}, f"Could not reproject UV point {current_uv} for design curve '{design_obj.name}'. Skipping point.")
            
            if points_3d_for_spline:
                 reprojected_splines_data.append({
                    "points": points_3d_for_spline,
                    "is_cyclic": spline.use_cyclic_u if spline.type == 'BEZIER' else spline.use_cyclic, # For poly splines
                    "type": spline.type
                })


        if not reprojected_splines_data:
            self.report({'ERROR'}, "No points could be reprojected from the design curve.")
            return {'CANCELLED'}

        # --- Step 2: Create a new 3D curve from reprojected points ---
        bpy.ops.object.select_all(action='DESELECT')
        
        # Create new curve data
        panel_count = context.scene.spp_panel_count
        panel_name_prop = context.scene.spp_panel_name
        base_curve_name = f"{panel_name_prop}_Curve3D_{panel_count}" if panel_name_prop and panel_name_prop.strip() else f"PanelCurve3D_{panel_count}"
        
        curve_data_3d = bpy.data.curves.new(name=f"{base_curve_name}_Data", type='CURVE')
        curve_data_3d.dimensions = '3D'

        for spline_data in reprojected_splines_data:
            new_spline = curve_data_3d.splines.new(type=spline_data["type"])
            
            if spline_data["type"] == 'BEZIER':
                new_spline.bezier_points.add(len(spline_data["points"]) -1) # Adds n-1 points if already 1 exists
                for i, coord_3d in enumerate(spline_data["points"]):
                    bp = new_spline.bezier_points[i]
                    bp.co = coord_3d
                    bp.handle_left_type = 'AUTO'
                    bp.handle_right_type = 'AUTO'
                new_spline.use_cyclic_u = spline_data["is_cyclic"]
            else: # POLY or NURBS (though we primarily expect POLY from simple curves)
                new_spline.points.add(len(spline_data["points"]) -1)
                for i, coord_3d in enumerate(spline_data["points"]):
                    new_spline.points[i].co = list(coord_3d) + [1.0] # Add W coordinate for poly points
                new_spline.use_cyclic = spline_data["is_cyclic"]


        curve_obj_3d = bpy.data.objects.new(base_curve_name, curve_data_3d)
        context.collection.objects.link(curve_obj_3d)
        context.view_layer.objects.active = curve_obj_3d
        curve_obj_3d.select_set(True)
        
        # Set curve to snap to surface again (optional, but good for refinement)
        if curve_obj_3d.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.select_all(action='SELECT')
        bpy.ops.transform.translate(value=(0,0,0), snap=True, snap_elements={'FACE_NEAREST'}, snap_target='CLOSEST')
        bpy.ops.object.mode_set(mode='OBJECT')


        # --- Step 3: Convert 3D curve to Mesh ---
        # We can directly call the convert to mesh operation
        # Store current active object (the new 3D curve)
        temp_active_curve = context.active_object
        
        bpy.ops.object.convert(target='MESH')
        boundary_mesh_obj = context.active_object # Object.convert makes the new mesh active
        
        # Rename the converted mesh properly
        mesh_name_base = f"{panel_name_prop}_BoundaryMesh_{panel_count}" if panel_name_prop and panel_name_prop.strip() else f"PanelBoundaryMesh_{panel_count}"
        boundary_mesh_obj.name = mesh_name_base
        boundary_mesh_obj.data.name = f"{mesh_name_base}_Data"
        add_object_to_panel_collection(boundary_mesh_obj, panel_count, panel_name_prop)


        # --- Step 4: Generate Panel using panel_generator ---
        # The boundary_mesh_obj is now our 'panel_obj' for panel_generator
        filled_obj_name = f"{panel_name_prop}_Panel_{panel_count}" if panel_name_prop and panel_name_prop.strip() else f"Panel_{panel_count}"
        grid_span = context.scene.spp_grid_fill_span
        
        # Make sure shell_obj is set in scene properties if panel_generator relies on it directly
        # panel_generator.generate_panel takes shell_obj as an argument

        generated_panel = generate_panel(
            panel_obj=boundary_mesh_obj,
            shell_obj=shell_obj,
            filled_obj_name=filled_obj_name,
            grid_span=grid_span,
            uv_layer_name=source_uv_map_name # Use same UV map name for consistency
        )

        if not generated_panel:
            self.report({'ERROR'}, "Panel generation step failed using panel_generator.")
            # Cleanup created objects if generation fails
            bpy.data.objects.remove(curve_obj_3d, do_unlink=True)
            bpy.data.curves.remove(curve_data_3d)
            if boundary_mesh_obj != temp_active_curve : # if convert created a new obj
                 bpy.data.objects.remove(boundary_mesh_obj, do_unlink=True)
            return {'CANCELLED'}
        
        # Hide intermediate objects
        design_obj.hide_viewport = True
        curve_obj_3d.hide_viewport = True
        if boundary_mesh_obj != generated_panel: # boundary_mesh_obj might be the one modified by generate_panel or a new one
            boundary_mesh_obj.hide_viewport = True


        # Final selection and naming for the generated panel
        bpy.ops.object.select_all(action='DESELECT')
        generated_panel.select_set(True)
        context.view_layer.objects.active = generated_panel
        add_object_to_panel_collection(generated_panel, panel_count, panel_name_prop) # ensure it's in correct collection

        context.scene.spp_panel_count += 1 # Increment panel count

        self.report({'INFO'}, f"Successfully created 3D panel: {generated_panel.name}")
        return {'FINISHED'}


# Module level registration
def register():
    bpy.utils.register_class(OBJECT_OT_ShellUVToPanel)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_ShellUVToPanel)