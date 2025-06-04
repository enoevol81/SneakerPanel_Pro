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

# In SneakerPanel_Pro/operators/panel_generator.py

# ... (info, error functions) ...
# ... (get_boundary_verts function) ...

def project_verts_to_surface(obj, vert_indices, shell_obj): # << MODIFIED: vert_indices is list of int
    """Project specific vertices (by index) onto a target surface"""
    info(f"Projecting {len(vert_indices)} boundary vertices for {obj.name}.")
    if not vert_indices:
        info("No vertex indices provided for projection.")
        return

    # Ensure in Object Mode for selection and modifier operations
    if obj.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    # Deselect all vertices of the object first
    for v_mesh in obj.data.vertices:
        v_mesh.select = False
    
    # Select vertices by their indices
    valid_indices_count = 0
    for idx in vert_indices:
        if idx < len(obj.data.vertices):
            obj.data.vertices[idx].select = True
            valid_indices_count +=1
        else:
            error(f"Invalid vertex index {idx} for object {obj.name} in project_verts_to_surface.")
    
    if valid_indices_count == 0:
        info("No valid vertices were selected for projection.")
        return

    # The selection is now set on obj.data.vertices.
    # bpy.ops calls that rely on selection in Edit Mode would need a mode switch.
    # However, for Shrinkwrap with vertex group, we can stay in Object Mode.

    mod_name = "BoundaryProjectShrinkwrap"
    mod = obj.modifiers.new(mod_name, 'SHRINKWRAP')
    mod.target = shell_obj
    mod.wrap_method = 'NEAREST_SURFACEPOINT' 
    mod.offset = 0.0001 

    # Use a temporary vertex group to limit the modifier's effect
    vg_name = "_temp_boundary_proj_vg"
    # Remove group if it somehow exists from a previous failed run
    existing_vg = obj.vertex_groups.get(vg_name)
    if existing_vg:
        obj.vertex_groups.remove(existing_vg)
        
    vg = obj.vertex_groups.new(name=vg_name)
    vg.add(vert_indices, 1.0, 'REPLACE') # Add valid indices to the group
    mod.vertex_group = vg_name # Assign the vertex group to the modifier

    # Apply the modifier
    # Need to ensure object is active and selected for bpy.ops.object.modifier_apply
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
    try:
        bpy.ops.object.modifier_apply(modifier=mod_name)
        info(f"Applied Shrinkwrap for boundary projection on {obj.name}.")
    except RuntimeError as e:
        error(f"Failed to apply Shrinkwrap for boundary projection: {e}. Modifier will be removed.")
        obj.modifiers.remove(mod) # Clean up modifier if apply fails

    # Clean up the temporary vertex group
    # Need to check if vg still exists, as modifier_apply might clear it if it was assigned by name.
    # Or more robustly, just try to remove by name.
    vg_to_remove = obj.vertex_groups.get(vg_name)
    if vg_to_remove:
        obj.vertex_groups.remove(vg_to_remove)
        info(f"Removed temporary vertex group '{vg_name}'.")
    
    # Deselect vertices again after operation if needed, though not strictly necessary here
    # for v_mesh in obj.data.vertices:
    #     v_mesh.select = False


# In SneakerPanel_Pro/operators/panel_generator.py

# ... (keep info, error, get_boundary_verts, project_verts_to_surface functions as previously corrected) ...

