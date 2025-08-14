import bpy
from bpy.types import Operator


class OBJECT_OT_quick_conform(Operator):
    """Quick conform selected mesh to shell surface by selecting all vertices and snapping to surface"""

    bl_idname = "mesh.quick_conform"
    bl_label = "Quick Conform"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != "MESH":
            self.report({"ERROR"}, "Please select a mesh object")
            return {"CANCELLED"}

        # Get shell object from scene properties
        shell = getattr(context.scene, "spp_shell_object", None)
        if shell and isinstance(shell, str):
            shell = bpy.data.objects.get(shell)

        if not shell or shell.type != "MESH":
            self.report(
                {"WARNING"},
                "No valid shell object found. Please set a shell object in Panel Configuration.",
            )
            return {"CANCELLED"}

        # Store original mode
        original_mode = obj.mode

        try:
            # Ensure we're in object mode first
            if obj.mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")

            # Make sure object is active and selected
            context.view_layer.objects.active = obj
            obj.select_set(True)

            # Add shrinkwrap modifier temporarily
            shrink_mod = obj.modifiers.new(name="QuickConform_Temp", type="SHRINKWRAP")
            shrink_mod.target = shell
            shrink_mod.wrap_method = "NEAREST_SURFACEPOINT"
            shrink_mod.wrap_mode = "ON_SURFACE"
            shrink_mod.offset = 0.0001  # Very small offset to prevent z-fighting

            # Apply the modifier immediately
            bpy.ops.object.modifier_apply(modifier=shrink_mod.name)

            # Return to original mode if it was edit mode
            if original_mode == "EDIT":
                bpy.ops.object.mode_set(mode="EDIT")
                # Select all vertices in edit mode
                bpy.ops.mesh.select_all(action="SELECT")

            self.report(
                {"INFO"}, f"Quick conform applied - mesh conformed to '{shell.name}'"
            )

        except Exception as e:
            self.report({"ERROR"}, f"Failed to apply quick conform: {e}")
            # Try to restore original mode
            try:
                if original_mode != "OBJECT":
                    bpy.ops.object.mode_set(mode=original_mode)
            except:
                pass
            return {"CANCELLED"}

        return {"FINISHED"}


def register():
    bpy.utils.register_class(OBJECT_OT_quick_conform)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_quick_conform)


if __name__ == "__main__":
    register()
