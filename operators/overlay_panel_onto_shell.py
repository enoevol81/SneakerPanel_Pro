
import bmesh
import bpy
from mathutils import Vector, geometry

from ..utils.collections import add_object_to_panel_collection


class MESH_OT_OverlayPanelOntoShell(bpy.types.Operator):
   
    bl_idname = "mesh.overlay_panel_onto_shell"
    bl_label = "Project 2D Panel to 3D Shell"
    bl_description = "Uses the shell's UVs to recreate the selected 2-D panel directly on the shell surface"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """Check if we have an active mesh and a valid shell object."""
        return (
            context.active_object
            and context.active_object.type == "MESH"
            and hasattr(context.scene, "spp_shell_object")
            and context.scene.spp_shell_object
            and context.scene.spp_shell_object.type == "MESH"
        )

    def find_uv_reference_mesh(self, context, shell_obj_name):

        for obj in context.scene.objects:
            if obj.type == "MESH" and "spp_original_3d_mesh_name" in obj:
                if obj["spp_original_3d_mesh_name"] == shell_obj_name:
                    return obj
        return None

    def check_uv_boundary_violations(self, panel_obj, uv_mesh_obj, scale_factor):

        violation_count = 0

        # Create bmesh from panel
        bm = bmesh.new()
        bm.from_mesh(panel_obj.data)

        try:
            # Check each vertex
            for vert in bm.verts:
                # Convert vertex to UV space
                p_world = panel_obj.matrix_world @ vert.co
                p_local_uv = uv_mesh_obj.matrix_world.inverted() @ p_world
                uv_coord = Vector(
                    (p_local_uv.x / scale_factor, p_local_uv.y / scale_factor)
                )

                # Check if outside UV bounds (0-1 range)
                if uv_coord.x < 0 or uv_coord.x > 1 or uv_coord.y < 0 or uv_coord.y > 1:
                    violation_count += 1

        finally:
            bm.free()

        return violation_count

    def check_uv_boundary_violations(self, panel_obj, uv_mesh_obj, scale_factor):

        violation_count = 0

        # Create bmesh from panel
        bm = bmesh.new()
        bm.from_mesh(panel_obj.data)

        try:
            # Check each vertex
            for vert in bm.verts:
                # Convert vertex to UV space
                p_world = panel_obj.matrix_world @ vert.co
                p_local_uv = uv_mesh_obj.matrix_world.inverted() @ p_world
                uv_coord = Vector(
                    (p_local_uv.x / scale_factor, p_local_uv.y / scale_factor)
                )

                # Check if outside UV bounds (0-1 range)
                if uv_coord.x < 0 or uv_coord.x > 1 or uv_coord.y < 0 or uv_coord.y > 1:
                    violation_count += 1

        finally:
            bm.free()

        return violation_count

    def execute(self, context):
        # Store original mode and switch to Object mode if needed
        original_mode = context.mode
        if original_mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        panel_obj_2d = context.active_object
        shell_obj = context.scene.spp_shell_object

        # Find the UV reference mesh
        uv_mesh_obj = self.find_uv_reference_mesh(context, shell_obj.name)
        if not uv_mesh_obj:
            self.report(
                {"ERROR"}, f"UV reference mesh for '{shell_obj.name}' not found."
            )
            return {"CANCELLED"}

        # Get required properties from the UV reference mesh
        scale_factor = uv_mesh_obj.get("spp_applied_scale_factor", None)
        source_uv_map_name = uv_mesh_obj.get("spp_source_uv_map_name", None)
        if scale_factor is None or source_uv_map_name is None:
            self.report(
                {"ERROR"}, "UV reference mesh missing required custom properties."
            )
            return {"CANCELLED"}
        if scale_factor == 0:
            self.report({"ERROR"}, "UV reference mesh scale factor is zero.")
            return {"CANCELLED"}

        # Pre-check for UV boundary violations
        boundary_violations = self.check_uv_boundary_violations(
            panel_obj_2d, uv_mesh_obj, scale_factor
        )

        if boundary_violations > 0:
            self.report(
                {"WARNING"},
                f"Found {boundary_violations} UV boundary violations. "
                "This may cause misprojections. Consider running 'Check UV Boundary' first.",
            )

        try:
            # Duplicate the panel so we keep the 2-D original intact
            bpy.ops.object.duplicate()
            panel_obj_3d = context.active_object
            panel_obj_3d.name = f"{panel_obj_3d.name}_3D"

            mesh = panel_obj_3d.data

            # -------- Build UV triangle list from shell once --------
            depsgraph = context.evaluated_depsgraph_get()
            eval_shell = shell_obj.evaluated_get(depsgraph)
            eval_mesh = eval_shell.to_mesh()
            bm_shell = bmesh.new()
            bm_shell.from_mesh(eval_mesh)
            bm_shell.transform(shell_obj.matrix_world)  # bring to world space

            # Get the UV layer from the shell
            uv_layer = bm_shell.loops.layers.uv.get(source_uv_map_name)
            if uv_layer is None:
                uv_layer = bm_shell.loops.layers.uv.active
            if uv_layer is None:
                self.report({"ERROR"}, "Shell mesh has no UVs.")
                bm_shell.free()
                eval_shell.to_mesh_clear()
                return {"CANCELLED"}

            # Create triangles list for barycentric mapping
            triangles = []  # list of tuples (uv0,uv1,uv2, v0, v1, v2)
            for face in bm_shell.faces:
                loops = face.loops
                if len(loops) < 3:
                    continue
                # triangulate quads manually; n-gons ignored for now
                if len(loops) == 3:
                    trio = (0, 1, 2)
                    uv_3d = [
                        Vector((loops[i][uv_layer].uv.x, loops[i][uv_layer].uv.y, 0.0))
                        for i in trio
                    ]
                    verts_3d = [loops[i].vert.co.copy() for i in trio]
                    triangles.append((*uv_3d, *verts_3d))
                elif len(loops) == 4:
                    pairs = [(0, 1, 2), (0, 2, 3)]
                    for trio in pairs:
                        uv_3d = [
                            Vector(
                                (loops[i][uv_layer].uv.x, loops[i][uv_layer].uv.y, 0.0)
                            )
                            for i in trio
                        ]
                        verts_3d = [loops[i].vert.co.copy() for i in trio]
                        triangles.append((*uv_3d, *verts_3d))

            # Free eval mesh after we finish using it
            eval_shell.to_mesh_clear()

            # -------- Project each vertex --------
            bm = bmesh.new()
            bm.from_mesh(mesh)
            for v in bm.verts:
                # Convert vertex to UV space
                p_world = panel_obj_3d.matrix_world @ v.co
                p_local_uv = uv_mesh_obj.matrix_world.inverted() @ p_world
                uv_coord = Vector(
                    (p_local_uv.x / scale_factor, p_local_uv.y / scale_factor, 0.0)
                )

                # Find the triangle in UV space that contains this point
                found = False
                for t in triangles:
                    uv0, uv1, uv2, v0, v1, v2 = t
                    if geometry.intersect_point_tri_2d(
                        uv_coord.xy, uv0.xy, uv1.xy, uv2.xy
                    ):
                        # Calculate barycentric coordinates
                        canonical_tri = (
                            Vector((0, 0, 0)),
                            Vector((1, 0, 0)),
                            Vector((0, 1, 0)),
                        )
                        bary = geometry.barycentric_transform(
                            uv_coord, uv0, uv1, uv2, *canonical_tri
                        )
                        w0 = 1.0 - bary.x - bary.y
                        w1 = bary.x
                        w2 = bary.y

                        # Apply barycentric coordinates to get 3D position
                        new_world = w0 * v0 + w1 * v1 + w2 * v2
                        v.co = panel_obj_3d.matrix_world.inverted() @ new_world
                        found = True
                        break

                if not found:
                    self.report(
                        {"WARNING"},
                        f"Vertex at UV ({uv_coord.x:.3f}, {uv_coord.y:.3f}) not inside any shell UV face.",
                    )

            # Apply changes to the mesh
            bm.to_mesh(mesh)
            mesh.update()

            # Optional shrinkwrap for safety
            shrink = panel_obj_3d.modifiers.new(name="Conform", type="SHRINKWRAP")
            shrink.target = shell_obj
            shrink.wrap_method = "NEAREST_SURFACEPOINT"
            shrink.offset = 0.00001
            bpy.ops.object.modifier_apply(modifier=shrink.name)

            # Put in correct collection and update panel counter
            panel_count = context.scene.spp_panel_count
            panel_name_prop = context.scene.spp_panel_name
            add_object_to_panel_collection(panel_obj_3d, panel_count, panel_name_prop)
            context.scene.spp_panel_count += 1

            self.report({"INFO"}, f"Panel '{panel_obj_3d.name}' projected onto shell.")

        except Exception as e:
            self.report({"ERROR"}, f"Error projecting panel: {str(e)}")
            return {"CANCELLED"}
        finally:
            # Clean up bmesh objects
            if "bm" in locals():
                bm.free()
            if "bm_shell" in locals():
                bm_shell.free()

            # Restore original mode
            try:
                if original_mode != "OBJECT":
                    bpy.ops.object.mode_set(mode=original_mode.split("_")[-1])
            except:
                pass  # If mode restoration fails, stay in current mode

        return {"FINISHED"}


# Registration
classes = [MESH_OT_OverlayPanelOntoShell]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
