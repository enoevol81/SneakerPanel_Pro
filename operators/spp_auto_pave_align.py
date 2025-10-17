bl_info = {
    "name": "SPP Auto-Pave Grid Align",
    "author": "Sneaker Panel Pro",
    "version": (3, 0, 0),
    "blender": (4, 4, 0),
    "location": "Search > SPP: Auto-Pave Grid Align",
    "description": "Curvature-aware directional relax + normal snap with pre-equalization, boundary slide, and adaptive stop",
    "category": "Mesh",
}

import bpy, bmesh, math, random
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from bpy.types import Operator
from bpy.props import StringProperty

# -----------------------------------------------------------------------------
# BVH + nearest sampling (world space), based on your current build
# -----------------------------------------------------------------------------

def build_bvh_world(obj, depsgraph):
    eval_obj = obj.evaluated_get(depsgraph)
    eval_mesh = eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)

    mw = eval_obj.matrix_world
    verts_world = [mw @ v.co for v in eval_mesh.vertices]
    polys = eval_mesh.polygons

    # world-space polygon normals (stable / low-noise)
    poly_normals_world = [(mw.to_3x3() @ p.normal).normalized() for p in polys]

    # prefer FromPolygons (fast + preserves poly mapping); fallback to triangles
    bvh = BVHTree.FromPolygons([v[:] for v in verts_world], [p.vertices[:] for p in polys], all_triangles=False)
    if bvh is None:
        eval_mesh.calc_loop_triangles()
        tri_pts = []
        for lt in eval_mesh.loop_triangles:
            tri_pts.append((verts_world[lt.vertices[0]], verts_world[lt.vertices[1]], verts_world[lt.vertices[2]]))
        bvh = BVHTree.FromTriangles(tri_pts)

    eval_obj.to_mesh_clear()
    return bvh, poly_normals_world


def nearest_on_shell(bvh, poly_normals_world, pt_world):
    hit = bvh.find_nearest(pt_world)
    if hit is None:
        return None, None
    loc, normal, poly_index, _ = hit
    if poly_index is not None and 0 <= poly_index < len(poly_normals_world):
        n = poly_normals_world[poly_index].copy()
    else:
        n = (normal.normalized() if normal.length > 0 else Vector((0, 0, 1)))
    return loc, n.normalized()

# -----------------------------------------------------------------------------
# Mesh utilities (selection, boundary detection) – same spirit as your current
# -----------------------------------------------------------------------------

def get_bmesh_and_selection(me):
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    sel_mask = [v.select for v in bm.verts]
    if not any(sel_mask):
        sel_mask = [True] * len(bm.verts)
    return bm, sel_mask


def detect_boundary_mask(bm):
    boundary = []
    for v in bm.verts:
        is_boundary = any(len(e.link_faces) == 1 for e in v.link_edges)
        boundary.append(is_boundary)
    return boundary

# -----------------------------------------------------------------------------
# Pre-equalization: damp extreme aspect/stretch before any smoothing
# -----------------------------------------------------------------------------

def vertex_edge_aspect(v):
    if len(v.link_edges) < 2:
        return 1.0
    lengths = [e.calc_length() for e in v.link_edges]
    mn = min(lengths) + 1e-12
    return max(lengths) / mn

def pre_equalize_stretch(bm, aspect_limit=5.0, damp=0.12):
    """Reduce local edge-length extremes without changing boundary lengths drastically."""
    # Store all vertex positions first to avoid cascading changes
    original_positions = {v: v.co.copy() for v in bm.verts}
    vertex_deltas = {v: Vector((0, 0, 0)) for v in bm.verts}
    
    for v in bm.verts:
        if vertex_edge_aspect(v) > aspect_limit:
            # Calculate deltas for endpoints along each incident edge
            for e in v.link_edges:
                a, b = e.verts[0], e.verts[1]
                d = (original_positions[b] - original_positions[a])
                vertex_deltas[a] += d * (damp * 0.5)
                vertex_deltas[b] -= d * (damp * 0.5)
    
    # Apply all deltas at once
    for v in bm.verts:
        v.co += vertex_deltas[v]

