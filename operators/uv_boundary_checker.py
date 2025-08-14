
import bmesh
import bpy
from mathutils import Vector

# Hidden defaults (no UI exposure except Padding (UV))
SMART_FACTOR = 0.20
MARGIN_UV = 0.01
EDGE_CHECK_LIMIT = 1000
TIMEOUT_SEC = 30.0


class MESH_OT_CheckUVBoundary(bpy.types.Operator):
    """Check and optionally fix UV boundary violations in 2D panel mesh."""

    bl_idname = "mesh.check_uv_boundary"
    bl_label = "Check UV Boundary"
    bl_description = "Check/fix UV boundary violations with safe inward padding"
    bl_options = {"REGISTER", "UNDO"}

    # ---------------------------- Poll ----------------------------
    @classmethod
    def poll(cls, context):
        return (
            context.active_object
            and context.active_object.type == "MESH"
            and hasattr(context.scene, "spp_shell_object")
            and context.scene.spp_shell_object
            and context.scene.spp_shell_object.type == "MESH"
        )

    # ------------------------ Boundary Utils ----------------------
    def find_uv_reference_mesh(self, context, shell_obj_name):
        for obj in context.scene.objects:
            if obj.type == "MESH" and "spp_original_3d_mesh_name" in obj:
                if obj["spp_original_3d_mesh_name"] == shell_obj_name:
                    return obj
        return None

    def get_uv_boundary_edges(self, shell_obj, uv_layer_name):
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_shell = shell_obj.evaluated_get(depsgraph)
        eval_mesh = eval_shell.to_mesh()
        bm_shell = bmesh.new()
        bm_shell.from_mesh(eval_mesh)
        bm_shell.verts.ensure_lookup_table()
        bm_shell.edges.ensure_lookup_table()
        bm_shell.faces.ensure_lookup_table()
        uv_layer = (
            bm_shell.loops.layers.uv.get(uv_layer_name)
            or bm_shell.loops.layers.uv.active
        )
        edges = []
        for e in bm_shell.edges:
            if len(e.link_faces) == 1:
                f = e.link_faces[0]
                loops = [lp for lp in f.loops if lp.vert in e.verts]
                if len(loops) == 2:
                    uv1 = Vector(loops[0][uv_layer].uv)
                    uv2 = Vector(loops[1][uv_layer].uv)
                    edges.append((uv1, uv2))
        bm_shell.free()
        eval_shell.to_mesh_clear()
        return edges

    def closest_point_on_segment(self, p, a, b):
        ab = b - a
        d2 = ab.length_squared
        if d2 == 0.0:
            return a
        t = (p - a).dot(ab) / d2
        return a + max(0.0, min(1.0, t)) * ab

    def ray_line_intersect_2d(self, ray_start, ray_dir, line_start, line_end):
        rs = Vector((ray_start.x, ray_start.y))
        rd = Vector((ray_dir.x, ray_dir.y))
        ls = Vector((line_start.x, line_start.y))
        le = Vector((line_end.x, line_end.y))
        ld = le - ls
        denom = rd.x * ld.y - rd.y * ld.x
        if abs(denom) < 1e-10:
            return False
        diff = rs - ls
        t2 = (rd.x * diff.y - rd.y * diff.x) / denom
        t1 = (ld.x * diff.y - ld.y * diff.x) / denom
        return (t1 >= 0) and (0 <= t2 <= 1)

    def is_point_outside_boundary(self, uv, boundary_edges):
        # quick bounds
        if uv.x < 0 or uv.x > 1 or uv.y < 0 or uv.y > 1:
            return True
        # points on boundary are inside
        eps = 1e-6
        for s, e in boundary_edges:
            if (self.closest_point_on_segment(uv, s, e) - uv).length <= eps:
                return False
        # single horizontal ray
        hits = 0
        ray_dir = Vector((1, 0))
        for s, e in boundary_edges:
            if self.ray_line_intersect_2d(uv, ray_dir, s, e):
                hits += 1
        return (hits % 2) == 0

    def find_closest_on_boundary(self, uv, boundary_edges):
        q, dmin = None, float("inf")
        for s, e in boundary_edges:
            c = self.closest_point_on_segment(uv, s, e)
            d = (uv - c).length
            if d < dmin:
                q, dmin = c, d
        return q

    def inward_from_boundary_point(self, q, boundary_edges):
        for s, e in boundary_edges:
            if (self.closest_point_on_segment(q, s, e) - q).length < 1e-4:
                t = (e - s).normalized() if (e - s).length > 0 else Vector((1, 0))
                n1 = Vector((-t.y, t.x))
                n2 = Vector((t.y, -t.x))
                return (
                    n1
                    if not self.is_point_outside_boundary(q + n1 * 1e-3, boundary_edges)
                    else n2
                )
        # fallback: toward centroid
        cx = sum(a.x + b.x for a, b in boundary_edges) / (2 * len(boundary_edges))
        cy = sum(a.y + b.y for a, b in boundary_edges) / (2 * len(boundary_edges))
        v = Vector((cx, cy)) - q
        return v.normalized() if v.length > 0 else Vector((0, -1))

    # --------------------------- Execute -------------------------
    def execute(self, context):
        import time

        start = time.time()
        bpy.ops.ed.undo_push(message="Check UV Boundary")

        panel_obj = context.active_object
        shell_obj = context.scene.spp_shell_object
        S = context.scene

        # Two actions only: CHECK or FIX
        action = S.spp_uv_boundary_action

        # Single exposed slider: user_min_pad_uv
        user_min_pad_uv = float(getattr(S, "spp_uv_padding_uv", 0.005))
        eps_inside = max(1e-4, 0.25 * MARGIN_UV)

        uv_mesh_obj = self.find_uv_reference_mesh(context, shell_obj.name)
        if not uv_mesh_obj:
            self.report(
                {"ERROR"}, f"UV reference mesh for '{shell_obj.name}' not found."
            )
            return {"CANCELLED"}

        scale_factor = uv_mesh_obj.get("spp_applied_scale_factor", None)
        source_uv_map = uv_mesh_obj.get("spp_source_uv_map_name", None)
        if scale_factor is None or source_uv_map is None:
            self.report(
                {"ERROR"}, "UV reference mesh missing required custom properties."
            )
            return {"CANCELLED"}

        try:
            original_mode = bpy.context.mode
            if original_mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")

            boundary_edges = self.get_uv_boundary_edges(shell_obj, source_uv_map)
            if not boundary_edges:
                self.report({"WARNING"}, "No UV boundary edges found.")
                return {"CANCELLED"}

            bm = bmesh.new()
            bm.from_mesh(panel_obj.data)
            bm.verts.ensure_lookup_table()
            bm.edges.ensure_lookup_table()

            # ---- Collect violations (outside OR within safety margin) ----
            violation_vert_ids = []
            for i, v in enumerate(bm.verts):
                if i % 200 == 0 and (time.time() - start) > TIMEOUT_SEC:
                    bm.free()
                    S.spp_uv_boundary_status = "ERROR"
                    self.report({"ERROR"}, "Operation timed out during vertex scan.")
                    return {"CANCELLED"}

                p_world = panel_obj.matrix_world @ v.co
                p_uv_local = uv_mesh_obj.matrix_world.inverted() @ p_world
                uv = Vector((p_uv_local.x / scale_factor, p_uv_local.y / scale_factor))

                if self.is_point_outside_boundary(uv, boundary_edges):
                    violation_vert_ids.append(i)
                else:
                    q = self.find_closest_on_boundary(uv, boundary_edges)
                    if q and (uv - q).length < MARGIN_UV:
                        violation_vert_ids.append(i)

            # optional light edge pass (cap for speed)
            edge_count = 0
            for e in bm.edges:
                edge_count += 1
                if edge_count % 50 == 0:
                    if (
                        time.time() - start
                    ) > TIMEOUT_SEC or edge_count > EDGE_CHECK_LIMIT:
                        break
                v1, v2 = e.verts
                p1w = panel_obj.matrix_world @ v1.co
                p2w = panel_obj.matrix_world @ v2.co
                p1u = uv_mesh_obj.matrix_world.inverted() @ p1w
                p2u = uv_mesh_obj.matrix_world.inverted() @ p2w
                uv1 = Vector((p1u.x / scale_factor, p1u.y / scale_factor))
                uv2 = Vector((p2u.x / scale_factor, p2u.y / scale_factor))
                mid = (uv1 + uv2) * 0.5
                if (
                    self.is_point_outside_boundary(uv1, boundary_edges)
                    or self.is_point_outside_boundary(uv2, boundary_edges)
                    or self.is_point_outside_boundary(mid, boundary_edges)
                ):
                    violation_vert_ids.extend([v1.index, v2.index])

            violation_vert_ids = sorted(set(violation_vert_ids))

            # ---- Actions ----
            if action == "CHECK":
                self._select_in_bmesh(bm, violation_vert_ids)
                bm.to_mesh(panel_obj.data)
                panel_obj.data.update()
                self._write_violation_group(panel_obj, violation_vert_ids)

                if original_mode == "EDIT_MESH" or violation_vert_ids:
                    bpy.ops.object.mode_set(mode="EDIT")

                if violation_vert_ids:
                    S.spp_uv_boundary_status = "VIOLATIONS"
                    self.report(
                        {"WARNING"},
                        f"Found {len(violation_vert_ids)} violating or near-boundary vertices",
                    )
                else:
                    S.spp_uv_boundary_status = "PASS"
                    self.report({"INFO"}, "No UV boundary violations found")

            elif action == "FIX":
                fixed = self._fix_with_padding(
                    bm,
                    panel_obj,
                    uv_mesh_obj,
                    scale_factor,
                    boundary_edges,
                    set(violation_vert_ids),
                    user_min_pad_uv,
                    eps_inside,
                )
                bm.to_mesh(panel_obj.data)
                panel_obj.data.update()

                # quick recheck subset
                remaining = 0
                if violation_vert_ids:
                    bm2 = bmesh.new()
                    bm2.from_mesh(panel_obj.data)
                    bm2.verts.ensure_lookup_table()
                    for vi in violation_vert_ids[: min(1000, len(violation_vert_ids))]:
                        v = bm2.verts[vi]
                        p_world = panel_obj.matrix_world @ v.co
                        p_uv = uv_mesh_obj.matrix_world.inverted() @ p_world
                        uv = Vector((p_uv.x / scale_factor, p_uv.y / scale_factor))
                        if self.is_point_outside_boundary(uv, boundary_edges):
                            remaining += 1
                    bm2.free()

                if fixed > 0 and remaining == 0:
                    S.spp_uv_boundary_status = "PASS"
                    self._clear_violation_group(panel_obj)
                    self.report({"INFO"}, f"Fixed {fixed} vertices. All clear!")
                elif fixed > 0:
                    S.spp_uv_boundary_status = "VIOLATIONS"
                    self.report(
                        {"INFO"}, f"Fixed {fixed} vertices. Some issues may remain."
                    )
                else:
                    S.spp_uv_boundary_status = "PASS"
                    self._clear_violation_group(panel_obj)
                    self.report({"INFO"}, "No violations found to fix")

            bm.free()

        except Exception as e:
            S.spp_uv_boundary_status = "ERROR"
            self.report({"ERROR"}, f"UV boundary check failed: {e}")
            try:
                if "bm" in locals():
                    bm.free()
            except:
                pass
            return {"CANCELLED"}

        return {"FINISHED"}

    # -------------------- Selection & Groups ---------------------
    def _select_in_bmesh(self, bm, vert_ids):
        for v in bm.verts:
            v.select = False
        for e in bm.edges:
            e.select = False
        for f in bm.faces:
            f.select = False
        for vi in vert_ids:
            if vi < len(bm.verts):
                bm.verts[vi].select = True

    def _write_violation_group(self, obj, vert_ids):
        # Use a single reliable group — vertex indices only
        for vg in list(obj.vertex_groups):
            if vg.name == "UV_Violations":
                obj.vertex_groups.remove(vg)
        if not vert_ids:
            return
        vg = obj.vertex_groups.new(name="UV_Violations")
        step = 256
        for i in range(0, len(vert_ids), step):
            vg.add(vert_ids[i : i + step], 1.0, "REPLACE")

    def _clear_violation_group(self, obj):
        for vg in list(obj.vertex_groups):
            if vg.name == "UV_Violations":
                obj.vertex_groups.remove(vg)

    # ------------------------ FIX with padding --------------------
    def _fix_with_padding(
        self,
        bm,
        panel_obj,
        uv_mesh_obj,
        scale_factor,
        boundary_edges,
        violation_set,
        user_min_pad_uv,
        eps_inside,
    ):
        M_panel = panel_obj.matrix_world
        Minv_panel = panel_obj.matrix_world.inverted()
        M_uv = uv_mesh_obj.matrix_world

        # UV cache
        uv_cache = {}
        for v in bm.verts:
            pw = M_panel @ v.co
            puv = uv_mesh_obj.matrix_world.inverted() @ pw
            uv_cache[v.index] = Vector((puv.x / scale_factor, puv.y / scale_factor))

        def local_spacing_uv(v):
            uv = uv_cache[v.index]
            dmin = None
            for e in v.link_edges:
                w = e.other_vert(v)
                d = (uv_cache[w.index] - uv).length
                if d > 0:
                    dmin = d if dmin is None else min(dmin, d)
            return dmin if dmin is not None else 0.002

        fixed = 0
        for v in bm.verts:
            if v.index not in violation_set:
                continue
            uv = uv_cache[v.index]
            q = self.find_closest_on_boundary(uv, boundary_edges)
            if not q:
                continue
            inward = self.inward_from_boundary_point(q, boundary_edges)

            min_pad = max(user_min_pad_uv, 1e-4)  # user slider wins as the minimum
            smart = SMART_FACTOR * local_spacing_uv(v)
            pad_uv = max(min_pad, smart) + eps_inside

            new_uv = q + inward * pad_uv
            tries = 0
            # if concave/corner still outside, back off
            while self.is_point_outside_boundary(new_uv, boundary_edges) and tries < 5:
                pad_uv *= 0.5
                new_uv = q + inward * pad_uv
                tries += 1

            p_local = Vector((new_uv.x * scale_factor, new_uv.y * scale_factor, 0.0))
            p_world = M_uv @ p_local
            v.co = Minv_panel @ p_world
            fixed += 1

        bm.normal_update()
        return fixed


class MESH_OT_ReselectUVViolations(bpy.types.Operator):

    bl_idname = "mesh.reselect_uv_violations"
    bl_label = "Re-select UV Violations"
    bl_description = "Re-select vertices marked as UV boundary violations"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not (obj and obj.type == "MESH"):
            return False
        return any(vg.name == "UV_Violations" for vg in obj.vertex_groups)

    def execute(self, context):
        obj = context.active_object
        if bpy.context.mode != "EDIT_MESH":
            bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="DESELECT")
        for vg in obj.vertex_groups:
            if vg.name == "UV_Violations":
                obj.vertex_groups.active = vg
                bpy.ops.object.vertex_group_select()
                break
        self.report({"INFO"}, "Re-selected violation vertices")
        return {"FINISHED"}


classes = [MESH_OT_CheckUVBoundary, MESH_OT_ReselectUVViolations]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
