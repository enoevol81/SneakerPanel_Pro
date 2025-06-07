# File: SneakerPanel_Pro/operators/create_quad_border.py
# This operator implements the user's visual workflow up to Stage 4.

import bpy
import bmesh
from bpy.props import IntProperty, BoolProperty, FloatProperty
from bpy.types import Operator
from ..utils.collections import add_object_to_panel_collection 

# --- Helper Function: Resample Polyline ---
def resample_polyline(points, num_samples):
    """Takes a list of 3D Vector points and returns a new list of evenly spaced points."""
    if not points or num_samples < 2:
        return []

    lengths = [0.0]
    total_length = 0.0
    for i in range(1, len(points)):
        seg_length = (points[i] - points[i-1]).length
        total_length += seg_length
        lengths.append(total_length)
    
    if total_length < 1e-6:
        return [points[0]] * num_samples

    # For a closed loop, we want N segments, so spacing is total_length / N
    spacing = total_length / num_samples
    if spacing < 1e-9: return [points[0]] * num_samples
    
    target_distances = [i * spacing for i in range(num_samples)]
    
    resampled_points = []
    current_seg_index = 0
    for d in target_distances:
        while current_seg_index < len(lengths) - 2 and d > lengths[current_seg_index + 1]:
            current_seg_index += 1
        
        seg_start_length = lengths[current_seg_index]
        seg_end_length = lengths[current_seg_index + 1]
        
        segment_length = seg_end_length - seg_start_length
        if segment_length < 1e-6:
            t = 0.0
        else:
            t = (d - seg_start_length) / segment_length
        
        p0 = points[current_seg_index]
        p1 = points[current_seg_index + 1]
        
        point = p0.lerp(p1, t)
        resampled_points.append(point)
    
    return resampled_points

