
import bpy

from ..utils.collections import add_object_to_panel_collection, get_panel_collection
from ..utils.panel_utils import update_stabilizer


class OBJECT_OT_AddGPDraw(bpy.types.Operator):

    bl_idname = "object.add_gp_draw"
    bl_label = "Add GPDraw Grease Pencil"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def execute(self, context):
        bpy.ops.ed.undo_push(message="Add Grease Pencil")

        bpy.context.tool_settings.use_mesh_automerge = True
        bpy.ops.object.grease_pencil_add(location=(0, 0, 0))
        gp_obj = context.active_object

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

        if panel_name and panel_name.strip():
            gp_obj.name = f"{panel_name}_GPDraw_{panel_count}"
        else:
            gp_obj.name = f"GPDraw_{panel_count}"

        add_object_to_panel_collection(gp_obj, panel_count, panel_name)

        bpy.ops.object.mode_set(mode="PAINT_GREASE_PENCIL")
        context.scene.tool_settings.gpencil_stroke_placement_view3d = "SURFACE"
        context.scene.tool_settings.use_gpencil_automerge_strokes = True

        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
        brush = bpy.context.tool_settings.gpencil_paint.brush

        if brush:
            brush.use_smooth_stroke = context.scene.spp_use_stabilizer
            brush.smooth_stroke_factor = context.scene.spp_stabilizer_factor
            brush.smooth_stroke_radius = context.scene.spp_stabilizer_radius

        self.report(
            {"INFO"},
            f"Grease Pencil object '{gp_obj.name}' created and ready to draw on surface.",
        )
        return {"FINISHED"}


# Registration
classes = [OBJECT_OT_AddGPDraw]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
