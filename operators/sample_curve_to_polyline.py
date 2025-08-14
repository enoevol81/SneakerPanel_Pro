"""
Curve sampling operator for SneakerPanel Pro.

This module provides an operator to convert Bezier curves to evenly sampled polyline meshes.
The sampling process ensures consistent vertex spacing along the curve, which is essential
for further operations like grid fill. The module also handles curve extraction from mesh data
and maintains proper collection management.
"""

import bpy
from ..utils.collections import add_object_to_panel_collection 

# --- Helper Function: Resample Polyline (from your script) ---
def resample_polyline(points, num_samples):
    """Takes a list of 3D Vector points and returns a new list of evenly spaced points.
    
    Args:
        points: List of 3D Vector points representing the original polyline
        num_samples: Number of evenly spaced points to generate
        
    Returns:
        List of evenly spaced 3D Vector points
    """
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
    
    # Using num_samples for spacing assumes a closed loop, which is appropriate for panels.
    spacing = total_length / num_samples if num_samples > 0 else 0
    if spacing < 1e-9: 
        return [points[0]] * num_samples
    
    target_distances = [i * spacing for i in range(num_samples)]
    resampled_points = []
    current_seg_index = 0
    
    for d in target_distances:
        while current_seg_index < len(lengths) - 2 and d > lengths[current_seg_index + 1]:
            current_seg_index += 1
            
        seg_start_length = lengths[current_seg_index]
        seg_end_length = lengths[current_seg_index + 1]
        segment_length = seg_end_length - seg_start_length
        t = (d - seg_start_length) / segment_length if segment_length > 1e-6 else 0.0
        p0 = points[current_seg_index]
        p1 = points[current_seg_index + 1]
        resampled_points.append(p0.lerp(p1, t))
        
    return resampled_points

# --- Helper Function: Extract ordered points from a mesh outline ---
def get_ordered_points_from_mesh(mesh_data):
    """Walks mesh edges to return a list of ordered vertex coordinate lists.
    
    Args:
        mesh_data: Blender mesh data object
        
    Returns:
        List of polylines, where each polyline is a list of 3D Vector points
    """
    if not mesh_data or not mesh_data.edges: 
        return []
    
    edge_lookup = {v.index: [] for v in mesh_data.vertices}
    for e in mesh_data.edges:
        edge_lookup[e.vertices[0]].append(e.vertices[1])
        edge_lookup[e.vertices[1]].append(e.vertices[0])
    
    all_polylines = []
    visited_globally = set()
    
    for v_idx in edge_lookup:
        if v_idx not in visited_globally:
            current_polyline = []
            visited_locally = set()
            start_node = v_idx
            
            # Prefer to start at an endpoint (a vertex with only one edge connection) if one exists in this island
            for check_v_idx, neighbors in edge_lookup.items():
                if len(neighbors) == 1 and check_v_idx not in visited_globally:
                    start_node = check_v_idx
                    break
            
            current_node = start_node
            # Loop while the current node is valid and hasn't been visited in this local pass
            while current_node != -1 and current_node not in visited_locally:
                visited_locally.add(current_node)
                visited_globally.add(current_node)
                current_polyline.append(mesh_data.vertices[current_node].co.copy())
                
                # Find the next unvisited neighbor
                next_node = -1 # Default to -1 (not found)
                # Use .get() for safety in case current_node somehow becomes an invalid key
                for neighbor_idx in edge_lookup.get(current_node, []):
                    if neighbor_idx not in visited_locally:
                        next_node = neighbor_idx
                        break
                
                # Update current_node for the next iteration
                current_node = next_node

            if current_polyline: 
                all_polylines.append(current_polyline)
                
    return all_polylines

