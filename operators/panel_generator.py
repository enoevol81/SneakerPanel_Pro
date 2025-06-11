"""
Panel generation utility module for SneakerPanel Pro.

This module provides utility functions for generating filled panel meshes from
panel outlines. It handles the creation of quad-based grid topology, boundary
projection onto a target shell, and UV mapping. This module is primarily used
by the panel_generate.py operator but can also be used by other modules.
"""
import bpy
import bmesh
from mathutils import Vector

def info(msg):
    """Print information message to console.
    
    Args:
        msg (str): Message to print
    """
    print(f"[PANEL GENERATOR] {msg}")

def error(msg):
    """Print error message to console.
    
    Args:
        msg (str): Error message to print
    """
    print(f"[PANEL GENERATOR ERROR] {msg}")

def get_boundary_verts(bm):
    """Get ordered boundary vertices in a mesh.
    
    This function finds all boundary edges (edges with only one connected face)
    and walks along them to collect vertices in a connected order.
    
    Args:
        bm (BMesh): BMesh to analyze
        
    Returns:
        list: List of boundary BMVerts in connected order, or empty list if no boundary
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

def project_verts_to_surface(obj, vert_indices, shell_obj):
    """Project specific vertices (by index) onto a target surface.
    
    This function projects the specified vertices of an object onto a target
    surface using Blender's vertex group and shrinkwrap modifier system.
    
    Args:
        obj (bpy.types.Object): Object containing vertices to project
        vert_indices (list): List of vertex indices to project
        shell_obj (bpy.types.Object): Target surface object for projection
    """
    info(f"Projecting {len(vert_indices)} boundary vertices for {obj.name}.")
    if not vert_indices:
        info("No vertex indices provided for projection.")
        return

    try:
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

        # Create a vertex group to store the selection
        vg_name = "TempProjectionGroup"
        if vg_name in obj.vertex_groups:
            obj.vertex_groups.remove(obj.vertex_groups[vg_name])
        vg = obj.vertex_groups.new(name=vg_name)
        
        # Store the selected vertices in the vertex group
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.vertex_group_assign()
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Add a shrinkwrap modifier targeting the shell
        mod = obj.modifiers.new(name="TempShrinkwrap", type='SHRINKWRAP')
        mod.target = shell_obj
        mod.wrap_method = 'NEAREST_SURFACEPOINT'
        mod.vertex_group = vg_name
        mod.offset = 0.0001  # Small offset to prevent z-fighting
        
        # Apply the modifier
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        info(f"Applied shrinkwrap to {valid_indices_count} vertices.")
        
        # Clean up by removing the vertex group
        if vg_name in obj.vertex_groups:
            obj.vertex_groups.remove(obj.vertex_groups[vg_name])
            info(f"Removed temporary vertex group '{vg_name}'.")
    
    except Exception as e:
        error(f"Error in project_verts_to_surface: {str(e)}")
        # Clean up if needed
        if "mod" in locals() and mod.name in obj.modifiers:
            obj.modifiers.remove(mod)
        if "vg" in locals() and vg_name in obj.vertex_groups:
            obj.vertex_groups.remove(obj.vertex_groups[vg_name])

def apply_surface_snap(obj_to_snap, target_shell_obj, iterations=1):
    """Apply surface snapping with multiple iterations using Shrinkwrap.
    
    This function applies a shrinkwrap modifier to the entire object
    multiple times to gradually conform it to the target surface.
    
    Args:
        obj_to_snap (bpy.types.Object): The object to apply the snap to
        target_shell_obj (bpy.types.Object): Target surface object for projection
        iterations (int): Number of iterations to apply
    """
    info(f"Applying iterative Shrinkwrap snap to '{obj_to_snap.name}' targeting '{target_shell_obj.name}'.")
    
    try:
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
        elif bpy.context.view_layer.objects.active != obj_to_snap and obj_to_snap.name in bpy.data.objects: # If active changed and obj_to_snap is not active, make it active
            bpy.context.view_layer.objects.active = obj_to_snap
    
    except Exception as e:
        error(f"Error in apply_surface_snap: {str(e)}")

def create_flow_based_quads(bm):
    """Create flow-based quad topology.
    
    This function recalculates face normals and applies smoothing
    to improve the flow of the quad grid.
    
    Args:
        bm (BMesh): BMesh to modify
        
    Returns:
        BMesh: Modified BMesh
    """
    try:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        for _ in range(3):
            bmesh.ops.smooth_vert(bm, verts=bm.verts, factor=0.5)
    except Exception as e:
        error(f"Flow-based quad op failed: {e}")
    return bm

def generate_panel(panel_obj, shell_obj, filled_obj_name=None, grid_span=4, uv_layer_name="UVMap"):
    """Generate a filled panel from an outline mesh.
    
    This function takes a panel outline mesh and generates a filled panel mesh
    with proper topology and surface conformity to the shoe shell.
    
    Args:
        panel_obj (bpy.types.Object): Panel outline mesh object
        shell_obj (bpy.types.Object): Target shell object for projection
        filled_obj_name (str, optional): Name for the generated panel mesh
        grid_span (int, optional): Grid fill span parameter
        uv_layer_name (str, optional): Name for the UV layer
        
    Returns:
        bpy.types.Object: Generated panel mesh object, or None if failed
    """
    info("Starting panel generation.")

    try:
        if not panel_obj:
            error("Input panel object not provided.")
            return None
            
        if not shell_obj:
            error("Shell object not provided.")
            return None
            
        if panel_obj.type != 'MESH':
            error(f"Input panel object {panel_obj.name} is not a mesh.")
            return None
            
        if shell_obj.type != 'MESH':
            error(f"Shell object {shell_obj.name} is not a mesh.")
            return None
        
        # Ensure we're in object mode
        if bpy.context.object and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        # Duplicate the panel object to work on a copy
        bpy.ops.object.select_all(action='DESELECT')
        panel_obj.select_set(True)
        bpy.context.view_layer.objects.active = panel_obj
        bpy.ops.object.duplicate()
        filled_obj = bpy.context.active_object
        filled_obj.name = filled_obj_name if filled_obj_name else f"{panel_obj.name}_Filled"
        info(f"Duplicated to '{filled_obj.name}'.")

        if filled_obj.type != 'MESH':
            error("Duplicate is not a mesh.")
            return None

        # Store original boundary positions
        bpy.ops.object.mode_set(mode='OBJECT')
        bm_orig_boundary = bmesh.new()
        bm_orig_boundary.from_mesh(filled_obj.data)
        orig_boundary_verts_bmesh = get_boundary_verts(bm_orig_boundary)
        orig_boundary_coords = [v.co.copy() for v in orig_boundary_verts_bmesh]
        bm_orig_boundary.free()
        info(f"Stored {len(orig_boundary_coords)} original boundary vertex positions.")
        
        if len(orig_boundary_coords) < 3:
            error("Invalid boundary after preprocessing: Not enough vertices.")
            return None

        # Grid fill
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        try:
            bpy.ops.mesh.fill_grid(span=grid_span if grid_span > 0 else 1)
            info(f"Grid fill succeeded with span={grid_span}.")
        except Exception as e:
            error(f"Grid fill failed: {e}")
            bpy.ops.object.mode_set(mode='OBJECT')
            return None
        bpy.ops.object.mode_set(mode='OBJECT')

        # Restore boundary positions
        bm_restore_boundary = bmesh.new()
        bm_restore_boundary.from_mesh(filled_obj.data)
        new_boundary_verts_bmesh = get_boundary_verts(bm_restore_boundary)
        if len(new_boundary_verts_bmesh) == len(orig_boundary_coords):
            # This matching logic relies on vertex order from get_boundary_verts being consistent
            # and grid fill not catastrophically changing boundary vertex count
            for bm_v, orig_co in zip(new_boundary_verts_bmesh, orig_boundary_coords):
                bm_v.co = orig_co
            info("Restored original boundary positions after grid fill.")
        else:
            error(f"Boundary vertex count mismatch after grid fill ({len(new_boundary_verts_bmesh)} vs {len(orig_boundary_coords)}); could not reliably restore outline coordinates.")
        bm_restore_boundary.to_mesh(filled_obj.data)
        bm_restore_boundary.free()
        filled_obj.data.update()

        # Project boundary verts of the grid-filled mesh onto shell
        bm_select_for_proj = bmesh.new()
        bm_select_for_proj.from_mesh(filled_obj.data)
        
        boundary_bmverts_for_proj = get_boundary_verts(bm_select_for_proj)
        boundary_indices_for_proj = [v.index for v in boundary_bmverts_for_proj]
        
        bm_select_for_proj.free()

        if boundary_indices_for_proj:
            project_verts_to_surface(filled_obj, boundary_indices_for_proj, shell_obj)
        else:
            info("No boundary vertices found on grid-filled mesh to project. Skipping boundary projection.")

        # Flow-based quads and UVs
        bm_flow = bmesh.new()
        bm_flow.from_mesh(filled_obj.data)
        bm_flow = create_flow_based_quads(bm_flow)
        if not filled_obj.data.uv_layers:
            filled_obj.data.uv_layers.new(name=uv_layer_name)
        uv_layer_bm_flow = bm_flow.loops.layers.uv.verify()
        for face in bm_flow.faces:
            for loop in face.loops:
                co = loop.vert.co
                loop[uv_layer_bm_flow].uv = (co.x, co.y)  # Simple XY to UV projection
        bm_flow.to_mesh(filled_obj.data)
        filled_obj.data.update()
        bm_flow.free()
        info("UVs assigned and mesh updated from flow_based_quads.")

        # Apply surface conformity operations
        bpy.context.view_layer.objects.active = filled_obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.vertices_smooth(factor=0.5)
        bpy.ops.object.mode_set(mode='OBJECT')
        apply_surface_snap(filled_obj, shell_obj, iterations=3)

        info("Panel generation complete!")
        return filled_obj
        
    except Exception as e:
        error(f"Error in generate_panel: {str(e)}")
        return None

# Register and unregister functions for addon integration
def register():
    # This module only contains utility functions, no classes to register
    pass

def unregister():
    # This module only contains utility functions, no classes to unregister
    pass

if __name__ == "__main__":
    # For testing
    register()
