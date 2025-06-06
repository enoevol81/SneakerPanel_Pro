# File: SneakerPanel_Pro/operators/sample_and_quad_fill.py
# This operator implements the "Sample + Quad Fill" workflow.

import bpy
import bmesh
from bpy.props import IntProperty, BoolProperty
from bpy.types import Operator
from ..utils.collections import add_object_to_panel_collection 

# --- Helper Function: Resample Polyline (from your provided script) ---
def resample_polyline(points, num_samples):
    """Takes a list of 3D Vector points and returns a new list of evenly spaced points."""
    if not points or num_samples < 2:
        return []

    # Compute cumulative lengths of the segments
    lengths = [0.0]
    total_length = 0.0
    for i in range(1, len(points)):
        seg_length = (points[i] - points[i-1]).length
        total_length += seg_length
        lengths.append(total_length)
    
    if total_length == 0.0: # Handle cases with zero length (e.g., all points at same location)
        return [points[0]] * num_samples

    # Determine the target distances for each new point
    spacing = total_length / (num_samples -1) # Use num_samples-1 for correct spacing
    target_distances = [i * spacing for i in range(num_samples)]
    
    resampled_points = []
    current_seg_index = 0
    for d in target_distances:
        # Find the segment that contains the target distance
        while current_seg_index < len(lengths) - 2 and d > lengths[current_seg_index + 1]:
            current_seg_index += 1
        
        # Interpolate within the segment
        seg_start_length = lengths[current_seg_index]
        seg_end_length = lengths[current_seg_index + 1]
        
        # Avoid division by zero if a segment has no length
        segment_length = seg_end_length - seg_start_length
        if segment_length == 0.0:
            t = 0.0
        else:
            t = (d - seg_start_length) / segment_length
        
        p0 = points[current_seg_index]
        p1 = points[current_seg_index + 1]
        
        point = p0.lerp(p1, t)
        resampled_points.append(point)
    
    return resampled_points