class CURVE_OT_CreateQuadPanelBorder(Operator):
    """Takes an active curve, creates a sampled outline, and generates a quad border loop via inset."""
    bl_idname = "curve.create_quad_panel_border"
    bl_label = "Create Quad Panel Border from Curve"
    bl_options = {'REGISTER', 'UNDO'}

    sample_count: IntProperty(
        name="Boundary Samples",
        default=64,
        min=4,
        max=512,
        description="Number of evenly spaced vertices for the panel boundary. Higher values preserve shape better."
    )
    
    inset_thickness: FloatProperty(
        name="Border Thickness",
        default=0.05, 
        min=0.001,
        soft_max=1.0,
        description="Thickness of the inset that forms the quad border"
    )

    keep_original_curve: BoolProperty(
        name="Keep Original Curve",
        default=True,
        description="Keep the original input curve object after creating the mesh"
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'CURVE')

    def execute(self, context):
        original_curve_obj = context.active_object
        if not original_curve_obj:
            self.report({'ERROR'}, "No active curve object selected."); return {'CANCELLED'}

        bpy.ops.ed.undo_push(message=self.bl_label)
        
        # --- Stage 1 & 2: Curve -> SampledCurvePolyline ---
        self.report({'INFO'}, f"Step 1 & 2: Creating evenly sampled mesh outline from '{original_curve_obj.name}'.")
        
        # Duplicate and flatten curve
        bpy.ops.object.select_all(action='DESELECT'); original_curve_obj.select_set(True); context.view_layer.objects.active = original_curve_obj
        bpy.ops.object.duplicate(); working_obj = context.active_object
        if working_obj.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
        working_obj.data.dimensions = '2D' 
        for spline in working_obj.data.splines:
            if spline.type == 'BEZIER':
                for bp in spline.bezier_points: bp.co.z = 0.0; bp.handle_left.z = 0.0; bp.handle_right.z = 0.0
            else: 
                for pt in spline.points: pt.co.z = 0.0 
        
        # Convert to temp mesh to get ordered points
        depsgraph = context.evaluated_depsgraph_get(); eval_obj = working_obj.evaluated_get(depsgraph)
        try: temp_mesh = eval_obj.to_mesh()
        except: self.report({'ERROR'}, "Curve to temp mesh conversion failed."); bpy.data.objects.remove(working_obj, do_unlink=True); return {'CANCELLED'}
        if not temp_mesh.vertices or not temp_mesh.edges:
            self.report({'ERROR'}, "Curve resulted in an empty mesh outline."); eval_obj.to_mesh_clear(); bpy.data.objects.remove(working_obj, do_unlink=True); return {'CANCELLED'}

        # Build ordered polyline from temp mesh
        edge_lookup = {v.index: [] for v in temp_mesh.vertices}
        for e in temp_mesh.edges:
            edge_lookup[e.vertices[0]].append(e.vertices[1]); edge_lookup[e.vertices[1]].append(e.vertices[0])
        visited = set(); polyline_points = []
        start_idx = next((idx for idx, neighbors in edge_lookup.items() if len(neighbors) == 1), list(edge_lookup.keys())[0])
        current_idx = start_idx
        while current_idx not in visited:
            visited.add(current_idx); polyline_points.append(temp_mesh.vertices[current_idx].co.copy())
            next_vertex_idx = next((n for n in edge_lookup[current_idx] if n not in visited), -1)
            if next_vertex_idx == -1: break 
            current_idx = next_vertex_idx
        if hasattr(eval_obj, 'to_mesh_clear'): eval_obj.to_mesh_clear()
        bpy.data.objects.remove(working_obj, do_unlink=True) # Delete the temp curve duplicate

        if len(polyline_points) < 3: self.report({'ERROR'}, "Not enough points in curve outline."); return {'CANCELLED'}
        
        # Resample the extracted polyline
        resampled_points = resample_polyline(polyline_points, self.sample_count)
        
        # Create the final mesh object with the resampled outline
        panel_count = getattr(context.scene, "spp_panel_count", 1)
        panel_name_prop = getattr(context.scene, "spp_panel_name", "Panel")
        border_mesh_name = f"{panel_name_prop}_{panel_count}_PanelBorder"
        
        mesh_data = bpy.data.meshes.new(f"{border_mesh_name}_Data")
        panel_border_obj = bpy.data.objects.new(border_mesh_name, mesh_data)
        edges = [(i, (i + 1) % len(resampled_points)) for i in range(len(resampled_points))]
        mesh_data.from_pydata(resampled_points, edges, [])
        mesh_data.update()
        context.collection.objects.link(panel_border_obj)
        
        # --- Stage 3 & 4: N-gon Fill, Inset, and Delete Interior ---
        self.report({'INFO'}, "Step 3 & 4: Creating N-gon, insetting, and deleting interior.")
        bpy.ops.object.select_all(action='DESELECT'); panel_border_obj.select_set(True); context.view_layer.objects.active = panel_border_obj
        if panel_border_obj.mode != 'EDIT': bpy.ops.object.mode_set(mode='EDIT')
        
        try:
            # Step 3: Fill boundary with single N-gon
            bpy.ops.mesh.select_all(action='SELECT') # Select the boundary edge loop
            bpy.ops.mesh.edge_face_add()
            self.report({'INFO'}, "Created N-gon face from boundary.")

            # Step 4: Inset the N-gon and delete the interior face
            # After edge_face_add, the new face is selected.
            bpy.ops.mesh.select_mode(type="FACE") # Switch to be sure
            bpy.ops.mesh.inset(thickness=self.inset_thickness, use_even_offset=True, depth=0)
            self.report({'INFO'}, f"Applied inset with thickness {self.inset_thickness}.")
            
            # The inset operation leaves the new interior face selected. Delete it.
            bpy.ops.mesh.delete(type='FACE')
            self.report({'INFO'}, "Deleted interior face, leaving quad border loop.")
            
            bpy.ops.mesh.select_mode(type="VERT") # Revert to vert select mode
        except RuntimeError as e:
            self.report({'ERROR'}, f"Failed during fill/inset/delete sequence: {e}")
            bpy.ops.object.mode_set(mode='OBJECT')
            if panel_border_obj.name in bpy.data.objects: bpy.data.objects.remove(panel_border_obj, do_unlink=True)
            return {'CANCELLED'}
            
        bpy.ops.object.mode_set(mode='OBJECT')

        # --- Finalize ---
        add_object_to_panel_collection(panel_border_obj, panel_count, panel_name_prop)
        if self.keep_original_curve:
            original_curve_obj.hide_viewport = True
        else:
            original_data = original_curve_obj.data
            bpy.data.objects.remove(original_curve_obj, do_unlink=True)
            if original_data and original_data.users == 0: bpy.data.curves.remove(original_data)
        
        bpy.ops.object.select_all(action='DESELECT')
        panel_border_obj.select_set(True)
        context.view_layer.objects.active = panel_border_obj
        self.report({'INFO'}, f"Successfully created quad panel border: '{panel_border_obj.name}'.")
        
        return {'FINISHED'}

def register():
    bpy.utils.register_class(CURVE_OT_CreateQuadPanelBorder)

def unregister():
    bpy.utils.unregister_class(CURVE_OT_CreateQuadPanelBorder)
