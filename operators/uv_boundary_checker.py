"""
UV Boundary Checker for SneakerPanel Pro

This module provides functionality to detect and fix UV boundary violations
in 2D panel meshes before they are projected onto 3D shell surfaces.
It prevents misprojections by ensuring no mesh geometry extends beyond
the UV boundaries of the target shell.
"""
import bpy
import bmesh
from mathutils import Vector, geometry

class MESH_OT_CheckUVBoundary(bpy.types.Operator):
    """Check and optionally fix UV boundary violations in 2D panel mesh.    
    This operator analyzes a 2D panel mesh to detect areas that extend beyond
    the UV boundaries of the target shell. It can either highlight problem
    areas or automatically fix them by constraining geometry within bounds.
    """
    bl_idname = "mesh.check_uv_boundary"
    bl_label = "Check UV Boundary"
    bl_description = "Check for UV boundary violations and optionally fix them"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """Check if we have an active mesh and a valid shell object."""
        return (context.active_object and context.active_object.type == 'MESH' and
                hasattr(context.scene, 'spp_shell_object') and context.scene.spp_shell_object and
                context.scene.spp_shell_object.type == 'MESH')

    def find_uv_reference_mesh(self, context, shell_obj_name):
        """Find the UV reference mesh that corresponds to the given shell object."""
        for obj in context.scene.objects:
            if obj.type == 'MESH' and "spp_original_3d_mesh_name" in obj:
                if obj["spp_original_3d_mesh_name"] == shell_obj_name:                  
                    return obj
        return None

    def get_uv_boundary_edges(self, shell_obj, uv_layer_name):
        """Extract UV boundary edges from the shell mesh.
        
        Returns:
            List of UV boundary edge segments as (uv_start, uv_end) tuples
        """
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_shell = shell_obj.evaluated_get(depsgraph)
        eval_mesh = eval_shell.to_mesh()
        bm_shell = bmesh.new()
        bm_shell.from_mesh(eval_mesh)
        
        # Ensure lookup tables are updated
        bm_shell.verts.ensure_lookup_table()
        bm_shell.edges.ensure_lookup_table()
        bm_shell.faces.ensure_lookup_table()
        
        # Get UV layer
        uv_layer = bm_shell.loops.layers.uv.get(uv_layer_name)
        if uv_layer is None:
            uv_layer = bm_shell.loops.layers.uv.active
        
        boundary_edges = []
        
        # Find boundary edges (edges with only one face)
        for edge in bm_shell.edges:
            if len(edge.link_faces) == 1:
                face = edge.link_faces[0]
                # Find the loops corresponding to this edge's vertices
                edge_loops = []
                for loop in face.loops:
                    if loop.vert in edge.verts:
                        edge_loops.append(loop)
                
                if len(edge_loops) == 2:
                    uv1 = Vector(edge_loops[0][uv_layer].uv)
                    uv2 = Vector(edge_loops[1][uv_layer].uv)
                    boundary_edges.append((uv1, uv2))
        
        bm_shell.free()
        eval_shell.to_mesh_clear()
        return boundary_edges

    def check_edge_boundary_violation(self, edge_start_uv, edge_end_uv, boundary_edges, samples=10):
        """Check if an edge crosses UV boundary using optimized line intersection.
        
        Args:
            edge_start_uv: Start UV coordinate of edge
            edge_end_uv: End UV coordinate of edge
            boundary_edges: List of boundary edge segments
            samples: Number of sample points along the edge (reduced for performance)
            
        Returns:
            Tuple (is_violation, violation_points)
        """
        # Quick check: if both endpoints are inside, likely no violation
        start_outside = self.is_point_outside_boundary(edge_start_uv, boundary_edges)
        end_outside = self.is_point_outside_boundary(edge_end_uv, boundary_edges)
        
        # If both endpoints are inside, do minimal sampling
        if not start_outside and not end_outside:
            # Just check midpoint for performance
            mid_uv = edge_start_uv.lerp(edge_end_uv, 0.5)
            mid_outside = self.is_point_outside_boundary(mid_uv, boundary_edges)
            if not mid_outside:
                return False, []  # Likely no violation
        
        # If we reach here, do more thorough check but with fewer samples
        violations = []
        reduced_samples = min(samples, 5)  # Limit samples for performance
        
        for i in range(reduced_samples + 1):
            t = i / reduced_samples
            sample_uv = edge_start_uv.lerp(edge_end_uv, t)
            
            # Quick bounds check first
            if (sample_uv.x < 0 or sample_uv.x > 1 or 
                sample_uv.y < 0 or sample_uv.y > 1):
                violations.append(sample_uv)
                continue
            
            # Check if point is outside boundary (optimized)
            if self.is_point_outside_boundary(sample_uv, boundary_edges):
                violations.append(sample_uv)
        
        return len(violations) > 0, violations

    def is_point_outside_boundary(self, point_uv, boundary_edges):
        """Optimized check if a point is outside the UV boundary using single ray cast.
        
        Args:
            point_uv: UV coordinate to check
            boundary_edges: List of boundary edge segments
            
        Returns:
            True if point is outside boundary, False if inside
        """
        # Quick bounds check first
        if (point_uv.x < 0 or point_uv.x > 1 or 
            point_uv.y < 0 or point_uv.y > 1):
            return True
        
        # Use single horizontal ray for efficiency
        ray_start = Vector((point_uv.x, point_uv.y))
        ray_dir = Vector((1, 0))  # Horizontal ray to the right
        intersection_count = 0
        
        for boundary_start, boundary_end in boundary_edges:
            if self.ray_line_intersect_2d(ray_start, ray_dir, boundary_start, boundary_end):
                intersection_count += 1
        
        # Point is outside if even number of intersections (or zero)
        return intersection_count % 2 == 0

    def ray_line_intersect_2d(self, ray_start, ray_dir, line_start, line_end):
        """Check if a 2D ray intersects with a line segment."""
        # Convert to Vector for easier calculation
        rs = Vector((ray_start.x, ray_start.y))
        rd = Vector((ray_dir.x, ray_dir.y))
        ls = Vector((line_start.x, line_start.y))
        le = Vector((line_end.x, line_end.y))
        
        # Line direction
        ld = le - ls
        
        # Solve ray_start + t1 * ray_dir = line_start + t2 * line_dir
        # Using cross product method (2D cross product = determinant)
        denominator = rd.x * ld.y - rd.y * ld.x
        if abs(denominator) < 1e-10:  # Parallel lines
            return False
        
        diff = rs - ls
        t2 = (rd.x * diff.y - rd.y * diff.x) / denominator
        t1 = (ld.x * diff.y - ld.y * diff.x) / denominator
        
        # Check if intersection is on the line segment and ray
        return t1 >= 0 and 0 <= t2 <= 1

    def line_intersect_2d(self, line1_start, line1_end, line2_start, line2_end):
        """Find intersection point of two 2D line segments.
        
        Returns:
            Vector of intersection point, or None if no intersection
        """
        # Convert to Vector for easier calculation
        l1s = Vector((line1_start.x, line1_start.y))
        l1e = Vector((line1_end.x, line1_end.y))
        l2s = Vector((line2_start.x, line2_start.y))
        l2e = Vector((line2_end.x, line2_end.y))
        
        # Line directions
        l1d = l1e - l1s
        l2d = l2e - l2s
        
        # Solve line1_start + t1 * line1_dir = line2_start + t2 * line2_dir
        denominator = l1d.x * l2d.y - l1d.y * l2d.x
        if abs(denominator) < 1e-10:  # Parallel lines
            return None
        
        diff = l1s - l2s
        t1 = (l2d.x * diff.y - l2d.y * diff.x) / denominator
        
        # Calculate intersection point
        intersection = l1s + t1 * l1d
        return Vector((intersection.x, intersection.y))

    def get_line_parameter(self, line_start, line_end, point):
        """Get the parameter t where point = line_start + t * (line_end - line_start).
        
        Returns:
            Parameter t, or None if point is not on the line
        """
        line_vec = line_end - line_start
        point_vec = point - line_start
        
        # Use the component with larger magnitude to avoid division by zero
        if abs(line_vec.x) > abs(line_vec.y):
            if abs(line_vec.x) < 1e-10:
                return None
            return point_vec.x / line_vec.x
        else:
            if abs(line_vec.y) < 1e-10:
                return None
            return point_vec.y / line_vec.y

    def is_point_outside_boundary_legacy(self, point, boundary_edges):
        """Check if a point is outside the UV mesh boundary using ray casting.
        
        Args:
            point: Vector2D point to check
            boundary_edges: List of UV boundary edge segments
            
        Returns:
            True if point is outside boundary, False if inside
        """
        if not boundary_edges:
            return False
            
        # Use ray casting algorithm - cast ray to the right and count intersections
        ray_start = point
        ray_end = Vector((point.x + 1000, point.y))  # Ray extending far to the right
        
        intersection_count = 0
        
        for edge_start, edge_end in boundary_edges:
            # Check if ray intersects with this boundary edge
            if self.line_segments_intersect_legacy(ray_start, ray_end, edge_start, edge_end):
                intersection_count += 1
        
        # If odd number of intersections, point is inside; if even, point is outside
        return intersection_count % 2 == 0

    def line_segments_intersect_legacy(self, line1_start, line1_end, line2_start, line2_end):
        """Check if two line segments intersect.
        
        Returns:
            True if segments intersect, False otherwise
        """
        # Convert to Vector for easier calculation
        l1s = Vector((line1_start.x, line1_start.y))
        l1e = Vector((line1_end.x, line1_end.y))
        l2s = Vector((line2_start.x, line2_start.y))
        l2e = Vector((line2_end.x, line2_end.y))
        
        # Line directions
        l1d = l1e - l1s
        l2d = l2e - l2s
        
        # Solve line1_start + t1 * line1_dir = line2_start + t2 * line2_dir
        denominator = l1d.x * l2d.y - l1d.y * l2d.x
        if abs(denominator) < 1e-10:  # Parallel lines
            return False
        
        diff = l1s - l2s
        t1 = (l2d.x * diff.y - l2d.y * diff.x) / denominator
        t2 = (l1d.x * diff.y - l1d.y * diff.x) / denominator
        
        # Check if intersection is within both line segments
        return 0 <= t1 <= 1 and 0 <= t2 <= 1

    def find_closest_point_on_boundary(self, point, boundary_edges):
        """Find the closest point on the UV boundary to the given point.
        
        Args:
            point: Vector2D point to find closest boundary point for
            boundary_edges: List of UV boundary edge segments
            
        Returns:
            Vector2D of closest point on boundary, or None if no boundary edges
        """
        if not boundary_edges:
            return None
            
        closest_point = None
        min_distance = float('inf')
        
        for edge_start, edge_end in boundary_edges:
            # Find closest point on this edge segment
            edge_point = self.closest_point_on_line_segment(point, edge_start, edge_end)
            distance = (point - edge_point).length
            
            if distance < min_distance:
                min_distance = distance
                closest_point = edge_point
        
        return closest_point
    
    def find_closest_boundary_point(self, point, boundary_edges):
        """Backward-compatible alias for find_closest_point_on_boundary."""
        return self.find_closest_point_on_boundary(point, boundary_edges)
    
    def closest_point_on_line_segment(self, point, line_start, line_end):
        """Find the closest point on a line segment to the given point.
        
        Args:
            point: Vector2D point
            line_start: Vector2D start of line segment
            line_end: Vector2D end of line segment
            
        Returns:
            Vector2D of closest point on line segment
        """
        # Vector from line start to line end
        line_vec = line_end - line_start
        line_length_sq = line_vec.length_squared
        
        if line_length_sq == 0:
            # Line segment is a point
            return line_start
        
        # Vector from line start to point
        point_vec = point - line_start
        
        # Project point onto line (parameter t)
        t = point_vec.dot(line_vec) / line_length_sq
        
        # Clamp t to [0, 1] to stay within line segment
        t = max(0, min(1, t))
        
        # Calculate closest point
        closest = line_start + t * line_vec
        return Vector((closest.x, closest.y))

    def fix_boundary_violations(self, bm, uv_mesh_obj, scale_factor, boundary_edges):
        """Fix violations by snapping directly to the boundary (no padding).
        
        Simple and reliable approach:
        1. Find vertices outside boundary
        2. Snap each to closest boundary point
        """
        fixed_count = 0
        padding_used = 0.0  # No padding; restore previous behavior
        
        for vert in bm.verts:
            # Convert vertex to UV space
            p_world = bpy.context.active_object.matrix_world @ vert.co
            p_local_uv = uv_mesh_obj.matrix_world.inverted() @ p_world
            uv_coord = Vector((p_local_uv.x / scale_factor, p_local_uv.y / scale_factor))
            
            # Check if vertex is outside the actual UV mesh boundary
            is_outside = self.is_point_outside_boundary(uv_coord, boundary_edges)
            
            if is_outside:
                # Find closest point on UV boundary
                closest_point = self.find_closest_boundary_point(uv_coord, boundary_edges)
                
                if closest_point:
                    # Snap directly onto the boundary (no padding)
                    new_uv = closest_point
                    
                    # Convert back to world space
                    p_local_fixed = Vector((new_uv.x * scale_factor, new_uv.y * scale_factor, p_local_uv.z))
                    p_world_fixed = uv_mesh_obj.matrix_world @ p_local_fixed
                    vert.co = bpy.context.active_object.matrix_world.inverted() @ p_world_fixed
                    fixed_count += 1
        
        return fixed_count, padding_used

    def calculate_inward_direction(self, boundary_point, boundary_edges):
        """Calculate the inward direction from a boundary point.
        
        Args:
            boundary_point: Point on the boundary
            boundary_edges: List of boundary edge segments
            
        Returns:
            Vector2D pointing inward from the boundary
        """
        # Find the boundary edge this point lies on
        edge_direction = None
        
        for edge_start, edge_end in boundary_edges:
            # Check if point is on this edge (within small tolerance)
            closest = self.closest_point_on_line_segment(boundary_point, edge_start, edge_end)
            if (closest - boundary_point).length < 0.001:
                edge_direction = (edge_end - edge_start).normalized()
                break
        
        if edge_direction:
            # Calculate perpendicular direction (normal to edge)
            # Try both perpendicular directions and pick the one pointing inward
            perp1 = Vector((-edge_direction.y, edge_direction.x))
            perp2 = Vector((edge_direction.y, -edge_direction.x))
            
            # Test which direction points more toward the inside
            test_point1 = boundary_point + perp1 * 0.001
            test_point2 = boundary_point + perp2 * 0.001
            
            # The direction that results in a point inside the boundary is inward
            if not self.is_point_outside_boundary(test_point1, boundary_edges):
                return perp1
            elif not self.is_point_outside_boundary(test_point2, boundary_edges):
                return perp2
        
        # Fallback: direction toward approximate center
        # Calculate rough center of boundary
        center_x = sum(edge[0].x + edge[1].x for edge in boundary_edges) / (2 * len(boundary_edges))
        center_y = sum(edge[0].y + edge[1].y for edge in boundary_edges) / (2 * len(boundary_edges))
        center = Vector((center_x, center_y))
        
        direction = (center - boundary_point)
        if direction.length > 0:
            return direction.normalized()
        else:
            return Vector((0, -0.1))  # Default inward direction

    def highlight_violations(self, bm, violation_verts, violation_edges=None, panel_obj=None):
        """Highlight violation vertices and edges by selecting them and creating vertex groups."""
        # Deselect all first
        for vert in bm.verts:
            vert.select = False
        for edge in bm.edges:
            edge.select = False
        for face in bm.faces:
            face.select = False
        
        # Select violation vertices
        for vert_idx in violation_verts:
            if vert_idx < len(bm.verts):
                bm.verts[vert_idx].select = True
                
        # Select violation edges
        if violation_edges:
            for edge in violation_edges:
                edge.select = True
        
        # Store violation data for vertex group creation after mesh update
        if panel_obj:
            panel_obj['_violation_verts'] = violation_verts
            panel_obj['_violation_edges'] = [edge.index for edge in violation_edges] if violation_edges else []

    def create_violation_vertex_groups(self, panel_obj):
        """Create vertex groups to persistently mark violation areas from stored data."""
        # Get stored violation data
        violation_verts = panel_obj.get('_violation_verts', [])
        violation_edge_indices = panel_obj.get('_violation_edges', [])
        
        if not violation_verts and not violation_edge_indices:
            return
        
        # Remove existing violation vertex groups
        groups_to_remove = []
        for vg in panel_obj.vertex_groups:
            if vg.name.startswith("UV_Violation_"):
                groups_to_remove.append(vg)
        
        for vg in groups_to_remove:
            panel_obj.vertex_groups.remove(vg)
        
        # Create vertex group for violating vertices
        if violation_verts:
            vertex_vg = panel_obj.vertex_groups.new(name="UV_Violation_Vertices")
            for vert_idx in violation_verts:
                if vert_idx < len(panel_obj.data.vertices):
                    vertex_vg.add([vert_idx], 1.0, 'REPLACE')
        
        # Create vertex group for vertices of violating edges
        if violation_edge_indices:
            edge_verts = set()
            for edge_idx in violation_edge_indices:
                if edge_idx < len(panel_obj.data.edges):
                    edge = panel_obj.data.edges[edge_idx]
                    edge_verts.add(edge.vertices[0])
                    edge_verts.add(edge.vertices[1])
            
            if edge_verts:
                edge_vg = panel_obj.vertex_groups.new(name="UV_Violation_Edges")
                for vert_idx in edge_verts:
                    edge_vg.add([vert_idx], 1.0, 'REPLACE')
        
        # Clean up stored data
        if '_violation_verts' in panel_obj:
            del panel_obj['_violation_verts']
        if '_violation_edges' in panel_obj:
            del panel_obj['_violation_edges']

    def select_violation_vertex_groups(self, panel_obj):
        """Re-select vertices from violation vertex groups."""
        # Switch to Edit mode if not already
        if bpy.context.mode != 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='EDIT')
        
        # Deselect all
        bpy.ops.mesh.select_all(action='DESELECT')
        
        # Select vertices from violation groups
        for vg in panel_obj.vertex_groups:
            if vg.name.startswith("UV_Violation_"):
                panel_obj.vertex_groups.active = vg
                bpy.ops.object.vertex_group_select()

    def execute(self, context):
        import time
        start_time = time.time()
        
        # Add undo checkpoint
        bpy.ops.ed.undo_push(message="Check UV Boundary")
        
        panel_obj = context.active_object
        shell_obj = context.scene.spp_shell_object
        scene = context.scene
        
        # Get action from scene properties (samples and margin now use smart defaults)
        action = scene.spp_uv_boundary_action
        
        # Use optimized defaults for performance and reliability
        raycast_samples = 5  # Fixed optimal value
        # No padding/margin used in FIX mode; vertices snap directly to boundary
        
        # Find UV reference mesh
        uv_mesh_obj = self.find_uv_reference_mesh(context, shell_obj.name)
        
        if not uv_mesh_obj:
            self.report({'ERROR'}, f"UV reference mesh for '{shell_obj.name}' not found.")
            return {'CANCELLED'}
        
        # Get required properties
        scale_factor = uv_mesh_obj.get("spp_applied_scale_factor", None)
        source_uv_map_name = uv_mesh_obj.get("spp_source_uv_map_name", None)
        
        if scale_factor is None or source_uv_map_name is None:
            self.report({'ERROR'}, "UV reference mesh missing required custom properties.")
            return {'CANCELLED'}
        
        try:
            # Store original mode and ensure we're in Object mode for mesh operations
            original_mode = bpy.context.mode
            if original_mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            
            # Get UV boundary edges
            boundary_edges = self.get_uv_boundary_edges(shell_obj, source_uv_map_name)
            if not boundary_edges:
                self.report({'WARNING'}, "No UV boundary edges found.")
                return {'CANCELLED'}
            
            # Analyze mesh
            bm = bmesh.new()
            bm.from_mesh(panel_obj.data)
            
            # Ensure lookup tables are updated
            bm.verts.ensure_lookup_table()
            bm.edges.ensure_lookup_table()
            bm.faces.ensure_lookup_table()
            
            violation_verts = []
            violation_edges = []
            
            # Check vertices against actual UV mesh boundary
            for i, vert in enumerate(bm.verts):
                # Timeout check every 100 vertices
                if i % 100 == 0 and time.time() - start_time > 30:
                    bm.free()
                    context.scene.spp_uv_boundary_status = 'ERROR'
                    self.report({'ERROR'}, "Operation timed out after 30 seconds. Try reducing sample count.")
                    return {'CANCELLED'}
                
                p_world = panel_obj.matrix_world @ vert.co
                p_local_uv = uv_mesh_obj.matrix_world.inverted() @ p_world
                uv_coord = Vector((p_local_uv.x / scale_factor, p_local_uv.y / scale_factor))
                
                # Check if vertex is outside the actual UV mesh boundary
                is_outside = self.is_point_outside_boundary(uv_coord, boundary_edges)
                if is_outside:
                    violation_verts.append(i)
            
            # Check edges for boundary crossings (with early termination for performance)
            edge_count = 0
            max_edges = min(len(bm.edges), 1000)  # Limit edge checks for performance
            
            for edge in bm.edges:
                edge_count += 1
                
                # Timeout and limit checks
                if edge_count % 50 == 0:
                    if time.time() - start_time > 30:
                        bm.free()
                        context.scene.spp_uv_boundary_status = 'ERROR'
                        self.report({'ERROR'}, "Operation timed out. Try reducing sample count or mesh complexity.")
                        return {'CANCELLED'}
                    
                    if edge_count > max_edges:
                        self.report({'WARNING'}, f"Checked {max_edges} edges (limit reached). Some violations may be missed.")
                        break
                
                v1, v2 = edge.verts
                
                # Convert vertices to UV space
                p1_world = panel_obj.matrix_world @ v1.co
                p1_local_uv = uv_mesh_obj.matrix_world.inverted() @ p1_world
                uv1 = Vector((p1_local_uv.x / scale_factor, p1_local_uv.y / scale_factor))
                
                p2_world = panel_obj.matrix_world @ v2.co
                p2_local_uv = uv_mesh_obj.matrix_world.inverted() @ p2_world
                uv2 = Vector((p2_local_uv.x / scale_factor, p2_local_uv.y / scale_factor))
                
                # Check edge for violations
                has_violation, _ = self.check_edge_boundary_violation(
                    uv1, uv2, boundary_edges, raycast_samples)
                
                if has_violation:
                    violation_edges.append(edge)
            
            # Perform action based on user choice
            if action == 'CHECK':
                self.highlight_violations(bm, violation_verts, violation_edges, panel_obj)
                bm.to_mesh(panel_obj.data)
                panel_obj.data.update()
                
                # Create vertex groups for persistent highlighting
                self.create_violation_vertex_groups(panel_obj)
                
                # Switch to Edit mode to show selection (or restore original if it was Edit)
                if original_mode == 'EDIT_MESH' or (violation_verts or violation_edges):
                    bpy.ops.object.mode_set(mode='EDIT')
                else:
                    # Restore original mode if no violations to show
                    if original_mode != 'OBJECT':
                        try:
                            mode_name = original_mode.split('_')[0].lower()
                            bpy.ops.object.mode_set(mode=mode_name.upper())
                        except:
                            pass  # Stay in Object mode if restoration fails
                
                message = f"Found {len(violation_verts)} vertex violations and {len(violation_edges)} edge violations"
                
                if violation_verts or violation_edges:
                    context.scene.spp_uv_boundary_status = 'VIOLATIONS'
                    self.report({'WARNING'}, message)
                else:
                    context.scene.spp_uv_boundary_status = 'PASS'
                    self.report({'INFO'}, "No UV boundary violations found")
                    
            elif action == 'FIX':
                try:
                    # Use the simple snap-to-boundary fix (no padding)
                    fixed_count, padding_used = self.fix_boundary_violations(bm, uv_mesh_obj, scale_factor, boundary_edges)
                    
                    # Update mesh
                    bm.to_mesh(panel_obj.data)
                    panel_obj.data.update()
                    
                    # Re-check for any remaining violations after fixing
                    remaining_violations = 0
                    for vert in bm.verts:
                        p_world = panel_obj.matrix_world @ vert.co
                        p_local_uv = uv_mesh_obj.matrix_world.inverted() @ p_world
                        uv_coord = Vector((p_local_uv.x / scale_factor, p_local_uv.y / scale_factor))
                        if self.is_point_outside_boundary(uv_coord, boundary_edges):
                            remaining_violations += 1
                    
                    # Report results
                    if fixed_count > 0:
                        message = f"Fixed {fixed_count} violations by snapping to boundary"
                        if remaining_violations > 0:
                            message += f". {remaining_violations} violations remain - try Interactive mode for manual fixing."
                            context.scene.spp_uv_boundary_status = 'VIOLATIONS'
                        else:
                            message += ". All violations fixed!"
                            context.scene.spp_uv_boundary_status = 'PASS'
                        self.report({'INFO'}, message)
                    else:
                        context.scene.spp_uv_boundary_status = 'PASS'
                        self.report({'INFO'}, "No violations found to fix")
                        
                except Exception as fix_error:
                    context.scene.spp_uv_boundary_status = 'ERROR'
                    self.report({'ERROR'}, f"Error fixing violations: {str(fix_error)}")
                
            elif action == 'INTERACTIVE':
                # Select violations for manual fixing
                self.highlight_violations(bm, violation_verts, violation_edges, panel_obj)
                bm.to_mesh(panel_obj.data)
                panel_obj.data.update()
                
                # Create vertex groups for persistent highlighting
                self.create_violation_vertex_groups(panel_obj)
                
                # Switch to Edit mode to show selection (always for INTERACTIVE)
                bpy.ops.object.mode_set(mode='EDIT')
                
                total_violations = len(violation_verts) + len(violation_edges)
                if total_violations > 0:
                    context.scene.spp_uv_boundary_status = 'VIOLATIONS'
                else:
                    context.scene.spp_uv_boundary_status = 'PASS'
                message = f"Selected {len(violation_verts)} vertices and {len(violation_edges)} edges ({total_violations} total) for manual editing"
                self.report({'INFO'}, message)
            
            # Clean up bmesh
            bm.free()
            
            # Performance report
            elapsed_time = time.time() - start_time
            if elapsed_time > 5:  # Only report if took more than 5 seconds
                self.report({'INFO'}, f"Boundary check completed in {elapsed_time:.1f} seconds")
            
        except Exception as e:
            context.scene.spp_uv_boundary_status = 'ERROR'
            self.report({'ERROR'}, f"Error checking UV boundary: {str(e)}")
            # Ensure bmesh is freed even on error
            if 'bm' in locals():
                bm.free()
            # Try to restore original mode on error
            try:
                if 'original_mode' in locals() and original_mode != 'OBJECT':
                    mode_name = original_mode.split('_')[0].lower()
                    bpy.ops.object.mode_set(mode=mode_name.upper())
            except:
                pass
            return {'CANCELLED'}
            
        return {'FINISHED'}

