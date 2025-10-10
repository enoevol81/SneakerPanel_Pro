import bmesh
import bpy
from bpy.props import BoolProperty, IntProperty
from bpy.types import Operator
from mathutils import Vector
from mathutils.bvhtree import BVHTree


class MESH_OT_SimpleGridFill(Operator):
    bl_idname = "mesh.simple_grid_fill"
    bl_label = "Simple Grid Fill"
    bl_description = "Fill selected geometry with grid pattern"
    bl_options = {"REGISTER", "UNDO"}

    span: IntProperty(
        name="Span",
        description="Number of grid cells in one direction",
        default=1,
        min=1,
        max=100,
    )

    close_first: BoolProperty(
        name="Close Open Edges",
        description="Connect open endpoints before grid fill",
        default=True,
    )

    smooth_after: BoolProperty(
        name="Smooth After Fill",
        description="Apply smoothing after grid fill",
        default=True,
    )

    smooth_iterations: IntProperty(
        name="Smooth Iterations",
        description="Number of smoothing iterations",
        default=2,
        min=1,
        max=10,
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == "MESH"

    def find_open_endpoints(self, bm):
        endpoints = []
        for vert in bm.verts:
            if len(vert.link_edges) == 1:
                endpoints.append(vert)
        return endpoints

    def close_open_edges(self, bm):
        endpoints = self.find_open_endpoints(bm)

        if len(endpoints) == 2:
            try:
                bm.edges.new(endpoints)
                bm.edges.ensure_lookup_table()
                self.report({"INFO"}, "Connected 2 endpoints")
                return True
            except Exception:
                self.report({"WARNING"}, "Could not connect endpoints")
                return False
        elif len(endpoints) > 2:
            try:
                for i in range(len(endpoints) - 1):
                    bm.edges.new([endpoints[i], endpoints[i + 1]])
                bm.edges.new([endpoints[-1], endpoints[0]])
                bm.edges.ensure_lookup_table()
                self.report({"INFO"}, f"Connected {len(endpoints)} endpoints in a loop")
                return True
            except Exception:
                self.report({"WARNING"}, "Could not connect all endpoints")
                return False

        return False

    def execute(self, context):
        # Context-agnostic execution - automatically switch to required mode
        obj = context.active_object
        if not obj or obj.type != "MESH":
            self.report({"ERROR"}, "No active mesh object")
            return {"CANCELLED"}

        # Store original mode for restoration
        original_mode = obj.mode

        # Switch to Edit Mode if not already there
        if context.mode != "EDIT_MESH":
            try:
                bpy.ops.object.mode_set(mode="EDIT")
            except Exception as e:
                self.report({"ERROR"}, f"Could not switch to Edit Mode: {str(e)}")
                return {"CANCELLED"}

        try:
            bm = bmesh.from_edit_mesh(obj.data)

            self.report(
                {"INFO"},
                f"Starting: {len(bm.verts)} verts, {len(bm.edges)} edges, {len(bm.faces)} faces",
            )

            if self.close_first:
                endpoints = self.find_open_endpoints(bm)
                if endpoints:
                    self.report({"INFO"}, f"Found {len(endpoints)} open endpoints")
                    self.close_open_edges(bm)
                    bmesh.update_edit_mesh(obj.data)
                else:
                    self.report({"INFO"}, "No open endpoints found")

            select_mode = context.tool_settings.mesh_select_mode[:]

            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.select_mode(type="EDGE")

            try:
                bpy.ops.mesh.fill_grid(span=self.span)
                self.report({"INFO"}, f"Grid fill successful with span={self.span}")
                success = True
            except Exception as e:
                self.report({"ERROR"}, f"Grid fill failed: {str(e)}")
                # Try alternative: triangle fill then convert to quads
                try:
                    self.report({"INFO"}, "Trying triangle fill as fallback...")
                    bpy.ops.mesh.fill()
                    bpy.ops.mesh.tris_convert_to_quads()
                    self.report({"INFO"}, "Triangle fill + quad conversion successful")
                    success = True
                except Exception as e2:
                    self.report({"ERROR"}, f"Triangle fill also failed: {str(e2)}")
                    success = False

            if success and self.smooth_after:
                try:
                    obj = context.active_object
                    bm = bmesh.from_edit_mesh(obj.data)
                    bm.faces.ensure_lookup_table()
                    bm.edges.ensure_lookup_table()
                    bm.verts.ensure_lookup_table()

                    boundary_verts = set()
                    for edge in bm.edges:
                        if edge.is_boundary:
                            boundary_verts.update(edge.verts)

                    interior_verts = [v for v in bm.verts if v not in boundary_verts]

                    if interior_verts:
                        self.report(
                            {"INFO"},
                            f"Smoothing {len(interior_verts)} interior vertices, preserving {len(boundary_verts)} boundary vertices",
                        )

                        for iteration in range(self.smooth_iterations):
                            new_positions = {}

                            for vert in interior_verts:
                                if len(vert.link_edges) == 0:
                                    continue

                                connected_positions = []
                                for edge in vert.link_edges:
                                    other_vert = edge.other_vert(vert)
                                    connected_positions.append(other_vert.co.copy())

                                if connected_positions:
                                    avg_pos = sum(
                                        connected_positions, vert.co * 0
                                    ) / len(connected_positions)
                                    new_pos = vert.co.lerp(avg_pos, 0.5)
                                    new_positions[vert] = new_pos

                            for vert, new_pos in new_positions.items():
                                vert.co = new_pos

                        bmesh.update_edit_mesh(obj.data)
                        obj.data.update()
                        self.report(
                            {"INFO"},
                            f"Applied {self.smooth_iterations} smoothing iterations",
                        )
                    else:
                        self.report(
                            {"INFO"},
                            "No interior vertices to smooth - all vertices are on boundary",
                        )

                except Exception as e:
                    self.report(
                        {"WARNING"}, f"Boundary-preserving smoothing failed: {str(e)}"
                    )

            # After fill (and optional smoothing), ensure face normals match shell orientation
            try:
                scene = context.scene
                shell_obj = getattr(scene, "spp_shell_object", None)
                bm = bmesh.from_edit_mesh(obj.data)
                bm.faces.ensure_lookup_table()

                if shell_obj and shell_obj.type == "MESH" and len(bm.faces) > 0:
                    # Compute average panel normal in shell local space
                    # Sample a subset of faces (up to 50) for robustness
                    faces = bm.faces
                    step = max(1, len(faces) // 50)
                    avg_panel_normal_world = Vector((0.0, 0.0, 0.0))
                    sample_points_world = []
                    mw = obj.matrix_world
                    for i in range(0, len(faces), step):
                        f = faces[i]
                        n_world = (mw.to_3x3() @ f.normal).normalized()
                        avg_panel_normal_world += n_world
                        # Use face center as corresponding sample point
                        sample_points_world.append(mw @ f.calc_center_median())
                    if sample_points_world:
                        avg_panel_normal_world.normalize()

                        # Build BVH for shell in its local space
                        dg = context.evaluated_depsgraph_get()
                        shell_eval = shell_obj.evaluated_get(dg)
                        shell_mesh = shell_eval.to_mesh()
                        try:
                            bvh = BVHTree.FromMesh(shell_mesh, epsilon=0.0)
                        except Exception:
                            bvh = None

                        if bvh is not None:
                            inv_shell = shell_obj.matrix_world.inverted()
                            # Compare average alignment across samples
                            dots = []
                            for p_world in sample_points_world:
                                p_shell = inv_shell @ p_world
                                hit = bvh.find_nearest(p_shell)
                                if hit is None:
                                    continue
                                _, _, face_index, normal_shell = hit
                                # normal_shell is in shell local space
                                # Bring panel avg normal into shell local space for a fair dot
                                panel_n_shell = (
                                    inv_shell.to_3x3() @ avg_panel_normal_world
                                ).normalized()
                                dots.append(
                                    panel_n_shell.dot(normal_shell.normalized())
                                )

                            if dots:
                                avg_dot = sum(dots) / len(dots)
                                # If opposing orientation (avg_dot < 0), flip panel normals
                                if avg_dot < 0.0:
                                    # Preserve select mode and flip faces
                                    prev_select_mode = (
                                        context.tool_settings.mesh_select_mode[:]
                                    )
                                    try:
                                        bpy.ops.mesh.select_all(action="SELECT")
                                        bpy.ops.mesh.select_mode(type="FACE")
                                        bpy.ops.mesh.flip_normals()
                                        self.report(
                                            {"INFO"},
                                            "Flipped panel normals to match shell orientation",
                                        )
                                        bmesh.update_edit_mesh(obj.data)
                                    except Exception as e:
                                        self.report(
                                            {"WARNING"},
                                            f"Failed to flip normals: {str(e)}",
                                        )
                                    finally:
                                        try:
                                            bpy.ops.mesh.select_mode(
                                                type="VERT"
                                                if prev_select_mode[0]
                                                else "EDGE"
                                                if prev_select_mode[1]
                                                else "FACE"
                                            )
                                        except Exception:
                                            pass

                        # Free evaluated mesh
                        try:
                            shell_eval.to_mesh_clear()
                        except Exception:
                            pass

            except Exception as e:
                # Non-fatal; proceed even if alignment check fails
                self.report({"WARNING"}, f"Normal alignment check failed: {str(e)}")

            bpy.ops.mesh.select_mode(
                type="VERT" if select_mode[0] else "EDGE" if select_mode[1] else "FACE"
            )

            if original_mode != "EDIT":
                try:
                    bpy.ops.object.mode_set(mode=original_mode)
                except Exception:
                    pass

            return {"FINISHED"} if success else {"CANCELLED"}

        except Exception as e:
            if original_mode != "EDIT":
                try:
                    bpy.ops.object.mode_set(mode=original_mode)
                except Exception:
                    pass
            self.report({"ERROR"}, f"Simple grid fill failed: {str(e)}")
            return {"CANCELLED"}


# Registration
classes = [MESH_OT_SimpleGridFill]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
