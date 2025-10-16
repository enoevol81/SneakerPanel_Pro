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
                
                if shell_obj is None:
                    self.report({"WARNING"}, "No shell object found in scene properties")
                elif shell_obj.type != "MESH":
                    self.report({"WARNING"}, f"Shell object '{shell_obj.name}' is not a mesh")
                else:
                    self.report({"INFO"}, f"Using shell object: {shell_obj.name}")
                
                # Ensure we're in edit mode and have valid mesh data
                if obj.mode != 'EDIT':
                    bpy.ops.object.mode_set(mode='EDIT')
                    
                bm = bmesh.from_edit_mesh(obj.data)
                bm.faces.ensure_lookup_table()
                bm.normal_update()
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
                        
                        if shell_mesh is None or len(shell_mesh.polygons) == 0:
                            self.report({"WARNING"}, "Shell object has no mesh data")
                            bvh = None
                        else:
                            self.report({"INFO"}, f"Shell mesh has {len(shell_mesh.polygons)} faces")
                            try:
                                # Create BVH tree - try multiple methods for compatibility
                                bvh = None
                                
                                # Method 1: Try FromBMesh (Blender 4.4+)
                                try:
                                    shell_bm = bmesh.new()
                                    shell_bm.from_mesh(shell_mesh)
                                    shell_bm.faces.ensure_lookup_table()
                                    shell_bm.normal_update()
                                    bvh = BVHTree.FromBMesh(shell_bm)
                                    shell_bm.free()
                                except (AttributeError, Exception):
                                    pass
                                
                                # Method 2: Try FromMesh if FromBMesh failed (older versions)
                                if bvh is None:
                                    try:
                                        bvh = BVHTree.FromMesh(shell_mesh)
                                    except (AttributeError, Exception):
                                        pass
                                
                                # Method 3: Try FromPolygons as fallback (very old versions)
                                if bvh is None:
                                    try:
                                        vertices = [v.co for v in shell_mesh.vertices]
                                        polygons = [p.vertices for p in shell_mesh.polygons]
                                        bvh = BVHTree.FromPolygons(vertices, polygons)
                                    except (AttributeError, Exception):
                                        pass
                                
                                if bvh is not None:
                                    self.report({"INFO"}, "BVH tree created successfully")
                                else:
                                    self.report({"WARNING"}, "Failed to create BVH tree with any method")
                                    
                            except Exception as e:
                                self.report({"WARNING"}, f"Failed to build BVH tree: {str(e)}")
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
                                
                                # Handle different BVH hit result formats across Blender versions
                                try:
                                    # Try new format: (location, normal, face_index, distance)
                                    location, normal_shell, face_index, distance = hit
                                except ValueError:
                                    try:
                                        # Try old format: (location, normal, face_index)
                                        location, normal_shell, face_index = hit
                                    except ValueError:
                                        # Skip if we can't unpack the hit result
                                        continue
                                
                                # normal_shell is in shell local space and should be a Vector
                                # Bring panel avg normal into shell local space for a fair dot
                                panel_n_shell = (
                                    inv_shell.to_3x3() @ avg_panel_normal_world
                                ).normalized()
                                
                                # Ensure normal_shell is a Vector (compatibility across versions)
                                try:
                                    if hasattr(normal_shell, 'normalized'):
                                        normal_shell_vec = normal_shell.normalized()
                                    elif hasattr(normal_shell, '__len__') and len(normal_shell) == 3:
                                        normal_shell_vec = Vector(normal_shell).normalized()
                                    else:
                                        # Skip if we can't convert to a proper normal vector
                                        continue
                                except Exception:
                                    continue
                                
                                dots.append(
                                    panel_n_shell.dot(normal_shell_vec)
                                )

                            if dots:
                                avg_dot = sum(dots) / len(dots)
                                self.report({"INFO"}, f"Analyzed {len(dots)} sample points, avg_dot: {avg_dot:.3f}")
                                
                                # If opposing orientation (avg_dot < 0), flip panel normals
                                if avg_dot < 0.0:
                                    self.report({"INFO"}, "Panel normals are opposing shell - flipping...")
                                    # Preserve select mode and flip faces
                                    prev_select_mode = (
                                        context.tool_settings.mesh_select_mode[:]
                                    )
                                    try:
                                        # Ensure we have faces selected
                                        bpy.ops.mesh.select_all(action="SELECT")
                                        bpy.ops.mesh.select_mode(type="FACE")
                                        
                                        # Update bmesh before flipping
                                        bmesh.update_edit_mesh(obj.data)
                                        
                                        # Flip normals
                                        bpy.ops.mesh.flip_normals()
                                        
                                        # Update mesh after flipping
                                        bm.normal_update()
                                        bmesh.update_edit_mesh(obj.data)
                                        
                                        self.report(
                                            {"INFO"},
                                            f"✓ Flipped panel normals to match shell orientation (was {avg_dot:.3f})",
                                        )
                                    except Exception as e:
                                        self.report(
                                            {"ERROR"},
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
                                else:
                                    self.report(
                                        {"INFO"},
                                        f"✓ Panel normals already aligned with shell (avg_dot: {avg_dot:.3f})",
                                    )
                            else:
                                self.report({"WARNING"}, "No valid sample points found for normal comparison")

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
