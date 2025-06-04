import bpy
from bpy.props import EnumProperty
from bpy.types import Operator

class CURVE_OT_MirrorSelectedPointsAtCursor(Operator):
    """Duplicates and mirrors selected curve points around the 3D cursor in Edit Mode"""
    bl_idname = "curve.mirror_selected_points_at_cursor"
    bl_label = "Mirror Selected Curve Points (Edit Mode)"
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
        # Operator can run if there is an active object, it's a CURVE, and we are in EDIT_CURVE mode
        obj = context.active_object
        return (obj and obj.type == 'CURVE' and context.mode == 'EDIT_CURVE')

    def execute(self, context):
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
            bpy.ops.curve.duplicate_move() # Duplicates and leaves new points selected, in move mode
            # We can cancel the move part if we want them duplicated in place first,
            # but mirror will transform them anyway.
            # Or, duplicate and then mirror:
            # bpy.ops.curve.duplicate() # Duplicates in place, new points selected

            # 2. Mirror the (newly duplicated and selected) points
            # The transform.mirror operator uses the view orientation by default for its axis,
            # unless orient_type is specified. For global axis around cursor, this should work.
            bpy.ops.transform.mirror(
                orient_type='GLOBAL', # Using GLOBAL to make axis choices more predictable
                constraint_axis=constraint_axis_tuple
            )
            self.report({'INFO'}, f"Duplicated and mirrored selected points around 3D cursor on {self.axis} axis.")

        except RuntimeError as e:
            self.report({'ERROR'}, f"Error during mirror operation: {e}")
            # Restore original pivot point even on error
            context.scene.tool_settings.transform_pivot_point = original_pivot_point
            return {'CANCELLED'}
        finally:
            # Restore original pivot point
            context.scene.tool_settings.transform_pivot_point = original_pivot_point
            
        # After mirroring, the user will likely need to:
        # - Deselect all (A)
        # - Select the two endpoints of the original spline and the two corresponding
        #   endpoints of the mirrored spline.
        # - Press 'F' (Make Segment) to join them if they are separate splines,
        #   or adjust handles if they are part of the same spline.
        # - Ensure the overall curve is cyclic if needed.

        return {'FINISHED'}

def register():
    bpy.utils.register_class(CURVE_OT_MirrorSelectedPointsAtCursor)

def unregister():
    bpy.utils.unregister_class(CURVE_OT_MirrorSelectedPointsAtCursor)