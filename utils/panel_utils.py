import bpy
from mathutils import Vector

def update_stabilizer(self, context):
    brush = bpy.context.tool_settings.gpencil_paint.brush
    if brush:
        brush.use_smooth_stroke = context.scene.spp_use_stabilizer
        brush.smooth_stroke_factor = context.scene.spp_stabilizer_factor
        brush.smooth_stroke_radius = context.scene.spp_stabilizer_radius

def update_stabilizer_ui(self, context):
    strength_ui = context.scene.spp_stabilizer_strength_ui
    mapped_value = 0.5 + (strength_ui / 10) * 0.5  # Maps 1-10 to 0.6-1.0
    context.scene.spp_stabilizer_factor = mapped_value
    update_stabilizer(self, context)

# In SneakerPanel_Pro/utils/panel_utils.py
import bpy # Make sure bpy is imported if not already

def apply_surface_snap():
    """Apply a fake transform to snap vertices to the nearest surface"""
    bpy.ops.transform.translate(
        value=(0, 0, 0),
        orient_type='GLOBAL',
        orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
        orient_matrix_type='GLOBAL',
        constraint_axis=(False, False, False),
        mirror=False,
        use_proportional_edit=False,
        proportional_edit_falloff='SMOOTH',
        proportional_size=1,
        use_proportional_connected=False,
        use_proportional_projected=False,
        snap=True,
        snap_elements={'FACE_NEAREST'},
        snap_target='CLOSEST',
        use_snap_project=False,
        use_snap_self=False,    # <--- CRITICAL CHANGE HERE
        use_snap_edit=True,
        use_snap_nonedit=True,
        use_snap_selectable=False # Allow snapping to non-selectable if shell is not selectable
    )

def reduce_mesh_verts(context, percentage):
    obj = context.active_object
    if obj and obj.type == 'MESH':
        if obj.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.decimate(ratio=(1 - percentage))
        bpy.ops.object.mode_set(mode='OBJECT')
        return True
    return False

def compute_curvature(bm, vert):
    """Compute approximate curvature at a BMVert using connected faces."""
    normal = vert.normal
    curvature = 0.0
    count = 0
    
    # Get connected faces
    connected_faces = [f for f in vert.link_faces]
    
    for face in connected_faces:
        face_normal = face.normal
        # Approximate curvature by normal difference
        curvature += abs(1.0 - normal.dot(face_normal))
        count += 1
    
    return curvature / max(count, 1)

def create_flow_based_quads(bm, target_quad_length=0.1):
    """Create a quad-dominant mesh with good edge flow."""
    # First, create a clean boundary
    boundary_edges = [e for e in bm.edges if len(e.link_faces) < 2]
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=0.001)
    
    # Delete existing faces while keeping boundary
    interior_faces = [f for f in bm.faces]
    bmesh.ops.delete(bm, geom=interior_faces, context='FACES')
    
    # Get boundary verts in order
    boundary_verts = []
    current = boundary_edges[0].verts[0]
    start = current
    used_edges = set()
    
    while True:
        boundary_verts.append(current)
        next_edge = None
        for edge in current.link_edges:
            if edge in used_edges or edge not in boundary_edges:
                continue
            next_vert = edge.other_vert(current)
            next_edge = edge
            break
        if next_edge is None or next_edge.other_vert(current) == start:
            break
        used_edges.add(next_edge)
        current = next_edge.other_vert(current)
    
    # Create initial grid
    num_rows = max(3, int(len(boundary_verts) / 4))
    grid_verts = []
    for i in range(num_rows):
        row = []
        t = i / (num_rows - 1)
        num_verts_in_row = max(3, int(len(boundary_verts) * (1 - t * 0.5)))
        
        for j in range(num_verts_in_row):
            if i == 0:
                # Use boundary verts for first row
                idx = int(j * len(boundary_verts) / num_verts_in_row)
                vert = boundary_verts[idx]
            else:
                # Interpolate between previous row points
                prev_row = grid_verts[-1]
                t2 = j / (num_verts_in_row - 1)
                idx1 = int(t2 * (len(prev_row) - 1))
                idx2 = min(idx1 + 1, len(prev_row) - 1)
                frac = t2 * (len(prev_row) - 1) - idx1
                
                p1 = prev_row[idx1].co
                p2 = prev_row[idx2].co
                pos = p1.lerp(p2, frac)
                
                # Move towards center based on row
                center = sum((v.co for v in boundary_verts), Vector((0,0,0))) / len(boundary_verts)
                pos = pos.lerp(center, t * 0.8)
                
                vert = bm.verts.new(pos)
            row.append(vert)
        grid_verts.append(row)
    
    # Create faces
    for i in range(len(grid_verts) - 1):
        row1 = grid_verts[i]
        row2 = grid_verts[i + 1]
        
        # Create faces between rows
        for j in range(len(row1) - 1):
            v1 = row1[j]
            v2 = row1[j + 1]
            
            # Find closest verts in next row
            idx1 = int(j * (len(row2) - 1) / (len(row1) - 1))
            idx2 = min(idx1 + 1, len(row2) - 1)
            v3 = row2[idx2]
            v4 = row2[idx1]
            
            try:
                bm.faces.new((v1, v2, v3, v4))
            except ValueError:
                continue
    
    # Smooth the result while preserving boundary
    for _ in range(3):
        bmesh.ops.smooth_vert(bm,
            verts=[v for v in bm.verts if v not in boundary_verts],
            factor=0.5,
            use_axis_x=True,
            use_axis_y=True,
            use_axis_z=True
        )
    
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm
