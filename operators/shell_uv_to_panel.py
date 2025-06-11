"""
Shell UV to Panel conversion operator for SneakerPanel Pro.

This module provides functionality to reproject a 2D design (curve) from UV space onto
the 3D shell and creates a panel. This is a critical part of the workflow for creating
3D panels from 2D designs drawn on UV maps, allowing for accurate pattern creation
from flat designs.
"""

import bpy
import bmesh
from mathutils import Vector, geometry
from ..utils.collections import add_object_to_panel_collection
from .panel_generator import generate_panel # Import the utility function
from ..utils.panel_utils import apply_surface_snap # For transform-based snap

# (get_3d_point_from_uv function remains as previously corrected - ensure it's here)
def get_3d_point_from_uv(shell_obj, uv_layer_name, uv_coord_target_2d, context):
    # Ensure this function is the fully corrected version from previous steps
    if not shell_obj or shell_obj.type != 'MESH': return None
    if not shell_obj.data.uv_layers: return None
    uv_layer = shell_obj.data.uv_layers.get(uv_layer_name)
    if not uv_layer:
        uv_layer = shell_obj.data.uv_layers.active 
        if not uv_layer: return None
    depsgraph = context.evaluated_depsgraph_get()
    eval_shell_obj = shell_obj.evaluated_get(depsgraph)
    eval_mesh = eval_shell_obj.to_mesh() 
    if not eval_mesh:
        if hasattr(eval_shell_obj, "to_mesh_clear"): eval_shell_obj.to_mesh_clear()
        return None
    bm = bmesh.new(); bm.from_mesh(eval_mesh); eval_shell_obj.to_mesh_clear() 
    bm.transform(shell_obj.matrix_world)
    uv_layer_bm = bm.loops.layers.uv.get(uv_layer.name) 
    if not uv_layer_bm: bm.free(); return None
    found_point_3d = None
    uv_coord_target_3d = Vector((uv_coord_target_2d.x, uv_coord_target_2d.y, 0.0))
    for face in bm.faces:
        if found_point_3d: break
        loops_on_face = list(face.loops); num_loops = len(loops_on_face)
        face_triangles_data = []
        if num_loops == 3: 
            tri_uvs_3d = [Vector((l[uv_layer_bm].uv.x, l[uv_layer_bm].uv.y, 0.0)) for l in loops_on_face]
            tri_verts_3d = [l.vert.co.copy() for l in loops_on_face]
            face_triangles_data.append({'uvs': tri_uvs_3d, 'verts': tri_verts_3d})
        elif num_loops == 4: 
            uvs1_3d = [Vector((loops_on_face[i][uv_layer_bm].uv.x, loops_on_face[i][uv_layer_bm].uv.y, 0.0)) for i in [0,1,2]]
            verts1 = [loops_on_face[i].vert.co.copy() for i in [0,1,2]]
            face_triangles_data.append({'uvs': uvs1_3d, 'verts': verts1})
            uvs2_3d = [Vector((loops_on_face[i][uv_layer_bm].uv.x, loops_on_face[i][uv_layer_bm].uv.y, 0.0)) for i in [0,2,3]]
            verts2 = [loops_on_face[i].vert.co.copy() for i in [0,2,3]]
            face_triangles_data.append({'uvs': uvs2_3d, 'verts': verts2})
        for tri_data in face_triangles_data:
            tri_uvs = tri_data['uvs']; tri_verts_3d = tri_data['verts']
            if not all(isinstance(uv, Vector) and len(uv) == 3 for uv in tri_uvs): continue
            if geometry.intersect_point_tri_2d(uv_coord_target_3d.xy, tri_uvs[0].xy, tri_uvs[1].xy, tri_uvs[2].xy):
                canonical_tri_p0=Vector((0.0,0.0,0.0)); canonical_tri_p1=Vector((1.0,0.0,0.0)); canonical_tri_p2=Vector((0.0,1.0,0.0))
                bary_uvw = geometry.barycentric_transform(uv_coord_target_3d, tri_uvs[0], tri_uvs[1], tri_uvs[2], canonical_tri_p0, canonical_tri_p1, canonical_tri_p2)
                w0=1.0-bary_uvw.x-bary_uvw.y; w1=bary_uvw.x; w2=bary_uvw.y; bary_coords=(w0,w1,w2)
                epsilon=1e-6
                if (0-epsilon<=bary_coords[0]<=1+epsilon and 0-epsilon<=bary_coords[1]<=1+epsilon and 0-epsilon<=bary_coords[2]<=1+epsilon and abs(sum(bary_coords)-1.0)<epsilon):
                    found_point_3d = (bary_coords[0]*tri_verts_3d[0] + bary_coords[1]*tri_verts_3d[1] + bary_coords[2]*tri_verts_3d[2])
                    break 
        if found_point_3d: break
    bm.free(); return found_point_3d

