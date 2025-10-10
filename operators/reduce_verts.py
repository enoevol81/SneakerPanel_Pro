import bmesh
import bpy

from ..utils.panel_utils import apply_surface_snap


def _collapse_shortest_edge_to_make_even(obj, context):
    if not obj or obj.type != "MESH":
        return False
    # Quick check in object mode
    if obj.mode != "EDIT" and len(obj.data.vertices) % 2 == 0:
        return False

    original_mode = obj.mode
    try:
        if obj.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")

        me = obj.data
        bm = bmesh.from_edit_mesh(me)

        if len(bm.verts) % 2 == 0:
            return False
        if len(bm.edges) == 0:
            return False

        # Find shortest edge to minimally affect shape
        shortest = None
        shortest_len = 1e30
        for edge in bm.edges:
            edge_length = (edge.verts[0].co - edge.verts[1].co).length
            if edge_length < shortest_len:
                shortest_len = edge_length
                shortest = edge
        if not shortest:
            return False

        # Select only the two verts of the shortest edge
        for v in bm.verts:
            v.select = False
        for v in shortest.verts:
            v.select = True
        bmesh.update_edit_mesh(me, loop_triangles=False, destructive=False)

        # Ensure vertex select mode
        try:
            context.tool_settings.mesh_select_mode = (True, False, False)
        except Exception:
            pass

        # Merge to center to collapse one vertex
        bpy.ops.mesh.merge(type="CENTER")
        bmesh.update_edit_mesh(me, loop_triangles=False, destructive=False)
        return True
    finally:
        if original_mode != "EDIT":
            try:
                bpy.ops.object.mode_set(mode=original_mode)
            except Exception:
                pass


def _collapse_n_shortest_edges(obj, count):
    if count <= 0:
        return 0
    if not obj or obj.type != "MESH":
        return 0
    # Ensure we're in edit mode; caller should manage this, but be safe
    if obj.mode != "EDIT":
        bpy.ops.object.mode_set(mode="EDIT")
    me = obj.data
    bm = bmesh.from_edit_mesh(me)
    collapsed = 0
    for _ in range(count):
        if len(bm.edges) == 0:
            break
        # Find shortest edge
        shortest = None
        shortest_len = 1e30
        for edge in bm.edges:
            edge_length = (edge.verts[0].co - edge.verts[1].co).length
            if edge_length < shortest_len:
                shortest = edge
                shortest_len = edge_length
        if not shortest:
            break
        try:
            bmesh.ops.collapse(bm, edges=[shortest])
            collapsed += 1
        except Exception:
            break
    bmesh.update_edit_mesh(me, loop_triangles=False, destructive=False)
    return collapsed


class MESH_OT_MakeEvenVerts(bpy.types.Operator):
    bl_idname = "mesh.make_even_verts"
    bl_label = "Make Even"
    bl_description = "Reduce Verts"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != "MESH":
            self.report({"ERROR"}, "Please select a mesh object")
            return {"CANCELLED"}

        changed = _collapse_shortest_edge_to_make_even(obj, context)
        if changed:
            self.report({"INFO"}, "Adjusted vertex count to be even")
            return {"FINISHED"}
        else:
            self.report({"INFO"}, "Vertex count already even or no change possible")
            return {"CANCELLED"}


class OBJECT_OT_ReduceVerts(bpy.types.Operator):
    bl_idname = "object.reduce_verts"
    bl_label = "Reduce Verts"
    bl_description = "Reduce mesh vertices while maintaining shape"
    bl_options = {"REGISTER", "UNDO"}

    factor: bpy.props.FloatProperty(
        name="Reduction Factor",
        description="Factor to reduce vertices by (0.0 to 1.0)",
        min=0.0,
        max=1.0,
        default=0.2,
    )

    @classmethod
    def poll(cls, context):
        """Check if the operator can be executed.

        Args:
            context: Blender context

        Returns:
            bool: True if active object is a mesh
        """
        return context.active_object and context.active_object.type == "MESH"

    def execute(self, context):
        # Add undo checkpoint
        bpy.ops.ed.undo_push(message="Reduce Vertices")

        try:
            obj = context.active_object
            if not obj or obj.type != "MESH":
                self.report({"WARNING"}, "Active object is not a mesh")
                return {"CANCELLED"}

            # Store original mode and switch to object mode
            original_mode = obj.mode
            bpy.ops.object.mode_set(mode="OBJECT")
            original_verts = len(obj.data.vertices)

            # Calculate target vertex count and ensure it's even
            target_verts = int(original_verts * (1.0 - self.factor))
            # Make sure target_verts is even
            if target_verts % 2 != 0:
                target_verts -= 1  # Subtract 1 to make it even

            if target_verts >= original_verts:
                self.report(
                    {"WARNING"}, "Reduction factor too small to make any changes"
                )
                bpy.ops.object.mode_set(mode=original_mode)
                return {"CANCELLED"}

            # Go to Edit Mode and select all
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")

            # Try increasing dissolve angles until desired reduction
            current_verts = original_verts
            for angle in [0.01, 0.05, 0.1, 0.2, 0.4, 0.8]:
                bpy.ops.mesh.dissolve_limited(angle_limit=angle)
                bpy.ops.object.mode_set(mode="OBJECT")
                current_verts = len(obj.data.vertices)

                if current_verts <= target_verts:
                    break

                if current_verts > target_verts:
                    bpy.ops.object.mode_set(mode="EDIT")

            # If we're still above target, collapse the shortest edges to hit it exactly
            if current_verts > target_verts:
                bpy.ops.object.mode_set(mode="EDIT")
                _collapse_n_shortest_edges(obj, current_verts - target_verts)
                bpy.ops.object.mode_set(mode="OBJECT")
                current_verts = len(obj.data.vertices)

            # Ensure we're in edit mode for Loop Tools
            bpy.ops.object.mode_set(mode="EDIT")

            # Run Loop Tools Space operator
            try:
                bpy.ops.mesh.looptools_space()
            except Exception as e:
                self.report(
                    {"WARNING"},
                    f"Could not run Loop Tools Space operator: {str(e)}. Make sure Loop Tools is enabled.",
                )

            # Apply surface snap
            try:
                apply_surface_snap()
            except Exception as e:
                self.report({"WARNING"}, f"Could not apply surface snap: {str(e)}")

            # Enforce even vertex count at the end (safety)
            bpy.ops.object.mode_set(mode="OBJECT")
            _collapse_shortest_edge_to_make_even(obj, context)

            # Restore original mode
            bpy.ops.object.mode_set(mode=original_mode)

            # Recompute current vert count for accurate reporting
            current_verts = len(obj.data.vertices)
            reduction_percent = (
                (original_verts - current_verts) / original_verts
            ) * 100
            self.report(
                {"INFO"},
                f"Reduced vertices from {original_verts} to {current_verts} ({reduction_percent:.1f}% reduction)",
            )
            return {"FINISHED"}

        except Exception as e:
            self.report({"ERROR"}, f"Error reducing vertices: {str(e)}")
            # Try to restore original mode
            try:
                bpy.ops.object.mode_set(mode=original_mode)
            except Exception:
                pass
            return {"CANCELLED"}


# Registration
classes = [OBJECT_OT_ReduceVerts, MESH_OT_MakeEvenVerts]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