# -----------------------------------------------------------------------------
# Curvature frames (principal directions) in tangent plane
# -----------------------------------------------------------------------------

def orthonormal_basis_from_normal(n):
    # create a stable tangent frame (t1, t2) from a normal n
    t1 = n.orthogonal()
    if t1.length_squared == 0.0:
        t1 = Vector((1, 0, 0))
    t1.normalize()
    t2 = n.cross(t1).normalized()
    return t1, t2

def eigenvec2_symm2(a, b, c):
    """
    Eigenvectors for 2x2 symmetric [[a, b],[b, c]].
    Returns unit vectors v1 (max eigen), v2 (min eigen) in R^2.
    """
    # trace and determinant
    tr = a + c
    det = a * c - b * b
    disc = max(tr * tr - 4.0 * det, 0.0)
    s = math.sqrt(disc)

    # eigenvalues
    l1 = 0.5 * (tr + s)  # max
    l2 = 0.5 * (tr - s)  # min

    # eigenvector for l1: (b, l1 - a) unless degenerate
    if abs(b) > 1e-12 or abs(l1 - a) > 1e-12:
        v1 = Vector((b, l1 - a))
    else:
        v1 = Vector((1.0, 0.0))
    if v1.length_squared == 0.0:
        v1 = Vector((1.0, 0.0))
    v1.normalize()

    # orthogonal
    v2 = Vector((-v1.y, v1.x))
    return v1, v2

def estimate_curvature_frame_at_point(bvh, base_loc, base_n, sample_radius=0.005, samples=16):
    """
    Sample neighborhood on shell, project offsets into tangent, build covariance,
    decompose to principal axes; map 2D eigenvectors back to 3D (t1, t2 basis).
    """
    if base_loc is None or base_n is None:
        # fallback: any orthonormal frame
        t1, t2 = orthonormal_basis_from_normal(Vector((0, 0, 1)))
        return t1, t2

    t1, t2 = orthonormal_basis_from_normal(base_n)

    # Collect tangent offsets
    uvs = []
    for _ in range(samples):
        # random direction in 3D, small jitter around base_loc
        rnd = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))).normalized()
        hit = bvh.find_nearest(base_loc + rnd * sample_radius)
        if not hit:
            continue
        loc, _, _, _ = hit
        d = loc - base_loc
        # project into tangent plane
        d -= base_n * d.dot(base_n)
        if d.length_squared == 0.0:
            continue
        # express in (t1, t2) 2D coords
        u = d.dot(t1)
        v = d.dot(t2)
        uvs.append((u, v))

    if len(uvs) < 3:
        # too sparse; return tangent basis as-is
        return t1, t2

    # build 2x2 covariance in tangent plane
    a = b = c = 0.0
    for (u, v) in uvs:
        a += u * u
        b += u * v
        c += v * v

    v1_2d, v2_2d = eigenvec2_symm2(a, b, c)  # v1=principal (max var), v2=secondary

    # map back to 3D: [u, v] -> u*t1 + v*t2
    dir_u = (t1 * v1_2d.x + t2 * v1_2d.y).normalized()
    dir_v = (t1 * v2_2d.x + t2 * v2_2d.y).normalized()
    return dir_u, dir_v

# -----------------------------------------------------------------------------
# Operator
# -----------------------------------------------------------------------------

