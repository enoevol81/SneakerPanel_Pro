
import bmesh
import bpy
from bpy.types import Operator
from mathutils import Vector


class OBJECT_OT_DefineToe(Operator):
    bl_idname = "object.define_toe"
    bl_label = "Define Toe"
    bl_description = "Place toe tip marker at cursor position"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        bpy.ops.ed.undo_push(message="Define Toe Tip")

        # Get the 3D cursor position
        cursor_location = context.scene.cursor.location.copy()

        # Check if toe marker already exists
        toe_marker = bpy.data.objects.get("Toe_Marker")

        if toe_marker:
            # Update existing marker
            toe_marker.location = cursor_location
            self.report({"INFO"}, "Toe tip marker updated.")
        else:
            # Create new toe marker
            toe_marker = bpy.data.objects.new("Toe_Marker", None)
            toe_marker.empty_display_type = "SPHERE"
            toe_marker.empty_display_size = 0.15
            toe_marker.color = (1.0, 0.0, 0.0, 1.0)  # Red for toe tip
            context.collection.objects.link(toe_marker)
            toe_marker.location = cursor_location
            self.report({"INFO"}, "Toe tip marker created.")

        return {"FINISHED"}


class OBJECT_OT_DefineUpDirection(Operator):
    bl_idname = "object.define_up_direction"
    bl_label = "Define Up Direction"
    bl_description = "Place direction marker at cursor position"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        bpy.ops.ed.undo_push(message="Define Up Direction")

        # Get the 3D cursor position
        cursor_location = context.scene.cursor.location.copy()

        # Check if direction marker already exists
        direction_marker = bpy.data.objects.get("Toe_Direction_Marker")

        if direction_marker:
            # Update existing marker
            direction_marker.location = cursor_location
            self.report({"INFO"}, "Up direction marker updated.")
        else:
            # Create new direction marker
            direction_marker = bpy.data.objects.new("Toe_Direction_Marker", None)
            direction_marker.empty_display_type = "SINGLE_ARROW"
            direction_marker.empty_display_size = 0.2
            direction_marker.color = (0.0, 1.0, 0.0, 1.0)  # Green for direction
            context.collection.objects.link(direction_marker)
            direction_marker.location = cursor_location
            self.report({"INFO"}, "Up direction marker created.")

        return {"FINISHED"}


# Registration
classes = [OBJECT_OT_DefineToe, OBJECT_OT_DefineUpDirection]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