def apply_surface_snap(obj_to_snap, target_shell_obj, iterations=1): # MODIFIED DEFINITION
    """Apply surface snapping with multiple iterations using Shrinkwrap.
    
    Args:
        obj_to_snap: The object to apply the snap to.
        target_shell_obj: Target surface object for projection.
        iterations: Number of iterations to apply.
    """
    info(f"Applying iterative Shrinkwrap snap to '{obj_to_snap.name}' targeting '{target_shell_obj.name}'.")
    
    # Store original active object and selection to restore later
    original_active = bpy.context.view_layer.objects.active
    original_selected_objects = bpy.context.selected_objects[:]

    for i in range(iterations):
        mod = None # Initialize mod to None for broader scope in except block
        try:
            # Add Shrinkwrap modifier directly to the obj_to_snap
            mod = obj_to_snap.modifiers.new(name=f"TempSnap_{i}", type='SHRINKWRAP')
            mod.target = target_shell_obj
            mod.wrap_method = 'NEAREST_SURFACEPOINT' # As used in project_verts_to_surface
            mod.offset = 0.0001 # Consistent with project_verts_to_surface

            # For modifier_apply to work correctly, obj_to_snap must be active and selected
            bpy.ops.object.select_all(action='DESELECT')
            obj_to_snap.select_set(True)
            bpy.context.view_layer.objects.active = obj_to_snap
            
            bpy.ops.object.modifier_apply(modifier=mod.name)
            info(f"Shrinkwrap snap iteration {i+1} applied to '{obj_to_snap.name}'.")
        except RuntimeError as e:
            error(f"Shrinkwrap snap iteration {i+1} failed for '{obj_to_snap.name}': {e}")
            # Attempt to remove the modifier if it was added but apply failed
            if mod and mod.name in obj_to_snap.modifiers:
                obj_to_snap.modifiers.remove(mod)
            break # Stop further iterations if one fails
        except Exception as e: # Catch any other unexpected errors
            error(f"Unexpected error in Shrinkwrap snap iteration {i+1} for '{obj_to_snap.name}': {e}")
            if mod and mod.name in obj_to_snap.modifiers:
                obj_to_snap.modifiers.remove(mod)
            break


    # Restore original selection and active object
    bpy.ops.object.select_all(action='DESELECT')
    for obj_sel in original_selected_objects:
        if obj_sel and obj_sel.name in bpy.data.objects: # Check if object still exists
            obj_sel.select_set(True)
    if original_active and original_active.name in bpy.data.objects: # Check if object still exists
        bpy.context.view_layer.objects.active = original_active
    elif bpy.context.view_layer.objects.active != obj_to_snap and obj_to_snap.name in bpy.data.objects : # If active changed and obj_to_snap is not active, make it active
        bpy.context.view_layer.objects.active = obj_to_snap