class CURVE_OT_SampleAndQuadFill(Operator):
    """Takes an active curve, creates an evenly spaced polyline, then creates a quad-filled mesh panel."""
    bl_idname = "curve.sample_and_quad_fill"
    bl_label = "Create Quad Panel from Curve"
    bl_options = {'REGISTER', 'UNDO'}

    desired_samples: IntProperty(
        name="Boundary Samples",
        default=64,
        min=4,
        max=512,
        description="Number of evenly spaced vertices for the panel boundary. Must be an even number for Grid Fill to work well."
    )

    grid_fill_span: IntProperty(
        name="Grid Fill Spans",
        default=1,
        min=1,
        max=100,
        description="Number of segments for the grid fill between opposing edges. Set to 1 to just connect."
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
            self.report({'ERROR'}, "No active curve object selected.")
            return {'CANCELLED'}

        bpy.ops.ed.undo_push(message=self.bl_label)
        
        # --- 1. Extract Ordered Polyline from Curve ---
        self.report({'INFO'}, f"Extracting polyline from '{original_curve_obj.name}'.")
        
        # Use Blender's dependency graph to get the evaluated version of the curve
        depsgraph = context.evaluated_depsgraph_get()
        eval_obj = original_curve_obj.evaluated_get(depsgraph)
        
        # Convert the evaluated curve to a temporary mesh to get an ordered vertex list
        # This is a robust way to handle complex curves with modifiers
        try:
            temp_mesh = eval_obj.to_mesh()
        except Exception as e:
            self.report({'ERROR'}, f"Could not convert curve to mesh: {e}")
            return {'CANCELLED'}

        if not temp_mesh.vertices or not temp_mesh.edges:
            self.report({'ERROR'}, "Curve resulted in a mesh with no vertices or edges.")
            eval_obj.to_mesh_clear()
            return {'CANCELLED'}

        # Build a map of edge connections
        edge_lookup = {v.index: [] for v in temp_mesh.vertices}
        for e in temp_mesh.edges:
            edge_lookup[e.vertices[0]].append(e.vertices[1])
            edge_lookup[e.vertices[1]].append(e.vertices[0])
        
        # Walk the edges to get an ordered list of vertex coordinates
        visited = set()
        polyline_points = []
        # Find a start vertex (one with only 1 connection is an endpoint, 2 is part of a loop)
        start_idx = -1
        for idx, neighbors in edge_lookup.items():
            if len(neighbors) == 1:
                start_idx = idx
                break
        if start_idx == -1: # If no endpoint found (i.e., it's a closed loop), start anywhere
            start_idx = list(edge_lookup.keys())[0]

        current_idx = start_idx
        while current_idx not in visited:
            visited.add(current_idx)
            polyline_points.append(temp_mesh.vertices[current_idx].co.copy())
            
            next_vertex_idx = -1
            for neighbor_idx in edge_lookup[current_idx]:
                if neighbor_idx not in visited:
                    next_vertex_idx = neighbor_idx
                    break
            
            if next_vertex_idx == -1:
                break # End of the line
            current_idx = next_vertex_idx

        # Cleanup the temporary mesh
        eval_obj.to_mesh_clear()

        if len(polyline_points) < 2:
            self.report({'ERROR'}, "Could not extract a valid polyline from the curve.")
            return {'CANCELLED'}

        # --- 2. Resample the Polyline ---
        self.report({'INFO'}, f"Resampling polyline from {len(polyline_points)} to {self.desired_samples} points.")
        resampled_points = resample_polyline(polyline_points, self.desired_samples)

        # --- 3. Create Quad-Filled Mesh (PanelFillMesh) ---
        self.report({'INFO'}, "Creating final quad-filled mesh panel.")
        
        panel_count = getattr(context.scene, "spp_panel_count", 1)
        panel_name_prop = getattr(context.scene, "spp_panel_name", "Panel")
        panel_fill_mesh_name = f"{panel_name_prop}_{panel_count}_PanelFillMesh"
        
        mesh_data = bpy.data.meshes.new(f"{panel_fill_mesh_name}_Data")
        panel_fill_obj = bpy.data.objects.new(panel_fill_mesh_name, mesh_data)
        context.collection.objects.link(panel_fill_obj)
        
        bm = bmesh.new()
        bm_verts = [bm.verts.new(p) for p in resampled_points]
        bm.verts.ensure_lookup_table()
        
        # Create the boundary edge loop from the resampled points
        for i in range(len(bm_verts)):
            try:
                bm.edges.new((bm_verts[i], bm_verts[i - 1])) # Connects to previous, wraps around at the end
            except ValueError:
                self.report({'WARNING'}, f"Could not create edge for vert {i}. May be a duplicate.")
        
        bm.edges.ensure_lookup_table()
        for edge in bm.edges:
            edge.select = True
            
        # Run Grid Fill on the open loop
        try:
            bmesh.ops.grid_fill(
                bm,
                edges=[e for e in bm.edges if e.select],
                use_interp_simple=True,
                span_count=self.grid_fill_span
            )
            self.report({'INFO'}, "Grid Fill successful.")
        except ValueError as e:
            self.report({'ERROR'}, f"Grid Fill failed: {e}. The number of boundary vertices must be even. Trying fallback.")
            try:
                bm.faces.new(bm_verts) # Fallback to N-gon
                self.report({'WARNING'}, "Used fallback N-gon fill.")
            except Exception as fill_e:
                self.report({'ERROR'}, f"Fallback fill also failed: {fill_e}")
        
        bm.to_mesh(mesh_data)
        bm.free()

        # --- 4. Finalize ---
        add_object_to_panel_collection(panel_fill_obj, panel_count, panel_name_prop)
        
        if self.keep_original_curve:
            original_curve_obj.hide_viewport = True
        else:
            bpy.data.objects.remove(original_curve_obj, do_unlink=True)
        
        bpy.ops.object.select_all(action='DESELECT')
        panel_fill_obj.select_set(True)
        context.view_layer.objects.active = panel_fill_obj
        
        self.report({'INFO'}, f"Successfully created quad panel: '{panel_fill_obj.name}'.")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(CURVE_OT_SampleAndQuadFill)

def unregister():
    bpy.utils.unregister_class(CURVE_OT_SampleAndQuadFill)
