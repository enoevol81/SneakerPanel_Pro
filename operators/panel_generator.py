import bpy
import bmesh
from mathutils import Vector

def info(msg):
    """Print information message"""
    print(f"[PANEL GENERATOR] {msg}")

def error(msg):
    """Print error message"""
    print(f"[PANEL GENERATOR ERROR] {msg}")

def get_boundary_verts(bm):
    """Get ordered boundary vertices in a mesh
    
    Args:
        bm: BMesh to analyze
        
    Returns:
        List of boundary BMVerts in connected order
    """
    # Find all boundary edges (edges with only one connected face)
    boundary_edges = [e for e in bm.edges if len(e.link_faces) < 2]
    
    # Return empty list if no boundary edges found
    if not boundary_edges:
        return []
    
    # Start with the first boundary edge's first vertex
    verts = []
    visited_edges = set()
    
    # Make sure we have at least one edge to start with
    if not boundary_edges:
        return []
    
    # Get the first edge and its vertices
    first_edge = boundary_edges[0]
    current = first_edge.verts[0]
    start = current
    
    # Walk along boundary edges to collect vertices in order
    while True:
        verts.append(current)
        
        # Find the next unvisited boundary edge connected to current vertex
        next_edge = None
        for edge in current.link_edges:
            if edge in boundary_edges and edge not in visited_edges:
                next_edge = edge
                visited_edges.add(edge)
                break
                
        # If no next edge found, we've reached the end of an open boundary
        if not next_edge:
            break
            
        # Move to the other vertex of the edge
        current = next_edge.other_vert(current)
        
        # If we've returned to the start, we've completed a closed loop
        if current == start:
            break
            
    return verts

def project_verts_to_surface(obj, verts, shell_obj):
    """Project specific vertices onto a target surface
    
    Args:
        obj: The object containing the vertices to project
        verts: List of BMVert to project
        shell_obj: Target surface object for projection
    """
    bpy.ops.object.mode_set(mode='OBJECT')
    for v in obj.data.vertices:
        v.select = False
    for v in verts:
        obj.data.vertices[v.index].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(type="VERT")
    bpy.ops.object.mode_set(mode='OBJECT')
    for v in verts:
        obj.data.vertices[v.index].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.transform.vertex_random(offset=0.00001)  # Dummy op to update selection
    bpy.ops.object.mode_set(mode='OBJECT')
    mod = obj.modifiers.new("BoundaryProject", 'SHRINKWRAP')
    mod.target = shell_obj
    mod.wrap_method = 'NEAREST_SURFACEPOINT'
    mod.offset = 0.0001
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    for v in obj.data.vertices:
        v.select = False
    for v in verts:
        obj.data.vertices[v.index].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.modifier_apply(modifier=mod.name)
    info("Boundary vertices projected onto shell surface.")

def apply_surface_snap(shell_obj, iterations=1):
    """Apply surface snapping with multiple iterations
    
    Args:
        shell_obj: Target surface object
        iterations: Number of iterations to apply
    """
    for i in range(iterations):
        try:
            obj = bpy.context.active_object
            mod = obj.modifiers.new(f"TempSnap_{i}", 'SHRINKWRAP')
            mod.target = shell_obj
            mod.wrap_method = 'NEAREST_SURFACEPOINT'
            mod.offset = 0.0001
            bpy.ops.object.modifier_apply(modifier=mod.name)
            info(f"Surface snap iteration {i+1} applied.")
        except Exception as e:
            error(f"Surface snap failed: {e}")

def create_flow_based_quads(bm):
    """Create flow-based quad topology
    
    Args:
        bm: BMesh to modify
        
    Returns:
        Modified BMesh
    """
    try:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        for _ in range(3):
            bmesh.ops.smooth_vert(bm, verts=bm.verts, factor=0.5)
    except Exception as e:
        error(f"Flow-based quad op failed: {e}")
    return bm

