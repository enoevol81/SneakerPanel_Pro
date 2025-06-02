import bpy

class OBJECT_OT_DecimateCurve(bpy.types.Operator):
    bl_idname = "object.decimate_curve"
    bl_label = "Decimate Curve"
    bl_description = "Simplify selected curve splines using the decimate operator"

    @classmethod
    def poll(cls, context):
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

def register():
    bpy.utils.register_class(OBJECT_OT_DecimateCurve)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_DecimateCurve)