class SPP_OT_AutoPaveGridAlign(Operator):
    """Curvature-aware relax + normal snap using shell BVH; pre-equalize stretch, boundary slide, adaptive stop"""
    bl_idname = "spp.auto_pave_grid_align"
    bl_label = "SPP: Auto-Pave Grid Align"
    bl_options = {"REGISTER", "UNDO"}

    # Keep only 'shell' to avoid viewport redo conflicts; all tuning via scene properties
    shell: StringProperty(
        name="Shell Object",
        description="Reference shoe shell object name",
        default="3DShoeShell"
    )

    def execute(self, context):
        # Store original mode for restoration
        original_mode = context.mode
        
        S = context.scene

        # Scene props (single source of truth per Windsurf fix)
        iterations       = getattr(S, "spp_auto_pave_iterations", 20)     # default: per your doc
        relax_strength   = getattr(S, "spp_auto_pave_relax_strength", 0.4)
        normal_snap      = getattr(S, "spp_auto_pave_normal_snap", 0.7)
        lock_boundary    = getattr(S, "spp_auto_pave_lock_boundary", False)  # Allow boundary to smooth with boundary_slide
        final_offset     = getattr(S, "spp_auto_pave_final_offset", 0.0005)
        move_threshold   = getattr(S, "spp_auto_pave_move_threshold", 1e-5)    # adaptive stop
        use_equalize     = getattr(S, "spp_auto_pave_equalize", True)  # Testing if this causes jagged edges
        use_boundary_slide = getattr(S, "spp_auto_pave_boundary_slide", True)  # OK - doesn't cause jagged edges
        use_curvature    = getattr(S, "spp_auto_pave_curvature", False)  # Disabled - testing for jagged edges
        curv_samples     = getattr(S, "spp_auto_pave_curv_samples", 14)
        curv_radius      = getattr(S, "spp_auto_pave_curv_radius", 0.005)
        use_retopo       = getattr(S, "spp_auto_pave_use_retopo", False)
        target_faces     = getattr(S, "spp_auto_pave_target_faces", 1500)

        # Always final-project for conformity
        final_project = True

        # Resolve shell object (same logic as your current implementation)
        shell_name = (self.shell or "").strip()
        shell_obj = S.objects.get(shell_name) if shell_name else None
        if (shell_obj is None) and hasattr(S, "spp_shell_object") and getattr(S, "spp_shell_object", None):
            if S.spp_shell_object and S.spp_shell_object.type == 'MESH':
                shell_obj = S.spp_shell_object
                try:
                    self.shell = shell_obj.name
                except Exception:
                    pass

        if shell_obj is None or shell_obj.type != 'MESH':
            self.report({'ERROR'}, "Shell object not set. Assign the shell in Panel Configuration.")
            return {'CANCELLED'}

        # Collect targets - need to switch to object mode first
        if context.mode == 'EDIT_MESH':
            obj = context.edit_object
            if not obj or obj.type != 'MESH':
                self.report({'ERROR'}, "Active object is not a mesh")
                return {'CANCELLED'}
            targets = [obj]
        else:
            if context.selected_objects:
                targets = [o for o in context.selected_objects if o.type == 'MESH']
            elif context.active_object and context.active_object.type == 'MESH':
                targets = [context.active_object]
            else:
                self.report({'ERROR'}, "No mesh object selected")
                return {'CANCELLED'}
        
        # Switch to object mode for mesh operations
        if original_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        try:
            depsgraph = context.evaluated_depsgraph_get()
            bvh, poly_normals_world = build_bvh_world(shell_obj, depsgraph)

            # -----------------------------------------------------------------------------------------
            # Process each target mesh
            # -----------------------------------------------------------------------------------------
            for obj in targets:
                me = obj.data
                mw = obj.matrix_world
                mw_inv = mw.inverted_safe()

                # BMesh + selection
                bm, sel_mask = get_bmesh_and_selection(me)
                boundary_mask = detect_boundary_mask(bm)

                # Build adjacency
                bm.verts.ensure_lookup_table()
                idx_map = {v.index: i for i, v in enumerate(bm.verts)}
                neighbors = [[] for _ in bm.verts]
                for e in bm.edges:
                    a = idx_map[e.verts[0].index]
                    b = idx_map[e.verts[1].index]
                    neighbors[a].append(b)
                    neighbors[b].append(a)

                # Optional pre-equalization pass (stabilize extreme stretch)
                if use_equalize:
                    pre_equalize_stretch(bm, aspect_limit=5.0, damp=0.12)

                # Pull world-space positions
                v_world = [mw @ v.co for v in bm.verts]

                # Helper: refresh nearest hits (location + normal) for all verts
                def refresh_targets():
                    t_locs, t_normals = [], []
                    for p in v_world:
                        loc, n = nearest_on_shell(bvh, poly_normals_world, p)
                        t_locs.append(loc); t_normals.append(n)
                    return t_locs, t_normals

                tgt_locs, tgt_normals = refresh_targets()

                # Precompute curvature frames (principal directions in tangent) if enabled
                curv_U = [None] * len(v_world)
                curv_V = [None] * len(v_world)
                if use_curvature:
                    for i, (p, n) in enumerate(zip(v_world, tgt_normals)):
                        if p is None or n is None:
                            t1, t2 = orthonormal_basis_from_normal(Vector((0, 0, 1)))
                            curv_U[i], curv_V[i] = t1, t2
                            continue
                        u, v = estimate_curvature_frame_at_point(
                            bvh, p, n, sample_radius=curv_radius, samples=curv_samples
                        )
                        curv_U[i], curv_V[i] = u, v

                # Pre-smooth boundary vertices to reduce stepping
                if use_boundary_slide:
                    for _ in range(5):  # 5 boundary-only smoothing passes
                        boundary_new_pos = []
                        for i, p in enumerate(v_world):
                            if boundary_mask[i]:
                                # Average with boundary neighbors only
                                avg = Vector((0, 0, 0))
                                count = 0
                                for j in neighbors[i]:
                                    if boundary_mask[j]:
                                        avg += v_world[j]
                                        count += 1
                                if count > 0:
                                    avg /= count
                                    # Smooth along boundary with moderate strength
                                    boundary_new_pos.append(p + (avg - p) * 0.5)
                                else:
                                    boundary_new_pos.append(p)
                            else:
                                boundary_new_pos.append(p)
                        v_world = boundary_new_pos

                # Adaptive smoothing loop
                for it in range(iterations):
                    active_mask = sel_mask
                    total_move = 0.0
                    new_positions = []

                    # Per-vertex relax strength depending on boundary handling
                    def local_relax_factor(i):
                        if lock_boundary and boundary_mask[i]:
                            return 0.0
                        if use_boundary_slide and boundary_mask[i]:
                            return relax_strength  # Full strength for smooth boundaries
                        return relax_strength

                    for i, p in enumerate(v_world):
                        if not active_mask[i]:
                            new_positions.append(p)
                            continue

                        # Average neighbor position (Laplacian core)
                        # For boundary vertices with boundary_slide, only average with boundary neighbors
                        if neighbors[i]:
                            avg = Vector((0, 0, 0))
                            neighbor_count = 0
                            
                            if use_boundary_slide and boundary_mask[i]:
                                # Boundary vertex: only average with other boundary vertices
                                for j in neighbors[i]:
                                    if boundary_mask[j]:
                                        avg += v_world[j]
                                        neighbor_count += 1
                            else:
                                # Interior vertex: average with all neighbors
                                for j in neighbors[i]:
                                    avg += v_world[j]
                                neighbor_count = len(neighbors[i])
                            
                            if neighbor_count == 0:
                                new_positions.append(p)
                                continue
                            avg /= neighbor_count
                        else:
                            new_positions.append(p)
                            continue

                        n = tgt_normals[i] if tgt_normals[i] is not None else Vector((0, 0, 1))
                        move = (avg - p)
                        # Project move to tangent plane
                        move_t = move - n * move.dot(n)

                        # Curvature-aware weighting: bias flow along principal dir_U
                        if use_curvature and curv_U[i] is not None:
                            # compute average neighbor edge direction, tangent-projected
                            if neighbors[i]:
                                edge_dirs = []
                                for j in neighbors[i]:
                                    e = v_world[j] - p
                                    e -= n * e.dot(n)
                                    if e.length_squared > 0.0:
                                        edge_dirs.append(e.normalized())
                                if edge_dirs:
                                    # how aligned are edges with principal U
                                    flow_w = sum(abs(ed.dot(curv_U[i])) for ed in edge_dirs) / len(edge_dirs)
                                    # weight 0.5..1.0 based on alignment
                                    move_t *= (0.5 + 0.5 * flow_w)

                        # Boundary slide: restrict to tangent direction along boundary rim
                        if use_boundary_slide and boundary_mask[i]:
                            # Approx boundary tangent: average of boundary edge directions
                            # Only consider edges to OTHER boundary vertices
                            bt = Vector((0, 0, 0))
                            cnt = 0
                            for j in neighbors[i]:
                                if boundary_mask[j]:  # Only boundary-to-boundary edges
                                    e_dir = v_world[j] - p
                                    e_dir -= n * e_dir.dot(n)
                                    if e_dir.length_squared > 0.0:
                                        bt += e_dir.normalized()
                                        cnt += 1
                            if cnt > 0:
                                bt.normalize()
                                # project move onto boundary tangent
                                move_t = bt * move_t.dot(bt)

                        # Apply local relax
                        w_relax = local_relax_factor(i)
                        new_p = p + w_relax * move_t

                        # Normal snap (keep attached to shell)
                        loc = tgt_locs[i]
                        if loc is not None:
                            delta_n = (loc - new_p).dot(n)
                            new_p = new_p + n * (normal_snap * delta_n)

                        total_move += (new_p - p).length
                        new_positions.append(new_p)

                    # Commit iteration
                    v_world = new_positions

                    # Update nearest targets every other iter (perf vs accuracy)
                    if it % 2 == 1 or it == iterations - 1:
                        tgt_locs, tgt_normals = refresh_targets()

                    # Adaptive stop
                    avg_move = total_move / max(len(v_world), 1)
                    if avg_move < move_threshold:
                        break

                # Final projection + micro offset to avoid z-fighting
                if final_project:
                    out_world = []
                    for p in v_world:
                        loc, n = nearest_on_shell(bvh, poly_normals_world, p)
                        if loc is None or n is None:
                            out_world.append(p)
                        else:
                            out_world.append(loc + n * final_offset)
                    v_world = out_world

                # Write back to mesh (local space)
                for i, v in enumerate(bm.verts):
                    v.co = mw_inv @ v_world[i]

                bm.normal_update()
                bm.to_mesh(me)
                bm.free()
                me.update()

                # -----------------------------------------------------------
                # Optional Quadriflow Retopo (clean topology after projection)
                # -----------------------------------------------------------
                if use_retopo and target_faces > 0:
                    self.report({'INFO'}, f"Running Quadriflow retopo (~{target_faces} faces)...")
                    try:
                        # Ensure object is selected and active (we're already in object mode)
                        obj.select_set(True)
                        context.view_layer.objects.active = obj
                        
                        # Run Quadriflow remesh with correct parameter names
                        result = bpy.ops.object.quadriflow_remesh(
                            mode='FACES',
                            target_faces=target_faces,
                            use_mesh_symmetry=False,
                            use_preserve_sharp=True,
                            use_preserve_boundary=True,
                            smooth_normals=True,
                            seed=0
                        )
                        
                        if result == {'FINISHED'}:
                            self.report({'INFO'}, f"Quadriflow retopo complete ({target_faces} target faces).")
                        else:
                            self.report({'WARNING'}, f"Quadriflow returned: {result}")
                            
                    except AttributeError as e:
                        self.report({'WARNING'}, "Quadriflow not available in this Blender build")
                    except Exception as e:
                        self.report({'WARNING'}, f"Quadriflow failed: {str(e)}")

            self.report({'INFO'}, "Auto-Pave complete.")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Auto-Pave failed: {str(e)}")
            return {'CANCELLED'}
            
        finally:
            # Restore original mode
            try:
                if original_mode != 'OBJECT':
                    bpy.ops.object.mode_set(mode=original_mode.split('_')[-1])
            except:
                pass  # If mode restoration fails, stay in current mode

# simple menus (unchanged)
def menu_func(self, context):
    self.layout.operator(SPP_OT_AutoPaveGridAlign.bl_idname, icon='MOD_SMOOTH')

def register():
    bpy.utils.register_class(SPP_OT_AutoPaveGridAlign)
    bpy.types.VIEW3D_MT_object.append(menu_func)
    bpy.types.VIEW3D_MT_edit_mesh.append(menu_func)

def unregister():
    bpy.types.VIEW3D_MT_edit_mesh.remove(menu_func)
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    bpy.utils.unregister_class(SPP_OT_AutoPaveGridAlign)

if __name__ == "__main__":
    register()
