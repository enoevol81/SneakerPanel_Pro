
import bmesh
import bpy
from bpy.props import BoolProperty, FloatProperty
from mathutils import Vector

from ..utils.collections import add_object_to_panel_collection


class MESH_OT_FillQuadBorder(bpy.types.Operator):
    bl_idname = "mesh.fill_quad_border"
    bl_label = "Fill Quad Border"
    bl_description = "Fill boundary edges with quad topology using inset border technique"
    bl_options = {"REGISTER", "UNDO"}

    inset_thickness: FloatProperty(
        name="Border Inset Thickness",
        description="Thickness of the inset border",
        default=0.05,
        min=0.001,
        max=1.0,
    )

    keep_original: BoolProperty(
        name="Keep Original Border",
        description="Keep the original border mesh after creating the filled panel",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == "MESH" and obj.mode == "EDIT"

    def execute(self, context):
        bpy.ops.ed.undo_push(message="Fill Quad Border")

        original_mode = context.active_object.mode
        if original_mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")

        obj = context.active_object
        if not obj or obj.type != "MESH":
            self.report({"ERROR"}, "Active object is not a mesh")
            return {"CANCELLED"}

        # Duplicate the object to work on
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.duplicate()
        working_obj = context.active_object

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

        # Name the working object
        if panel_name and panel_name.strip():
            working_obj.name = f"{panel_name}_FilledQuad_{panel_count}"
        else:
            working_obj.name = f"FilledQuad_{panel_count}"

        # Switch to edit mode
        bpy.ops.object.mode_set(mode="EDIT")

        # Select all vertices
        bpy.ops.mesh.select_all(action="SELECT")

        try:
            # Create a face from the border edges
            bpy.ops.mesh.edge_face_add()

            # Switch to face selection mode
            bpy.ops.mesh.select_mode(type="FACE")

            # Inset the face
            bpy.ops.mesh.inset(thickness=self.inset_thickness, depth=0)

            # Delete the inner face
            bpy.ops.mesh.delete(type="FACE")

            # Switch back to vertex selection mode
            bpy.ops.mesh.select_mode(type="VERT")

            # Select all vertices
            bpy.ops.mesh.select_all(action="SELECT")

            # Triangulate the face
            bpy.ops.mesh.quads_convert_to_tris(
                quad_method="BEAUTY", ngon_method="BEAUTY"
            )

            # Convert triangles back to quads for cleaner topology
            bpy.ops.mesh.tris_convert_to_quads()

            # Return to object mode
            bpy.ops.object.mode_set(mode="OBJECT")

            # Add to proper collection
            add_object_to_panel_collection(working_obj, panel_count, panel_name)

            # Handle the original object
            if not self.keep_original:
                # Delete the original object
                bpy.data.objects.remove(obj, do_unlink=True)
            else:
                # Hide the original object
                obj.hide_viewport = True

            # Select the new object
            bpy.ops.object.select_all(action="DESELECT")
            working_obj.select_set(True)
            context.view_layer.objects.active = working_obj

            self.report(
                {"INFO"}, f"Successfully created filled quad panel: {working_obj.name}"
            )
            return {"FINISHED"}

        except Exception as e:
            self.report({"ERROR"}, f"Failed to create quad fill: {str(e)}")
            # Clean up the working object if operation failed
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.data.objects.remove(working_obj, do_unlink=True)
            # Restore original selection
            obj.select_set(True)
            context.view_layer.objects.active = obj
            # Restore original mode
            bpy.ops.object.mode_set(mode=original_mode)
            return {"CANCELLED"}


# Registration
classes = [MESH_OT_FillQuadBorder]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