# --- Main Operator ---
class CURVE_OT_SampleToPolyline(bpy.types.Operator):
    """Convert Bezier curve to an evenly sampled polyline mesh.
    
    This operator converts a selected Bezier curve to a mesh with evenly spaced vertices.
    The sampling density is controlled by the spp_sampler_fidelity scene property.
    The operator ensures that the resulting mesh has an even number of vertices for
    compatibility with grid fill operations. The original curve is hidden after conversion.
    
    Note:
        The operator requires a curve object to be selected.
        The resulting mesh is added to the appropriate SneakerPanel Pro collection.
    """
    bl_idname = "curve.sample_to_polyline"
    bl_label = "Sample Curve to Polyline"
    bl_description = "Convert selected Bezier curve to an evenly sampled polyline mesh"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """Check if the operator can be executed.
        
        Args:
            context: Blender context
            
        Returns:
            bool: True if active object is a curve
        """
        obj = context.active_object
        return (obj and obj.type == 'CURVE')

    def execute(self, context):
        # Context-agnostic execution - automatically switch to required mode
        original_curve_obj = context.active_object
        if not (original_curve_obj and original_curve_obj.type == 'CURVE'):
            self.report({'ERROR'}, "No active curve object")
            return {'CANCELLED'}
        
        # Store original mode for restoration
        original_mode = original_curve_obj.mode
        
        # Switch to Object Mode if not already there
        if context.mode != 'OBJECT':
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except Exception as e:
                self.report({'ERROR'}, f"Could not switch to Object Mode: {str(e)}")
                return {'CANCELLED'}
        
        try:
            
            # Get desired sample count from the scene property
            samples_per_spline = int(context.scene.spp_sampler_fidelity)
            
            # --- Enforce Even Number of Vertices for Grid Fill compatibility ---
            if samples_per_spline % 2 != 0:
                samples_per_spline += 1
                self.report({'INFO'}, f"Sample count adjusted to {samples_per_spline} (must be even).")
            
            depsgraph = context.evaluated_depsgraph_get()
            eval_obj = original_curve_obj.evaluated_get(depsgraph)
            
            polylines = []
            temp_mesh = None
            try:
                temp_mesh = eval_obj.to_mesh()
                if not temp_mesh:
                    raise RuntimeError("Curve to mesh conversion yielded no mesh data.")
                
                # Extract polylines WHILE the temp_mesh is valid
                polylines = get_ordered_points_from_mesh(temp_mesh)
                
            except Exception as e:
                self.report({'ERROR'}, f"Failed to process curve geometry: {e}")
                return {'CANCELLED'}
            finally:
                # Clear the temporary mesh data AFTER we are done with it
                if hasattr(eval_obj, 'to_mesh_clear') and temp_mesh:
                    eval_obj.to_mesh_clear()

            self.report({'INFO'}, f"Extracted {len(polylines)} polyline(s) from the curve.")
            
            if not polylines:
                self.report({'ERROR'}, "Could not extract any polylines from the curve object.")
                return {'CANCELLED'}

            created_objects = []
            for idx, poly in enumerate(polylines):
                if len(poly) < 2:
                    continue
                    
                resampled = resample_polyline(poly, samples_per_spline)
                
                panel_count = getattr(context.scene, "spp_panel_count", 1)
                panel_name_prop = getattr(context.scene, "spp_panel_name", "Panel")
                mesh_name = f"{panel_name_prop}_{panel_count}_SampledOutline_{idx}"
                
                new_mesh_data = bpy.data.meshes.new(f"{mesh_name}_Data")
                new_obj = bpy.data.objects.new(mesh_name, new_mesh_data)
                
                edges = [(i, (i + 1)) for i in range(len(resampled) - 1)]
                # Check if original spline was cyclic to close the loop
                if idx < len(original_curve_obj.data.splines) and original_curve_obj.data.splines[idx].use_cyclic_u:
                    edges.append((len(resampled) - 1, 0))

                new_mesh_data.from_pydata(resampled, edges, [])
                new_mesh_data.update()
                
                context.collection.objects.link(new_obj)
                # Use the main panel collection, not an "Intermediates" sub-collection
                add_object_to_panel_collection(new_obj, panel_count, panel_name_prop)
                created_objects.append(new_obj)

            if not created_objects:
                self.report({'ERROR'}, "Failed to create any sampled polyline meshes.")
                return {'CANCELLED'}

            bpy.ops.object.select_all(action='DESELECT')
            for obj in created_objects:
                obj.select_set(True)
            context.view_layer.objects.active = created_objects[0]
            original_curve_obj.hide_viewport = True
            self.report({'INFO'}, f"Sampling complete. Created {len(created_objects)} outline object(s).")
            # Restore original mode if it was different
            if original_mode != 'OBJECT':
                try:
                    bpy.ops.object.mode_set(mode=original_mode)
                except:
                    pass  # Don't fail if mode restoration fails
            
            return {'FINISHED'}
            
        except Exception as e:
            # Restore original mode on error
            if original_mode != 'OBJECT':
                try:
                    bpy.ops.object.mode_set(mode=original_mode)
                except:
                    pass
            self.report({'ERROR'}, f"Error during curve sampling: {str(e)}")
            return {'CANCELLED'}

# --- Registration ---
classes = [CURVE_OT_SampleToPolyline]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
if __name__ == "__main__":
    register()