class MESH_OT_ReselectUVViolations(bpy.types.Operator):
    """Re-select UV boundary violations from vertex groups"""
    bl_idname = "mesh.reselect_uv_violations"
    bl_label = "Re-select UV Violations"
    bl_description = "Re-select vertices marked as UV boundary violations"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """Check if we have an active mesh with violation vertex groups."""
        if not (context.active_object and context.active_object.type == 'MESH'):
            return False
        
        # Check if object has violation vertex groups
        for vg in context.active_object.vertex_groups:
            if vg.name.startswith("UV_Violation_"):
                return True
        return False

    def execute(self, context):
        panel_obj = context.active_object
        
        # Switch to Edit mode if not already
        if bpy.context.mode != 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='EDIT')
        
        # Deselect all
        bpy.ops.mesh.select_all(action='DESELECT')
        
        # Select vertices from violation groups
        violation_count = 0
        for vg in panel_obj.vertex_groups:
            if vg.name.startswith("UV_Violation_"):
                panel_obj.vertex_groups.active = vg
                bpy.ops.object.vertex_group_select()
                violation_count += len([v for v in panel_obj.data.vertices if vg.index in [g.group for g in v.groups]])
        
        if violation_count > 0:
            self.report({'INFO'}, f"Re-selected {violation_count} violation vertices")
        else:
            self.report({'WARNING'}, "No violation vertex groups found")
        
        return {'FINISHED'}

# Registration
classes = [MESH_OT_CheckUVBoundary, MESH_OT_ReselectUVViolations]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
