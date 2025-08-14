"""
Fills selected edge loop in edit mode using grid fill with configurable span and offset.

This operator takes a selected edge loop in edit mode and fills it with a grid
pattern using Blender's grid fill operator. The span and offset can be configured
to control the density and orientation of the grid.
"""

import bpy
from bpy.props import IntProperty
from bpy.types import Operator


class MESH_OT_FillBorderGrid(Operator):
    """Fill selected edge loop with grid pattern.

    Takes a selected edge loop in edit mode and fills it with a grid pattern
    using Blender's grid fill operator. The span and offset can be configured
    to control the density and orientation of the grid.

    This operator is useful for creating clean quad topology inside border loops.
    """

    bl_idname = "mesh.fill_border_grid"
    bl_label = "Fill Border with Grid"
    bl_options = {"REGISTER", "UNDO"}

    span: IntProperty(
        name="Span",
        description="Number of grid cells in one direction",
        default=1,
        min=1,
        max=1000,
    )

    offset: IntProperty(
        name="Offset",
        description="Offset grid to change the edge flow",
        default=0,
        min=-1000,
        max=1000,
    )

    @classmethod
    def poll(cls, context):
        """Check if we're in edit mode with a mesh."""
        obj = context.active_object
        return obj and obj.type == "MESH" and obj.mode == "EDIT"

    def execute(self, context):
        # Add undo checkpoint
        bpy.ops.ed.undo_push(message="Fill Border with Grid")

        try:
            # Get the current selection mode
            select_mode = context.tool_settings.mesh_select_mode[:]

            # Ensure we're in edge select mode
            bpy.ops.mesh.select_mode(type="EDGE")

            # Apply grid fill with the specified parameters
            bpy.ops.mesh.fill_grid(span=self.span, offset=self.offset)

            # Restore the original selection mode
            bpy.ops.mesh.select_mode(
                type="VERT" if select_mode[0] else "EDGE" if select_mode[1] else "FACE"
            )

            self.report(
                {"INFO"},
                f"Grid fill applied with span={self.span}, offset={self.offset}",
            )
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Grid fill failed: {str(e)}")
            return {"CANCELLED"}


# Registration
classes = [MESH_OT_FillBorderGrid]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
