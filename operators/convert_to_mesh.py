
import bpy

from ..utils.collections import add_object_to_panel_collection
from ..utils.panel_utils import apply_surface_snap


class OBJECT_OT_ConvertToMesh(bpy.types.Operator):

    bl_idname = "object.convert_to_mesh"
    bl_label = "Convert to Mesh"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """Check if there's an active object that could potentially be converted."""
        return context.active_object is not None

    def execute(self, context):
        # Store original mode and switch to Object mode if needed
        original_mode = context.mode
        if original_mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        try:
            obj = context.active_object
            if not obj:
                self.report({"ERROR"}, "No active object selected")
                return {"CANCELLED"}

            # Check if object can be converted to mesh
            if obj.type not in {"CURVE", "SURFACE", "META", "FONT"}:
                self.report(
                    {"ERROR"},
                    f"Cannot convert {obj.type} object to mesh. Select a curve, surface, metaball, or text object.",
                )
                return {"CANCELLED"}

            bpy.ops.object.convert(target="MESH")
            mesh_obj = context.active_object

            # Get panel count and name for naming
            panel_count = (
                context.scene.spp_panel_count
                if hasattr(context.scene, "spp_panel_count")
                else 1
            )
            panel_name = (
                context.scene.spp_panel_name
                if hasattr(context.scene, "spp_panel_name")
                else "Panel"
            )

            # Use descriptive name if provided, otherwise use default naming
            if panel_name and panel_name.strip():
                mesh_obj.name = f"{panel_name}_Mesh_{panel_count}"
            else:
                mesh_obj.name = f"PanelMesh_{panel_count}"

            # Add to proper collection
            add_object_to_panel_collection(mesh_obj, panel_count, panel_name)

            # Switch to Edit mode for mesh operations
            bpy.ops.object.mode_set(mode="EDIT")

            if mesh_obj.type == "MESH":
                bpy.ops.mesh.select_mode(type="VERT")
                bpy.ops.mesh.select_all(action="SELECT")

                # First apply surface snap
                apply_surface_snap()

                # Then try to space vertices evenly
                try:
                    bpy.ops.mesh.looptools_space(
                        influence=100,
                        input="selected",
                        interpolation="cubic",
                        lock_x=False,
                        lock_y=False,
                        lock_z=False,
                    )
                except Exception as e:
                    self.report({"WARNING"}, f"LoopTools not available: {str(e)}")

                # Apply surface snap again after spacing
                apply_surface_snap()
            else:
                self.report({"ERROR"}, "Active object is not a mesh.")
                return {"CANCELLED"}

            # Switch back to Object mode
            bpy.ops.object.mode_set(mode="OBJECT")
            self.report(
                {"INFO"}, f"Curve converted to Mesh and renamed to '{mesh_obj.name}'."
            )

        except Exception as e:
            self.report({"ERROR"}, f"Error converting curve to mesh: {str(e)}")
            return {"CANCELLED"}
        finally:
            # Restore original mode
            try:
                if original_mode != "OBJECT":
                    bpy.ops.object.mode_set(mode=original_mode.split("_")[-1])
            except:
                pass  # If mode restoration fails, stay in current mode

        return {"FINISHED"}


# Registration
classes = [OBJECT_OT_ConvertToMesh]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