class OBJECT_OT_ShellUVToPanel(bpy.types.Operator):
    bl_idname = "object.shell_uv_to_panel"
    bl_label = "Shell UV Design to 3D Panel"
    bl_description = "Reprojects a 2D design (curve) from UV space onto the 3D shell and creates a panel"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        active_obj = context.active_object
        return (active_obj and active_obj.type == 'CURVE' and
                hasattr(context.scene, 'spp_shell_object') and context.scene.spp_shell_object and
                context.scene.spp_shell_object.type == 'MESH')

    def find_uv_reference_mesh(self, context, shell_obj_name):
        for obj in context.scene.objects:
            if obj.type == 'MESH' and "spp_original_3d_mesh_name" in obj:
                if obj["spp_original_3d_mesh_name"] == shell_obj_name:
                    return obj
        return None

    def execute(self, context):
        bpy.ops.ed.undo_push(message="Shell UV to Panel")

        design_obj = context.active_object
        shell_obj = context.scene.spp_shell_object
        
        intermediate_curve_obj_name = None 
        curve_data_3d_ref = None # Python reference to the Curve datablock
        curve_data_3d_name_for_report = None # Store name before potential removal
        
        boundary_mesh_obj_name = None 
        mesh_data_boundary_ref = None # Python reference to Mesh datablock
        mesh_data_boundary_name_for_report = None # Store name before potential removal


        if not shell_obj: self.report({'ERROR'}, "Scene 'Shell Object' not set."); return {'CANCELLED'}
        uv_mesh_obj = self.find_uv_reference_mesh(context, shell_obj.name)
        if not uv_mesh_obj: self.report({'ERROR'}, f"UV ref mesh for '{shell_obj.name}' not found."); return {'CANCELLED'}
        if "spp_applied_scale_factor" not in uv_mesh_obj or "spp_source_uv_map_name" not in uv_mesh_obj:
            self.report({'ERROR'}, "UV ref mesh missing props."); return {'CANCELLED'}
        scale_factor = uv_mesh_obj["spp_applied_scale_factor"]
        source_uv_map_name = uv_mesh_obj["spp_source_uv_map_name"]
        if scale_factor == 0: self.report({'ERROR'}, "UV ref scale factor is zero."); return {'CANCELLED'}

        reprojected_splines_data = []
        for spline in design_obj.data.splines:
            if not spline.bezier_points and not spline.points: continue
            points_3d_for_spline = []
            source_points = spline.bezier_points if spline.type == 'BEZIER' else spline.points
            for point_idx, point in enumerate(source_points):
                p_world_curve = design_obj.matrix_world @ point.co.xyz
                p_local_uv_mesh = uv_mesh_obj.matrix_world.inverted() @ p_world_curve
                uv_original_x = p_local_uv_mesh.x / scale_factor
                uv_original_y = p_local_uv_mesh.y / scale_factor
                current_uv = Vector((uv_original_x, uv_original_y))
                point_3d = get_3d_point_from_uv(shell_obj, source_uv_map_name, current_uv, context)
                if point_3d: points_3d_for_spline.append(point_3d)
                else: self.report({'WARNING'}, f"Pt {point_idx}: No 3D map for UV {current_uv} on '{design_obj.name}'.")
            if points_3d_for_spline:
                 reprojected_splines_data.append({"points": points_3d_for_spline, "is_cyclic": spline.use_cyclic_u if spline.type == 'BEZIER' else spline.use_cyclic, "type": spline.type})
        if not reprojected_splines_data: self.report({'ERROR'}, "No points reprojected."); return {'CANCELLED'}

        panel_count = context.scene.spp_panel_count
        panel_name_prop = context.scene.spp_panel_name
        base_curve_name = f"{panel_name_prop}_Curve3D_{panel_count}" if panel_name_prop and panel_name_prop.strip() else f"PanelCurve3D_{panel_count}"
        
        curve_data_3d_ref = bpy.data.curves.new(name=f"{base_curve_name}_Data", type='CURVE')
        curve_data_3d_ref.dimensions = '3D'
        curve_data_3d_name_for_report = curve_data_3d_ref.name # Store name before it might be removed
        for spline_data in reprojected_splines_data:
            new_spline = curve_data_3d_ref.splines.new(type=spline_data["type"])
            if spline_data["type"] == 'BEZIER':
                if spline_data["points"]: 
                    new_spline.bezier_points.add(len(spline_data["points"]) -1)
                    for i, coord_3d in enumerate(spline_data["points"]):
                        bp = new_spline.bezier_points[i]; bp.co = coord_3d; bp.handle_left_type = bp.handle_right_type = 'AUTO'
                    new_spline.use_cyclic_u = spline_data["is_cyclic"]
            else: 
                if spline_data["points"]:
                    new_spline.points.add(len(spline_data["points"]) -1)
                    for i, coord_3d in enumerate(spline_data["points"]): new_spline.points[i].co = list(coord_3d) + [1.0]
                    new_spline.use_cyclic = spline_data["is_cyclic"]

        curve_obj_3d_ref = bpy.data.objects.new(base_curve_name, curve_data_3d_ref) 
        intermediate_curve_obj_name = curve_obj_3d_ref.name 
        context.collection.objects.link(curve_obj_3d_ref)
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = curve_obj_3d_ref
        curve_obj_3d_ref.select_set(True)
        if curve_obj_3d_ref.mode != 'EDIT': bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.select_all(action='SELECT'); bpy.ops.transform.translate(value=(0,0,0), snap=True, snap_elements={'FACE_NEAREST'}, snap_target='CLOSEST'); bpy.ops.object.mode_set(mode='OBJECT')
        
        bpy.ops.object.convert(target='MESH') 
        boundary_mesh_obj_ref = context.active_object 
        if boundary_mesh_obj_ref.type != 'MESH' : 
            self.report({'ERROR'}, "Conversion to mesh failed.")
            obj_curve_check = bpy.data.objects.get(intermediate_curve_obj_name)
            if obj_curve_check: bpy.data.objects.remove(obj_curve_check, do_unlink=True)
            if curve_data_3d_ref and curve_data_3d_ref.users == 0: bpy.data.curves.remove(curve_data_3d_ref)
            return {'CANCELLED'}

        boundary_mesh_obj_name = f"{panel_name_prop}_BoundaryMesh_{panel_count}" if panel_name_prop and panel_name_prop.strip() else f"PanelBoundaryMesh_{panel_count}"
        boundary_mesh_obj_ref.name = boundary_mesh_obj_name
        mesh_data_boundary_ref = boundary_mesh_obj_ref.data 
        mesh_data_boundary_name_for_report = mesh_data_boundary_ref.name # Store name
        mesh_data_boundary_ref.name = f"{boundary_mesh_obj_name}_Data"
        add_object_to_panel_collection(boundary_mesh_obj_ref, panel_count, panel_name_prop)

        filled_obj_name = f"{panel_name_prop}_Panel_{panel_count}" if panel_name_prop and panel_name_prop.strip() else f"Panel_{panel_count}"
        grid_span = getattr(context.scene, "spp_grid_fill_span", 2)
        created_panel_obj = generate_panel(panel_obj=boundary_mesh_obj_ref, shell_obj=shell_obj, filled_obj_name=filled_obj_name, grid_span=grid_span, uv_layer_name=source_uv_map_name)

        if not created_panel_obj:
            self.report({'ERROR'}, "Panel generation (generate_panel function) failed.")
            obj_curve_check = bpy.data.objects.get(intermediate_curve_obj_name)
            if obj_curve_check: bpy.data.objects.remove(obj_curve_check, do_unlink=True)
            if curve_data_3d_ref and curve_data_3d_ref.users == 0: bpy.data.curves.remove(curve_data_3d_ref)
            obj_boundary_mesh_check = bpy.data.objects.get(boundary_mesh_obj_name)
            if obj_boundary_mesh_check:
                data_b_mesh = obj_boundary_mesh_check.data
                bpy.data.objects.remove(obj_boundary_mesh_check, do_unlink=True)
                if data_b_mesh and data_b_mesh.users == 0: bpy.data.meshes.remove(data_b_mesh)
            elif mesh_data_boundary_ref and mesh_data_boundary_ref.users == 0: 
                bpy.data.meshes.remove(mesh_data_boundary_ref)
            return {'CANCELLED'}

        # (Transform-based snap, optional subdivision/conform, and shade smooth on created_panel_obj as before)
        # ... (This whole section remains the same)
        self.report({'INFO'}, "Attempting transform-based surface snap on panel.")
        bpy.ops.object.select_all(action='DESELECT'); created_panel_obj.select_set(True); context.view_layer.objects.active = created_panel_obj
        original_mode = created_panel_obj.mode
        if original_mode != 'EDIT': bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        original_tool_snap_state = context.tool_settings.use_snap
        context.tool_settings.use_snap = True
        try:
            apply_surface_snap() 
            self.report({'INFO'}, "Transform-based surface snap applied.")
        except Exception as e:
            self.report({'WARNING'}, f"Transform-based surface snap failed: {e}")
        finally: 
            context.tool_settings.use_snap = original_tool_snap_state
            if created_panel_obj.mode == 'EDIT': bpy.ops.object.mode_set(mode='OBJECT')
        
        try:
            add_subdivision_prop = getattr(context.scene, "spp_panel_add_subdivision", False)
            subdivision_levels_prop = getattr(context.scene, "spp_panel_subdivision_levels", 0)
            conform_after_subd_prop = getattr(context.scene, "spp_panel_conform_after_subdivision", False)
            apply_added_modifiers_prop = getattr(context.scene, "spp_panel_apply_added_modifiers", True)
            shade_smooth_prop = getattr(context.scene, "spp_panel_shade_smooth", True)
            self.report({'INFO'}, f"Post-Pro: AddSubD={add_subdivision_prop}, Levels={subdivision_levels_prop}, ConformAfter={conform_after_subd_prop}, ApplyMods={apply_added_modifiers_prop}, ShadeSmooth={shade_smooth_prop}")
            if add_subdivision_prop and subdivision_levels_prop > 0:
                bpy.ops.object.select_all(action='DESELECT'); created_panel_obj.select_set(True); context.view_layer.objects.active = created_panel_obj
                self.report({'INFO'}, f"Adding Subdivision: {subdivision_levels_prop} levels.")
                subdiv_mod = created_panel_obj.modifiers.new(name="PanelSubdiv", type='SUBSURF')
                subdiv_mod.levels = subdivision_levels_prop; subdiv_mod.render_levels = subdivision_levels_prop
                if apply_added_modifiers_prop:
                    self.report({'INFO'}, "Applying Subdivision modifier."); bpy.ops.object.modifier_apply(modifier=subdiv_mod.name)
                else: self.report({'INFO'}, "Subdivision modifier left live.")
                if conform_after_subd_prop: 
                    bpy.ops.object.select_all(action='DESELECT'); created_panel_obj.select_set(True); context.view_layer.objects.active = created_panel_obj
                    self.report({'INFO'}, "Adding Post-Subd Conform (Shrinkwrap).")
                    conform_mod = created_panel_obj.modifiers.new(name="PostSubdConform", type='SHRINKWRAP')
                    conform_mod.target = shell_obj; conform_mod.wrap_method = 'NEAREST_SURFACEPOINT'; conform_mod.offset = 0.00001 
                    if apply_added_modifiers_prop:
                        self.report({'INFO'}, "Applying Post-Subd Conform modifier."); bpy.ops.object.modifier_apply(modifier=conform_mod.name)
                    else: self.report({'INFO'}, "Post-Subd Conform modifier left live.")
            if shade_smooth_prop:
                 if created_panel_obj.data.polygons:
                    bpy.ops.object.select_all(action='DESELECT'); created_panel_obj.select_set(True); context.view_layer.objects.active = created_panel_obj
                    bpy.ops.object.shade_smooth(); self.report({'INFO'}, "Applied smooth shading.")
        except Exception as e: self.report({'WARNING'}, f"Post-processing error: {e}")


        # --- REVISED CLEANUP INTERMEDIATE OBJECTS ---
        self.report({'INFO'}, "Cleaning up intermediate objects.")
        if design_obj and design_obj.name in bpy.data.objects:
            design_obj.hide_viewport = True 
            self.report({'INFO'}, f"Hid input design curve: {design_obj.name}")

        # Cleanup the intermediate 3D curve object (using its stored name)
        obj_to_delete_curve = bpy.data.objects.get(intermediate_curve_obj_name)
        if obj_to_delete_curve:
            # Check if this object is not one of the later, important objects
            if obj_to_delete_curve != boundary_mesh_obj_ref and obj_to_delete_curve != created_panel_obj :
                bpy.data.objects.remove(obj_to_delete_curve, do_unlink=True)
                self.report({'INFO'}, f"Deleted intermediate object that was curve: {intermediate_curve_obj_name}")
        
        # Remove the original curve_data_3d_ref if it's orphaned
        # Use the stored name for reporting if data is removed.
        if curve_data_3d_ref and curve_data_3d_ref.users == 0:
            bpy.data.curves.remove(curve_data_3d_ref) # Use the reference to the datablock
            self.report({'INFO'}, f"Deleted intermediate curve data: {curve_data_3d_name_for_report}")


        # Cleanup boundary_mesh_obj (using its stored name) if it's not the final panel
        if boundary_mesh_obj_name:
            obj_to_delete_boundary_mesh = bpy.data.objects.get(boundary_mesh_obj_name)
            if obj_to_delete_boundary_mesh and obj_to_delete_boundary_mesh != created_panel_obj:
                data_to_delete = obj_to_delete_boundary_mesh.data 
                bpy.data.objects.remove(obj_to_delete_boundary_mesh, do_unlink=True)
                self.report({'INFO'}, f"Deleted intermediate boundary mesh object: {boundary_mesh_obj_name}")
                if data_to_delete and data_to_delete.users == 0:
                    bpy.data.meshes.remove(data_to_delete)
                    self.report({'INFO'}, f"Deleted its mesh data: {mesh_data_boundary_name_for_report}")
            elif mesh_data_boundary_ref and mesh_data_boundary_ref.users == 0 and mesh_data_boundary_ref.name in bpy.data.meshes:
                 if (not obj_to_delete_boundary_mesh) or \
                    (obj_to_delete_boundary_mesh == created_panel_obj and created_panel_obj.data != mesh_data_boundary_ref):
                    self.report({'INFO'}, f"Cleaning up orphaned boundary mesh data: {mesh_data_boundary_name_for_report}")
                    bpy.data.meshes.remove(mesh_data_boundary_ref)
        # --- END OF REVISED CLEANUP ---

        bpy.ops.object.select_all(action='DESELECT'); created_panel_obj.select_set(True); context.view_layer.objects.active = created_panel_obj
        add_object_to_panel_collection(created_panel_obj, panel_count, panel_name_prop) 
        context.scene.spp_panel_count += 1
        self.report({'INFO'}, f"Successfully created panel: {created_panel_obj.name}")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(OBJECT_OT_ShellUVToPanel)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_ShellUVToPanel)