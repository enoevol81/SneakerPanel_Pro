# File: SneakerPanel_Pro/operators/fill_border_grid.py
# This operator fills the user's selected edge loop in Edit Mode using Grid Fill.

import bpy
from bpy.props import IntProperty
from bpy.types import Operator

class MESH_OT_FillBorderGrid(Operator):
    """Fills the selected edge loop in Edit Mode using Grid Fill."""
    bl_idname = "mesh.fill_border_grid"
    bl_label = "Fill Selected Loop with Grid"
    bl_options = {'REGISTER', 'UNDO'}
    
    span: IntProperty(
        name="Grid Fill Spans",
        default=1,
        min=1,
        max=100,
        description="Number of segments for the grid fill between opposing edges."
    )
    offset: IntProperty(
        name="Grid Fill Offset",
        default=-1,
        min=-100,
        max=100,
        description="Offset for the grid fill pattern."
    )

    @classmethod
    def poll(cls, context):
        # This operator now only works in Edit Mode on a Mesh object.
        return (context.active_object and context.active_object.type == 'MESH' and context.mode == 'EDIT_MESH')

    def execute(self, context):
        # The operator now assumes the user has already selected the correct edge loop.
        # It no longer needs to find the loop, duplicate the object, or manage collections.
        
        self.report({'INFO'}, "Attempting to apply Grid Fill to current selection.")
        
        try:
            # Run Grid Fill directly on the user's selection.
            bpy.ops.mesh.fill_grid(span=self.span, offset=self.offset)
            self.report({'INFO'}, f"Grid Fill applied with span={self.span}, offset={self.offset}.")

        except RuntimeError as e:
            self.report({'ERROR'}, f"Fill operation failed: {e}. Is an appropriate edge loop selected? Does it have an even number of vertices?")
            return {'CANCELLED'}
        
        return {'FINISHED'}

classes = [MESH_OT_FillBorderGrid]
def register():
    for cls in classes: bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
