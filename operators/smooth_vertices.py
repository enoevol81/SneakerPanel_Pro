"""
Vertex smoothing operator for SneakerPanel Pro.

This module provides functionality to smooth mesh vertices while maintaining
their position on the target surface. It's particularly useful for refining
panel geometry after operations like grid fill or vertex reduction.
"""

import bpy

from ..utils.panel_utils import apply_surface_snap


class OBJECT_OT_SmoothVertices(bpy.types.Operator):
    """Smooth mesh vertices while maintaining surface projection.

    This operator applies smoothing to the selected vertices of a mesh while
    ensuring they stay aligned with the target surface. It's typically used
    to refine panel geometry after operations that may create uneven vertex
    distribution.

    The smoothing strength is controlled by the scene property
    'spp_smooth_factor' which should be between 0.0 and 1.0.
    """

    bl_idname = "object.smooth_vertices"
    bl_label = "Smooth Vertices"
    bl_description = "Smooth mesh vertices while maintaining surface projection"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """Check if the operator can be executed.

        Args:
            context: Blender context

        Returns:
            bool: True if there's an active mesh object in edit or object mode
        """
        obj = context.active_object
        return obj and obj.type == "MESH" and context.mode in {"EDIT_MESH", "OBJECT"}

    def execute(self, context):
        """Execute the smoothing operation.

        Args:
            context: Blender context

        Returns:
            set: {'FINISHED'} on success, {'CANCELLED'} on error
        """
        # Add undo checkpoint
        bpy.ops.ed.undo_push(message="Smooth Vertices")

        try:
            obj = context.active_object
            if not obj or obj.type != "MESH":
                self.report({"WARNING"}, "Active object is not a mesh")
                return {"CANCELLED"}

            # Store original mode
            original_mode = obj.mode
            if original_mode != "EDIT":
                bpy.ops.object.mode_set(mode="EDIT")

            # Select all vertices
            bpy.ops.mesh.select_all(action="SELECT")

            # Apply smoothing
            smooth_factor = getattr(context.scene, "spp_smooth_factor", 0.5)
            bpy.ops.mesh.vertices_smooth(factor=smooth_factor)

            # Ensure vertices stay on surface
            try:
                apply_surface_snap()
            except Exception as e:
                self.report({"WARNING"}, f"Surface snap failed: {str(e)}")
                # Continue execution even if snap fails

            # Restore original mode
            if original_mode != "EDIT":
                bpy.ops.object.mode_set(mode=original_mode)

            self.report(
                {"INFO"},
                f"Vertices smoothed with factor {smooth_factor:.2f} and snapped to surface",
            )
            return {"FINISHED"}

        except Exception as e:
            self.report({"ERROR"}, f"Error smoothing vertices: {str(e)}")
            # Try to restore original mode
            if "original_mode" in locals() and original_mode != obj.mode:
                try:
                    bpy.ops.object.mode_set(mode=original_mode)
                except:
                    pass
            return {"CANCELLED"}


# Registration
classes = [OBJECT_OT_SmoothVertices]


def register():
    """Register the operator."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister the operator."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
