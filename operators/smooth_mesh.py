
import bmesh
import bpy
from bpy.props import BoolProperty, FloatProperty, IntProperty
from bpy.types import Operator


class MESH_OT_SmoothMesh(Operator):

    bl_idname = "mesh.smooth_mesh"
    bl_label = "Smooth Mesh"
    bl_description = "Smooth mesh vertices with boundary preservation"
    bl_options = {"REGISTER", "UNDO"}

    iterations: IntProperty(
        name="Iterations",
        description="Number of smoothing iterations",
        default=2,
        min=1,
        max=20,
    )

    factor: FloatProperty(
        name="Smoothing Factor",
        description="Strength of smoothing (0.0 = no change, 1.0 = maximum)",
        default=0.5,
        min=0.0,
        max=1.0,
    )

    preserve_boundary: BoolProperty(
        name="Preserve Boundary",
        description="Keep boundary vertices unchanged (CRITICAL for UV workflow)",
        default=True,
    )

    selected_only: BoolProperty(
        name="Selected Only", description="Smooth only selected vertices", default=False
    )

    @classmethod
    def poll(cls, context):
        """Check if we have an active mesh object."""
        obj = context.active_object
        return obj and obj.type == "MESH"

    def smooth_with_bmesh(self, context):
        """Apply smoothing using bmesh for more control."""
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)

        # Ensure lookup tables are current
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        # Get vertices to smooth
        if self.selected_only:
            verts_to_smooth = [v for v in bm.verts if v.select]
        else:
            verts_to_smooth = list(bm.verts)

        # Filter out boundary vertices if preserve_boundary is True
        if self.preserve_boundary:
            boundary_verts = set()
            for edge in bm.edges:
                if edge.is_boundary:
                    boundary_verts.update(edge.verts)

            verts_to_smooth = [v for v in verts_to_smooth if v not in boundary_verts]
            boundary_count = len(boundary_verts)
            smooth_count = len(verts_to_smooth)
            self.report(
                {"INFO"},
                f"Smoothing {smooth_count} vertices, preserving {boundary_count} boundary vertices",
            )
        else:
            smooth_count = len(verts_to_smooth)
            self.report({"INFO"}, f"Smoothing {smooth_count} vertices")

        if not verts_to_smooth:
            self.report({"WARNING"}, "No vertices to smooth")
            return False

        # Apply smoothing iterations
        for iteration in range(self.iterations):
            # Store new positions
            new_positions = {}

            for vert in verts_to_smooth:
                if len(vert.link_edges) == 0:
                    continue

                # Calculate average position of connected vertices
                connected_positions = []
                for edge in vert.link_edges:
                    other_vert = edge.other_vert(vert)
                    connected_positions.append(other_vert.co.copy())

                if connected_positions:
                    # Use mathutils.Vector for proper vector math
                    from mathutils import Vector

                    avg_pos = Vector((0, 0, 0))
                    for pos in connected_positions:
                        avg_pos += pos
                    avg_pos /= len(connected_positions)

                    # Blend between original and average position
                    new_pos = vert.co.lerp(avg_pos, self.factor)
                    new_positions[vert] = new_pos

            # Apply new positions
            for vert, new_pos in new_positions.items():
                vert.co = new_pos

        # Update mesh
        bmesh.update_edit_mesh(obj.data)
        return True

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

        # Use bmesh method for reliable smoothing
        try:
            if self.smooth_with_bmesh(context):
                # Restore original mode if it was different
                if original_mode != "EDIT":
                    try:
                        bpy.ops.object.mode_set(mode=original_mode)
                    except:
                        pass  # Don't fail if mode restoration fails
                return {"FINISHED"}
            else:
                # Restore original mode on failure
                if original_mode != "EDIT":
                    try:
                        bpy.ops.object.mode_set(mode=original_mode)
                    except:
                        pass
                self.report({"ERROR"}, "Smoothing failed")
                return {"CANCELLED"}
        except Exception as e:
            # Restore original mode on error
            if original_mode != "EDIT":
                try:
                    bpy.ops.object.mode_set(mode=original_mode)
                except:
                    pass
            self.report({"ERROR"}, f"Smoothing error: {str(e)}")
            return {"CANCELLED"}


# Registration
classes = [MESH_OT_SmoothMesh]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