# ... (keep create_flow_based_quads, generate_panel, register/unregister functions, ensuring generate_panel uses the corrected apply_surface_snap call implicitly)

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
    info("Starting panel generation.")

    if not panel_obj: # ... (keep existing initial checks)
        error("Input panel object not provided.")
        return None
    # ... (other checks) ...
    
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    bpy.ops.object.select_all(action='DESELECT')
    panel_obj.select_set(True)
    bpy.context.view_layer.objects.active = panel_obj
    bpy.ops.object.duplicate()
    filled_obj = bpy.context.active_object
    filled_obj.name = filled_obj_name if filled_obj_name else f"{panel_obj.name}_Filled" # Simplified naming
    info(f"Duplicated to '{filled_obj.name}'.")

    if filled_obj.type != 'MESH': # ... (keep checks) ...
        error("Duplicate is not a mesh.")
        return None # Make sure to return None on error

    # Preprocessing (keep as is)
    # ...

    # Store original boundary positions
    bpy.ops.object.mode_set(mode='OBJECT')
    bm_orig_boundary = bmesh.new()
    bm_orig_boundary.from_mesh(filled_obj.data)
    orig_boundary_verts_bmesh = get_boundary_verts(bm_orig_boundary) # BMVerts
    orig_boundary_coords = [v.co.copy() for v in orig_boundary_verts_bmesh]
    bm_orig_boundary.free() # Free this BM
    info(f"Stored {len(orig_boundary_coords)} original boundary vertex positions.")
    
    if len(orig_boundary_coords) < 3: # ... (keep check) ...
        error("Invalid boundary after preprocessing: Not enough vertices.")
        return None


    # Grid fill (keep as is)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    try:
        bpy.ops.mesh.fill_grid(span=grid_span if grid_span > 0 else 1) # ensure span >= 1 if not 0
        info(f"Grid fill succeeded with span={grid_span}.")
    except Exception as e:
        error(f"Grid fill failed: {e}")
        bpy.ops.object.mode_set(mode='OBJECT') # Ensure object mode before returning
        return None
    bpy.ops.object.mode_set(mode='OBJECT') # Ensure object mode after grid fill

    # Restore boundary positions
    bm_restore_boundary = bmesh.new()
    bm_restore_boundary.from_mesh(filled_obj.data)
    new_boundary_verts_bmesh = get_boundary_verts(bm_restore_boundary) # BMVerts
    if len(new_boundary_verts_bmesh) == len(orig_boundary_coords):
        # This matching logic relies on vertex order from get_boundary_verts being consistent
        # and grid fill not catastrophically changing boundary vertex count.
        for bm_v, orig_co in zip(new_boundary_verts_bmesh, orig_boundary_coords):
            bm_v.co = orig_co
        info("Restored original boundary positions after grid fill.")
    else:
        error(f"Boundary vertex count mismatch after grid fill ({len(new_boundary_verts_bmesh)} vs {len(orig_boundary_coords)}); could not reliably restore outline coordinates.")
    bm_restore_boundary.to_mesh(filled_obj.data)
    bm_restore_boundary.free() # Free this BM
    filled_obj.data.update()


    # --- MODIFICATION FOR project_verts_to_surface ---
    # Project boundary verts of the grid-filled mesh onto shell
    bm_select_for_proj = bmesh.new()
    bm_select_for_proj.from_mesh(filled_obj.data)
    
    boundary_bmverts_for_proj = get_boundary_verts(bm_select_for_proj) # Get BMVerts
    boundary_indices_for_proj = [v.index for v in boundary_bmverts_for_proj] # << GET INDICES HERE
    
    bm_select_for_proj.free() # << FREE BMESH AFTER GETTING INDICES

    if boundary_indices_for_proj:
        project_verts_to_surface(filled_obj, boundary_indices_for_proj, shell_obj) # << PASS INDICES
    else:
        info("No boundary vertices found on grid-filled mesh to project. Skipping boundary projection.")
    # --- END OF MODIFICATION ---


    # Flow-based quads and UVs (keep as is, but ensure bm is fresh if needed)
    bm_flow = bmesh.new()
    bm_flow.from_mesh(filled_obj.data)
    bm_flow = create_flow_based_quads(bm_flow) # This function should handle its bmesh
    if not filled_obj.data.uv_layers:
        filled_obj.data.uv_layers.new(name=uv_layer_name)
    uv_layer_bm_flow = bm_flow.loops.layers.uv.verify() # Use the bmesh that was modified
    for face in bm_flow.faces:
        for loop in face.loops:
            co = loop.vert.co # Use vertex coords from the potentially smoothed bmesh
            loop[uv_layer_bm_flow].uv = (co.x, co.y) # Simple XY to UV projection
    bm_flow.to_mesh(filled_obj.data)
    filled_obj.data.update() # update after to_mesh
    bm_flow.free() # Free this BM
    info("UVs assigned and mesh updated from flow_based_quads.")

    # Apply surface conformity operations (keep as is)
    # Ensure filled_obj is active for bpy.ops
    bpy.context.view_layer.objects.active = filled_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.vertices_smooth(factor=0.5) # Consider making factor a parameter or property
    bpy.ops.object.mode_set(mode='OBJECT')
    apply_surface_snap(filled_obj, shell_obj, iterations=3) # This is the local shrinkwrap based snap

    # Final conformity pass (keep as is)
    # ...

    info("Panel generation complete!")
    return filled_obj


# Add register and unregister functions to fix the error when disabling the addon
def register():
    # This module only contains utility functions, no classes to register
    pass

def unregister():
    # This module only contains utility functions, no classes to unregister
    pass
