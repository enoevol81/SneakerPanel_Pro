
import bpy


class OBJECT_OT_DecimateCurve(bpy.types.Operator):
    bl_idname = "object.decimate_curve"
    bl_label = "Decimate Curve"
    bl_description = "Simplify selected curve splines using the decimate operator"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """Check if the active object is a curve."""
        obj = context.active_object
        return obj and obj.type == "CURVE"

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != "CURVE":
            self.report({"ERROR"}, "No active curve object")
            return {"CANCELLED"}

        original_mode = obj.mode

        if context.mode != "EDIT_CURVE":
            try:
                bpy.ops.object.mode_set(mode="EDIT")
            except Exception as e:
                self.report({"ERROR"}, f"Could not switch to Edit Mode: {str(e)}")
                return {"CANCELLED"}

        bpy.ops.curve.select_all(action="SELECT")
        # Set all selected handles to automatic for better decimation
        bpy.ops.curve.handle_type_set(type="AUTOMATIC")

        ratio = context.scene.spp_decimate_ratio  # Get ratio from UI
        try:
            bpy.ops.curve.decimate(ratio=ratio)
            self.report({"INFO"}, f"Curve decimated with ratio {ratio}.")

            # Restore original mode if it was different
            if original_mode != "EDIT":
                try:
                    bpy.ops.object.mode_set(mode=original_mode)
                except:
                    pass  # Don't fail if mode restoration fails

            return {"FINISHED"}
        except Exception as e:
            # Restore original mode on error
            if original_mode != "EDIT":
                try:
                    bpy.ops.object.mode_set(mode=original_mode)
                except:
                    pass
            self.report({"ERROR"}, f"Curve decimate failed: {str(e)}")
            return {"CANCELLED"}


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