def generate_panel(panel_obj, shell_obj, filled_obj_name=None, grid_span=4, uv_layer_name="UVMap"):
    """Generate a panel from a mesh object
    
    Args:
        panel_obj: Input mesh object (should be a mesh created from a curve)
        shell_obj: Target surface object
        filled_obj_name: Name for the output object (if None, will use panel_obj.name + "_Filled")
        grid_span: Grid fill span value
        uv_layer_name: Name for the UV layer
        
    Returns:
        The generated panel object or None if failed
    """
    info("Starting panel generation.")

    if not panel_obj:
        error("Input panel object not provided.")
        return None
        
    if not shell_obj or shell_obj.type != 'MESH':
        error(f"Shell object not found or not a mesh.")
        return None

    # Ensure input is a mesh with enough vertices
    if panel_obj.type != 'MESH':
        error("Input must be a mesh object, not a curve. Convert curve to mesh first.")
        return None
        
    if len(panel_obj.data.vertices) < 3:
        error("Input mesh has fewer than 3 vertices.")
        return None

    # Set default name if not provided
    if not filled_obj_name:
        filled_obj_name = f"{panel_obj.name}_Filled"
    
    # Ensure we're in object mode
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    # Create a copy for the filled version
    bpy.ops.object.select_all(action='DESELECT')
    panel_obj.select_set(True)
    bpy.context.view_layer.objects.active = panel_obj
    bpy.ops.object.duplicate()
    filled_obj = bpy.context.active_object
    filled_obj.name = filled_obj_name
    info(f"Duplicated to '{filled_obj_name}'.")

    # Ensure we're working with a mesh
    if filled_obj.type != 'MESH':
        error("Duplicate is not a mesh. This should not happen.")
        return None

    # Preprocessing to ensure we have a valid boundary
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    
    # First ensure the curve is closed
    try:
        bpy.ops.mesh.edge_face_add()
        bpy.ops.mesh.delete(type='ONLY_FACE')
    except Exception as e:
        info(f"Preprocessing step (edge_face_add) failed: {e}")
    
    # Now remove doubles to clean up the mesh
    try:
        # Store initial vertex count
        bpy.ops.object.mode_set(mode='OBJECT')
        initial_vert_count = len(filled_obj.data.vertices)
        bpy.ops.object.mode_set(mode='EDIT')
        
        # Remove doubles
        bpy.ops.mesh.remove_doubles(threshold=0.0001)
        
        # Check how many vertices were removed
        bpy.ops.object.mode_set(mode='OBJECT')
        final_vert_count = len(filled_obj.data.vertices)
        removed_count = initial_vert_count - final_vert_count
        info(f"Removed {removed_count} vertices")
        
        # Back to edit mode
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
    except Exception as e:
        info(f"Preprocessing step (remove_doubles) failed: {e}")
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')

    # Store original boundary positions
    bpy.ops.object.mode_set(mode='OBJECT')
    bm = bmesh.new()
    bm.from_mesh(filled_obj.data)
    orig_boundary_verts = get_boundary_verts(bm)
    orig_boundary_coords = [v.co.copy() for v in orig_boundary_verts]
    bm.free()
    info(f"Stored {len(orig_boundary_coords)} boundary vertex positions.")
    
    # Check if we have enough vertices for a valid shape
    if len(orig_boundary_coords) < 3:
        error("Invalid boundary: Not enough vertices to form a shape.")
        return None

    # Grid fill
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    try:
        if grid_span > 0:
            bpy.ops.mesh.fill_grid(span=grid_span)
        else:
            bpy.ops.mesh.fill_grid()
        info(f"Grid fill succeeded with span={grid_span}.")
    except Exception as e:
        error(f"Grid fill failed: {e}")
        return None

    # Restore boundary positions
    bpy.ops.object.mode_set(mode='OBJECT')
    bm = bmesh.new()
    bm.from_mesh(filled_obj.data)
    new_boundary_verts = get_boundary_verts(bm)
    if len(new_boundary_verts) == len(orig_boundary_coords):
        for v, co in zip(new_boundary_verts, orig_boundary_coords):
            v.co = co
        info("Restored original boundary positions after grid fill.")
    else:
        error("Boundary vertex count mismatch after grid fill; could not restore outline.")
    bm.to_mesh(filled_obj.data)
    bm.free()
    filled_obj.data.update()

    # Project boundary verts onto shell
    bm = bmesh.new()
    bm.from_mesh(filled_obj.data)
    boundary_verts = get_boundary_verts(bm)
    bm.free()
    project_verts_to_surface(filled_obj, boundary_verts, shell_obj)

    # Flow-based quads and UVs
    bm = bmesh.new()
    bm.from_mesh(filled_obj.data)
    bm = create_flow_based_quads(bm)
    if not filled_obj.data.uv_layers:
        filled_obj.data.uv_layers.new(name=uv_layer_name)
    uv_layer = bm.loops.layers.uv.verify()
    for face in bm.faces:
        for loop in face.loops:
            co = loop.vert.co
            loop[uv_layer].uv = (co.x, co.y)
    bm.to_mesh(filled_obj.data)
    filled_obj.data.validate()
    filled_obj.data.update()
    bm.free()
    info("UVs assigned and mesh updated.")

    # Apply surface conformity operations
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.vertices_smooth(factor=0.5)
    bpy.ops.object.mode_set(mode='OBJECT')
    apply_surface_snap(shell_obj, iterations=3)

    # Final conformity pass
    try:
        mod = filled_obj.modifiers.new("FinalConform", 'SHRINKWRAP')
        mod.target = shell_obj
        mod.wrap_method = 'NEAREST_SURFACEPOINT'
        mod.offset = 0.0001
        bpy.ops.object.modifier_apply(modifier=mod.name)
        info("Final shrinkwrap applied.")
    except Exception as e:
        error(f"Final shrinkwrap failed: {e}")

    info("Panel generation complete!")
    return filled_obj
