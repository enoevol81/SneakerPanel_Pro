"""
Mirrors selected curve points around the 3D cursor.

This operator duplicates and mirrors selected curve points around the 3D cursor
in Edit Mode. It allows mirroring across the X, Y, or Z axis relative to the
3D cursor position, which is useful for creating symmetrical curve designs.
"""
import bpy
from bpy.props import EnumProperty
from bpy.types import Operator

class CURVE_OT_MirrorSelectedPointsAtCursor(Operator):
    """Duplicate and mirror selected curve points around the 3D cursor.
    
    This operator duplicates the currently selected curve points and mirrors
    them across a specified axis (X, Y, or Z) using the 3D cursor as the pivot point.
    This is useful for creating symmetrical curve designs for panels.
    
    Note: After mirroring, you may need to manually join endpoints or adjust
    handles to create a continuous curve if desired.
    """
    bl_idname = "curve.mirror_selected_points_at_cursor"
    bl_label = "Mirror Selected Curve Points"
    bl_description = "Duplicate and mirror selected curve points around the 3D cursor"
    bl_options = {'REGISTER', 'UNDO'}

    mirror_axis_items = [
        ('X', "X Axis", "Mirror across the X axis relative to the 3D cursor"),
        ('Y', "Y Axis", "Mirror across the Y axis relative to the 3D cursor"),
        ('Z', "Z Axis", "Mirror across the Z axis relative to the 3D cursor"),
    ]
    axis: EnumProperty(
        name="Mirror Axis",
        items=mirror_axis_items,
        default='X',
        description="Axis to mirror across (relative to 3D cursor and view orientation)"
    )

    @classmethod
    def poll(cls, context):
        """Check if we're in edit mode with a curve."""
        obj = context.active_object
        return obj and obj.type == 'CURVE' and context.mode == 'EDIT_CURVE'

    def execute(self, context):
        # Add undo checkpoint
        bpy.ops.ed.undo_push(message="Mirror Curve Points")
        
        if not (context.active_object and context.active_object.type == 'CURVE' and context.mode == 'EDIT_CURVE'):
            self.report({'ERROR'}, "Active object is not a Curve in Edit Mode.")
            return {'CANCELLED'}

        # Store original pivot point and set to 3D Cursor for the operation
        original_pivot_point = context.scene.tool_settings.transform_pivot_point
        context.scene.tool_settings.transform_pivot_point = 'CURSOR'

        # Determine constraint axis based on user choice
        constraint_axis_tuple = (self.axis == 'X', self.axis == 'Y', self.axis == 'Z')

        try:
            # 1. Duplicate selected points
            bpy.ops.curve.duplicate_move()

            # 2. Mirror the (newly duplicated and selected) points
            bpy.ops.transform.mirror(
                orient_type='GLOBAL',  # Using GLOBAL to make axis choices more predictable
                constraint_axis=constraint_axis_tuple
            )
            self.report({'INFO'}, f"Duplicated and mirrored selected points around 3D cursor on {self.axis} axis.")

        except Exception as e:
            self.report({'ERROR'}, f"Error during mirror operation: {str(e)}")
            # Restore original pivot point even on error
            context.scene.tool_settings.transform_pivot_point = original_pivot_point
            return {'CANCELLED'}
        finally:
            # Restore original pivot point
            context.scene.tool_settings.transform_pivot_point = original_pivot_point

        return {'FINISHED'}

# Registration
classes = [CURVE_OT_MirrorSelectedPointsAtCursor]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()