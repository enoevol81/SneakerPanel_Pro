"""
Simplifies selected curve splines using the decimate operator.

This operator takes a curve object and simplifies it by reducing the number
of points while maintaining the overall shape based on the decimate ratio
specified in the scene properties.
"""
import bpy

class OBJECT_OT_DecimateCurve(bpy.types.Operator):
    """Simplify selected curve splines using the decimate operator.
    
    Reduces the number of points in the selected curve while maintaining
    its overall shape based on the decimate ratio specified in scene properties.
    This helps create cleaner curves with fewer control points.
    """
    bl_idname = "object.decimate_curve"
    bl_label = "Decimate Curve"
    bl_description = "Simplify selected curve splines using the decimate operator"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """Check if the active object is a curve."""
        obj = context.active_object
        return obj and obj.type == 'CURVE'

    def execute(self, context):
        # Add undo checkpoint
        bpy.ops.ed.undo_push(message="Decimate Curve")
        
        obj = context.active_object

        if obj.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        bpy.ops.curve.select_all(action='SELECT')
        # Set all selected handles to automatic for better decimation
        bpy.ops.curve.handle_type_set(type='AUTOMATIC')
        

        ratio = context.scene.spp_decimate_ratio  # Get ratio from UI
        try:
            bpy.ops.curve.decimate(ratio=ratio)
            self.report({'INFO'}, f"Curve decimated with ratio {ratio}.")
        except Exception as e:
            self.report({'ERROR'}, f"Curve decimate failed: {str(e)}")
            return {'CANCELLED'}

        return {'FINISHED'}

# Registration
classes = [OBJECT_OT_DecimateCurve]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
